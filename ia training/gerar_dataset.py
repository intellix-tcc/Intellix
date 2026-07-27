# -*- coding: utf-8 -*-
"""
gerar_dataset.py — transforma os moldes em milhares de exemplos etiquetados.

COMO USAR
---------
    python gerar_dataset.py

Ele lê moldes.py e escreve dados/dataset.jsonl

Vocês quase nunca precisam mexer neste arquivo. O que vocês editam é moldes.py.
"""

import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

from moldes import MOLDES, VALORES, INTENCOES, TAGS

SEMENTE = 42                 # deixa o resultado sempre igual (reprodutibilidade do TCC)
VARIACOES_POR_MOLDE = 60     # quantas frases gerar de cada molde
POR_INTENCAO = 400           # teto: todas as intenções ficam com este tamanho
SAIDA = Path("dados/dataset.jsonl")

random.seed(SEMENTE)


# =============================================================================
# TOKENIZADOR — A PEÇA MAIS IMPORTANTE DO PROJETO
# =============================================================================
# ⚠️ ATENÇÃO: esta função tem que ser usada em TRÊS lugares:
#    1. aqui, ao gerar o dataset
#    2. no treino
#    3. no backend, na hora de responder o usuário de verdade
# Se os três usarem tokenizadores diferentes, o modelo funciona no teste
# e falha em produção. É um bug clássico e silencioso.

def normalizar(texto: str) -> str:
    """Padroniza o texto. NÃO tira acento — acento importa em português."""
    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)          # espaços duplos viram um só
    # normalização unicode: garante que "ç" digitado de dois jeitos vire o mesmo
    texto = unicodedata.normalize("NFC", texto)
    abreviacoes = {
        "qnt": "quanto", "qto": "quanto", "qtd": "quantidade",
        "qtas": "quantas", "qts": "quantos", "vlr": "valor",
        "tkt": "ticket", "fat": "faturamento", "pq": "porque",
        "vc": "você", "q": "que", "pra": "para", "pro": "para o",
    }
    palavras = [abreviacoes.get(p, p) for p in texto.split()]
    return " ".join(palavras)


def tokenizar(texto: str) -> list[str]:
    """
    Quebra a frase em tokens, separando pontuação.

        "quanto faturei em março?"  ->  ['quanto','faturei','em','março','?']

    Repare que o '?' vira um token separado. Se não fizesse isso,
    'março?' seria uma palavra diferente de 'março' e o modelo se perderia.
    """
    return re.findall(r"\w+|[^\w\s]", normalizar(texto), re.UNICODE)


# =============================================================================
# GERADOR
# =============================================================================

PADRAO_SLOT = re.compile(r"(\{[a-zà-ú_]+\d*\})")


def tipo_do_slot(slot: str) -> str:
    """{periodo2} -> 'periodo'   |   {canal} -> 'canal'"""
    return re.sub(r"\d+$", "", slot.strip("{}"))


def gerar_exemplo(intencao: str, molde: str) -> dict | None:
    """Preenche um molde e devolve tokens + tags BIO alinhados."""
    tokens: list[str] = []
    tags: list[str] = []
    usados: dict[str, set] = {}

    for parte in PADRAO_SLOT.split(molde):
        if not parte.strip():
            continue

        if parte.startswith("{") and parte.endswith("}"):
            tipo = tipo_do_slot(parte)
            if tipo not in VALORES:
                raise KeyError(
                    f"Slot '{parte}' do molde '{molde}' não existe em VALORES. "
                    f"Slots válidos: {sorted(VALORES)}"
                )
            # sorteia um valor diferente dos já usados do mesmo tipo na frase
            # (evita 'vendi mais em março ou março')
            disponiveis = [v for v in VALORES[tipo] if v not in usados.get(tipo, set())]
            if not disponiveis:
                return None
            valor = random.choice(disponiveis)
            usados.setdefault(tipo, set()).add(valor)

            toks = tokenizar(valor)
            if not toks:
                return None
            tokens += toks
            tags += [f"B-{tipo.upper()}"] + [f"I-{tipo.upper()}"] * (len(toks) - 1)

        else:
            toks = tokenizar(parte)
            tokens += toks
            tags += ["O"] * len(toks)

    if not tokens:
        return None

    return {
        "texto": " ".join(tokens),
        "intencao": intencao,
        "tokens": tokens,
        "tags": tags,
        "origem": "molde",
    }


def gerar_tudo() -> list[dict]:
    exemplos = []
    for intencao, lista_moldes in MOLDES.items():
        for molde in lista_moldes:
            for _ in range(VARIACOES_POR_MOLDE):
                ex = gerar_exemplo(intencao, molde)
                if ex:
                    exemplos.append(ex)

    # tira frases repetidas (moldes sem slot geram sempre a mesma frase)
    unicos = {}
    for ex in exemplos:
        unicos[(ex["texto"], ex["intencao"])] = ex
    exemplos = list(unicos.values())

    # ---- BALANCEAMENTO ----
    # Moldes com dois buracos ({periodo} e {periodo2}) geram muito mais
    # combinações que moldes sem buraco nenhum. Sem corrigir isso, uma intenção
    # fica com 750 exemplos e outra com 330, e o modelo aprende a "chutar" a
    # intenção maior quando tem dúvida. Aqui cortamos todas no mesmo tamanho.
    por_intencao: dict[str, list] = {}
    for ex in exemplos:
        por_intencao.setdefault(ex["intencao"], []).append(ex)

    balanceado = []
    for intencao, lista in por_intencao.items():
        random.shuffle(lista)
        if len(lista) < POR_INTENCAO:
            print(f"  ⚠️  '{intencao}' só tem {len(lista)} exemplos (meta: {POR_INTENCAO}). "
                  f"Escreva mais moldes ou mais valores para ela.")
        balanceado += lista[:POR_INTENCAO]

    return balanceado


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    dataset = gerar_tudo()
    random.shuffle(dataset)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8") as f:
        for ex in dataset:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    # ---- Relatório ----
    print(f"\n✅ {len(dataset)} exemplos únicos gerados em {SAIDA}\n")

    por_intencao = Counter(ex["intencao"] for ex in dataset)
    print("Exemplos por intenção (o ideal é estarem parecidos entre si):")
    for intencao in INTENCOES:
        n = por_intencao[intencao]
        barra = "█" * (n // 10)
        print(f"  {intencao:<24} {n:>4}  {barra}")

    menor, maior = min(por_intencao.values()), max(por_intencao.values())
    print(f"\n  Menor: {menor} | Maior: {maior} | Razão: {maior/menor:.2f}x")
    if maior / menor > 1.6:
        print("  ⚠️  Desbalanceado. Escreva mais moldes para as intenções de baixo.")
    else:
        print("  ✅ Balanceamento OK.")

    print("\nTags de entidade encontradas:")
    tags_vistas = Counter(t for ex in dataset for t in ex["tags"] if t != "O")
    for tag, n in sorted(tags_vistas.items()):
        print(f"  {tag:<14} {n:>5}")
    faltando = [t for t in TAGS if t != "O" and t not in tags_vistas]
    if faltando:
        print(f"\n  ⚠️  Tags SEM NENHUM exemplo: {faltando}")
        print("      O modelo nunca vai aprender essas. Escreva moldes que as usem.")

    print("\n--- 5 exemplos sorteados ---")
    for ex in random.sample(dataset, 5):
        print(f"\n  intenção: {ex['intencao']}")
        for tok, tag in zip(ex["tokens"], ex["tags"]):
            marca = "  " if tag == "O" else "->"
            print(f"    {marca} {tok:<16} {tag}")
