# -*- coding: utf-8 -*-
"""
anotar.py — ajuda a etiquetar as frases que VOCÊS escreveram à mão.

POR QUE ISTO EXISTE
-------------------
O conjunto de TESTE tem que ser escrito por pessoas, não por molde. Mas
etiquetar BIO na mão é chato e dá erro. Este script faz o rascunho e vocês
só revisam.

COMO USAR
---------
1) Crie o arquivo dados/frases_cruas.txt, uma frase por linha, assim:

       total_vendas_periodo | oi, quanto que eu vendi mês passado?
       top_produtos         | qual foi o produto que mais saiu em abril
       ticket_medio         | quanto em média cada cliente deixa na loja

2) Rode:

       python anotar.py

3) Ele gera dados/teste_manual.jsonl com as tags já preenchidas.

4) ⚠️ REVISEM À MÃO. O script acerta a maioria, mas erra em coisas novas
   (um produto que não está em VALORES, por exemplo). Ele marca com "?"
   as frases que ele mesmo achou suspeitas — comecem por essas.

REGRA SAGRADA
-------------
As frases de dados/frases_cruas.txt NÃO PODEM ter saído dos moldes.
Escrevam como vocês perguntariam de verdade. Peçam pra mãe, pro tio que tem
loja, pra um amigo. Quanto mais "torto" e natural, mais honesto vai ser o
número que vocês colocam no TCC.
"""

import json
import re
from pathlib import Path

from gerar_dataset import tokenizar
from moldes import VALORES, INTENCOES

ENTRADA = Path("dados/frases_cruas.txt")
SAIDA = Path("dados/teste_manual.jsonl")

# Monta um dicionário: tokens do valor -> tipo da entidade.
# Ordena do maior para o menor para casar "cartão de crédito" antes de "cartão".
CATALOGO: list[tuple[list[str], str]] = []
for tipo, valores in VALORES.items():
    for valor in valores:
        toks = tokenizar(valor)
        if toks:
            CATALOGO.append((toks, tipo.upper()))
CATALOGO.sort(key=lambda x: -len(x[0]))


def pre_etiquetar(frase: str) -> tuple[list[str], list[str], bool]:
    """Devolve (tokens, tags, suspeita)."""
    tokens = tokenizar(frase)
    tags = ["O"] * len(tokens)

    i = 0
    while i < len(tokens):
        casou = False
        for valor_toks, tipo in CATALOGO:
            n = len(valor_toks)
            if tokens[i:i + n] == valor_toks and all(t == "O" for t in tags[i:i + n]):
                tags[i] = f"B-{tipo}"
                for k in range(1, n):
                    tags[i + k] = f"I-{tipo}"
                i += n
                casou = True
                break
        if not casou:
            i += 1

    # heurística: número solto que não foi pego vira NUMERO
    for i, tok in enumerate(tokens):
        if tags[i] == "O" and re.fullmatch(r"\d+", tok):
            tags[i] = "B-NUMERO"

    # marca como suspeita se não achou entidade nenhuma
    # (quase toda pergunta real tem pelo menos um período)
    suspeita = all(t == "O" for t in tags)
    return tokens, tags, suspeita


def main():
    if not ENTRADA.exists():
        ENTRADA.parent.mkdir(parents=True, exist_ok=True)
        ENTRADA.write_text(
            "# Uma frase por linha, no formato:  intencao | frase\n"
            "# Apague estas linhas de comentário e escreva as suas.\n"
            "total_vendas_periodo | oi, quanto que eu vendi mês passado?\n",
            encoding="utf-8",
        )
        print(f"📝 Criei {ENTRADA} com um exemplo. Escreva as frases lá e rode de novo.")
        return

    saida, suspeitas, invalidas = [], 0, 0

    for n, linha in enumerate(ENTRADA.read_text(encoding="utf-8").splitlines(), 1):
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if "|" not in linha:
            print(f"⚠️  linha {n}: falta o '|' -> {linha!r}")
            invalidas += 1
            continue

        intencao, frase = (p.strip() for p in linha.split("|", 1))
        if intencao not in INTENCOES:
            print(f"⚠️  linha {n}: intenção '{intencao}' não existe")
            invalidas += 1
            continue

        tokens, tags, suspeita = pre_etiquetar(frase)
        if suspeita:
            suspeitas += 1
        saida.append({
            "texto": " ".join(tokens),
            "intencao": intencao,
            "tokens": tokens,
            "tags": tags,
            "origem": "manual",
            "revisar": suspeita,
        })

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8") as f:
        for ex in saida:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\n✅ {len(saida)} frases etiquetadas em {SAIDA}")
    if invalidas:
        print(f"⚠️  {invalidas} linha(s) ignorada(s) por erro de formato")
    print(f"🔍 {suspeitas} frase(s) marcadas com \"revisar\": true — comecem por elas")

    por_intencao = {}
    for ex in saida:
        por_intencao[ex["intencao"]] = por_intencao.get(ex["intencao"], 0) + 1
    print("\nFrases por intenção (a meta é 10 de cada):")
    for intencao in INTENCOES:
        n = por_intencao.get(intencao, 0)
        marca = "✅" if n >= 10 else "❌"
        print(f"  {marca} {intencao:<24} {n}")

    print("\n--- Confira estas 3 ---")
    for ex in saida[:3]:
        print(f"\n  {ex['intencao']}")
        for tok, tag in zip(ex["tokens"], ex["tags"]):
            print(f"    {'->' if tag != 'O' else '  '} {tok:<16} {tag}")
    print("\n👉 Agora rode: python validar_dataset.py dados/teste_manual.jsonl")


if __name__ == "__main__":
    main()
