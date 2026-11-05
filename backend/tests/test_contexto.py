"""Contexto conversacional (app/contexto.py): frases elípticas como
"e em abril?" herdam a intenção da resposta anterior. Sem banco."""

from app.contexto import aplicar_contexto
from app.models import Contexto, Interpretacao


def _elidida(texto: str) -> Interpretacao:
    # Como o NLU devolve uma frase elíptica sozinha: sem intenção reconhecida.
    return Interpretacao(intencao=None, confianca=0.0, entidades={}, texto_original=texto)


def test_herda_intencao_anterior_em_followup_de_periodo():
    ctx = Contexto(
        intencao="total_vendas_periodo",
        entidades={"periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31"},
    )
    out = aplicar_contexto(_elidida("e em abril de 2024?"), ctx, "e em abril de 2024?")
    assert out.intencao == "total_vendas_periodo"
    assert out.confianca >= 0.70
    assert out.entidades["periodo_inicio"] == "2024-04-01"
    assert out.entidades["periodo_fim"] == "2024-04-30"


def test_nao_herda_quando_a_frase_atual_ja_se_classificou():
    ctx = Contexto(intencao="total_vendas_periodo", entidades={})
    atual = Interpretacao(
        intencao="top_produtos",
        confianca=0.95,
        entidades={"periodo_inicio": "2024-01-01", "periodo_fim": "2024-12-31", "limite": 5},
        texto_original="top 5 produtos de 2024",
    )
    out = aplicar_contexto(atual, ctx, "top 5 produtos de 2024")
    assert out.intencao == "top_produtos"  # permanece a da frase atual


def test_sem_contexto_anterior_nao_muda_nada():
    atual = _elidida("e em abril?")
    out = aplicar_contexto(atual, None, "e em abril?")
    assert out.intencao is None


def test_followup_sem_periodo_nao_herda():
    # "e o Carlos?" não traz período -> não dá para saber o que mudou: não herda
    # (segue para baixa_confianca/422, em vez de responder errado).
    ctx = Contexto(
        intencao="total_vendas_periodo",
        entidades={"periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31"},
    )
    out = aplicar_contexto(_elidida("e o Carlos?"), ctx, "e o Carlos?")
    assert out.intencao is None
