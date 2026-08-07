#!/usr/bin/env python3
"""
seed.py — popula o banco do Intellix com dados sintéticos de vendas.

Uso:
    python seed.py --dry-run   # gera em memória e mostra as estatísticas (NÃO toca no banco)
    python seed.py             # insere no banco apontado por DATABASE_URL

Pré-requisitos:
    - 001_schema.sql e 002_dim_data.sql já aplicados (dim_data com 1461 linhas)
    - variável de ambiente DATABASE_URL (pooler do Supabase, porta 6543)
    - pip install "psycopg[binary]"   (só necessário para inserir de verdade)

Idempotente: usa um seed aleatório fixo e "on conflict do nothing".
Rodar duas vezes NÃO duplica dados.

A sazonalidade (dezembro ~4x fevereiro) é DE PROPÓSITO: deixa a demo
("vendi mais em março ou abril?") interessante.
"""

import argparse
import os
import random
import sys
from datetime import date

# --------------------------------------------------------------------- #
# Parâmetros                                                            #
# --------------------------------------------------------------------- #
SEED = 42
EMPRESA_ID = "00000000-0000-0000-0000-000000000001"

N_VENDAS = 3527                 # ~2,7 mi de faturamento com o resto dos parâmetros
ANOS = [2023, 2024, 2025, 2026]

# Peso sazonal por mês. dez/fev = 3.60/0.90 = 4x, de propósito.
PESO_MES = {
    1: 1.00, 2: 0.90, 3: 1.15, 4: 1.25, 5: 1.35, 6: 1.50,
    7: 1.20, 8: 1.10, 9: 1.30, 10: 1.55, 11: 2.10, 12: 3.60,
}

# itens por venda (média ~2,5)  ->  ~8.800 itens
ITENS_QTD = [1, 2, 3, 4, 5, 6]
ITENS_PESO = [0.28, 0.30, 0.20, 0.12, 0.06, 0.04]

# quantidade por item (média ~2,4)
UNID_QTD = [1, 2, 3, 4, 5]
UNID_PESO = [0.28, 0.30, 0.22, 0.13, 0.07]

CANAIS = ["loja", "site", "whatsapp", "marketplace"]
CANAIS_PESO = [0.45, 0.25, 0.20, 0.10]
PAGAMENTOS = ["pix", "cartao_credito", "cartao_debito", "dinheiro", "boleto"]
PAGAMENTOS_PESO = [0.34, 0.30, 0.16, 0.14, 0.06]

# Catálogo: (nome, preço). Média ~127, o que fecha o ticket médio ~760-780.
CATALOGO = {
    "Vestuário": [
        ("Camiseta básica", 49.90), ("Calça jeans", 159.90), ("Vestido casual", 189.90),
        ("Jaqueta corta-vento", 249.90), ("Moletom", 139.90), ("Camisa social", 119.90),
    ],
    "Calçados": [
        ("Tênis casual", 279.90), ("Sandália rasteira", 89.90), ("Bota couro", 329.90),
        ("Chinelo", 39.90), ("Sapatênis", 199.90),
    ],
    "Acessórios": [
        ("Boné", 59.90), ("Cinto de couro", 69.90), ("Bolsa transversal", 199.90),
        ("Carteira", 89.90), ("Óculos de sol", 149.90), ("Relógio digital", 249.90),
    ],
    "Eletrônicos": [
        ("Fone bluetooth", 149.90), ("Caixa de som portátil", 219.90), ("Carregador rápido", 49.90),
        ("Cabo USB-C", 29.90), ("Smartwatch", 399.90), ("Power bank", 119.90),
    ],
    "Casa": [
        ("Jogo de toalhas", 99.90), ("Panela antiaderente", 129.90), ("Luminária de mesa", 79.90),
        ("Almofada decorativa", 39.90), ("Kit organizador", 59.90),
    ],
    "Beleza": [
        ("Perfume importado", 189.90), ("Kit skincare", 149.90), ("Shampoo profissional", 34.90),
        ("Batom matte", 29.90), ("Creme hidratante", 59.90),
    ],
    "Alimentos": [
        ("Caixa de bombons", 44.90), ("Cesta de café", 129.90), ("Kit gourmet", 89.90),
    ],
    "Bebidas": [
        ("Vinho tinto", 79.90), ("Espumante", 99.90), ("Kit cervejas artesanais", 69.90),
        ("Café especial", 49.90),
    ],
}

PRIMEIROS = ["Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Henrique",
             "Isabela", "João", "Karina", "Lucas", "Marina", "Nicolas", "Olívia", "Pedro",
             "Renata", "Samuel", "Tatiane", "Vinícius", "Beatriz", "Rafael", "Camila", "Thiago"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Pereira", "Lima", "Costa", "Ferreira",
              "Almeida", "Ribeiro", "Carvalho", "Gomes", "Martins", "Araújo", "Barbosa"]

VENDEDORES = ["Amanda Rocha", "Carlos Nunes", "Fernanda Dias", "Rodrigo Melo",
              "Patrícia Alves", "Gustavo Pinto"]


# --------------------------------------------------------------------- #
# Geração em memória                                                    #
# --------------------------------------------------------------------- #
def gerar():
    random.seed(SEED)

    produtos = [(nome, cat, preco)
                for cat, itens in CATALOGO.items()
                for (nome, preco) in itens]

    # clientes com peso desigual -> top_clientes fica interessante
    clientes = []
    for _ in range(160):
        nome = f"{random.choice(PRIMEIROS)} {random.choice(SOBRENOMES)}"
        clientes.append(nome)
    clientes = list(dict.fromkeys(clientes))  # remove eventuais repetidos
    pesos_cli = [random.random() ** 2 + 0.05 for _ in clientes]  # skew

    meses = list(PESO_MES.keys())
    pesos_mes = list(PESO_MES.values())

    vendas = []   # cada venda: dict com cabeçalho + lista de itens
    for i in range(N_VENDAS):
        ano = random.choice(ANOS)
        mes = random.choices(meses, weights=pesos_mes, k=1)[0]
        dia = random.randint(1, _dias_no_mes(ano, mes))
        d = date(ano, mes, dia)

        cabecalho = {
            "venda_id": f"V{i:06d}",
            "data": d,
            "cliente": random.choices(clientes, weights=pesos_cli, k=1)[0],
            "vendedor": random.choice(VENDEDORES),
            "canal": random.choices(CANAIS, weights=CANAIS_PESO, k=1)[0],
            "pagamento": random.choices(PAGAMENTOS, weights=PAGAMENTOS_PESO, k=1)[0],
        }

        n_itens = random.choices(ITENS_QTD, weights=ITENS_PESO, k=1)[0]
        n_itens = min(n_itens, len(produtos))
        escolhidos = random.sample(produtos, n_itens)  # produtos distintos na mesma venda

        itens = []
        for (nome, cat, preco) in escolhidos:
            qtd = random.choices(UNID_QTD, weights=UNID_PESO, k=1)[0]
            bruto = round(qtd * preco, 2)
            desconto = 0.0
            if random.random() < 0.08:                 # 8% dos itens têm desconto
                desconto = round(bruto * random.uniform(0.05, 0.10), 2)
            total = round(bruto - desconto, 2)
            itens.append({
                "produto": nome, "categoria": cat, "qtd": qtd,
                "valor_unitario": preco, "desconto": desconto, "valor_total": total,
            })

        cabecalho["itens"] = itens
        vendas.append(cabecalho)

    return produtos, clientes, vendas


def _dias_no_mes(ano, mes):
    if mes == 12:
        prox = date(ano + 1, 1, 1)
    else:
        prox = date(ano, mes + 1, 1)
    return (prox - date(ano, mes, 1)).days


# --------------------------------------------------------------------- #
# Estatísticas (dry-run e run)                                          #
# --------------------------------------------------------------------- #
def imprimir_estatisticas(vendas):
    total_itens = sum(len(v["itens"]) for v in vendas)
    faturamento = sum(it["valor_total"] for v in vendas for it in v["itens"])
    ticket = faturamento / len(vendas) if vendas else 0

    por_mes = {m: 0.0 for m in range(1, 13)}
    for v in vendas:
        for it in v["itens"]:
            por_mes[v["data"].month] += it["valor_total"]
    maximo = max(por_mes.values()) or 1

    print(f"  {total_itens:,} itens em {len(vendas):,} vendas")
    print(f"  faturamento total: R$ {faturamento:,.2f}")
    print(f"  ticket médio: R$ {ticket:,.2f}")
    print("  faturamento por mês:")
    for m in range(1, 13):
        barra = "█" * int(40 * por_mes[m] / maximo)
        print(f"    {m:2d}: R$ {por_mes[m]:>12,.2f}  {barra}")


# --------------------------------------------------------------------- #
# Inserção no banco                                                     #
# --------------------------------------------------------------------- #
def inserir(produtos, clientes, vendas, dsn):
    import psycopg  # importado só aqui: dry-run não precisa da lib

    # prepare_threshold=None: o Transaction pooler (6543) opera em modo transação
    # e não suporta prepared statements. Sem isto, o executemany quebra no meio.
    with psycopg.connect(dsn, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            # dimensões (on conflict resolve dedupe via nome_norm)
            cur.executemany(
                "insert into dim_produto (empresa_id, nome, categoria) "
                "values (%s,%s,%s) on conflict (empresa_id, nome_norm) do nothing",
                [(EMPRESA_ID, nome, cat) for (nome, cat, _) in produtos],
            )
            cur.executemany(
                "insert into dim_cliente (empresa_id, nome) "
                "values (%s,%s) on conflict (empresa_id, nome_norm) do nothing",
                [(EMPRESA_ID, c) for c in clientes],
            )
            cur.executemany(
                "insert into dim_vendedor (empresa_id, nome) "
                "values (%s,%s) on conflict (empresa_id, nome_norm) do nothing",
                [(EMPRESA_ID, v) for v in VENDEDORES],
            )

            # mapas nome -> id
            cur.execute("select id, nome from dim_produto where empresa_id=%s", (EMPRESA_ID,))
            prod_id = {n: i for i, n in cur.fetchall()}
            cur.execute("select id, nome from dim_cliente where empresa_id=%s", (EMPRESA_ID,))
            cli_id = {n: i for i, n in cur.fetchall()}
            cur.execute("select id, nome from dim_vendedor where empresa_id=%s", (EMPRESA_ID,))
            vend_id = {n: i for i, n in cur.fetchall()}

            # mapa data -> data_id
            cur.execute("select id, data from dim_data")
            data_id = {d: i for i, d in cur.fetchall()}
            if not data_id:
                sys.exit("dim_data está vazia. Rode o 002_dim_data.sql antes do seed.")

            # fato em lote
            linhas = []
            for v in vendas:
                for it in v["itens"]:
                    linhas.append((
                        EMPRESA_ID, v["venda_id"], data_id[v["data"]],
                        prod_id[it["produto"]], cli_id[v["cliente"]], vend_id[v["vendedor"]],
                        v["canal"], v["pagamento"], it["qtd"],
                        it["valor_unitario"], it["desconto"], it["valor_total"],
                    ))

            cur.executemany(
                "insert into fato_item_venda "
                "(empresa_id, venda_id, data_id, produto_id, cliente_id, vendedor_id, "
                " canal, forma_pagamento, quantidade, valor_unitario, desconto, valor_total) "
                "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "on conflict (empresa_id, venda_id, produto_id) do nothing",
                linhas,
            )

            # atualiza a view materializada de totais mensais
            cur.execute("refresh materialized view mv_faturamento_mensal;")
        conn.commit()

    print(f"\n  inseridas {len(vendas):,} vendas / "
          f"{sum(len(v['itens']) for v in vendas):,} itens no banco.")


# --------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Seed de dados de vendas do Intellix.")
    ap.add_argument("--dry-run", action="store_true",
                    help="gera em memória e mostra as estatísticas, sem tocar no banco")
    args = ap.parse_args()

    produtos, clientes, vendas = gerar()
    imprimir_estatisticas(vendas)

    if args.dry_run:
        print("\n  [dry-run] nada foi inserido.")
        return

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("\nDefina DATABASE_URL antes de rodar sem --dry-run.")
    inserir(produtos, clientes, vendas, dsn)


if __name__ == "__main__":
    main()
