#!/usr/bin/env python3
"""
gerar_der.py — gera o DER (lógico/físico) a partir do banco IMPLANTADO, por
introspecção (feedback TC2 F07: "a figura apresentada como DER é um diagrama de
software"). Sai em Mermaid erDiagram + uma lista de colunas, PK/FK e unicidade.

Usa só as tabelas do projeto (não as internas do Supabase). O DDL sanitizado
fica versionado em database/migrations/ — este diagrama reflete o que de fato
está no banco.

Uso:
    python gerar_der.py                 # usa o .env
    python gerar_der.py --url "postgresql://...6543/postgres"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backup_db import TABELAS, _resolver_url  # noqa: E402

# tipo Postgres -> rótulo curto e válido no Mermaid (sem espaços/parênteses)
_TIPO = {
    "uuid": "uuid", "text": "text", "bigint": "bigint", "integer": "int",
    "numeric": "numeric", "timestamp with time zone": "timestamptz",
    "date": "date", "jsonb": "jsonb", "boolean": "bool",
    "character varying": "varchar", "double precision": "float",
}


def main():
    ap = argparse.ArgumentParser(description="Gera o DER do schema implantado.")
    ap.add_argument("--url", default=None)
    args = ap.parse_args()
    url = _resolver_url(args.url)

    import psycopg

    with psycopg.connect(url, prepare_threshold=None) as conn, conn.cursor() as cur:
        colunas, pks, fks, uniques = {}, {}, {}, {}
        for t in TABELAS:
            cur.execute(
                "select column_name, data_type, is_nullable "
                "from information_schema.columns "
                "where table_schema='public' and table_name=%s order by ordinal_position",
                (t,),
            )
            colunas[t] = cur.fetchall()

            cur.execute(
                "select kcu.column_name from information_schema.table_constraints tc "
                "join information_schema.key_column_usage kcu "
                "  on tc.constraint_name=kcu.constraint_name and tc.table_schema=kcu.table_schema "
                "where tc.table_schema='public' and tc.table_name=%s "
                "  and tc.constraint_type='PRIMARY KEY'",
                (t,),
            )
            pks[t] = {r[0] for r in cur.fetchall()}

            cur.execute(
                "select kcu.column_name, ccu.table_name, ccu.column_name "
                "from information_schema.table_constraints tc "
                "join information_schema.key_column_usage kcu "
                "  on tc.constraint_name=kcu.constraint_name and tc.table_schema=kcu.table_schema "
                "join information_schema.constraint_column_usage ccu "
                "  on tc.constraint_name=ccu.constraint_name "
                "where tc.table_schema='public' and tc.table_name=%s "
                "  and tc.constraint_type='FOREIGN KEY'",
                (t,),
            )
            fks[t] = cur.fetchall()  # (coluna, tabela_ref, coluna_ref)

            cur.execute(
                "select tc.constraint_name, "
                "  string_agg(kcu.column_name, ', ' order by kcu.ordinal_position) "
                "from information_schema.table_constraints tc "
                "join information_schema.key_column_usage kcu "
                "  on tc.constraint_name=kcu.constraint_name and tc.table_schema=kcu.table_schema "
                "where tc.table_schema='public' and tc.table_name=%s "
                "  and tc.constraint_type='UNIQUE' group by tc.constraint_name",
                (t,),
            )
            uniques[t] = [r[1] for r in cur.fetchall()]

    # ---- Mermaid erDiagram ----
    linhas = ["```mermaid", "erDiagram"]
    for t in TABELAS:
        fk_cols = {c for c, _, _ in fks[t]}
        linhas.append(f"  {t} {{")
        for nome, tipo, _nulavel in colunas[t]:
            marca = "PK" if nome in pks[t] else ("FK" if nome in fk_cols else "")
            linhas.append(f"    {_TIPO.get(tipo, tipo.replace(' ', '_'))} {nome} {marca}".rstrip())
        linhas.append("  }")
    # relações (pai ||--o{ filho : coluna); ignora refs a tabelas de fora (auth.users)
    for t in TABELAS:
        for col, ref_t, _ref_c in fks[t]:
            if ref_t in TABELAS:
                linhas.append(f"  {ref_t} ||--o{{ {t} : {col}")
            else:
                linhas.append(f"  {ref_t}_externo ||--o{{ {t} : {col}")
    linhas.append("```")

    # ---- Tabela de unicidade e grão ----
    extra = ["", "## Chaves e unicidade", "", "| Tabela | PK | Unicidade |", "|---|---|---|"]
    for t in TABELAS:
        pk = ", ".join(sorted(pks[t])) or "—"
        uq = " · ".join(f"({u})" for u in uniques[t]) or "—"
        extra.append(f"| {t} | {pk} | {uq} |")

    cab = [
        "# DER — modelo de dados implantado (TC2 F07)", "",
        "Gerado por introspecção do banco real (`scripts/gerar_der.py`), não um",
        "diagrama de software. DDL versionado em `database/migrations/` (001–005).",
        "",
        "- **Grão da fato (`fato_item_venda`): um ITEM de venda** (produto dentro de",
        "  uma venda). `quantidade_vendas` usa `count(distinct venda_id)`; o ticket",
        "  médio = faturamento / vendas distintas (ver sql/templates.py).",
        "- **`empresa.dono_id`** referencia `auth.users` (gerido pelo Supabase, em",
        "  outro schema), por isso essa relação não é desenhada aqui. Não há",
        "  tabela `usuario` própria do projeto.",
        "",
    ]
    md = "\n".join(cab + linhas + extra) + "\n"
    destino = Path(__file__).resolve().parent.parent / "docs" / "diagramas" / "der.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(md, encoding="utf-8")
    print(md)
    print("Arquivo:", destino)


if __name__ == "__main__":
    main()
