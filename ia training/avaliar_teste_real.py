"""Avalia modelos de NLU no conjunto de teste real (frases escritas à mão).

Mede, para cada .pt informado, as métricas do Quadro 12 do TCC:
  - acurácia de intenção e precisão/revocação/F1 por intenção (scikit-learn);
  - F1 de entidades por entidade completa (seqeval), micro, macro e ponderada;
  - matriz de confusão (linhas = intenção verdadeira, colunas = prevista).

Mesmo procedimento do notebook de treino (Intellix_NLU_Colab.ipynb): os
tokens e as tags vêm prontos do arquivo de teste e entram direto no modelo,
sem tokenizar de novo, para a comparação ser idêntica à do treino.

Também mede o subconjunto com "revisar": false, as frases cuja anotação de
entidades foi marcada como conferida.

Uso (na raiz do repositório):
    python "ia training/avaliar_teste_real.py" \
        --teste "ia training/teste_manual.jsonl" \
        --modelos backend/app/nlu/intellix_nlu_v1.2.0.pt [outro.pt ...] \
        --saida docs/evidencias/
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import torch
from seqeval.metrics import classification_report as relatorio_entidades
from seqeval.metrics import f1_score, precision_score, recall_score
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
from app.nlu.modelo_nlu import ModeloIntellix  # noqa: E402


def carregar(caminho: Path) -> list[dict]:
    return [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines() if linha.strip()]


def prever(modelo: ModeloIntellix, exemplos: list[dict]):
    intencoes, tags = [], []
    for ex in exemplos:
        ids = [modelo.vocab.get(t, modelo.vocab["<UNK>"]) for t in ex["tokens"]]
        with torch.no_grad():
            logits_i, logits_t = modelo.modelo(torch.tensor([ids]))
        intencoes.append(modelo.id2intent[int(logits_i.argmax(1)[0])])
        tags.append([modelo.id2tag[i] for i in logits_t.argmax(-1)[0].tolist()])
    return intencoes, tags


def metricas(exemplos, intencoes_prev, tags_prev) -> dict:
    y = [ex["intencao"] for ex in exemplos]
    gold_tags = [ex["tags"] for ex in exemplos]
    rotulos = sorted(set(y))
    p, r, f, n = precision_recall_fscore_support(y, intencoes_prev, labels=rotulos, zero_division=0)
    _, _, f_macro, _ = precision_recall_fscore_support(y, intencoes_prev, average="macro", zero_division=0)
    return {
        "n": len(exemplos),
        "acuracia_intencao": accuracy_score(y, intencoes_prev),
        "f1_intencao_macro": f_macro,
        "por_intencao": {
            rot: {"precisao": p[i], "revocacao": r[i], "f1": f[i], "n": int(n[i])} for i, rot in enumerate(rotulos)
        },
        "f1_entidades_micro": f1_score(gold_tags, tags_prev),
        "f1_entidades_macro": f1_score(gold_tags, tags_prev, average="macro"),
        "f1_entidades_ponderada": f1_score(gold_tags, tags_prev, average="weighted"),
        "precisao_entidades_micro": precision_score(gold_tags, tags_prev),
        "revocacao_entidades_micro": recall_score(gold_tags, tags_prev),
        "relatorio_entidades": relatorio_entidades(gold_tags, tags_prev, digits=3, zero_division=0),
        "rotulos": rotulos,
        "matriz": confusion_matrix(y, intencoes_prev, labels=rotulos).tolist(),
        "erros": [
            (ex["texto"], ex["intencao"], prev)
            for ex, prev in zip(exemplos, intencoes_prev)
            if ex["intencao"] != prev
        ],
    }


def pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def num(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def relatorio(caminho_teste: Path, resultados: list[tuple[str, dict, dict]]) -> str:
    agora = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    linhas = [
        "# Avaliação dos modelos no conjunto de teste real",
        "",
        f"- **Data:** {agora}",
        f"- **Conjunto:** `{caminho_teste.as_posix()}` ({resultados[0][1]['n']} frases escritas à mão, "
        "10 por intenção). Confira se alguma também aparece no treino: o gerador tem semente fixa.",
        "- **Procedimento:** o mesmo do notebook de treino (tokens e tags do arquivo entram direto no "
        "modelo); intenção com scikit-learn, entidades por entidade completa com seqeval.",
        "- **Script:** `ia training/avaliar_teste_real.py`",
        "",
        "## Resumo",
        "",
        "| Modelo | Acurácia de intenção | F1 de intenção (macro) | F1 de entidades (micro) | "
        "Precisão / revocação de entidades | Só frases conferidas: acurácia · F1 entidades |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for versao, m, c in resultados:
        linhas.append(
            f"| {versao} | **{pct(m['acuracia_intencao'])}** | {num(m['f1_intencao_macro'])} | "
            f"**{num(m['f1_entidades_micro'])}** | {num(m['precisao_entidades_micro'])} / "
            f"{num(m['revocacao_entidades_micro'])} | {pct(c['acuracia_intencao'])} · "
            f"{num(c['f1_entidades_micro'])} (n={c['n']}) |"
        )
    for versao, m, _ in resultados:
        linhas += ["", f"## Modelo {versao}", "", "### Por intenção", "",
                   "| Intenção | Precisão | Revocação | F1 |", "|---|---:|---:|---:|"]
        for rot, v in m["por_intencao"].items():
            linhas.append(f"| {rot} | {num(v['precisao'])} | {num(v['revocacao'])} | {num(v['f1'])} |")
        linhas += ["", "### Matriz de confusão (linhas = verdadeira, colunas = prevista)", ""]
        abrev = [r[:10] for r in m["rotulos"]]
        linhas.append("| | " + " | ".join(abrev) + " |")
        linhas.append("|---|" + "---:|" * len(abrev))
        for rot, linha in zip(m["rotulos"], m["matriz"]):
            linhas.append(f"| {rot} | " + " | ".join(str(v) for v in linha) + " |")
        linhas += ["", f"### Frases com intenção errada ({len(m['erros'])})", "",
                   "| Frase | Verdadeira | Prevista |", "|---|---|---|"]
        linhas += [f"| {t} | {v} | {p} |" for t, v, p in m["erros"]]
        linhas += ["", "### Entidades (seqeval)", "", "```", m["relatorio_entidades"].rstrip(), "```"]
    return "\n".join(linhas) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--teste", default=str(RAIZ / "ia training" / "teste_manual.jsonl"))
    ap.add_argument("--modelos", nargs="+", required=True)
    ap.add_argument("--saida", default=str(RAIZ / "docs" / "evidencias"))
    args = ap.parse_args()

    caminho_teste = Path(args.teste)
    exemplos = carregar(caminho_teste)
    conferidos = [ex for ex in exemplos if not ex.get("revisar")]
    resultados = []
    for caminho in args.modelos:
        modelo = ModeloIntellix(caminho)
        intencoes, tags = prever(modelo, exemplos)
        m = metricas(exemplos, intencoes, tags)
        idx = [i for i, ex in enumerate(exemplos) if not ex.get("revisar")]
        c = metricas(conferidos, [intencoes[i] for i in idx], [tags[i] for i in idx])
        resultados.append((modelo.versao, m, c))
        print(f"{modelo.versao}: acurácia {pct(m['acuracia_intencao'])} · F1 entidades {num(m['f1_entidades_micro'])}")

    destino = Path(args.saida) / f"avaliacao_teste_real_{dt.datetime.now():%Y-%m-%d_%H%M}.md"
    destino.write_text(relatorio(caminho_teste.relative_to(RAIZ) if caminho_teste.is_absolute() and RAIZ in caminho_teste.parents else caminho_teste, resultados), encoding="utf-8")
    print(f"Relatório: {destino}")


if __name__ == "__main__":
    main()
