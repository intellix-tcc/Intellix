"""Produtos sem saída respeita o recorte da venda (integração, com banco).

"Quais produtos não venderam no site?" = produtos sem venda PELO SITE no
período, e não sem venda nenhuma. Antes o canal era ignorado.
"""

import os

import psycopg
import pytest
from app.models import Interpretacao
from app.sql.executor import executar_template

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa de DATABASE_URL")

PERIODO = {"periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31"}


@pytest.fixture
def empresa():
    with psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None) as conn:
        emp = str(conn.execute("insert into empresa (nome) values ('TESTE sem saida') returning id").fetchone()[0])
        ids = {}
        for nome in ("Caneca", "Bolsa"):
            ids[nome] = conn.execute(
                "insert into dim_produto (empresa_id, nome, categoria) values (%s, %s, 'Casa') returning id",
                (emp, nome),
            ).fetchone()[0]
        did = conn.execute("select id from dim_data where data = '2024-03-10'").fetchone()[0]
        # Caneca vendeu na loja; Bolsa vendeu no site
        for venda, produto, canal in (("V1", "Caneca", "loja"), ("V2", "Bolsa", "site")):
            conn.execute(
                "insert into fato_item_venda (empresa_id, venda_id, data_id, produto_id, canal, "
                "quantidade, valor_unitario, desconto, valor_total) values (%s,%s,%s,%s,%s,1,10,0,10)",
                (emp, venda, did, ids[produto], canal),
            )
    yield emp
    with psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None) as conn:
        for tabela in ("fato_item_venda", "dim_produto"):
            conn.execute(f"delete from {tabela} where empresa_id = %s", (emp,))
        conn.execute("delete from empresa where id = %s", (emp,))


def _sem_saida(emp, **filtros):
    interp = Interpretacao(intencao="produtos_sem_saida", confianca=0.9,
                           entidades={**PERIODO, **filtros}, texto_original="x")
    with psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None) as conn:
        return executar_template(interp, emp, conn)


def test_sem_recorte_todos_venderam(empresa):
    assert _sem_saida(empresa).linhas == []


def test_no_site_a_caneca_ficou_parada(empresa):
    assert [linha[0] for linha in _sem_saida(empresa, canal="site").linhas] == ["Caneca"]


def test_na_loja_a_bolsa_ficou_parada(empresa):
    assert [linha[0] for linha in _sem_saida(empresa, canal="loja").linhas] == ["Bolsa"]
