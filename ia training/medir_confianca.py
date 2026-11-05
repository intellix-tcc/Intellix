# -*- coding: utf-8 -*-
"""
medir_confianca.py — mede o comportamento do limiar de confiança e do filtro de
domínio (feedback TC2 F05: "confiança alta e SQL fixo não garantem interpretação
correta" — medir aceitação indevida fora de domínio, a margem entre intenções e
o custo do filtro léxico contra paráfrases válidas sem palavra-chave).

O limiar vem de backend/app/fallbacks.py (CONFIANCA_MINIMA = 0,70). Uma pergunta
é ACEITA quando: o modelo não dá fallback, a confiança >= limiar E o texto passa
no filtro de domínio (adaptador_modelo._tem_termo_dominio). Tudo offline.
"""

import statistics
import sys
from pathlib import Path

import torch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "scripts"))

from avaliar_100_perguntas import ler_perguntas, ARQ_PERGUNTAS, FORA_DE_ESCOPO, PARAM_FALTANDO, SEM_RESULTADO  # noqa: E402
from app.nlu import adaptador_modelo as AD  # noqa: E402
from app.nlu.modelo_nlu import ModeloIntellix, tokenizar  # noqa: E402

# Perguntas VÁLIDAS de vendas, mas redigidas SEM as palavras-chave óbvias do
# filtro de domínio — para medir se o filtro rejeita pergunta boa (custo).
VALIDAS_SEM_PALAVRA_CHAVE = [
    "como foi março em comparação com fevereiro",
    "o que saiu mais mês passado",
    "quem é o destaque do time esse ano",
    "o João está indo bem?",
    "me mostra os números de 2024",
    "qual o resumo do trimestre",
    "quanto entrou no caixa em março",
    "o azul vendeu mais que o vermelho?",
]

# Fora do domínio de vendas — deveriam ser rejeitadas (nunca aceitas).
FORA_EXTRA = [
    "qual a capital da França",
    "me conta uma piada",
    "que horas são",
    "qual a previsão do tempo amanhã",
    "quem descobriu o Brasil",
    "como faço um bolo de cenoura",
]


def _margem_e_conf(modelo, texto):
    """(confiança top1, margem top1-top2) — a margem mede o quão 'sozinha' a
    classe vencedora ficou; margem pequena = decisão disputada."""
    toks = tokenizar(texto)
    if not toks:
        return 0.0, 0.0
    x = torch.tensor([[modelo.vocab.get(t, modelo.vocab["<UNK>"]) for t in toks]])
    with torch.no_grad():
        logits_i, _ = modelo.modelo(x)
    probs = torch.softmax(logits_i, dim=1)[0]
    top2 = torch.topk(probs, 2).values.tolist()
    return top2[0], top2[0] - top2[1]


def _aceita(modelo, texto, limiar):
    r = modelo.prever(texto)
    return (not r["fallback"]) and r["confianca"] >= limiar and AD._tem_termo_dominio(texto)


def main():
    modelo = ModeloIntellix(str(RAIZ / "backend/app/nlu/intellix_nlu_v1.1.0.pt"))
    perguntas = ler_perguntas(ARQ_PERGUNTAS)
    validas = [p["pergunta"] for p in perguntas
               if p["categoria"] not in (FORA_DE_ESCOPO, PARAM_FALTANDO, SEM_RESULTADO)]
    fora = [p["pergunta"] for p in perguntas if p["categoria"] == FORA_DE_ESCOPO] + FORA_EXTRA

    L = ["# Confiança e filtro de domínio (TC2 F05)", "",
         "- Limiar atual (fallbacks.py): **0,70**",
         f"- Válidas (12 intenções): {len(validas)} · Fora de domínio: {len(fora)}", ""]

    # 1) Varredura do limiar: aceite correto nas válidas × aceite indevido fora.
    L += ["## Varredura do limiar", "",
          "| Limiar | Aceitas (válidas) | Aceite indevido (fora de domínio) |",
          "|---:|---:|---:|"]
    for limiar in (0.50, 0.60, 0.70, 0.80):
        acc_v = sum(_aceita(modelo, t, limiar) for t in validas)
        acc_f = sum(_aceita(modelo, t, limiar) for t in fora)
        L.append(f"| {limiar:.2f} | {acc_v}/{len(validas)} | {acc_f}/{len(fora)} |")

    # 2) Margem (top1-top2): o quão disputada é a decisão.
    mv = [_margem_e_conf(modelo, t)[1] for t in validas]
    mf = [_margem_e_conf(modelo, t)[1] for t in fora]
    L += ["", "## Margem entre intenções (top1 − top2)", "",
          "| Conjunto | Margem mediana | Margem mínima |", "|---|---:|---:|",
          f"| Válidas | {statistics.median(mv):.2f} | {min(mv):.2f} |",
          f"| Fora de domínio | {statistics.median(mf):.2f} | {min(mf):.2f} |",
          "", "Margem pequena numa pergunta aceita = candidata a pedir confirmação."]

    # 3) Custo do filtro de domínio: quantas VÁLIDAS sem palavra-chave ele barra.
    barradas = [t for t in VALIDAS_SEM_PALAVRA_CHAVE if not AD._tem_termo_dominio(t)]
    L += ["", "## Custo do filtro de domínio (paráfrases válidas sem palavra-chave)", "",
          f"- {len(barradas)}/{len(VALIDAS_SEM_PALAVRA_CHAVE)} perguntas válidas foram "
          f"barradas pelo filtro léxico (falso-negativo do filtro):"]
    L += [f"  - {t}" for t in barradas] or ["  (nenhuma)"]

    md = "\n".join(L) + "\n"
    saida = RAIZ / "docs" / "evidencias"
    saida.mkdir(parents=True, exist_ok=True)
    import datetime as dt
    destino = saida / f"confianca_filtro_{dt.datetime.now():%Y-%m-%d_%H%M}.md"
    destino.write_text(md, encoding="utf-8")
    print(md)
    print("Arquivo:", destino)


if __name__ == "__main__":
    main()
