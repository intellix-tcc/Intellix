"""ETL da planilha para o star schema.

Mesmo padrão do `database/seed.py`: dedupe de dimensões via
`on conflict (empresa_id, nome_norm) do nothing`, montagem da fato e
`refresh materialized view` no fim. A diferença é a fonte (planilha do
cliente, não dados sintéticos) e o registro de controle em `importacao` +
`staging_venda`.

Carga tolerante a sujeira: linha inválida (data fora do calendário, número
ilegível, produto em branco) é **rejeitada** com motivo gravado em
`staging_venda.erros`, sem derrubar o lote. A resposta devolve quantas
entraram e quantas caíram, para a tela ser honesta com o usuário.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime
from typing import Any

import psycopg

from app.importacao.leitor_excel import ler_planilha


def _norm_key(txt: Any) -> str:
    """Equivalente em Python da função norm_key() do banco (001_schema.sql):
    lower(btrim(unaccent(txt))). Usado para casar um nome vindo da planilha
    com a linha de dimensão já deduplicada por `nome_norm`, mesmo quando a
    grafia difere em acento/caixa/espaço."""
    s = "" if txt is None else str(txt)
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.strip().lower()


def _parse_data(valor: Any) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)  # 2026-03-05
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            # data de calendário (sem hora/fuso); só o .date() interessa
            return datetime.strptime(texto, fmt).date()  # noqa: DTZ007
        except ValueError:
            continue
    return None


def _parse_numero(valor: Any) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if not texto:
        return None
    # tira símbolo de moeda e espaços
    texto = re.sub(r"[^\d,.\-]", "", texto)
    if not texto:
        return None
    if "," in texto and "." in texto:
        # formato pt-BR: 1.234,56 -> ponto é milhar, vírgula é decimal
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _parse_int(valor: Any) -> int | None:
    n = _parse_numero(valor)
    if n is None:
        return None
    return round(n)


def _texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def importar(
    conteudo: bytes, nome_arquivo: str, conn: psycopg.Connection, dono_id: str | None = None
) -> dict:
    """Lê a planilha e carrega no star schema, num dataset próprio.

    Cada importação cria uma **empresa nova** (dataset isolado) e devolve o
    `empresa_id` no relatório, para o frontend reenviar nas perguntas — assim
    o chat responde sobre os dados importados, não sobre a base demo (ver
    docs/plano-ingestao-dados.md, seção multi-tenant).

    Levanta ErroImportacao (do leitor) quando a planilha é inválida como um
    todo; erros de linha isolada viram linhas rejeitadas, não exceção.
    """
    leitura = ler_planilha(conteudo, nome_arquivo)
    linhas = leitura["linhas"]
    hash_arq = hashlib.sha256(conteudo).hexdigest()

    with conn.cursor() as cur:
        # Dataset próprio deste upload: isola os dados da planilha dos demais.
        nome_empresa = f"Importação: {nome_arquivo or 'planilha.xlsx'}"
        # dono_id: usuário logado que importou (None = sem login; ver acesso.py)
        cur.execute(
            "insert into empresa (nome, dono_id) values (%s, %s) returning id",
            (nome_empresa, dono_id),
        )
        empresa_id = str(cur.fetchone()[0])

        cur.execute(
            "insert into importacao (empresa_id, nome_arquivo, hash_arquivo, status) "
            "values (%s, %s, %s, 'pendente') returning id",
            (empresa_id, nome_arquivo or "planilha.xlsx", hash_arq),
        )
        importacao_id = cur.fetchone()[0]

        # ---- valida/transforma cada linha em memória ----
        validas: list[dict] = []
        staging_rows: list[tuple] = []

        for reg in linhas:
            n = reg["_linha"]
            d = _parse_data(reg.get("data_venda"))
            produto = _texto(reg.get("produto"))
            qtd = _parse_int(reg.get("quantidade"))
            v_unit = _parse_numero(reg.get("valor_unitario"))
            desconto = _parse_numero(reg.get("desconto")) or 0.0
            v_total = _parse_numero(reg.get("valor_total"))

            erro = None
            if d is None:
                erro = "data inválida ou ausente"
            elif not produto:
                erro = "produto em branco"
            elif qtd is None or qtd <= 0:
                erro = "quantidade inválida"
            elif v_total is None and v_unit is None:
                erro = "sem valor (unitário ou total)"

            if v_total is None and v_unit is not None and qtd is not None:
                v_total = round(qtd * v_unit - desconto, 2)
            if v_unit is None and v_total is not None and qtd:
                v_unit = round((v_total + desconto) / qtd, 2)

            # venda_id: usa o informado ou sintetiza por linha (idempotente via hash)
            venda_id = _texto(reg.get("venda_id")) or f"XLS-{hash_arq[:8]}-{n}"

            staging_rows.append((
                importacao_id, empresa_id, n,
                _texto(reg.get("data_venda")), produto, _texto(reg.get("categoria")),
                _texto(reg.get("cliente")), _texto(reg.get("vendedor")),
                _texto(reg.get("canal")), _texto(reg.get("forma_pagamento")),
                _texto(reg.get("quantidade")), _texto(reg.get("valor_unitario")),
                _texto(reg.get("desconto")), _texto(reg.get("valor_total")),
                erro,
            ))

            if erro:
                continue

            validas.append({
                "venda_id": venda_id,
                "data": d,
                "produto": produto,
                "categoria": _texto(reg.get("categoria")) or None,
                "cliente": _texto(reg.get("cliente")) or None,
                "vendedor": _texto(reg.get("vendedor")) or None,
                "canal": _texto(reg.get("canal")) or None,
                "forma_pagamento": _texto(reg.get("forma_pagamento")) or None,
                "quantidade": qtd,
                "valor_unitario": v_unit,
                "desconto": desconto,
                "valor_total": v_total,
            })

        # ---- staging: grava tudo como texto (auditoria) ----
        if staging_rows:
            cur.executemany(
                "insert into staging_venda "
                "(importacao_id, empresa_id, linha_origem, data_venda, produto, categoria, "
                " cliente, vendedor, canal, forma_pagamento, quantidade, valor_unitario, "
                " desconto, valor_total, erros) "
                "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                staging_rows,
            )

        # ---- dimensões (dedupe por nome_norm) ----
        produtos = {}
        for r in validas:
            produtos.setdefault(r["produto"], r["categoria"])
        clientes = {r["cliente"] for r in validas if r["cliente"]}
        vendedores = {r["vendedor"] for r in validas if r["vendedor"]}

        if produtos:
            cur.executemany(
                "insert into dim_produto (empresa_id, nome, categoria) values (%s,%s,%s) "
                "on conflict (empresa_id, nome_norm) do nothing",
                [(empresa_id, nome, cat) for nome, cat in produtos.items()],
            )
        if clientes:
            cur.executemany(
                "insert into dim_cliente (empresa_id, nome) values (%s,%s) "
                "on conflict (empresa_id, nome_norm) do nothing",
                [(empresa_id, c) for c in clientes],
            )
        if vendedores:
            cur.executemany(
                "insert into dim_vendedor (empresa_id, nome) values (%s,%s) "
                "on conflict (empresa_id, nome_norm) do nothing",
                [(empresa_id, v) for v in vendedores],
            )

        # ---- mapas nome_norm -> id ----
        # Chaveados pela chave canônica (nome_norm, gerado pelo banco), não
        # pelo nome cru: "Camiseta" e "camiseta " apontam para a MESMA linha
        # de dimensão, então a busca precisa normalizar igual.
        cur.execute("select id, nome_norm from dim_produto where empresa_id=%s", (empresa_id,))
        prod_id = {nk: i for i, nk in cur.fetchall()}
        cur.execute("select id, nome_norm from dim_cliente where empresa_id=%s", (empresa_id,))
        cli_id = {nk: i for i, nk in cur.fetchall()}
        cur.execute("select id, nome_norm from dim_vendedor where empresa_id=%s", (empresa_id,))
        vend_id = {nk: i for i, nk in cur.fetchall()}
        cur.execute("select id, data from dim_data")
        data_id = {d: i for i, d in cur.fetchall()}

        # ---- fato ----
        fato_rows = []
        for r in validas:
            did = data_id.get(r["data"])
            if did is None:
                # data válida mas fora do intervalo de dim_data (2023-2026):
                # conta como rejeitada (linhas_lidas - linhas_validas)
                continue
            fato_rows.append((
                empresa_id, r["venda_id"], did, prod_id[_norm_key(r["produto"])],
                cli_id.get(_norm_key(r["cliente"])) if r["cliente"] else None,
                vend_id.get(_norm_key(r["vendedor"])) if r["vendedor"] else None,
                r["canal"], r["forma_pagamento"], r["quantidade"],
                r["valor_unitario"], r["desconto"], r["valor_total"],
                importacao_id,
            ))

        if fato_rows:
            cur.executemany(
                "insert into fato_item_venda "
                "(empresa_id, venda_id, data_id, produto_id, cliente_id, vendedor_id, "
                " canal, forma_pagamento, quantidade, valor_unitario, desconto, valor_total, "
                " origem_importacao) "
                "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "on conflict (empresa_id, venda_id, produto_id) do nothing",
                fato_rows,
            )

        linhas_validas = len(fato_rows)
        linhas_rejeitadas = leitura["total_linhas"] - linhas_validas

        cur.execute(
            "update importacao set status='processada', linhas_lidas=%s, "
            "linhas_validas=%s, linhas_rejeitadas=%s where id=%s",
            (leitura["total_linhas"], linhas_validas, linhas_rejeitadas, importacao_id),
        )

        # view materializada de totais mensais (ajuda a meta de < 3s no /chat)
        cur.execute("refresh materialized view mv_faturamento_mensal;")

    conn.commit()

    return {
        "importacao_id": str(importacao_id),
        "empresa_id": empresa_id,
        "status": "processada",
        "linhas_lidas": leitura["total_linhas"],
        "linhas_validas": linhas_validas,
        "linhas_rejeitadas": linhas_rejeitadas,
        "colunas_encontradas": leitura["colunas_encontradas"],
        "colunas_ignoradas": leitura["extras"],
    }
