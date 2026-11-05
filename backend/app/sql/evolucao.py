"""Evolução de uma resposta de um mês só: a mesma métrica nos 12 meses até ele.

"Quanto faturei em outubro?" responde com um número. Sozinho, ele não diz se
outubro foi bom ou ruim. Para essas perguntas (faturamento, quantidade de
vendas, ticket médio) o /chat também devolve a série mensal dos 12 meses que
terminam no mês perguntado, e o frontend desenha a evolução com o mês em
destaque.

Mesma regra dos templates: SQL fixo e parametrizado; o usuário só influencia
os valores das datas, nunca a estrutura da consulta.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal
from typing import Any

import psycopg

from app.filtros import FILTROS
from app.sql.templates import com_filtros

MESES_DE_EVOLUCAO = 12

# intenção -> (coluna da métrica, título da evolução, SQL mensal)
CONSULTAS: dict[str, tuple[str, str, str]] = {
    "total_vendas_periodo": (
        "faturamento",
        "Faturamento mês a mês",
        """
            select to_char(d.data, 'YYYY-MM') as periodo,
                   sum(f.valor_total) as valor
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data >= %(inicio)s and d.data < %(fim)s
            group by 1
        """,
    ),
    "quantidade_vendas": (
        "quantidade_vendas",
        "Quantidade de vendas mês a mês",
        """
            select to_char(d.data, 'YYYY-MM') as periodo,
                   count(distinct f.venda_id) as valor
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data >= %(inicio)s and d.data < %(fim)s
            group by 1
        """,
    ),
    "unidades_vendidas": (
        "unidades",
        "Unidades vendidas mês a mês",
        """
            select to_char(d.data, 'YYYY-MM') as periodo,
                   sum(f.quantidade) as valor
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data >= %(inicio)s and d.data < %(fim)s
            group by 1
        """,
    ),
    # mesma fórmula do template ticket_medio (média por item vendido)
    "ticket_medio": (
        "ticket_medio",
        "Ticket médio mês a mês",
        """
            select to_char(d.data, 'YYYY-MM') as periodo,
                   avg(f.valor_total) as valor
            from fato_item_venda f
            join dim_data d on d.id = f.data_id
            where f.empresa_id = %(empresa_id)s
              and d.data >= %(inicio)s and d.data < %(fim)s
            group by 1
        """,
    ),
}


# Mesmo recorte da resposta (produto, categoria...): a evolução de "botas de
# couro em março" é a das botas, não a da loja inteira.
CONSULTAS = {k: (c, t, com_filtros(sql)) for k, (c, t, sql) in CONSULTAS.items()}


def parametros_de_filtro(entidades: dict[str, Any]) -> dict[str, Any]:
    return {k: entidades.get(k) for k in FILTROS}


def mes_unico(entidades: dict[str, Any]) -> tuple[int, int] | None:
    """(ano, mês) quando o período pedido é exatamente um mês do calendário."""
    try:
        ini = date.fromisoformat(str(entidades["periodo_inicio"]))
        fim = date.fromisoformat(str(entidades["periodo_fim"]))
    except (KeyError, ValueError):
        return None
    ultimo = calendar.monthrange(ini.year, ini.month)[1]
    if ini.day == 1 and fim == date(ini.year, ini.month, ultimo):
        return ini.year, ini.month
    return None


def meses_ate(ano: int, mes: int, quantidade: int = MESES_DE_EVOLUCAO) -> list[str]:
    """Rótulos 'AAAA-MM' dos `quantidade` meses que terminam em (ano, mes)."""
    rotulos = []
    for passos in range(quantidade - 1, -1, -1):
        total = ano * 12 + (mes - 1) - passos
        rotulos.append(f"{total // 12:04d}-{total % 12 + 1:02d}")
    return rotulos


def preencher(rotulos: list[str], valores: dict[str, float]) -> list[list[Any]]:
    """Série completa, com 0 nos meses sem venda (o gráfico não pula meses)."""
    return [[r, round(valores.get(r, 0.0), 2)] for r in rotulos]


def evolucao_mensal(intencao: str | None, entidades: dict[str, Any], empresa_id: str,
                    conn: psycopg.Connection) -> dict[str, Any] | None:
    consulta = CONSULTAS.get(intencao or "")
    mes = mes_unico(entidades)
    if consulta is None or mes is None:
        return None
    coluna, titulo, sql = consulta
    rotulos = meses_ate(*mes)
    a0, m0 = (int(x) for x in rotulos[0].split("-"))
    a1, m1 = mes
    inicio = date(a0, m0, 1)
    fim = date(a1 + (m1 // 12), m1 % 12 + 1, 1)  # 1º dia do mês seguinte

    linhas = conn.execute(sql, {
        "empresa_id": empresa_id, "inicio": inicio, "fim": fim,
        **parametros_de_filtro(entidades),
    }).fetchall()
    valores = {p: float(v) if isinstance(v, Decimal) else float(v or 0) for p, v in linhas}
    if sum(1 for v in valores.values() if v) < 2:
        return None  # sem histórico para comparar: fica só o número
    return {
        "titulo": titulo,
        "colunas": ["periodo", coluna],
        "linhas": preencher(rotulos, valores),
        "destaque": rotulos[-1],
    }
