import re

from app.sql.templates import TEMPLATES

CHAVES_ESPERADAS = {"sql", "obrigatorios", "titulo", "visual"}

# As 12 intencoes definidas em `ia training/moldes.py`.
INTENCOES_ESPERADAS = {
    "comparacao_periodos",
    "desempenho_vendedor",
    "produtos_sem_saida",
    "quantidade_vendas",
    "ticket_medio",
    "top_clientes",
    "top_produtos",
    "total_vendas_periodo",
    "variacao_periodo",
    "vendas_por_canal",
    "vendas_por_categoria",
    "vendas_por_pagamento",
}


# Refinamentos sobre a intenção do modelo (app/refino.py), sem classe própria.
REFINAMENTOS = {"unidades_vendidas", "melhor_mes"}


def test_todas_as_12_intencoes_tem_template():
    assert TEMPLATES.keys() == INTENCOES_ESPERADAS | REFINAMENTOS


def test_toda_consulta_sobre_vendas_aceita_os_filtros():
    # Os seis recortes (produto, categoria...) entram em toda consulta que lê
    # fato_item_venda. produtos_sem_saida filtra a categoria na lista e o
    # recorte da venda (vendedor, cliente, canal, pagamento) na checagem de
    # "teve venda?"; produto não se aplica (é o próprio item listado).
    for nome, template in TEMPLATES.items():
        if nome == "produtos_sem_saida":
            assert "%(categoria)s" in template["sql"]
            for filtro in ("vendedor", "cliente", "canal", "forma_pagamento"):
                assert f"%({filtro})s::text is null" in template["sql"], f"{nome}.{filtro}"
            continue
        for filtro in ("produto", "categoria", "vendedor", "cliente", "canal", "forma_pagamento"):
            assert f"%({filtro})s::text is null" in template["sql"], f"{nome}.{filtro}"


def test_templates_tem_formato_correto():
    for nome, template in TEMPLATES.items():
        assert CHAVES_ESPERADAS.issubset(template.keys()), nome
        assert isinstance(template["obrigatorios"], list)


def test_obrigatorios_aparecem_como_parametros_no_sql():
    # Todo parametro declarado como obrigatorio precisa estar como %(nome)s
    # no SQL -- garante que o valor sempre passa pelo psycopg, nunca por
    # f-string/concatenacao.
    for nome, template in TEMPLATES.items():
        for parametro in template["obrigatorios"]:
            assert f"%({parametro})s" in template["sql"], f"{nome}.{parametro}"


def test_sql_nao_usa_f_string_de_valor():
    # Garante que ninguem trocou %(...)s por interpolacao direta.
    for nome, template in TEMPLATES.items():
        assert not re.search(r"\{[a-z_]+\}", template["sql"]), nome
