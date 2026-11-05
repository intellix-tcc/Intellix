"""Refino da intenção (app/refino.py): perguntas mais específicas que as 12
classes do modelo, sem retreino. Sem banco."""

from app.models import Interpretacao
from app.refino import refinar

ANO_2026 = {"periodo_inicio": "2026-01-01", "periodo_fim": "2026-12-31"}


def _i(intencao, texto, confianca=0.99, **ent):
    return Interpretacao(intencao=intencao, confianca=confianca,
                         entidades={**ANO_2026, **ent}, texto_original=texto)


def test_qual_mes_mais_vendeu_um_produto_e_por_unidades():
    texto = "Qual foi o mês do ano que mais vendeu botas de couro?"
    # é o que o modelo devolve nessa frase: top_produtos, abaixo do limiar
    out = refinar(_i("top_produtos", texto, confianca=0.62, limite=5, produto="Bota couro"), texto)
    assert out.intencao == "melhor_mes"
    assert out.confianca >= 0.70
    assert out.entidades["metrica"] == "unidades"
    assert out.entidades["sentido"] == "maior"
    assert "limite" not in out.entidades


def test_melhor_mes_sem_produto_e_por_faturamento_e_pior_mes_inverte():
    out = refinar(_i("total_vendas_periodo", "qual o melhor mês de 2026?"), "qual o melhor mês de 2026?")
    assert (out.intencao, out.entidades["metrica"], out.entidades["sentido"]) == ("melhor_mes", "faturamento", "maior")
    out = refinar(_i("total_vendas_periodo", "em que mês vendemos menos?"), "em que mês vendemos menos?")
    assert out.entidades["sentido"] == "menor"


def test_melhor_mes_sobre_um_mes_so_olha_o_ano():
    ent = {"periodo_inicio": "2026-03-01", "periodo_fim": "2026-03-31"}
    i = Interpretacao(intencao="total_vendas_periodo", confianca=0.9, entidades=ent, texto_original="x")
    out = refinar(i, "qual foi o mês que mais vendeu?")
    assert out.entidades["periodo_inicio"] == "2026-01-01"
    assert out.entidades["periodo_fim"] == "2026-12-31"


def test_mes_sem_pedir_extremo_nao_vira_melhor_mes():
    texto = "qual o faturamento do mês passado?"
    assert refinar(_i("total_vendas_periodo", texto), texto).intencao == "total_vendas_periodo"


def test_quantas_botas_sao_unidades_e_quantas_vendas_continua_pedidos():
    texto = "Quantas botas de couro a gente vendeu no ano?"
    assert refinar(_i("quantidade_vendas", texto, produto="Bota couro"), texto).intencao == "unidades_vendidas"
    texto = "quantas vendas de bota tivemos?"
    assert refinar(_i("quantidade_vendas", texto, produto="Bota couro"), texto).intencao == "quantidade_vendas"
    texto = "quantos itens vendemos em 2026?"
    assert refinar(_i("quantidade_vendas", texto), texto).intencao == "unidades_vendidas"


def test_quebra_pela_dimensao_ja_filtrada_vira_total_do_recorte():
    texto = "quanto vendi no pix em março"
    out = refinar(_i("vendas_por_pagamento", texto, forma_pagamento="pix"), texto)
    assert out.intencao == "total_vendas_periodo"
    texto = "Quantas vendas no pix em janeiro de 2024?"
    assert refinar(_i("vendas_por_pagamento", texto, forma_pagamento="pix"), texto).intencao == "quantidade_vendas"
    texto = "quanto vendi de bota couro em 2026"  # o modelo lê vendas_por_categoria
    assert refinar(_i("vendas_por_categoria", texto, produto="Bota couro"), texto).intencao == "total_vendas_periodo"


def test_ranking_dentro_de_uma_categoria_continua_ranking():
    texto = "top 5 produtos de calçados"
    out = refinar(_i("top_produtos", texto, limite=5, categoria="Calçados"), texto)
    assert out.intencao == "top_produtos"
    assert out.entidades["limite"] == 5


def test_vendedor_do_catalogo_vira_o_filtro_do_desempenho():
    texto = "como foi a Fernanda?"
    out = refinar(_i("desempenho_vendedor", texto, vendedor="Fernanda Dias"), texto)
    assert out.entidades["vendedor_nome"] == "%fernanda dias%"


def test_baixa_confianca_sem_pedido_explicito_fica_como_esta():
    texto = "qual a capital da França?"
    i = _i("desempenho_vendedor", texto, confianca=0.59)
    assert refinar(i, texto) is i


def test_frase_comum_nao_muda():
    texto = "quanto faturei em março de 2024"
    i = _i("total_vendas_periodo", texto)
    assert refinar(i, texto) is i


def test_quando_vendeu_mais_e_pergunta_de_mes():
    # o modelo lê total_vendas_periodo; a frase pede o mês de maior venda
    texto = "quando o perfume importado vendeu mais?"
    out = refinar(_i("total_vendas_periodo", texto, produto="Perfume importado"), texto)
    assert (out.intencao, out.entidades["metrica"], out.entidades["sentido"]) == ("melhor_mes", "unidades", "maior")
    texto = "quanto vendi quando teve promoção?"  # sem "mais/menos": não é mês extremo
    assert refinar(_i("total_vendas_periodo", texto), texto).intencao == "total_vendas_periodo"
