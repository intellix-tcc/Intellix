import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection() -> psycopg.Connection:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL nao definida. Copie backend/.env.example para "
            "backend/.env e preencha com a connection string do Supabase."
        )
    return psycopg.connect(url)


def get_empresa_id() -> str:
    # MVP de tenant unico: sem autenticacao ainda, a empresa vem de config.
    # Quando houver login (fora do escopo do TCC por ora), isso passa a vir
    # do usuario autenticado em vez de uma env var fixa.
    empresa_id = os.environ.get("EMPRESA_ID")
    if not empresa_id:
        raise RuntimeError("EMPRESA_ID nao definida em backend/.env")
    return empresa_id
