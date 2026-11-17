#!/usr/bin/env python3
"""
reconciliacao_carga.py — Invariantes de carga e RECONCILIAÇÃO com planilha de
teste (parecer da banca final, F06).

A banca observa que a contagem de 9 tabelas na restauração "não prova igualdade
de valores e relações" e pede: explicitar o tratamento de linhas repetidas do
mesmo produto na mesma venda (para o reenvio não duplicar nem a deduplicação
eliminar itens legítimos), mostrar os invariantes de carga e reconciliar vendas
distintas, itens, faturamento e ticket, validando chaves e integridade
referencial.

Este script monta uma planilha de teste com conteúdo conhecido, carrega pela
ETL real (`app.importacao.etl.importar`) e reconcilia o ESPERADO (recomputado da
planilha em Python) contra o CARREGADO (consultado no banco), célula a célula.
Invariantes verificados:

  - grão (empresa, venda, produto): produto repetido na mesma venda é SOMADO
    (não descartado); o mesmo produto em vendas diferentes continua separado;
  - reconciliação de valor: vendas distintas, itens, faturamento, ticket;
  - integridade referencial: nenhuma linha de fato órfã (produto/data/cliente/
    vendedor);
  - idempotência: reenviar o mesmo arquivo gera um dataset isolado com os mesmos
    totais, sem duplicar itens dentro do dataset.

Uso:
    DATABASE_URL=postgresql://... python scripts/reconciliacao_carga.py --saida docs/evidencias
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))

import psycopg  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from app.importacao.etl import importar  # noqa: E402  (ETL REAL)

CAB = ["venda_id", "data_venda", "produto", "categoria", "cliente", "vendedor",
       "canal", "forma_pagamento", "quantidade", "valor_total"]

# Planilha de teste (valores conferíveis à mão). Inclui, de propósito:
#  - V1: produto repetido na mesma venda (Caneca + "caneca ") -> deve SOMAR;
#  - V1: multi-item (Caneca somada + Camiseta);
#  - Camiseta em V1 e V3 (vendas distintas) -> NÃO pode fundir entre vendas.
LINHAS = [
    # venda, data,          produto,   categoria,  cliente,      vendedor,  canal, pagamento, qtd, total
    ["V1", "2024-03-10", "Caneca",   "Casa",     "Ana Lima",   "Bia",     "loja", "pix",    2, 50.00],
    ["V1", "2024-03-10", "caneca ",  "Casa",     "Ana Lima",   "Bia",     "loja", "pix",    1, 25.00],
    ["V1", "2024-03-10", "Camiseta", "Vestuário","Ana Lima",   "Bia",     "loja", "pix",    1, 80.00],
    ["V2", "2024-03-11", "Caneca",   "Casa",     "João Souza", "Caio",    "site", "cartao", 1, 25.00],
    ["V2", "2024-03-11", "Bolo",     "Alimentos","João Souza", "Caio",    "site", "cartao", 2, 30.00],
    ["V3", "2024-03-12", "Camiseta", "Vestuário","Marcos Reis","Bia",     "loja", "boleto", 1, 80.00],
]


def _esperado():
    """Reconstitui, da planilha, a verdade esperada aplicando o grão."""
    itens: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    qtd: dict[tuple[str, str], int] = defaultdict(int)
    vendas, faturamento = set(), Decimal("0.00")
    for (vid, _d, prod, *_rest, q, tot) in LINHAS:
        chave = (vid, prod.strip().lower())  # norm_key simplificado (sem acento aqui)
        itens[chave] += Decimal(str(tot))
        qtd[chave] += q
        vendas.add(vid)
        faturamento += Decimal(str(tot))
    return {
        "vendas_distintas": len(vendas),
        "itens": len(itens),                       # linhas de fato após o grão
        "faturamento": faturamento,
        "ticket": (faturamento / len(vendas)).quantize(Decimal("0.01")),
        "linhas_planilha": len(LINHAS),
        "linhas_agrupadas": len(LINHAS) - len(itens),
        "caneca_v1_qtd": qtd[("V1", "caneca")],    # repetida somada
        "caneca_v1_total": itens[("V1", "caneca")],
    }


def _xlsx_bytes():
    wb = Workbook()
    ws = wb.active
    ws.append(CAB)
    for ln in LINHAS:
        ws.append(ln)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _carregado(cur, emp):
    cur.execute(
        "select count(distinct venda_id), count(*), coalesce(sum(valor_total),0), "
        "coalesce(sum(valor_total)/nullif(count(distinct venda_id),0),0) "
        "from fato_item_venda where empresa_id=%s", (emp,))
    v, itens, fat, ticket = cur.fetchone()
    cur.execute(
        "select f.quantidade, f.valor_total from fato_item_venda f "
        "join dim_produto p on p.id=f.produto_id "
        "where f.empresa_id=%s and p.nome_norm='caneca' and f.venda_id='V1'", (emp,))
    caneca = cur.fetchone()
    # integridade referencial: nenhuma linha de fato órfã
    cur.execute(
        "select count(*) from fato_item_venda f where empresa_id=%s and ("
        " not exists (select 1 from dim_produto p where p.id=f.produto_id)"
        " or not exists (select 1 from dim_data d where d.id=f.data_id)"
        " or (f.cliente_id is not null and not exists (select 1 from dim_cliente c where c.id=f.cliente_id))"
        " or (f.vendedor_id is not null and not exists (select 1 from dim_vendedor v where v.id=f.vendedor_id)))",
        (emp,))
    orfas = cur.fetchone()[0]
    return {
        "vendas_distintas": v, "itens": itens,
        "faturamento": Decimal(str(fat)), "ticket": Decimal(str(ticket)).quantize(Decimal("0.01")),
        "caneca_v1_qtd": caneca[0] if caneca else None,
        "caneca_v1_total": Decimal(str(caneca[1])) if caneca else None,
        "orfas": orfas,
    }


def main():
    ap = argparse.ArgumentParser(description="Reconciliação de carga com planilha de teste (F06).")
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("Defina DATABASE_URL (banco com as migrations aplicadas).")

    esp = _esperado()
    conteudo = _xlsx_bytes()
    criadas = []
    try:
        with psycopg.connect(dsn, prepare_threshold=None) as conn:
            rel1 = importar(conteudo, "reconciliacao_teste.xlsx", conn, dono_id=None)
            criadas.append(rel1["empresa_id"])
            # idempotência: reenviar o MESMO arquivo -> dataset isolado novo
            rel2 = importar(conteudo, "reconciliacao_teste.xlsx", conn, dono_id=None)
            criadas.append(rel2["empresa_id"])
            with conn.cursor() as cur:
                car1 = _carregado(cur, rel1["empresa_id"])
                car2 = _carregado(cur, rel2["empresa_id"])

        # ---- checagens ----
        def ok(a, b):
            return "✅" if a == b else "❌"

        checagens = [
            ("Vendas distintas", esp["vendas_distintas"], car1["vendas_distintas"]),
            ("Itens (linhas de fato, após o grão)", esp["itens"], car1["itens"]),
            ("Faturamento total", esp["faturamento"], car1["faturamento"]),
            ("Ticket médio", esp["ticket"], car1["ticket"]),
            ("Linhas agrupadas (repetidas somadas)", esp["linhas_agrupadas"], rel1["linhas_agrupadas"]),
            ("Caneca em V1 — quantidade somada", esp["caneca_v1_qtd"], car1["caneca_v1_qtd"]),
            ("Caneca em V1 — valor somado", esp["caneca_v1_total"], car1["caneca_v1_total"]),
        ]
        tudo_ok = all(a == b for _n, a, b in checagens) and car1["orfas"] == 0
        idem_ok = (rel1["empresa_id"] != rel2["empresa_id"]
                   and car1["faturamento"] == car2["faturamento"]
                   and car1["itens"] == car2["itens"])

        agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")
        L = [
            "# Reconciliação de carga com planilha de teste (F06)",
            "",
            "Planilha de teste com conteúdo conhecido, carregada pela ETL real",
            "(`app.importacao.etl.importar`) e reconciliada contra o banco. Gerado por",
            "`scripts/reconciliacao_carga.py`.",
            "",
            f"- **Data:** {agora}",
            f"- **Planilha:** {esp['linhas_planilha']} linhas · {esp['vendas_distintas']} vendas · "
            f"inclui produto repetido na mesma venda (grão) e multi-item",
            "",
            "## Reconciliação (planilha esperado × banco carregado)",
            "",
            "| Invariante | Esperado (planilha) | Carregado (banco) | OK |",
            "|---|---|---|:-:|",
        ]
        for nome, a, b in checagens:
            L.append(f"| {nome} | {a} | {b} | {ok(a, b)} |")
        L.append(f"| Integridade referencial (linhas de fato órfãs) | 0 | {car1['orfas']} | "
                 f"{'✅' if car1['orfas'] == 0 else '❌'} |")
        L += [
            "",
            "## Invariantes de grão",
            "",
            "- **Produto repetido na mesma venda é SOMADO, não descartado:** as duas linhas",
            f"  de \"Caneca\"/\"caneca \" em V1 viram **1 item** com quantidade "
            f"**{esp['caneca_v1_qtd']}** e total **R$ {esp['caneca_v1_total']}** "
            "(a dedupe por `nome_norm` casa as duas grafias; o valor não se perde).",
            "- **Mesmo produto em vendas diferentes continua separado:** \"Camiseta\" em V1 e V3",
            "  são dois itens, em duas vendas — a chave do grão é (empresa, venda, produto).",
            "",
            "## Idempotência / reenvio",
            "",
            f"Reenviar o mesmo arquivo criou um dataset isolado "
            f"(`{rel2['empresa_id'][:8]}…` ≠ `{rel1['empresa_id'][:8]}…`) com **os mesmos**",
            f"totais (faturamento R$ {car2['faturamento']}, {car2['itens']} itens), sem duplicar",
            f"itens dentro do dataset (chave única da fato `on conflict do nothing`): "
            f"**{'✅' if idem_ok else '❌'}**.",
            "",
            f"## Resultado: {'✅ reconciliação completa' if tudo_ok and idem_ok else '❌ divergência'}",
            "",
            "A reconciliação de **valor** (não só contagem de tabelas) também é a prova que a",
            "banca pede após uma restauração: as mesmas consultas (vendas, itens, faturamento,",
            "ticket, órfãs) aplicadas ao banco restaurado devem bater com a origem — ver",
            "`docs/evidencias/backup_restauracao_2026-11-05.md` para o ciclo de dump/restore.",
            "",
        ]
        md = "\n".join(L) + "\n"
        print(md)
        if args.saida:
            destino = Path(args.saida)
            destino.mkdir(parents=True, exist_ok=True)
            arq = destino / f"reconciliacao_carga_{dt.datetime.now():%Y-%m-%d_%H%M}.md"
            arq.write_text(md, encoding="utf-8")
            print("Arquivo:", arq)
        return 0 if (tudo_ok and idem_ok) else 1
    finally:
        # limpa os datasets de teste
        with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
            for emp in criadas:
                for t in ("log_consulta", "fato_item_venda", "staging_venda", "importacao",
                          "dim_produto", "dim_cliente", "dim_vendedor"):
                    cur.execute(f"delete from {t} where empresa_id=%s", (emp,))
                cur.execute("delete from empresa where id=%s", (emp,))
            conn.commit()


if __name__ == "__main__":
    raise SystemExit(main())
