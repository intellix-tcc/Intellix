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


# ---- contexto ampliado: filtros, métrica e período --------------------------

ANO_2026 = {"periodo_inicio": "2026-01-01", "periodo_fim": "2026-12-31"}


def _modelo(intencao, texto, confianca=0.99, **ent):
    """Como a frase chega do modelo + filtros (já resolvidos no catálogo)."""
    return Interpretacao(intencao=intencao, confianca=confianca, entidades=ent, texto_original=texto)


def test_elipse_com_filtro_novo_herda_intencao_periodo_e_limite():
    # "Qual o produto mais vendido em 2026?" -> "E de calçados?"
    ctx = Contexto(intencao="top_produtos", entidades={**ANO_2026, "limite": 5})
    out = aplicar_contexto(_elidida("e de calçados?").model_copy(
        update={"entidades": {"categoria": "Calçados"}}), ctx, "e de calçados?")
    assert out.intencao == "top_produtos"
    assert out.entidades == {**ANO_2026, "limite": 5, "categoria": "Calçados"}


def test_categoria_nova_substitui_o_produto_anterior():
    ctx = Contexto(intencao="unidades_vendidas", entidades={**ANO_2026, "produto": "Bota couro"})
    atual = _elidida("e de acessórios?").model_copy(update={"entidades": {"categoria": "Acessórios"}})
    out = aplicar_contexto(atual, ctx, "e de acessórios?")
    assert "produto" not in out.entidades
    assert out.entidades["categoria"] == "Acessórios"


def test_elipse_de_periodo_mantem_os_filtros():
    # "Quantas botas em 2026?" -> "E em 2025?" continua sendo sobre as botas
    ctx = Contexto(intencao="unidades_vendidas", entidades={**ANO_2026, "produto": "Bota couro"})
    out = aplicar_contexto(_elidida("e em 2025?"), ctx, "e em 2025?")
    assert out.intencao == "unidades_vendidas"
    assert out.entidades["produto"] == "Bota couro"
    assert out.entidades["periodo_inicio"] == "2025-01-01"


def test_mes_sem_ano_usa_o_ano_da_conversa():
    ctx = Contexto(intencao="total_vendas_periodo", entidades={**ANO_2026})
    out = aplicar_contexto(_elidida("e em abril?"), ctx, "e em abril?", ano_ref=2024)
    assert out.entidades["periodo_inicio"] == "2026-04-01"


def test_pergunta_nova_sem_periodo_continua_no_periodo_da_conversa():
    # "Qual o produto mais vendido em 2026?" -> "Quantas botas de couro vendemos no ano?"
    ctx = Contexto(intencao="top_produtos", entidades={**ANO_2026, "limite": 5})
    texto = "quantas botas de couro a gente vendeu no ano?"
    atual = _modelo("quantidade_vendas", texto, periodo_inicio="2024-01-01",
                    periodo_fim="2024-12-31", produto="Bota couro")
    out = aplicar_contexto(atual, ctx, texto, ano_ref=2024)
    assert out.intencao == "quantidade_vendas"  # a intenção nova vale
    assert out.entidades["periodo_inicio"] == "2026-01-01"
    assert out.entidades["produto"] == "Bota couro"
    assert "limite" not in out.entidades  # parâmetro da pergunta anterior não vaza


def test_no_ano_depois_de_um_mes_e_o_ano_inteiro():
    ctx = Contexto(intencao="total_vendas_periodo",
                   entidades={"periodo_inicio": "2026-03-01", "periodo_fim": "2026-03-31"})
    texto = "e quantos itens vendemos no ano?"
    atual = _modelo("quantidade_vendas", texto, periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
    out = aplicar_contexto(atual, ctx, texto)
    assert (out.entidades["periodo_inicio"], out.entidades["periodo_fim"]) == ("2026-01-01", "2026-12-31")


def test_pergunta_nova_nao_herda_os_filtros():
    ctx = Contexto(intencao="unidades_vendidas", entidades={**ANO_2026, "produto": "Bota couro"})
    texto = "qual o ticket médio de 2025?"
    atual = _modelo("ticket_medio", texto, periodo_inicio="2025-01-01", periodo_fim="2025-12-31")
    out = aplicar_contexto(atual, ctx, texto)
    assert "produto" not in out.entidades
    assert out.entidades["periodo_inicio"] == "2025-01-01"


def test_continuacao_com_metrica_nova_herda_filtros_e_periodo():
    # "Quantas botas em 2026?" -> "E o ticket médio?"
    ctx = Contexto(intencao="unidades_vendidas", entidades={**ANO_2026, "produto": "Bota couro"})
    texto = "e o ticket médio?"
    atual = _modelo("ticket_medio", texto, periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
    out = aplicar_contexto(atual, ctx, texto)
    assert out.intencao == "ticket_medio"
    assert out.entidades == {**ANO_2026, "produto": "Bota couro"}


def test_continuacao_que_so_troca_o_recorte_mantem_a_pergunta():
    # "Quantas botas em 2026?" -> "E no pix?": o modelo lê vendas_por_pagamento,
    # mas a pessoa só trocou o recorte.
    ctx = Contexto(intencao="unidades_vendidas", entidades={**ANO_2026, "produto": "Bota couro"})
    texto = "e no pix?"
    atual = _modelo("vendas_por_pagamento", texto, periodo_inicio="2024-01-01",
                    periodo_fim="2024-12-31", forma_pagamento="pix")
    out = aplicar_contexto(atual, ctx, texto)
    assert out.intencao == "unidades_vendidas"
    assert out.entidades == {**ANO_2026, "produto": "Bota couro", "forma_pagamento": "pix"}


def test_elipse_que_pede_o_melhor_mes_herda_o_recorte():
    # "Quantas botas em 2026?" -> "E qual mês vendeu mais?"
    ctx = Contexto(intencao="unidades_vendidas", entidades={**ANO_2026, "produto": "Bota couro"})
    out = aplicar_contexto(_elidida("e qual mês vendeu mais?"), ctx, "e qual mês vendeu mais?")
    assert out.intencao == "unidades_vendidas"  # o refino troca para melhor_mes depois
    assert out.entidades["produto"] == "Bota couro"


def test_periodo_relativo_na_conversa_parte_de_hoje_e_nao_do_ano_da_conversa():
    # Conversa sobre 2025; "e no mês passado?" em novembro de 2026 = outubro de 2026.
    from datetime import date

    from app.nlu import regras as R
    ctx = Contexto(intencao="total_vendas_periodo",
                   entidades={"periodo_inicio": "2025-01-01", "periodo_fim": "2025-12-31"})
    with R.usar_referencia(date(2026, 11, 5)):
        out = aplicar_contexto(_elidida("e no mês passado?"), ctx, "e no mês passado?")
        assert out.entidades["periodo_inicio"] == "2026-10-01"
        # já um mês por nome, sem ano, fica no ano da conversa
        out = aplicar_contexto(_elidida("e em abril?"), ctx, "e em abril?")
        assert out.entidades["periodo_inicio"] == "2025-04-01"
