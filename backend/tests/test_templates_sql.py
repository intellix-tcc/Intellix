import re

from app.sql.templates import TEMPLATES

CHAVES_ESPERADAS = {"sql", "obrigatorios", "titulo", "visual"}


def test_templates_essenciais_existem():
    for nome in ("total_vendas_periodo", "top_produtos", "ticket_medio"):
        assert nome in TEMPLATES


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
