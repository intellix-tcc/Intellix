#!/usr/bin/env python3
"""
backup_db.py — Backup lógico (dados) do banco Intellix.

Gera um arquivo .sql com os INSERTs de todas as tabelas e imprime um
"manifesto" (contagem por tabela + soma de faturamento) para você conferir
na hora de restaurar.

Uso:
    python backup_db.py                    # usa DATABASE_URL do ambiente/.env
    python backup_db.py --url "postgresql://...6543/postgres"
    python backup_db.py --out-dir scripts/backups

O SCHEMA (estrutura das tabelas) NÃO entra aqui: ele é versionado em
database/migrations/ (001_schema, 002_dim_data, 003_views). Restaurar =
rodar as migrations num banco limpo e depois aplicar este arquivo de dados.
Por isso o backup é pequeno e legível: são só os dados.

Requer: pip install "psycopg[binary]"  (já instalado no venv do projeto)
Funciona pelo Transaction pooler (6543) — prepare_threshold=None.
"""
import argparse
import datetime as dt
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

# Ordem FK-safe: tabelas "pai" antes das que as referenciam.
TABELAS = [
    "empresa",
    "dim_data",
    "dim_produto",
    "dim_cliente",
    "dim_vendedor",
    "importacao",
    "staging_venda",
    "fato_item_venda",
    "log_consulta",
]


def _lit(v):
    """Converte um valor Python em literal SQL seguro."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float, Decimal)):
        return str(v)
    if isinstance(v, (dict, list)):  # jsonb
        return "'" + json.dumps(v).replace("'", "''") + "'"
    return "'" + str(v).replace("'", "''") + "'"


def _resolver_url(passada):
    """Descobre a connection string de forma tolerante a erros comuns:
    - usa --url ou DATABASE_URL do ambiente;
    - se faltar, carrega backend/.env automaticamente;
    - remove aspas e um prefixo 'DATABASE_URL=' colado por engano;
    - valida que é mesmo uma URL postgres."""
    import os
    from pathlib import Path

    url = passada
    if not url:
        # tenta backend/.env (rodando de backend/ ou da raiz do repo)
        try:
            from dotenv import load_dotenv
            aqui = Path(__file__).resolve().parent
            for cand in (Path.cwd() / ".env",
                         aqui.parent / "backend" / ".env",
                         Path.cwd() / "backend" / ".env"):
                if cand.exists():
                    load_dotenv(cand)
                    break
        except Exception:
            pass
        url = os.environ.get("DATABASE_URL")

    if url:
        url = url.strip().strip('"').strip("'").strip()
        low = url.lower()
        if low.startswith("database_url="):
            url = url.split("=", 1)[1].strip().strip('"').strip("'").strip()
        elif low.startswith("url="):
            url = url.split("=", 1)[1].strip().strip('"').strip("'").strip()
        if low.startswith("export "):
            url = url[len("export "):].strip()
            if url.lower().startswith("database_url="):
                url = url.split("=", 1)[1].strip().strip('"').strip("'").strip()

    if not url:
        import sys
        sys.exit("Sem connection string. Rode de backend/ (usa o .env) ou passe --url.")
    if not (url.startswith("postgresql://") or url.startswith("postgres://")):
        import sys
        sys.exit(
            "DATABASE_URL nao parece uma URL postgres (deve comecar com "
            "postgresql:// e terminar em :6543/postgres). Valor recebido comeca com: "
            + repr(url[:20])
        )
    return url


def main():
    ap = argparse.ArgumentParser(description="Backup de dados do Intellix.")
    ap.add_argument("--url", default=os.environ.get("DATABASE_URL"))
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    url = _resolver_url(args.url)
    out_dir = Path(args.out_dir) if args.out_dir else Path(__file__).resolve().parent / "backups"

    import psycopg
    from psycopg import sql

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"intellix_backup_{ts}.sql"

    manifesto = {}
    total = 0
    with psycopg.connect(url, prepare_threshold=None) as conn, \
         open(out_file, "w", encoding="utf-8") as f:
        f.write(f"-- Intellix — backup de dados — {dt.datetime.now().isoformat()}\n")
        f.write("-- Restaurar: num banco com as migrations 001-003 aplicadas,\n")
        f.write("--   python restore_db.py <este arquivo> --url <ALVO>\n\n")
        with conn.cursor() as cur:
            for t in TABELAS:
                cur.execute(
                    """
                    select column_name, is_identity, identity_generation
                    from information_schema.columns
                    where table_schema = 'public' and table_name = %s
                      and is_generated = 'NEVER'
                    order by ordinal_position
                    """,
                    (t,),
                )
                info = cur.fetchall()
                cols = [r[0] for r in info]
                if not cols:
                    continue
                # coluna identity GENERATED ALWAYS exige OVERRIDING SYSTEM VALUE
                # para aceitar o id explícito (necessário p/ preservar as FKs).
                overriding = any(
                    r[1] == "YES" and r[2] == "ALWAYS" for r in info
                )
                osv = "overriding system value " if overriding else ""
                collist = ", ".join(cols)
                cur.execute(
                    sql.SQL("select {} from {}").format(
                        sql.SQL(", ").join(map(sql.Identifier, cols)),
                        sql.Identifier(t),
                    )
                )
                rows = cur.fetchall()
                manifesto[t] = len(rows)
                f.write(f"\n-- {t}: {len(rows)} linhas\n")
                for row in rows:
                    vals = ", ".join(_lit(v) for v in row)
                    f.write(
                        f"insert into {t} ({collist}) {osv}values ({vals}) "
                        f"on conflict do nothing;\n"
                    )
            cur.execute("select coalesce(sum(valor_total), 0) from fato_item_venda")
            total = cur.fetchone()[0]

    print(f"\n  Backup salvo em: {out_file}")
    print("  Manifesto (confira estes números após o restore):")
    for t, n in manifesto.items():
        print(f"    {t:20s} {n:>8d}")
    print(f"    {'sum(valor_total)':20s} {total:>14}")


if __name__ == "__main__":
    main()
