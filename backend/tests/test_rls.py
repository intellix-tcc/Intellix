"""C14: declaração da empresa por transação e isolamento por RLS.

Os primeiros testes não usam banco: conferem que o backend declara a empresa
ANTES de qualquer leitura. Os de integração só rodam com DATABASE_URL e, os de
isolamento, só quando a conexão usa o usuário da aplicação (intellix_app): o
`postgres` é dono das tabelas e não passa pelo RLS.
"""

import os
import uuid

import pytest
from app import acesso, db
from app.auth import Usuario

DEMO = "00000000-0000-0000-0000-000000000001"


class _ConexaoGravadora:
    """Anota cada comando e responde ao select de dono_id."""

    def __init__(self, donos=None):
        self.donos = donos or {}
        self.comandos = []

    def execute(self, sql, params=()):
        self.comandos.append((" ".join(sql.split()), params))
        linha = (self.donos[params[0]],) if params and params[0] in self.donos else None
        return type("Cursor", (), {"fetchone": lambda _self: linha})()


@pytest.fixture(autouse=True)
def _demo(monkeypatch):
    monkeypatch.setenv("EMPRESA_ID", DEMO)
    monkeypatch.setenv("AUTH_OBRIGATORIA", "false")


def test_declarar_empresa_e_local_a_transacao():
    conn = _ConexaoGravadora()
    db.declarar_empresa(conn, DEMO)
    sql, params = conn.comandos[0]
    assert sql == "select set_config('app.empresa_id', %s, true)"  # true = só nesta transação
    assert params == (DEMO,)


def test_base_demo_tambem_e_declarada():
    conn = _ConexaoGravadora()
    assert acesso.resolver_empresa(conn, None, None) == DEMO
    assert conn.comandos[0][1] == (DEMO,)


def test_empresa_pedida_e_declarada_antes_de_ler_o_dono():
    usuario = Usuario(id=str(uuid.uuid4()))
    dataset = str(uuid.uuid4())
    conn = _ConexaoGravadora({dataset: usuario.id})
    assert acesso.resolver_empresa(conn, dataset, usuario) == dataset
    primeiro, segundo = conn.comandos[0][0], conn.comandos[1][0]
    assert "set_config" in primeiro
    assert "from empresa" in segundo


# ---- integração --------------------------------------------------------------

com_banco = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="precisa de backend/.env com DATABASE_URL"
)


def _usuario_do_banco():
    with db.get_connection() as conn:
        return conn.execute("select current_user").fetchone()[0]


@com_banco
def test_sem_declarar_empresa_o_app_nao_ve_vendas():
    if _usuario_do_banco() != "intellix_app":
        pytest.skip("só vale conectado como intellix_app (migration 006)")
    with db.get_connection() as conn:
        assert conn.execute("select count(*) from fato_item_venda").fetchone()[0] == 0


@com_banco
def test_declarando_a_demo_ve_so_a_demo():
    if _usuario_do_banco() != "intellix_app":
        pytest.skip("só vale conectado como intellix_app (migration 006)")
    with db.get_connection() as conn:
        db.declarar_empresa(conn, DEMO)
        total, empresas = conn.execute(
            "select count(*), count(distinct empresa_id) from fato_item_venda"
        ).fetchone()
    assert total > 0
    assert empresas == 1


@com_banco
def test_declaracao_nao_vaza_para_a_proxima_transacao():
    if _usuario_do_banco() != "intellix_app":
        pytest.skip("só vale conectado como intellix_app (migration 006)")
    with db.get_connection() as conn:
        db.declarar_empresa(conn, DEMO)
    with db.get_connection() as conn:
        valor = conn.execute("select current_setting('app.empresa_id', true)").fetchone()[0]
        assert not valor  # vazio ou nulo: a conexão reaproveitada volta "sem empresa"
        assert conn.execute("select count(*) from fato_item_venda").fetchone()[0] == 0


@com_banco
def test_app_nao_apaga_vendas():
    if _usuario_do_banco() != "intellix_app":
        pytest.skip("só vale conectado como intellix_app (migration 006)")
    import psycopg

    with pytest.raises(psycopg.errors.InsufficientPrivilege), db.get_connection() as conn:
        db.declarar_empresa(conn, DEMO)
        conn.execute("delete from fato_item_venda")
