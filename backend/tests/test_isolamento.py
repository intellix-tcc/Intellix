"""Isolamento por empresa (feedback TC2 F09) e auditoria.

Os testes de `resolver_empresa` são determinísticos (conexão falsa) e provam a
matriz de autorização sem precisar de banco nem de usuário real. O teste de
auditoria é de integração (precisa de DATABASE_URL).
"""

import os
import uuid
from types import SimpleNamespace

import psycopg
import pytest
from app.acesso import resolver_empresa
from app.db import get_empresa_id
from fastapi import HTTPException

DEMO = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def _empresa_demo(monkeypatch):
    # get_empresa_id() lê EMPRESA_ID; fixar aqui faz os testes rodarem sem .env.
    monkeypatch.setenv("EMPRESA_ID", DEMO)
    monkeypatch.delenv("AUTH_OBRIGATORIA", raising=False)  # garante auth desligada


class _Cursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _Conn:
    """Conexão falsa: resolver_empresa só chama conn.execute(...).fetchone()."""

    def __init__(self, row):
        self._row = row

    def execute(self, *_a, **_k):
        return _Cursor(self._row)


DONO = str(uuid.uuid4())
OUTRO = str(uuid.uuid4())
EMP = str(uuid.uuid4())


def test_demo_e_sempre_acessivel():
    assert resolver_empresa(_Conn(None), None, None) == get_empresa_id()
    assert resolver_empresa(_Conn(None), DEMO, None) == DEMO


def test_dataset_sem_dono_e_acessivel_sem_login():
    assert resolver_empresa(_Conn((None,)), EMP, None) == EMP


def test_dataset_de_outro_dono_bloqueia_anonimo():
    with pytest.raises(HTTPException) as e:
        resolver_empresa(_Conn((DONO,)), EMP, None)
    assert e.value.status_code == 404
    assert e.value.detail["tipo"] == "dataset_nao_encontrado"


def test_dataset_de_outro_dono_bloqueia_usuario_errado():
    with pytest.raises(HTTPException) as e:
        resolver_empresa(_Conn((DONO,)), EMP, SimpleNamespace(id=OUTRO))
    assert e.value.status_code == 404


def test_dono_acessa_o_proprio_dataset():
    assert resolver_empresa(_Conn((DONO,)), EMP, SimpleNamespace(id=DONO)) == EMP


def test_id_inexistente_bloqueia():
    with pytest.raises(HTTPException) as e:
        resolver_empresa(_Conn(None), EMP, None)  # conn devolve None = não existe
    assert e.value.status_code == 404


def test_id_malformado_bloqueia():
    with pytest.raises(HTTPException) as e:
        resolver_empresa(_Conn(None), "nao-e-uuid", None)
    assert e.value.status_code == 404


# --------------------------------------------------------------------------- #
# Auditoria: o /chat grava em log_consulta (integração, precisa de banco).
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa de DATABASE_URL")
def test_chat_grava_auditoria_em_log_consulta():
    from app.main import app
    from fastapi.testclient import TestClient

    dsn = os.environ["DATABASE_URL"]
    with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
        cur.execute("insert into empresa (nome, dono_id) values ('TESTE auditoria', null) returning id")
        emp = str(cur.fetchone()[0])
        cur.execute("insert into dim_produto (empresa_id, nome, categoria) values (%s,'Prod','Cat')", (emp,))
        cur.execute("select id from dim_produto where empresa_id=%s", (emp,))
        pid = cur.fetchone()[0]
        cur.execute("select id from dim_data where data = '2024-03-10'")
        did = cur.fetchone()[0]
        cur.execute(
            "insert into fato_item_venda (empresa_id, venda_id, data_id, produto_id, "
            "quantidade, valor_unitario, desconto, valor_total) values (%s,'V1',%s,%s,1,10,0,10)",
            (emp, did, pid),
        )
        conn.commit()
    try:
        r = TestClient(app).post(
            "/chat", json={"pergunta": "quanto faturei em março de 2024", "empresa_id": emp}
        )
        assert r.status_code == 200
        with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
            cur.execute(
                "select pergunta, intencao, confianca from log_consulta where empresa_id=%s", (emp,)
            )
            linha = cur.fetchone()
        assert linha is not None, "a consulta não foi registrada em log_consulta"
        assert linha[1] == "total_vendas_periodo"
    finally:
        with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
            for t in ("log_consulta", "fato_item_venda", "dim_produto"):
                cur.execute(f"delete from {t} where empresa_id=%s", (emp,))
            cur.execute("delete from empresa where id=%s", (emp,))
            conn.commit()
