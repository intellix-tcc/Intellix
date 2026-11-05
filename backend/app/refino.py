"""Refino da intenção: perguntas mais específicas sem retreinar o modelo.

O modelo continua escolhendo a intenção entre as 12 em que foi treinado. Aqui
só se ajusta o que a frase deixa explícito e o modelo não tem classe para:

  - "Qual foi o MÊS que mais vendeu (botas)?"  -> melhor_mes
    (o modelo diz "faturamento" ou "produtos mais vendidos"; a pessoa quer o mês)
  - "QUANTAS botas de couro vendemos?"          -> unidades_vendidas
    (peças, não pedidos: "quantas vendas" continua quantidade_vendas)
  - "Quanto vendi no PIX?" (modelo: vendas_por_pagamento) com o pix filtrado
    -> total_vendas_periodo filtrado. Uma rosca com uma fatia só, 100%, não
    responde nada; o total do recorte, com a evolução mês a mês, responde.
  - desempenho_vendedor com o vendedor achado no catálogo -> usa o nome exato.

Regras curtas, determinísticas e testadas (tests/test_refino.py). Se a frase
não bate com nenhuma, a interpretação do modelo segue intacta.
"""

from __future__ import annotations

import re

from app.fallbacks import CONFIANCA_MINIMA
from app.filtros import FILTROS, sem_acento
from app.models import Interpretacao
from app.nlu import regras as R
from app.nlu.adaptador_modelo import _periodo_relativo

_MES_EXTREMO = re.compile(
    r"\b(?:qual|que|em\s+que|em\s+qual)\s+(?:foi\s+|e\s+|era\s+)?(?:o\s+)?mes\b"
    r"|\b(?:melhor|pior)\s+mes\b"
    r"|\bmes\s+(?:que|com|de|em\s+que)\s+(?:a\s+gente\s+|eu\s+|nos\s+|mais\s+|menos\s+)?"
    r"(?:mais|menos|maior|menor|vend|fatur)",
)
_EXTREMO = re.compile(r"\b(?:mais|menos|maior|menor|melhor|pior|campe|recorde|pico|bombou)")
_MENOR = re.compile(r"\b(?:menos|menor|pior|fraco|baixo)\b")
_UNIDADES = re.compile(r"\bunidades?\b|\bpecas?\b|\bitens\b|\bquantidade\s+de\s+(?!vendas|pedidos)")
_QUANTAS_COISAS = re.compile(r"\bquant[oa]s\b(?!\s+(?:vendas?|pedidos?|transac|compras?|notas?|clientes?))")
_QUANTAS_PEDIDOS = re.compile(
    r"\bquant[oa]s\s+(?:vendas?|pedidos?|transac|compras?)"
    r"|\b(?:numero|quantidade)\s+de\s+(?:vendas|pedidos|transac)"
)
_DINHEIRO = re.compile(r"fatur|receita|r\$|\bvalor|dinheiro|\breais\b|quanto\s+(?:eu\s+|a\s+gente\s+)?vend")

# Intenção que é a "quebra" por uma dimensão -> filtros que a tornam trivial
# (ranking de produtos de UM produto, categorias de um produto, canais de UM canal).
QUEBRA_POR = {
    "top_produtos": {"produto"},
    "vendas_por_categoria": {"produto", "categoria"},
    "vendas_por_canal": {"canal"},
    "vendas_por_pagamento": {"forma_pagamento"},
    "top_clientes": {"cliente"},
}

_UM_PERIODO = ("periodo_inicio", "periodo_fim")


def pede_refino(t: str) -> bool:
    """A frase (sem acento, minúscula) pede o mês extremo ou unidades?
    Usado pelo contexto: "e qual mês vendeu mais?" é uma continuação válida."""
    return _pede_mes_extremo(t) or bool(_UNIDADES.search(t))


def _tem_item(ent: dict) -> bool:
    return bool(ent.get("produto") or ent.get("categoria"))


def _pede_mes_extremo(t: str) -> bool:
    return bool(_MES_EXTREMO.search(t) and _EXTREMO.search(t))


def _um_periodo(ent: dict) -> bool:
    return all(k in ent for k in _UM_PERIODO)


def _periodo_da_frase(t: str) -> dict:
    """Um período só, tirado da frase ("mês passado", "em 2025", "em março"),
    a partir de hoje (R.referencia()); o ano inteiro quando ela não diz."""
    return _periodo_relativo(t) or R._extrai_periodo(t, ano_completo_se_ausente=True)


def refinar(interp: Interpretacao, texto: str) -> Interpretacao:
    t = sem_acento(texto.lower())
    mes_extremo = _pede_mes_extremo(t)
    if not interp.intencao and not mes_extremo:
        return interp
    # O modelo não foi treinado em "qual mês" nem em "unidades": nessas frases
    # ele às vezes fica abaixo do limiar, ou aponta uma classe qualquer
    # ("qual o pior mês de 2025?" sai como desempenho_vendedor a 0,42). Quando
    # a frase pede isso com todas as letras, o refino assume.
    if interp.confianca < CONFIANCA_MINIMA or not interp.intencao:
        if not (mes_extremo or (_UNIDADES.search(t) and _um_periodo(interp.entidades))):
            return interp
        interp = interp.model_copy(update={
            "confianca": max(interp.confianca, CONFIANCA_MINIMA),
            "intencao": interp.intencao or "total_vendas_periodo",
        })
    ent = dict(interp.entidades)
    intencao = interp.intencao

    # 1) "qual mês mais/menos vendeu ..." — a classe melhor_mes do modelo (v1.2+)
    #    ou a frase explícita, qualquer que seja a classe que o modelo escolheu;
    #    o período vira um só (o modelo pode ter lido dois).
    if mes_extremo or intencao == "melhor_mes":
        if not _um_periodo(ent):
            ent = {k: v for k, v in ent.items() if not k.startswith("periodo_")}
            ent.update(_periodo_da_frase(t))
        ent.pop("vendedor_nome", None)
        por_unidades = (_tem_item(ent) or _UNIDADES.search(t)) and not re.search(r"fatur|receita", t)
        ent["metrica"] = "unidades" if por_unidades else "faturamento"
        ent["sentido"] = "menor" if _MENOR.search(t) else "maior"
        ent.pop("limite", None)
        # "qual o melhor mês" sobre um mês só não diz nada: olha o ano dele
        ini, fim = str(ent["periodo_inicio"]), str(ent["periodo_fim"])
        if ini[:7] == fim[:7]:
            ent["periodo_inicio"], ent["periodo_fim"] = f"{ini[:4]}-01-01", f"{ini[:4]}-12-31"
        intencao = "melhor_mes"

    # 2) a pergunta é a quebra por uma dimensão, mas já filtrou essa dimensão
    elif intencao in QUEBRA_POR and any(ent.get(k) for k in QUEBRA_POR[intencao]):
        ent.pop("limite", None)
        if "ticket" in t:
            intencao = "ticket_medio"  # "ticket médio no cartão de crédito"
        elif _QUANTAS_PEDIDOS.search(t):
            intencao = "quantidade_vendas"  # "quantas vendas no pix?"
        elif _QUANTAS_COISAS.search(t):
            intencao = "unidades_vendidas"  # "quantas botas pelo site?"
        else:
            intencao = "total_vendas_periodo"

    # 3a) o modelo leu "unidades", mas a frase conta pedidos: "quantidade de
    #     vendas", "quantos pedidos" -> quantidade_vendas
    elif intencao == "unidades_vendidas" and _QUANTAS_PEDIDOS.search(t):
        intencao = "quantidade_vendas"

    # 3) "quantas botas", "quantas unidades", "quantos itens"
    elif intencao in ("quantidade_vendas", "total_vendas_periodo", "top_produtos") and (
        _UNIDADES.search(t) or (_tem_item(ent) and _QUANTAS_COISAS.search(t) and not _DINHEIRO.search(t))
    ):
        ent.pop("limite", None)
        intencao = "unidades_vendidas"

    # desempenho_vendedor: o nome exato do catálogo é mais certeiro que a heurística
    if intencao == "desempenho_vendedor" and ent.get("vendedor"):
        ent["vendedor_nome"] = f"%{sem_acento(ent['vendedor'].lower())}%"

    # produtos sem saída: só a categoria faz sentido como recorte
    if intencao == "produtos_sem_saida":
        for k in FILTROS:
            if k != "categoria":
                ent.pop(k, None)

    if intencao == interp.intencao and ent == interp.entidades:
        return interp
    return interp.model_copy(update={"intencao": intencao, "entidades": ent})
