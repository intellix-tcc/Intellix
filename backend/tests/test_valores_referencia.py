"""Verificação de VALORES (não só status/tipo) numa base pequena, calculável à
mão. Atende ao feedback TC2 F01 ("o oráculo funcional não verifica os valores
analíticos") e comprova a correção do ticket médio (F08).

Base de referência (dataset isolado, criado e removido pela fixture):

  Venda V1 (10/03/2024): Produto A  2 x 50,00 = 100,00  (Cat1, loja, pix)
                         Produto B  1 x 30,00 =  30,00  (Cat2, loja, pix)
  Venda V2 (20/03/2024): Produto A  1 x 50,00 =  50,00  (Cat1, site, cartao)

Valores esperados em março/2024 (conferíveis a mão):
  - faturamento total ....... 180,00
  - vendas distintas ........ 2           (V1, V2)
  - ticket médio ............ 90,00       (= 180 / 2; média por ITEM daria 60)
  - Produto A ............... qtd 3, faturamento 150,00
  - Produto B ............... qtd 1, faturamento  30,00
"""

import os
import uuid

import psycopg
import pytest
from app.main import app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="precisa de backend/.env com DATABASE_URL (Bloco 2)",
)

client = TestClient(app)


@pytest.fixture
def base_pequena():
    """Cria o dataset de referência e devolve o empresa_id; apaga tudo no fim."""
    dsn = os.environ["DATABASE_URL"]
    nome = f"TESTE valores referencia {uuid.uuid4().hex[:8]}"
    with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
        cur.execute(
            "insert into empresa (nome, dono_id) values (%s, null) returning id", (nome,)
        )
        emp = str(cur.fetchone()[0])
        cur.execute(
            "insert into dim_produto (empresa_id, nome, categoria) "
            "values (%s,'Produto A','Cat1'),(%s,'Produto B','Cat2')",
            (emp, emp),
        )
        cur.execute("select id, nome from dim_produto where empresa_id=%s", (emp,))
        pid = {n: i for i, n in cur.fetchall()}
        cur.execute(
            "select id, to_char(data,'YYYY-MM-DD') from dim_data "
            "where data in ('2024-03-10','2024-03-20')"
        )
        did = {d: i for i, d in cur.fetchall()}
        linhas = [
            (emp, "V1", did["2024-03-10"], pid["Produto A"], "loja", "pix", 2, 50, 0, 100),
            (emp, "V1", did["2024-03-10"], pid["Produto B"], "loja", "pix", 1, 30, 0, 30),
            (emp, "V2", did["2024-03-20"], pid["Produto A"], "site", "cartao", 1, 50, 0, 50),
        ]
        cur.executemany(
            "insert into fato_item_venda (empresa_id, venda_id, data_id, produto_id, "
            "canal, forma_pagamento, quantidade, valor_unitario, desconto, valor_total) "
            "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            linhas,
        )
        conn.commit()
    yield emp
    with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
        # log_consulta primeiro: o /chat audita (F09) e a FK impede apagar a
        # empresa enquanto houver registro de auditoria dela.
        cur.execute("delete from log_consulta where empresa_id=%s", (emp,))
        cur.execute("delete from fato_item_venda where empresa_id=%s", (emp,))
        cur.execute("delete from dim_produto where empresa_id=%s", (emp,))
        cur.execute("delete from empresa where id=%s", (emp,))
        conn.commit()


def _chat(emp, pergunta):
    return client.post("/chat", json={"pergunta": pergunta, "empresa_id": emp})


def test_faturamento_total_de_marco(base_pequena):
    r = _chat(base_pequena, "quanto faturei em março de 2024")
    assert r.status_code == 200
    # colunas: [periodo, faturamento] -> uma linha do mês
    assert r.json()["linhas"][0][1] == pytest.approx(180.0)


def test_ticket_medio_e_por_venda_nao_por_item(base_pequena):
    # F08: ticket = 180 / 2 vendas = 90. A média por item (antiga) daria 60.
    r = _chat(base_pequena, "qual o ticket médio em março de 2024")
    assert r.status_code == 200
    assert r.json()["linhas"][0][0] == pytest.approx(90.0)


@pytest.mark.skipif(
    os.environ.get("NLU_BACKEND", "regras").strip().lower() != "modelo",
    reason="'quantas vendas' só é entendida pelo modelo treinado (NLU_BACKEND=modelo); "
    "o baseline de regras não cobre quantidade_vendas",
)
def test_quantidade_de_vendas_distintas(base_pequena):
    r = _chat(base_pequena, "quantas vendas tiveram em março de 2024")
    assert r.status_code == 200
    # colunas: [periodo, quantidade_vendas]
    assert r.json()["linhas"][0][1] == 2


def test_top_produtos_ordem_e_valores(base_pequena):
    r = _chat(base_pequena, "quais os produtos mais vendidos em março de 2024")
    assert r.status_code == 200
    linhas = r.json()["linhas"]  # [produto, quantidade, faturamento], desc por faturamento
    assert linhas[0][0] == "Produto A"
    assert linhas[0][1] == 3
    assert linhas[0][2] == pytest.approx(150.0)
    assert linhas[1][0] == "Produto B"
    assert linhas[1][2] == pytest.approx(30.0)


def test_periodo_sem_vendas_responde_sem_resultado(base_pequena):
    # fronteira: mês sem dados neste dataset -> 404 (não um ticket nulo como 200)
    r = _chat(base_pequena, "qual o ticket médio em janeiro de 2024")
    assert r.status_code == 404
    assert r.json()["detail"]["tipo"] == "sem_resultado"
