"""Recria o conjunto de dados que treinou o modelo 1.0.0 e confere que é o mesmo.

O dataset.jsonl nunca foi versionado (só o gerador). Como o gerador usa
semente fixa, ele pode ser recriado a partir do commit em que foi usado
(55613ea, 27/07/2026; o modelo 1.0.0 foi treinado em 08/09/2026, sem mudança
no gerador entre as duas datas).

Prova de que é o mesmo conjunto: refazendo a divisão do notebook de treino
(70/15/15, estratificada, random_state=42) e o vocabulário (frequência mínima
2 no treino), o vocabulário sai IDÊNTICO ao gravado no modelo 1.0.0.

Gera o relatório com as estatísticas do TCC (seção 5.2, Tabelas 2 e 3) e a
taxa de palavras do teste real fora do vocabulário.

Uso (na raiz do repositório, com o histórico do git disponível):
    python "ia training/reproduzir_dataset_v1.0.0.py" \
        --modelo "ia training/modelos/intellix_nlu_v1.0.0_2026-09-08.pt" \
        --saida docs/evidencias/
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import io
import json
import statistics
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import torch
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parent.parent
COMMIT_GERADOR = "55613ea"
ENTIDADES = ["PERIODO", "CANAL", "PAGAMENTO", "NUMERO", "CATEGORIA", "PRODUTO", "VENDEDOR", "CLIENTE", "DATA"]


def recriar_dataset(destino: Path) -> Path:
    tar = subprocess.run(["git", "archive", COMMIT_GERADOR, "ia training"], cwd=RAIZ,
                         capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as arquivo:
        arquivo.extractall(destino, filter="data")
    pasta = destino / "ia training"
    subprocess.run([sys.executable, "gerar_dataset.py"], cwd=pasta, check=True, capture_output=True)
    return pasta / "dados" / "dataset.jsonl"


def trechos(ex: dict) -> list[tuple[str, str]]:
    """Entidades completas (tipo, texto) de um exemplo anotado em BIO."""
    saida, atual = [], None
    for token, tag in zip(ex["tokens"], ex["tags"], strict=False):
        if tag.startswith("B-"):
            atual = [tag[2:], [token]]
            saida.append(atual)
        elif tag.startswith("I-") and atual and atual[0] == tag[2:]:
            atual[1].append(token)
        else:
            atual = None
    return [(ent, " ".join(palavras)) for ent, palavras in saida]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--modelo", default=str(RAIZ / "ia training" / "modelos" / "intellix_nlu_v1.0.0_2026-09-08.pt"))
    ap.add_argument("--teste", default=str(RAIZ / "ia training" / "teste_manual.jsonl"))
    ap.add_argument("--saida", default=str(RAIZ / "docs" / "evidencias"))
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        dados = [json.loads(linha) for linha in recriar_dataset(Path(tmp)).read_text(encoding="utf-8").splitlines()]

    rotulos = [d["intencao"] for d in dados]
    treino, _ = train_test_split(dados, test_size=0.30, random_state=42, stratify=rotulos)
    contagem = collections.Counter(t for ex in treino for t in ex["tokens"])
    vocab = {p for p, n in contagem.items() if n >= 2}
    modelo = torch.load(args.modelo, map_location="cpu", weights_only=False)
    vocab_modelo = set(modelo["vocab"]) - {"<PAD>", "<UNK>"}

    por_intencao = collections.Counter(rotulos)
    tags = collections.Counter(t for ex in dados for t in ex["tags"])
    tamanhos = [len(ex["tokens"]) for ex in dados]
    teste = [json.loads(linha) for linha in Path(args.teste).read_text(encoding="utf-8").splitlines() if linha.strip()]
    palavras = {t for ex in teste for t in ex["tokens"]}
    fora = sorted(t for t in palavras if t not in modelo["vocab"])
    b = {e: tags[f"B-{e}"] for e in ENTIDADES}
    ordem = sorted(ENTIDADES, key=lambda e: -b[e])
    valores_treino = collections.defaultdict(set)
    valores_teste = collections.defaultdict(set)
    for ex in dados:
        for ent, valor in trechos(ex):
            valores_treino[ent].add(valor)
    for ex in teste:
        for ent, valor in trechos(ex):
            valores_teste[ent].add(valor)
    palavras_de_entidade = {p for vs in valores_teste.values() for v in vs for p in v.split()}
    fora_em_entidade = sorted(set(fora) & palavras_de_entidade)

    linhas = [
        "# Conjunto de dados do modelo 1.0.0 (recriado)",
        "",
        f"- **Data:** {dt.datetime.now().astimezone():%d/%m/%Y %H:%M}",
        f"- **Gerador:** `ia training/gerar_dataset.py` e `moldes.py` do commit `{COMMIT_GERADOR}` (semente fixa)",
        f"- **Modelo comparado:** `{Path(args.modelo).relative_to(RAIZ).as_posix()}` (treinado em {modelo['data']})",
        "- **Script:** `ia training/reproduzir_dataset_v1.0.0.py`",
        "",
        "## Prova de identidade",
        "",
        "Divisão do notebook de treino (70/15/15, estratificada por intenção, `random_state=42`) e vocabulário",
        "com frequência mínima 2 no subconjunto de treino:",
        "",
        "| | Recriado | Gravado no modelo 1.0.0 |",
        "|---|---:|---:|",
        f"| Exemplos de treino | {len(treino)} | {modelo['treino']['n_treino']} |",
        f"| Vocabulário (com `<PAD>` e `<UNK>`) | {len(vocab) + 2} | {len(modelo['vocab'])} |",
        f"| Vocabulários idênticos | {'sim' if vocab == vocab_modelo else 'NÃO'} | |",
        "",
        "## Estatísticas (seção 5.2 do TCC)",
        "",
        f"- Exemplos: **{len(dados)}**; intenções: {len(por_intencao)}; etiquetas usadas: {len(tags)}",
        f"- Tamanho das frases: mínimo {min(tamanhos)}, média **{statistics.mean(tamanhos):.1f}**, máximo {max(tamanhos)} tokens",
        "",
        "### Exemplos por intenção (Tabela 2)",
        "",
        "| Intenção | Exemplos |",
        "|---|---:|",
        *[f"| {k} | {v} |" for k, v in sorted(por_intencao.items())],
        "",
        "### Etiquetas de entidade (Tabela 3)",
        "",
        "| Entidade | Início (B) | Continuação (I) |",
        "|---|---:|---:|",
        *[f"| {e} | {b[e]} | {tags[f'I-{e}']} |" for e in ordem],
        "",
        f"Razão entre a entidade mais frequente e a segunda: {b[ordem[0]] / b[ordem[1]]:.1f} vezes.",
        "",
        "## Teste real: palavras fora do vocabulário",
        "",
        f"{len(fora)} de {len(palavras)} palavras distintas do `teste_manual.jsonl` ({100 * len(fora) / len(palavras):.1f}%)",
        "não estão no vocabulário do modelo 1.0.0:",
        "",
        ", ".join(fora),
        "",
        f"Dessas, {len(fora_em_entidade)} fazem parte de algum valor de entidade anotado no teste"
        + (f": {', '.join(fora_em_entidade)}." if fora_em_entidade else "."),
        "",
        "## Teste real: valores de entidade já vistos no treino",
        "",
        "Valores distintos de cada entidade anotados no `teste_manual.jsonl` e quantos deles também aparecem,",
        "com a mesma grafia, como valor da mesma entidade no conjunto de treino:",
        "",
        "| Entidade | Valores no treino | Valores no teste | Do teste presentes no treino |",
        "|---|---:|---:|---:|",
        *[f"| {e} | {len(valores_treino[e])} | {len(valores_teste[e])} | "
          f"{len(valores_teste[e] & valores_treino[e])} |" for e in ordem],
        "",
    ]
    destino = Path(args.saida) / f"dataset_v1.0.0_{dt.datetime.now().astimezone():%Y-%m-%d}.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")
    print(f"vocabulário idêntico: {vocab == vocab_modelo} · relatório: {destino}")


if __name__ == "__main__":
    main()
