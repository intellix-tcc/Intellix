"""Minhas planilhas (GET/DELETE /planilhas, migration 007).

Sem banco: as rotas exigem login. Com banco (DATABASE_URL, como no CI): cada
usuário lista só as próprias planilhas e só apaga as próprias; a de outra
pessoa, a base demo e um id inexistente recebem o mesmo 404.
"""

import io
import os
import uuid

import psycopg
import pytest
from app.auth import Usuario, usuario_atual
from app.main import app
from fastapi.testclient import TestClient
from openpyxl import Workbook

DEMO = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def _ambiente(monkeypatch):
    monkeypatch.setenv("EMPRESA_ID", DEMO)
    monkeypatch.setenv("AUTH_OBRIGATORIA", "false")
    monkeypatch.setenv("LIMITE_REQUISICOES", "0")
    yield
    app.dependency_overrides.clear()


def _como(usuario_id: str | None) -> TestClient:
    app.dependency_overrides[usuario_atual] = lambda: Usuario(id=usuario_id) if usuario_id else None
    return TestClient(app)


# ---- sem banco ---------------------------------------------------------------

def test_listar_exige_login():
    r = _como(None).get("/planilhas")
    assert r.status_code == 401
    assert r.json()["detail"]["tipo"] == "nao_autenticado"


def test_excluir_exige_login():
    r = _como(None).delete(f"/planilhas/{uuid.uuid4()}")
    assert r.status_code == 401


# ---- com banco ---------------------------------------------------------------

com_banco = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa de DATABASE_URL")


def _xlsx() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["data_venda", "produto", "quantidade", "valor_total"])
    ws.append(["2024-03-10", "Caneca", 2, 50])
    ws.append(["2024-04-02", "Camiseta", 1, 80])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _sql(comando: str, params=()):
    with psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None) as conn:
        cur = conn.execute(comando, params)
        return cur.fetchone() if cur.description else None


@pytest.fixture
def usuarios():
    """Dois usuários em auth.users (no Postgres do CI/local é a tabela mínima
    de database/local/supabase_minimo.sql)."""
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    try:
        for u in (a, b):
            _sql("insert into auth.users (id) values (%s)", (u,))
    except psycopg.Error:
        pytest.skip("auth.users não aceita inserção direta (banco do Supabase)")
    yield a, b
    for u in (a, b):
        for (emp,) in _ids_de(u):
            _como(u).delete(f"/planilhas/{emp}")
        _sql("delete from auth.users where id = %s", (u,))


def _ids_de(dono: str) -> list[tuple]:
    with psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None) as conn:
        return conn.execute("select id from empresa where dono_id = %s", (dono,)).fetchall()


def _importar(dono: str, nome: str) -> str:
    r = _como(dono).post(
        "/import",
        files={"arquivo": (nome, _xlsx(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200, r.text
    return r.json()["empresa_id"]


@com_banco
def test_lista_so_as_planilhas_do_proprio_usuario(usuarios):
    a, b = usuarios
    da_a = _importar(a, "vendas_a.xlsx")
    _importar(b, "vendas_b.xlsx")

    r = _como(a).get("/planilhas")
    assert r.status_code == 200
    planilhas = r.json()["planilhas"]
    assert [p["empresa_id"] for p in planilhas] == [da_a]
    p = planilhas[0]
    assert p["nome_arquivo"] == "vendas_a.xlsx"
    assert p["linhas_validas"] == 2
    assert (p["primeira_venda"], p["ultima_venda"]) == ("2024-03-10", "2024-04-02")


@com_banco
def test_nao_apaga_planilha_de_outra_pessoa_nem_a_demo(usuarios):
    a, b = usuarios
    da_b = _importar(b, "vendas_b.xlsx")
    cliente_a = _como(a)
    assert cliente_a.delete(f"/planilhas/{da_b}").status_code == 404
    assert cliente_a.delete(f"/planilhas/{DEMO}").status_code == 404
    assert cliente_a.delete("/planilhas/nao-e-uuid").status_code == 404
    assert cliente_a.delete(f"/planilhas/{uuid.uuid4()}").status_code == 404
    assert _ids_de(b) == [(uuid.UUID(da_b),)]  # continua lá


@com_banco
def test_dono_apaga_a_propria_planilha_por_inteiro(usuarios):
    a, _ = usuarios
    emp = _importar(a, "vendas_a.xlsx")
    r = _como(a).delete(f"/planilhas/{emp}")
    assert r.status_code == 200
    assert r.json() == {"excluida": True, "empresa_id": emp}
    for tabela in ("fato_item_venda", "staging_venda", "importacao", "dim_produto"):
        restante = _sql(f"select count(*) from {tabela} where empresa_id = %s", (emp,))
        assert restante == (0,), tabela
    assert _ids_de(a) == []
    assert _como(a).get("/planilhas").json()["planilhas"] == []
