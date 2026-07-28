"""Diagnostico de conexao (B7/B8). Roda de dentro de backend/:

    ../venv/Scripts/python.exe check_db.py

Nao imprime a DATABASE_URL nem a senha -- so o que precisamos saber para
ajustar os templates SQL ao schema real.
"""

from app.db import get_connection


def main() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select version()")
            print("Conectado com sucesso.")
            print("Postgres:", cur.fetchone()[0])

            cur.execute("""
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                order by table_name
            """)
            tabelas = [row[0] for row in cur.fetchall()]
            print(f"\n{len(tabelas)} tabela(s) no schema public:")
            for tabela in tabelas:
                print(f"\n  {tabela}")
                cur.execute(
                    """
                    select column_name, data_type
                    from information_schema.columns
                    where table_schema = 'public' and table_name = %(tabela)s
                    order by ordinal_position
                    """,
                    {"tabela": tabela},
                )
                for coluna, tipo in cur.fetchall():
                    print(f"    - {coluna} ({tipo})")


if __name__ == "__main__":
    main()
