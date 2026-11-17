#!/usr/bin/env python3
"""
demo_isolamento.py — Demonstração de isolamento entre empresas com dados
FICTÍCIOS (parecer da banca final, F05/F09).

A banca pede, para a defesa, "demonstrar o isolamento entre empresas com dados
fictícios ... o perfil restrito, as regras de acesso e a auditoria, sem usar
contas reais". Os testes já provam a matriz de autorização (test_isolamento.py)
e o RLS (test_rls.py); este script é a DEMONSTRAÇÃO ao vivo: cria duas empresas
inventadas, conecta como o usuário de aplicação de privilégio mínimo
(`intellix_app`) e mostra, consulta a consulta, que uma empresa não alcança a
outra — nem quando tenta de propósito.

Camadas demonstradas:
  1. RLS no Postgres: sem declarar a empresa, o app não vê nada (padrão nega);
     declarada a empresa A, vê só A; pedir B explicitamente devolve zero linhas.
  2. Privilégio mínimo: `intellix_app` não consegue apagar vendas.
  3. Auditoria: cada consulta grava em `log_consulta`, também sujeita ao RLS.
  4. Contraste: os scripts administrativos (`postgres`) enxergam as duas — por
     isso o backend de produção conecta como `intellix_app`, não como `postgres`.

Nenhum dado real é usado. As empresas têm ids e nomes fictícios e são removidas
ao final (use --manter para deixá-las para uma demonstração interativa).

Uso:
    DATABASE_URL=postgresql://postgres:***@localhost:5432/intellix \\
        python scripts/demo_isolamento.py --saida docs/evidencias
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from decimal import Decimal
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parent.parent

# Duas empresas fictícias, com dono fictício distinto (para a camada de app).
A = {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa000a",
     "nome": "Padaria Pão Quente (fictícia)",
     "dono": "11111111-1111-1111-1111-111111111111"}
B = {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbb000b",
     "nome": "Livraria Saber Ler (fictícia)",
     "dono": "22222222-2222-2222-2222-222222222222"}

# Vendas fictícias: (venda_id, produto, categoria, qtd, valor_unitario, valor_total)
VENDAS_A = [
    ("VA1", "Pão francês (kg)", "Padaria", 3, 15.00, 45.00),
    ("VA1", "Bolo de fubá", "Padaria", 1, 25.00, 25.00),   # mesma venda, 2 itens
    ("VA2", "Sonho", "Padaria", 4, 6.00, 24.00),
]
VENDAS_B = [
    ("VB1", "Dom Casmurro", "Livros", 2, 39.90, 79.80),
    ("VB2", "Gramática", "Livros", 1, 89.00, 89.00),
]


def _linhas(emp, vendas):
    return [(emp["id"], vid, prod, cat, q, vu, vt) for (vid, prod, cat, q, vu, vt) in vendas]


def _total(vendas) -> Decimal:
    return sum((Decimal(str(vt)) for *_r, vt in vendas), Decimal("0.00"))


def _vendas_distintas(vendas) -> int:
    return len({vid for vid, *_ in vendas})


def criar(cur, emp, vendas):
    # dono fictício no stub auth.users (FK de empresa.dono_id) — nunca uma conta real
    cur.execute("insert into auth.users (id) values (%s) on conflict (id) do nothing", (emp["dono"],))
    cur.execute("insert into empresa (id, nome, dono_id) values (%s,%s,%s) "
                "on conflict (id) do update set dono_id = excluded.dono_id",
                (emp["id"], emp["nome"], emp["dono"]))
    for (_e, vid, prod, cat, q, vu, vt) in _linhas(emp, vendas):
        cur.execute("insert into dim_produto (empresa_id, nome, categoria) values (%s,%s,%s) "
                    "on conflict (empresa_id, nome_norm) do nothing", (emp["id"], prod, cat))
    cur.execute("select id, nome from dim_produto where empresa_id=%s", (emp["id"],))
    pid = {n: i for i, n in cur.fetchall()}
    cur.execute("select id from dim_data where data='2024-03-15'")
    did = cur.fetchone()[0]
    for (_e, vid, prod, cat, q, vu, vt) in _linhas(emp, vendas):
        cur.execute(
            "insert into fato_item_venda (empresa_id, venda_id, data_id, produto_id, "
            "canal, forma_pagamento, quantidade, valor_unitario, desconto, valor_total) "
            "values (%s,%s,%s,%s,'loja','pix',%s,%s,0,%s) "
            "on conflict (empresa_id, venda_id, produto_id) do nothing",
            (emp["id"], vid, did, pid[prod], q, vu, vt))


def limpar(cur):
    for emp in (A, B):
        for t in ("log_consulta", "fato_item_venda", "dim_produto"):
            cur.execute(f"delete from {t} where empresa_id=%s", (emp["id"],))
        cur.execute("delete from empresa where id=%s", (emp["id"],))
        cur.execute("delete from auth.users where id=%s", (emp["dono"],))


class Passo:
    def __init__(self, titulo, ok, detalhe):
        self.titulo, self.ok, self.detalhe = titulo, ok, detalhe


def executar(dsn: str, manter: bool) -> list[Passo]:
    passos: list[Passo] = []

    def reg(titulo, ok, detalhe):
        passos.append(Passo(titulo, ok, detalhe))

    with psycopg.connect(dsn, prepare_threshold=None, autocommit=True) as conn:
        with conn.cursor() as cur:
            limpar(cur)  # idempotente
            criar(cur, A, VENDAS_A)
            criar(cur, B, VENDAS_B)
            tot_a, tot_b = _total(VENDAS_A), _total(VENDAS_B)

            # ---- contraste: postgres (admin) vê as duas -------------------
            cur.execute("select count(distinct empresa_id) from fato_item_venda "
                        "where empresa_id in (%s,%s)", (A["id"], B["id"]))
            n_admin = cur.fetchone()[0]
            reg("Admin (`postgres`) enxerga as duas empresas",
                n_admin == 2, f"count(distinct empresa_id) = {n_admin} (scripts de backup/seed usam este papel)")

        # ---- como o app: intellix_app sob RLS -----------------------------
        with conn.cursor() as cur:
            cur.execute("set role intellix_app")

            # 1. sem declarar empresa: nada aparece (padrão nega)
            cur.execute("select count(*) from fato_item_venda")
            n0 = cur.fetchone()[0]
            reg("Sem declarar empresa, o app não vê nada",
                n0 == 0, f"count(*) = {n0} (RLS nega por padrão)")

            # 2. declarada A: vê só A
            cur.execute("select set_config('app.empresa_id', %s, false)", (A["id"],))
            cur.execute("select count(*), coalesce(sum(valor_total),0), count(distinct empresa_id) "
                        "from fato_item_venda")
            qa, sa, da = cur.fetchone()
            reg("Declarada a empresa A, vê só a empresa A",
                da == 1 and Decimal(str(sa)) == tot_a,
                f"{qa} itens, ∑=R$ {sa} (esperado {tot_a}), empresas distintas = {da}")

            # 3. declarada A, pedir B explicitamente: zero linhas
            cur.execute("select count(*) from fato_item_venda where empresa_id = %s", (B["id"],))
            nb = cur.fetchone()[0]
            reg("Com A declarada, pedir B de propósito devolve zero",
                nb == 0, f"count(*) where empresa_id = B  →  {nb} (RLS barra mesmo com filtro explícito)")

            # 4. privilégio mínimo: não apaga vendas
            try:
                cur.execute("delete from fato_item_venda")
                negou, msg = False, "APAGOU (não deveria!)"
            except psycopg.errors.InsufficientPrivilege as e:
                negou, msg = True, "permission denied (sem grant de delete)"
                conn.rollback() if not conn.autocommit else None
            reg("Privilégio mínimo: o app não apaga vendas", negou, msg)

            # 5. auditoria sob RLS: grava sob A; tentar gravar para B é barrado
            # (intellix_app tem insert mas NÃO select em log_consulta — o app
            # audita, não lê auditoria de volta; isso é lido pelo admin abaixo).
            cur.execute("select set_config('app.empresa_id', %s, false)", (A["id"],))
            cur.execute("insert into log_consulta (empresa_id, pergunta, intencao, confianca) "
                        "values (%s,'quanto faturei em março?','total_vendas_periodo',0.99)",
                        (A["id"],))
            try:
                # estando em A, tentar gravar auditoria de B viola o WITH CHECK do RLS
                cur.execute("insert into log_consulta (empresa_id, pergunta, intencao, confianca) "
                            "values (%s,'espiando a outra empresa','x',0.5)", (B["id"],))
                barrou_b = False
            except psycopg.errors.InsufficientPrivilege:
                barrou_b = True
            cur.execute("reset role")

        # admin confirma a atribuição: o registro é de A, nenhum de B
        with conn.cursor() as cur:
            cur.execute("select empresa_id::text, count(*) from log_consulta "
                        "where empresa_id in (%s,%s) group by 1", (A["id"], B["id"]))
            poremp = dict(cur.fetchall())
            log_a, log_b = poremp.get(A["id"], 0), poremp.get(B["id"], 0)
            reg("Auditoria: grava sob A, barra escrita para B, fica atribuída a A",
                barrou_b and log_a >= 1 and log_b == 0,
                f"gravou em A ({log_a}); escrita de B barrada = {barrou_b}; registros de B = {log_b}")

            if manter:
                print(f"\n[--manter] empresas fictícias preservadas: A={A['id']} B={B['id']}")
            else:
                limpar(cur)

    return passos


def relatorio_md(passos: list[Passo], dsn_rotulo: str) -> str:
    agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")
    ok = sum(p.ok for p in passos)
    L = [
        "# Demonstração de isolamento entre empresas (dados fictícios)",
        "",
        "Demonstração ao vivo pedida pela banca final (F05/F09): duas empresas",
        "inventadas, o usuário de aplicação de privilégio mínimo `intellix_app`, e a",
        "prova de que uma não alcança a outra. Gerado por `scripts/demo_isolamento.py`.",
        "Nenhuma conta real é usada.",
        "",
        f"- **Data:** {agora}",
        f"- **Alvo:** {dsn_rotulo}",
        f"- **Empresas fictícias:** A `{A['nome']}` · B `{B['nome']}`",
        "",
        "## Passos",
        "",
        "| # | Demonstração | Resultado |",
        "|---|---|:-:|",
    ]
    for i, p in enumerate(passos, 1):
        L.append(f"| {i} | {p.titulo} — {p.detalhe} | {'✅' if p.ok else '❌'} |")
    L += [
        "",
        f"**{ok}/{len(passos)}** passos conferem.",
        "",
        "## Camadas do isolamento",
        "",
        "- **Autorização na aplicação** (`app/acesso.py::resolver_empresa`): dataset de",
        "  outro dono responde 404 `dataset_nao_encontrado`, idêntico ao de id inexistente",
        "  (não revela quais ids existem). Provado em `backend/tests/test_isolamento.py`.",
        "- **RLS no banco** (migration `006_rls_e_usuario_app.sql`): mesmo que uma consulta",
        "  escape, o Postgres só devolve linhas da empresa declarada na transação",
        "  (`set_config('app.empresa_id', …, true)`). Provado aqui e em `test_rls.py`.",
        "- **Privilégio mínimo**: `intellix_app` lê e insere, mas não apaga nem altera vendas,",
        "  e não acessa as views materializadas.",
        "- **Auditoria** (`log_consulta`): toda consulta é registrada, e o registro também é",
        "  isolado por empresa.",
        "",
        "## Reproduzir",
        "",
        "```bash",
        "DATABASE_URL=postgresql://postgres:***@localhost:5432/intellix \\",
        "    python scripts/demo_isolamento.py --saida docs/evidencias",
        "# para uma demonstração interativa, --manter deixa as empresas no banco",
        "cd backend && pytest tests/test_isolamento.py tests/test_rls.py -q",
        "```",
        "",
    ]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Demonstração de isolamento com empresas fictícias (F05/F09).")
    ap.add_argument("--saida", default=None, help="diretório para gravar o .md (ex.: docs/evidencias)")
    ap.add_argument("--manter", action="store_true", help="não remove as empresas fictícias ao final")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("Defina DATABASE_URL (banco com as migrations aplicadas, incluindo o RLS 006).")

    passos = executar(dsn, args.manter)
    print(f"\n{'OK':3}  DEMONSTRAÇÃO")
    for p in passos:
        print(f"{'✅' if p.ok else '❌':3}  {p.titulo} — {p.detalhe}")
    ok = sum(p.ok for p in passos)
    print(f"\n{ok}/{len(passos)} passos conferem.")

    if args.saida:
        destino = Path(args.saida)
        destino.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        arq = destino / f"demo_isolamento_{stamp}.md"
        arq.write_text(relatorio_md(passos, dsn.split("@")[-1]), encoding="utf-8")
        print(f"Relatório: {arq}")

    return 0 if ok == len(passos) else 1


if __name__ == "__main__":
    raise SystemExit(main())
