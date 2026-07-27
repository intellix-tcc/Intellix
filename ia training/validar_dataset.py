# -*- coding: utf-8 -*-
"""
validar_dataset.py — o "detector de bug" do dataset.

RODEM ISTO SEMPRE, antes de qualquer treino:

    python validar_dataset.py dados/dataset.jsonl
    python validar_dataset.py dados/teste_manual.jsonl

Se der ✅ em tudo, pode treinar. Se der ❌, conserta antes.
Treinar com dataset quebrado desperdiça horas e dá resultado sem sentido.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from moldes import INTENCOES, TAGS


def carregar(caminho: Path) -> list[dict]:
    exemplos = []
    with caminho.open(encoding="utf-8") as f:
        for i, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                exemplos.append(json.loads(linha))
            except json.JSONDecodeError as e:
                print(f"❌ Linha {i}: JSON inválido — {e}")
                sys.exit(1)
    return exemplos


def validar(caminho: Path) -> bool:
    exemplos = carregar(caminho)
    erros: list[str] = []
    avisos: list[str] = []

    for i, ex in enumerate(exemplos, 1):
        # --- campos obrigatórios ---
        for campo in ("texto", "intencao", "tokens", "tags"):
            if campo not in ex:
                erros.append(f"linha {i}: falta o campo '{campo}'")
        if erros:
            continue

        # --- ERRO Nº1: tokens e tags de tamanhos diferentes ---
        if len(ex["tokens"]) != len(ex["tags"]):
            erros.append(
                f"linha {i}: {len(ex['tokens'])} tokens mas {len(ex['tags'])} tags "
                f"-> {ex['texto']!r}"
            )

        # --- intenção existe? ---
        if ex["intencao"] not in INTENCOES:
            erros.append(f"linha {i}: intenção desconhecida {ex['intencao']!r}")

        # --- tags existem? ---
        for tag in ex["tags"]:
            if tag not in TAGS:
                erros.append(f"linha {i}: tag desconhecida {tag!r}")

        # --- BIO bem formado: I-X só pode vir depois de B-X ou I-X ---
        anterior = "O"
        for j, tag in enumerate(ex["tags"]):
            if tag.startswith("I-"):
                tipo = tag[2:]
                if anterior not in (f"B-{tipo}", f"I-{tipo}"):
                    erros.append(
                        f"linha {i}: '{tag}' na posição {j} sem B-{tipo} antes "
                        f"-> {ex['texto']!r}"
                    )
            anterior = tag

        # --- frase vazia ou gigante ---
        if len(ex["tokens"]) == 0:
            erros.append(f"linha {i}: frase sem nenhum token")
        elif len(ex["tokens"]) > 40:
            avisos.append(f"linha {i}: frase com {len(ex['tokens'])} tokens (muito longa)")

    # --- duplicatas ---
    textos = Counter(ex.get("texto") for ex in exemplos)
    duplicadas = {t: n for t, n in textos.items() if n > 1}
    if duplicadas:
        avisos.append(f"{len(duplicadas)} frases repetidas (ex: {list(duplicadas)[:3]})")

    # --- mesma frase com intenções diferentes: isso é veneno para o modelo ---
    por_texto: dict[str, set] = {}
    for ex in exemplos:
        por_texto.setdefault(ex["texto"], set()).add(ex["intencao"])
    conflitos = {t: i for t, i in por_texto.items() if len(i) > 1}
    for texto, intencoes in list(conflitos.items())[:10]:
        erros.append(f"frase {texto!r} está etiquetada como {sorted(intencoes)} — escolha UMA")

    # --- cobertura ---
    intencoes_vistas = Counter(ex["intencao"] for ex in exemplos)
    sem_exemplo = [i for i in INTENCOES if i not in intencoes_vistas]
    if sem_exemplo:
        erros.append(f"intenções sem nenhum exemplo: {sem_exemplo}")

    tags_vistas = {t for ex in exemplos for t in ex["tags"]}
    tags_sem_exemplo = [t for t in TAGS if t not in tags_vistas]
    if tags_sem_exemplo:
        avisos.append(f"tags sem exemplo (o modelo nunca vai prever): {tags_sem_exemplo}")

    # =================== RELATÓRIO ===================
    print(f"\n{'='*60}")
    print(f"Validando: {caminho}")
    print(f"{'='*60}")
    print(f"Exemplos: {len(exemplos)}")
    print(f"Intenções: {len(intencoes_vistas)}/12")
    print(f"Tags usadas: {len(tags_vistas & set(TAGS))}/19")
    tam = [len(ex["tokens"]) for ex in exemplos if "tokens" in ex]
    if tam:
        print(f"Tamanho das frases: min {min(tam)} | média {sum(tam)/len(tam):.1f} | max {max(tam)}")

    if avisos:
        print(f"\n⚠️  {len(avisos)} aviso(s):")
        for a in avisos[:10]:
            print(f"   • {a}")

    if erros:
        print(f"\n❌ {len(erros)} ERRO(S) — conserte antes de treinar:")
        for e in erros[:20]:
            print(f"   • {e}")
        if len(erros) > 20:
            print(f"   ... e mais {len(erros)-20}")
        return False

    print("\n✅ Dataset válido. Pode treinar.")
    return True


if __name__ == "__main__":
    caminho = Path(sys.argv[1] if len(sys.argv) > 1 else "dados/dataset.jsonl")
    if not caminho.exists():
        print(f"❌ Arquivo não encontrado: {caminho}")
        sys.exit(1)
    sys.exit(0 if validar(caminho) else 1)
