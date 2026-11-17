#!/usr/bin/env bash
# =============================================================================
# configurar_reproducao.sh — prepara um PostgreSQL local para reproduzir as
# evidências do Intellix (parecer da banca final, F07: pacote de reprodução).
#
# Cria o banco, aplica o stub do Supabase + as migrações em ordem e popula a
# base de demonstração determinística (SEED=42). Idempotente: pode rodar de novo.
#
# Pré-requisitos: PostgreSQL 16 no ar, Python 3.12+ com psycopg instalado
# (pip install "psycopg[binary]").
#
# Uso (valores padrão entre colchetes):
#   PGPASSWORD=suasenha ./scripts/configurar_reproducao.sh
# Variáveis: DB[intellix] PGUSER[postgres] PGHOST[localhost] PGPORT[5432]
#            PYTHON[python3]
#
# Ao final, imprime o DATABASE_URL a usar nos scripts de evidência.
# =============================================================================
set -euo pipefail

DB=${DB:-intellix}
PGUSER=${PGUSER:-postgres}
PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5432}
PYTHON=${PYTHON:-python3}
: "${PGPASSWORD:?defina PGPASSWORD com a senha do usuário $PGUSER do Postgres}"
export PGPASSWORD

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"

ADMIN="postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/postgres"
DSN="postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${DB}"

echo "==> (re)criando o banco '${DB}'"
psql "$ADMIN" -v ON_ERROR_STOP=1 -tAc "drop database if exists ${DB}" >/dev/null
psql "$ADMIN" -v ON_ERROR_STOP=1 -tAc "create database ${DB}" >/dev/null

echo "==> stub do Supabase (schema auth/extensions, papéis)"
psql "$DSN" -v ON_ERROR_STOP=1 -q -f database/local/supabase_minimo.sql

echo "==> migrações (001 a 008, em ordem)"
for f in database/migrations/*.sql; do
  echo "    - $(basename "$f")"
  psql "$DSN" -v ON_ERROR_STOP=1 -q -f "$f"
done

echo "==> base de demonstração (database/seed.py, SEED=42)"
DATABASE_URL="$DSN" "$PYTHON" database/seed.py | tail -1

echo
echo "Pronto. Exporte o DATABASE_URL e rode as evidências (ver REPRODUZIR.md):"
echo "    export DATABASE_URL='${DSN}'"
