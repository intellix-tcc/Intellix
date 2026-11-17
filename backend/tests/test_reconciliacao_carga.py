"""Reconciliação de carga com planilha de teste (parecer banca final, F06).

Carrega uma planilha de conteúdo conhecido pela ETL real e reconcilia os
VALORES (vendas distintas, itens, faturamento, ticket) e os invariantes de grão
e integridade referencial contra o banco. Complementa `test_import_carga.py`
(que cobre a soma do produto repetido) com a reconciliação de valor que a banca
pede. Precisa de DATABASE_URL.
"""
import os
import sys
from pathlib import Path

import psycopg
import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="precisa de DATABASE_URL"
)


def test_reconciliacao_valor_e_grao():
    from scripts.reconciliacao_carga import _esperado, _xlsx_bytes, _carregado
    from app.importacao.etl import importar

    dsn = os.environ["DATABASE_URL"]
    esp = _esperado()
    emp = None
    try:
        with psycopg.connect(dsn, prepare_threshold=None) as conn:
            rel = importar(_xlsx_bytes(), "reconc_test.xlsx", conn, dono_id=None)
            emp = rel["empresa_id"]
            with conn.cursor() as cur:
                car = _carregado(cur, emp)

        assert car["vendas_distintas"] == esp["vendas_distintas"]
        assert car["itens"] == esp["itens"]
        assert car["faturamento"] == esp["faturamento"]
        assert car["ticket"] == esp["ticket"]
        assert rel["linhas_agrupadas"] == esp["linhas_agrupadas"]
        assert car["caneca_v1_qtd"] == esp["caneca_v1_qtd"]       # repetida somada
        assert car["caneca_v1_total"] == esp["caneca_v1_total"]
        assert car["orfas"] == 0                                  # integridade referencial
    finally:
        if emp:
            with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
                for t in ("log_consulta", "fato_item_venda", "staging_venda", "importacao",
                          "dim_produto", "dim_cliente", "dim_vendedor"):
                    cur.execute(f"delete from {t} where empresa_id=%s", (emp,))
                cur.execute("delete from empresa where id=%s", (emp,))
                conn.commit()
