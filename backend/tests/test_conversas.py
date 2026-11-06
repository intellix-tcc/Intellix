"""Histórico de conversas (GET/PUT/DELETE /conversas, migration 008).

Sem banco: as rotas exigem login. Com banco (DATABASE_URL, como no CI): cada
usuário lista só as próprias conversas, não sobrescreve nem apaga a de outra
pessoa, e o upsert cria e depois atualiza a mesma conversa.
"""

import os
import uuid

import psycopg
import pytest
from app.auth import Usuario, usuario_atual
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _ambiente(monkeypatch):
    monkeypatch.setenv("AUTH_OBRIGATORIA", "false")
    monkeypatch.setenv("LIMITE_REQUISICOES", "0")
    yield
    app.dependency_overrides.clear()


def _como(usuario_id: str | None) -> TestClient:
    app.dependency_overrides[usuario_atual] = lambda: Usuario(id=usuario_id) if usuario_id else None
    return TestClient(app)


# ---- sem banco ---------------------------------------------------------------

def test_listar_exige_login():
    r = _como(None).get("/conversas")
    assert r.status_code == 401
    assert r.json()["detail"]["tipo"] == "nao_autenticado"


def test_gravar_exige_login():
    r = _como(None).put(f"/conversas/{uuid.uuid4()}", json={"titulo": "Olá", "mensagens": []})
    assert r.status_code == 401


def test_excluir_exige_login():
    r = _como(None).delete(f"/conversas/{uuid.uuid4()}")
    assert r.status_code == 401


# ---- com banco ---------------------------------------------------------------

com_banco = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="precisa de DATABASE_URL")


def _sql(comando: str, params=()):
    with psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None) as conn:
        cur = conn.execute(comando, params)
        return cur.fetchone() if cur.description else None


@pytest.fixture
def usuarios():
    """Dois usuários em auth.users. Apagar o usuário leva junto as conversas
    (conversa.dono_id -> auth.users on delete cascade)."""
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    try:
        for u in (a, b):
            _sql("insert into auth.users (id) values (%s)", (u,))
    except psycopg.Error:
        pytest.skip("auth.users não aceita inserção direta (banco do Supabase)")
    yield a, b
    for u in (a, b):
        _sql("delete from auth.users where id = %s", (u,))


def _corpo(titulo: str, mensagens=None) -> dict:
    return {"titulo": titulo, "mensagens": mensagens or []}


@com_banco
def test_lista_so_as_conversas_do_proprio_usuario(usuarios):
    a, b = usuarios
    id_a = str(uuid.uuid4())
    msgs = [{"tipo": "usuario", "texto": "Quanto faturei em março?"}]
    assert _como(a).put(f"/conversas/{id_a}", json=_corpo("Março", msgs)).status_code == 200
    assert _como(b).put(f"/conversas/{uuid.uuid4()}", json=_corpo("Outra")).status_code == 200

    r = _como(a).get("/conversas")
    assert r.status_code == 200
    conversas = r.json()["conversas"]
    assert [c["id"] for c in conversas] == [id_a]
    assert conversas[0]["titulo"] == "Março"
    assert conversas[0]["mensagens"] == msgs
    assert conversas[0]["criadoEm"] and conversas[0]["atualizadoEm"]


@com_banco
def test_nao_sobrescreve_conversa_de_outra_pessoa(usuarios):
    a, b = usuarios
    id_a = str(uuid.uuid4())
    assert _como(a).put(f"/conversas/{id_a}", json=_corpo("Do A")).status_code == 200

    # B usa o MESMO id: 404, e o título do A continua.
    r = _como(b).put(f"/conversas/{id_a}", json=_corpo("Invasão"))
    assert r.status_code == 404
    assert _como(a).get("/conversas").json()["conversas"][0]["titulo"] == "Do A"
    assert _como(b).get("/conversas").json()["conversas"] == []


@com_banco
def test_nao_apaga_conversa_de_outra_pessoa(usuarios):
    a, b = usuarios
    id_a = str(uuid.uuid4())
    assert _como(a).put(f"/conversas/{id_a}", json=_corpo("Do A")).status_code == 200

    assert _como(b).delete(f"/conversas/{id_a}").status_code == 404
    assert _como(b).delete("/conversas/nao-e-uuid").status_code == 404
    assert _como(b).delete(f"/conversas/{uuid.uuid4()}").status_code == 404
    assert [c["id"] for c in _como(a).get("/conversas").json()["conversas"]] == [id_a]


@com_banco
def test_upsert_cria_e_depois_atualiza(usuarios):
    a, _ = usuarios
    cid = str(uuid.uuid4())
    assert _como(a).put(f"/conversas/{cid}", json=_corpo("Rascunho", [])).status_code == 200
    # mesmo id, novo conteúdo: atualiza, não duplica
    novas = [{"tipo": "usuario", "texto": "e em abril?"}]
    assert _como(a).put(f"/conversas/{cid}", json=_corpo("Faturamento de março", novas)).status_code == 200

    conversas = _como(a).get("/conversas").json()["conversas"]
    assert len(conversas) == 1
    assert conversas[0]["titulo"] == "Faturamento de março"
    assert conversas[0]["mensagens"] == novas


@com_banco
def test_dono_apaga_a_propria_conversa(usuarios):
    a, _ = usuarios
    cid = str(uuid.uuid4())
    assert _como(a).put(f"/conversas/{cid}", json=_corpo("Some")).status_code == 200
    r = _como(a).delete(f"/conversas/{cid}")
    assert r.status_code == 200
    assert r.json() == {"excluida": True, "id": cid}
    assert _como(a).get("/conversas").json()["conversas"] == []
