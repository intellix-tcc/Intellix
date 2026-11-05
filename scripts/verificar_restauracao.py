#!/usr/bin/env python3
"""
verificar_restauracao.py — prova que o backup de dados é restaurável (TC2 F10).

Restaura o .sql gerado pelo backup_db.py num **schema separado** do mesmo banco
(ambiente de verificação isolado, descartado no fim), confere as contagens
contra o manifesto do próprio dump e registra o tempo de restauração.

Por que um schema separado e não outro banco: o plano gratuito do Supabase não
dá um segundo banco à vontade; um schema próprio é um ambiente isolado de
verdade (tabelas próprias, descartado ao fim) e não toca os dados de produção.

Uso:
    python verificar_restauracao.py scripts/backups/intellix_backup_XXXX.sql
    python verificar_restauracao.py <dump.sql> --url "postgresql://...6543/postgres"

O schema (DDL) não entra no dump: ele é versionado em database/migrations/. Aqui
as tabelas do schema de verificação são criadas com `like public.<t>`.
"""
import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backup_db import TABELAS, _resolver_url  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Verifica a restauração de um backup.")
    ap.add_argument("dump", help="arquivo .sql gerado pelo backup_db.py")
    ap.add_argument("--url", default=None)
    ap.add_argument("--schema", default="verif_restore")
    args = ap.parse_args()
    url = _resolver_url(args.url)
    schema = args.schema
    script = Path(args.dump).read_text(encoding="utf-8")

    # contagens declaradas no manifesto do dump ("-- <tabela>: N linhas").
    esperado = {t: int(n) for t, n in re.findall(r"^-- (\w+): (\d+) linhas", script, re.M)}

    import psycopg
    from psycopg import sql

    with psycopg.connect(url, prepare_threshold=None, autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute(sql.SQL("drop schema if exists {} cascade").format(sql.Identifier(schema)))
        cur.execute(sql.SQL("create schema {}").format(sql.Identifier(schema)))
        for t in TABELAS:
            # like ... including all copia colunas, defaults, identity, PK/unique
            # e índices (NÃO copia FK, o que é ideal: restauração sem ordem).
            cur.execute(sql.SQL("create table {}.{} (like public.{} including all)").format(
                sql.Identifier(schema), sql.Identifier(t), sql.Identifier(t)))

        t0 = time.perf_counter()
        cur.execute(sql.SQL("set search_path to {}, public").format(sql.Identifier(schema)))
        cur.execute(script)  # inserts sem schema -> caem no schema de verificação
        segundos = time.perf_counter() - t0
        cur.execute("set search_path to public")

        print(f"\n  Restaurado no schema '{schema}' em {segundos:.1f} s")
        print(f"  {'tabela':20s} {'restaurado':>10s} {'esperado':>10s}  ok")
        tudo_ok = True
        for t in TABELAS:
            cur.execute(sql.SQL("select count(*) from {}.{}").format(
                sql.Identifier(schema), sql.Identifier(t)))
            n = cur.fetchone()[0]
            exp = esperado.get(t, n)
            ok = n == exp
            tudo_ok = tudo_ok and ok
            print(f"  {t:20s} {n:>10d} {exp:>10d}  {'OK' if ok else 'DIVERGE'}")

        cur.execute(sql.SQL("drop schema {} cascade").format(sql.Identifier(schema)))
        print("  schema de verificação descartado.")
        print("\n  RESULTADO:", "restauração VALIDADA" if tudo_ok else "DIVERGÊNCIA — ver acima")
        sys.exit(0 if tudo_ok else 1)


if __name__ == "__main__":
    main()
