"""Carga da planilha no banco (integração, precisa de DATABASE_URL).

- mesmo produto duas vezes na mesma venda: as linhas são SOMADAS num item;
- data fora do calendário do banco e valor negativo: rejeitados COM motivo,
  gravado em staging_venda.erros (com o número da linha do Excel) e
  devolvido na resposta.
"""

import io
import os

import psycopg
import pytest
from app.main import app
from fastapi.testclient import TestClient
from openpyxl import Workbook

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa de DATABASE_URL")


@pytest.fixture(autouse=True)
def _ambiente(monkeypatch):
    monkeypatch.setenv("EMPRESA_ID", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setenv("AUTH_OBRIGATORIA", "false")
    monkeypatch.setenv("LIMITE_REQUISICOES", "0")


def _xlsx(linhas):
    wb = Workbook()
    ws = wb.active
    for linha in linhas:
        ws.append(linha)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _conectar():
    return psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None)


@pytest.fixture
def importar():
    criadas = []

    def _importar(linhas):
        r = TestClient(app).post("/import", files={"arquivo": ("teste_carga.xlsx", _xlsx(linhas))})
        assert r.status_code == 200, r.text
        criadas.append(r.json()["empresa_id"])
        return r.json()

    yield _importar
    with _conectar() as conn:
        for emp in criadas:
            for tabela in ("fato_item_venda", "staging_venda", "importacao",
                           "dim_produto", "dim_cliente", "dim_vendedor", "log_consulta"):
                conn.execute(f"delete from {tabela} where empresa_id = %s", (emp,))
            conn.execute("delete from empresa where id = %s", (emp,))


CABECALHO = ["venda_id", "data_venda", "produto", "quantidade", "valor_total"]


def test_mesmo_produto_na_mesma_venda_e_somado(importar):
    r = importar([
        CABECALHO,
        ["V1", "2024-03-10", "Caneca", 2, 50],
        ["V1", "2024-03-10", "caneca ", 1, 25],   # mesma venda, mesmo produto (grafia diferente)
        ["V1", "2024-03-10", "Camiseta", 1, 80],
    ])
    assert r["linhas_validas"] == 3
    assert r["linhas_rejeitadas"] == 0
    assert r["linhas_agrupadas"] == 1
    with _conectar() as conn:
        itens = conn.execute(
            "select p.nome_norm, f.quantidade, f.valor_total from fato_item_venda f "
            "join dim_produto p on p.id = f.produto_id where f.empresa_id = %s order by 1",
            (r["empresa_id"],),
        ).fetchall()
    assert [(n, q, float(v)) for n, q, v in itens] == [("camiseta", 1, 80.0), ("caneca", 3, 75.0)]


def test_data_fora_do_calendario_e_valor_negativo_tem_motivo(importar):
    r = importar([
        CABECALHO,
        ["V1", "2024-03-10", "Caneca", 1, 25],
        ["V2", "2019-05-01", "Caneca", 1, 25],    # antes do calendário (linha 3)
        [None, None, None, None, None],           # linha 4 em branco
        ["V3", "2024-03-11", "Caneca", 1, -10],   # negativo (linha 5)
    ])
    assert r["linhas_validas"] == 1
    assert r["linhas_rejeitadas"] == 2
    motivos = r["motivos_rejeicao"]
    assert motivos["valor negativo"] == 1
    assert [m for m in motivos if m.startswith("data fora do período aceito")] != []
    with _conectar() as conn:
        erros = conn.execute(
            "select linha_origem, erros from staging_venda where empresa_id = %s and erros is not null "
            "order by linha_origem",
            (r["empresa_id"],),
        ).fetchall()
    assert [n for n, _ in erros] == [3, 5]  # números das linhas no Excel
    assert erros[0][1].startswith("data fora do período aceito")
    assert erros[1][1] == "valor negativo"
