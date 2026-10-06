#!/usr/bin/env python3
"""
restore_db.py — Restaura um backup de dados (.sql do backup_db.py) num banco.

PRÉ-REQUISITO: o banco ALVO já deve ter o schema. Rode as migrations
001_schema.sql, 002_dim_data.sql e 003_views.sql nele antes (SQL Editor
do Supabase). Este script carrega só os dados.

Uso:
    python restore_db.py scripts/backups/intellix_backup_XXXX.sql --url "postgresql://ALVO...6543/postgres"

Ao final, imprime as contagens no alvo para você comparar com o manifesto
que o backup_db.py mostrou. Se baterem, o backup é restaurável de verdade.

Requer: pip install "psycopg[binary]"  (já instalado no venv do projeto)
"""
import argparse
import os
import sys

TABELAS = [
    "empresa", "dim_data", "dim_produto", "dim_cliente", "dim_vendedor",
    "importacao", "staging_venda", "fato_item_venda", "log_consulta",
]


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
    ap = argparse.ArgumentParser(description="Restore de dados do Intellix.")
    ap.add_argument("dump", help="arquivo .sql gerado pelo backup_db.py")
    ap.add_argument("--url", default=os.environ.get("DATABASE_URL"))
    args = ap.parse_args()
    url = _resolver_url(args.url)

    import psycopg

    with open(args.dump, encoding="utf-8") as fh:
        script = fh.read()

    with psycopg.connect(url, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            cur.execute(script)  # multi-statement (sem parâmetros -> simple protocol)
        conn.commit()
        # Reinserimos ids explícitos em colunas identity; sem isto, a próxima
        # inserção normal (seed/importador) colidiria. Ressincroniza cada
        # sequence para max(id).
        with conn.cursor() as cur:
            for t in ["dim_data", "dim_produto", "dim_cliente", "dim_vendedor",
                      "staging_venda", "fato_item_venda", "log_consulta"]:
                cur.execute(
                    "select setval(pg_get_serial_sequence(%s, 'id'), "
                    "coalesce((select max(id) from " + t + "), 1), "
                    "(select count(*) from " + t + ") > 0)",
                    (t,),
                )
        conn.commit()
        with conn.cursor() as cur:
            print("\n  Restore aplicado. Contagens no banco alvo:")
            total = 0
            for t in TABELAS:
                cur.execute(f"select count(*) from {t}")
                print(f"    {t:20s} {cur.fetchone()[0]:>8d}")
            cur.execute("select coalesce(sum(valor_total), 0) from fato_item_venda")
            total = cur.fetchone()[0]
            print(f"    {'sum(valor_total)':20s} {total:>14}")
    print("\n  Compare com o manifesto do backup. Iguais = restauração validada.")


if __name__ == "__main__":
    main()
