"""Pool de conexões (app/db.py).

Os dois primeiros testes rodam sem banco (CI). Os de integração só rodam com
DATABASE_URL, como os de test_chat_integration.py.
"""

import os

import psycopg
import pytest
from app import db
from psycopg_pool import PoolTimeout

com_banco = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="precisa de backend/.env com DATABASE_URL",
)


def test_importar_db_nao_exige_banco(monkeypatch):
    # o pool é preguiçoso: sem DATABASE_URL, só falha quando alguém pede conexão
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(db, "_pool", None)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db.get_connection()


def test_timeout_do_pool_e_tratado_como_banco_fora_do_ar():
    # o executor e o fallback 503 tratam psycopg.OperationalError
    assert issubclass(PoolTimeout, psycopg.OperationalError)


@com_banco
def test_conexao_e_reaproveitada():
    # O pool pode ter mais de uma conexão e as entrega em rodízio, então o
    # objeto pode mudar; o que importa é que nenhuma conexão NOVA é aberta.
    pool = db.get_pool()
    pool.wait()
    abertas_antes = pool.get_stats().get("connections_num", 0)
    for _ in range(5):
        with db.get_connection() as conn:
            conn.execute("select 1")
    assert pool.get_stats().get("connections_num", 0) == abertas_antes


@com_banco
def test_consulta_repetida_nao_quebra_no_transaction_pooler():
    # Sem prepare_threshold=None, a 5a execução da mesma consulta vira
    # prepared statement e o pooler (porta 6543) responde erro nas seguintes.
    for _ in range(8):
        with db.get_connection() as conn:
            linha = conn.execute("select %s::int + 1", (1,)).fetchone()
            assert linha[0] == 2
