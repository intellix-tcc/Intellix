"""Panorama do mês para a tela Início (GET /resumo).

Antes, a Início era um painel com números fixos de exemplo
(frontend/src/utils/resumoExemplo.js). Este módulo entrega os mesmos blocos
com dado real do dataset consultado: indicadores com variação sobre o mês
anterior, série diária, tendência dos últimos 12 meses, categorias, canais,
ranking de produtos e observações.

Duas regras do projeto valem aqui como no /chat:
  - número sai cru (float/int), formatação de moeda é do frontend;
  - nada de adivinhar: cada observação nasce de uma regra fixa sobre os dados
    (limiares abaixo). Se nenhuma regra dispara, a lista volta vazia.

As consultas são SQL fixo e parametrizado, como os templates do /chat: o
usuário escolhe ano e mês, nunca a estrutura da consulta.

A parte de montar observações e texto é função pura (sem banco), para ser
testada sem DATABASE_URL -- ver tests/test_resumo.py.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import psycopg
from fastapi import HTTPException

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

# Limiares das observações. Baixos demais viram ruído ("cresceu 1%"); altos
# demais escondem o que interessa. Ajustáveis num lugar só.
VARIACAO_RELEVANTE_PCT = 3.0      # faturamento do mês vs anterior
VARIACAO_PRODUTO_PCT = 15.0       # alta/queda de um produto
PRODUTOS_COMPARADOS = 10          # só produtos do topo entram na comparação
# Base mínima no mês anterior (fatia do faturamento) para um produto entrar
# na comparação: sem isso, um item que vendeu uma unidade vira "+500%".
BASE_MINIMA_PRODUTO = 0.02
MAX_OBSERVACOES = 5
TOP_PRODUTOS = 5


# --------------------------------------------------------------------- #
# Datas                                                                 #
# --------------------------------------------------------------------- #
def rotulo_mes(ano: int, mes: int) -> str:
    return f"{MESES[mes - 1]} de {ano}"


def rotulo_curto(ano: int, mes: int) -> str:
    return f"{MESES[mes - 1][:3]}/{str(ano)[2:]}"


def mes_anterior(ano: int, mes: int, passos: int = 1) -> tuple[int, int]:
    total = ano * 12 + (mes - 1) - passos
    return total // 12, total % 12 + 1


def limites_mes(ano: int, mes: int) -> tuple[date, date]:
    """[início, fim) do mês -- fim exclusivo, para usar `data < fim`."""
    prox_ano, prox_mes = mes_anterior(ano, mes, -1)
    return date(ano, mes, 1), date(prox_ano, prox_mes, 1)


def escolher_mes(meses: list[tuple[int, int]], hoje: date) -> tuple[int, int]:
    """Mês padrão do painel: o mais recente com dados que já começou.

    `meses` vem do mais recente para o mais antigo. Uma planilha (ou a base
    de demonstração) pode ter datas futuras; abrir o painel num mês que ainda
    não aconteceu confundiria mais do que ajudaria.
    """
    for ano, mes in meses:
        if date(ano, mes, 1) <= hoje:
            return ano, mes
    return meses[-1]  # tudo no futuro: o mais próximo de hoje


# --------------------------------------------------------------------- #
# Formatação (só para frases; os campos numéricos saem crus)             #
# --------------------------------------------------------------------- #
def moeda(valor: float) -> str:
    inteiro, centavos = f"{valor:,.2f}".split(".")
    return f"R$ {inteiro.replace(',', '.')},{centavos}"


def pct(valor: float) -> str:
    texto = f"{abs(valor):.1f}".replace(".", ",")
    return texto.removesuffix(",0")


def variacao(atual: float, anterior: float | None) -> float | None:
    """Variação percentual com 1 casa. None quando não há base de comparação."""
    if not anterior:
        return None
    return round((atual - anterior) / anterior * 100, 1)


def nome_canal(bruto: str | None) -> str:
    if not bruto:
        return "Não informado"
    especiais = {"whatsapp": "WhatsApp", "site": "Site"}
    chave = bruto.strip().lower()
    return especiais.get(chave, chave.replace("_", " ").capitalize())


# --------------------------------------------------------------------- #
# Consultas                                                             #
# --------------------------------------------------------------------- #
SQL_MESES = """
select d.ano, d.mes, sum(f.valor_total) as faturamento
from fato_item_venda f
join dim_data d on d.id = f.data_id
where f.empresa_id = %(empresa_id)s
group by d.ano, d.mes
order by d.ano desc, d.mes desc
"""

SQL_KPIS = """
select
  coalesce(sum(f.valor_total), 0)    as faturamento,
  count(distinct f.venda_id)         as vendas,
  coalesce(sum(f.quantidade), 0)     as itens,
  count(distinct f.produto_id)       as produtos,
  count(distinct f.cliente_id)       as clientes,
  count(*)                           as registros
from fato_item_venda f
join dim_data d on d.id = f.data_id
where f.empresa_id = %(empresa_id)s
  and d.data >= %(inicio)s and d.data < %(fim)s
"""

SQL_DIARIO = """
select d.dia, sum(f.valor_total) as faturamento
from fato_item_venda f
join dim_data d on d.id = f.data_id
where f.empresa_id = %(empresa_id)s
  and d.data >= %(inicio)s and d.data < %(fim)s
group by d.dia
order by d.dia
"""

SQL_CATEGORIAS = """
select coalesce(nullif(btrim(p.categoria), ''), 'Sem categoria') as categoria,
       sum(f.valor_total) as faturamento
from fato_item_venda f
join dim_data d on d.id = f.data_id
join dim_produto p on p.id = f.produto_id
where f.empresa_id = %(empresa_id)s
  and d.data >= %(inicio)s and d.data < %(fim)s
group by 1
order by faturamento desc
"""

SQL_CANAIS = """
select f.canal, sum(f.valor_total) as faturamento
from fato_item_venda f
join dim_data d on d.id = f.data_id
where f.empresa_id = %(empresa_id)s
  and d.data >= %(inicio)s and d.data < %(fim)s
group by f.canal
order by faturamento desc
"""

# Faturamento por produto no mês e no anterior, numa passada só.
SQL_PRODUTOS = """
select p.nome,
       coalesce(sum(f.valor_total) filter (where d.data >= %(inicio)s), 0) as atual,
       coalesce(sum(f.valor_total) filter (where d.data <  %(inicio)s), 0) as anterior
from fato_item_venda f
join dim_data d on d.id = f.data_id
join dim_produto p on p.id = f.produto_id
where f.empresa_id = %(empresa_id)s
  and d.data >= %(ant_inicio)s and d.data < %(fim)s
group by p.nome
"""

# Produtos com venda nos 3 meses anteriores e nenhuma no mês escolhido.
SQL_SEM_GIRO = """
select count(*) from (
  select f.produto_id
  from fato_item_venda f
  join dim_data d on d.id = f.data_id
  where f.empresa_id = %(empresa_id)s
    and d.data >= %(tri_inicio)s and d.data < %(fim)s
  group by f.produto_id
  having sum(f.quantidade) filter (where d.data >= %(inicio)s) is null
) x
"""


def _num(valor: Any) -> float:
    if valor is None:
        return 0.0
    return float(valor)


def _kpis(conn: psycopg.Connection, empresa_id: str, inicio: date, fim: date) -> dict[str, float]:
    linha = conn.execute(SQL_KPIS, {"empresa_id": empresa_id, "inicio": inicio, "fim": fim}).fetchone()
    fat, vendas, itens, produtos, clientes, registros = linha
    return {
        "faturamento": _num(fat),
        "vendas": int(vendas),
        "itens": int(itens),
        "produtos": int(produtos),
        "clientes": int(clientes),
        "registros": int(registros),
    }


def _fatias(linhas: list[tuple], nomear=lambda n: n) -> list[dict[str, Any]]:
    total = sum(_num(v) for _, v in linhas)
    return [
        {
            "nome": nomear(nome),
            "valor": round(_num(v), 2),
            "pct": round(_num(v) / total * 100, 1) if total else 0.0,
        }
        for nome, v in linhas
    ]


# --------------------------------------------------------------------- #
# Regras de observação e texto (funções puras)                          #
# --------------------------------------------------------------------- #
def melhor_e_pior_dia_semana(ano: int, mes: int, por_dia: dict[int, float]) -> tuple[int, int] | None:
    """Índices (0=segunda) do dia da semana com maior e menor média diária.

    Média sobre todos os dias do calendário daquele dia da semana -- um dia sem
    venda conta como zero, senão um sábado com uma venda só pareceria ótimo.
    """
    if not por_dia:
        return None
    soma = [0.0] * 7
    quantos = [0] * 7
    for dia in range(1, calendar.monthrange(ano, mes)[1] + 1):
        ds = date(ano, mes, dia).weekday()
        soma[ds] += por_dia.get(dia, 0.0)
        quantos[ds] += 1
    medias = [soma[i] / quantos[i] for i in range(7)]
    melhor = max(range(7), key=lambda i: medias[i])
    pior = min(range(7), key=lambda i: medias[i])
    if melhor == pior or medias[melhor] == 0:
        return None
    return melhor, pior


def gerar_observacoes(
    *,
    ano: int,
    mes: int,
    kpi_atual: dict[str, float],
    kpi_anterior: dict[str, float],
    produtos: list[tuple[str, float, float]],
    sem_giro: int,
    canais: list[dict[str, Any]],
    dias_semana: tuple[int, int] | None,
) -> list[dict[str, Any]]:
    """Observações do mês, cada uma ligada a uma pergunta que o chat entende.

    `tipo` decide ícone e cor no frontend: alta | queda | atencao | padrao.
    """
    obs: list[dict[str, Any]] = []
    rotulo = rotulo_mes(ano, mes)
    ano_ant, mes_ant = mes_anterior(ano, mes)
    nome_mes, nome_ant = MESES[mes - 1], MESES[mes_ant - 1]

    var_fat = variacao(kpi_atual["faturamento"], kpi_anterior["faturamento"])
    if var_fat is not None and abs(var_fat) >= VARIACAO_RELEVANTE_PCT:
        sentido = "acima" if var_fat > 0 else "abaixo"
        obs.append({
            "tipo": "alta" if var_fat > 0 else "queda",
            "texto": f"Faturamento {pct(var_fat)}% {sentido} de {nome_ant}.",
            "pergunta": (
                f"Compare o faturamento de {nome_ant} de {ano_ant} com {nome_mes} de {ano}"
            ),
        })

    # Altas e quedas só entre os produtos que importam: o topo do mês anterior
    # (para queda) e do mês atual (para alta), com base de comparação real.
    base_minima = kpi_anterior["faturamento"] * BASE_MINIMA_PRODUTO
    comparaveis = [p for p in produtos if p[2] > 0 and p[2] >= base_minima]
    topo_atual = sorted(comparaveis, key=lambda p: p[1], reverse=True)[:PRODUTOS_COMPARADOS]
    topo_anterior = sorted(comparaveis, key=lambda p: p[2], reverse=True)[:PRODUTOS_COMPARADOS]

    altas = [(n, variacao(a, b)) for n, a, b in topo_atual]
    altas = [(n, v) for n, v in altas if v is not None and v >= VARIACAO_PRODUTO_PCT]
    if altas:
        nome, v = max(altas, key=lambda x: x[1])
        obs.append({
            "tipo": "alta",
            "texto": f"{nome} cresceu {pct(v)}% sobre {nome_ant}.",
            "pergunta": f"Quais os 5 produtos mais vendidos em {rotulo}?",
        })

    quedas = [(n, variacao(a, b)) for n, a, b in topo_anterior]
    quedas = [(n, v) for n, v in quedas if v is not None and v <= -VARIACAO_PRODUTO_PCT]
    if quedas:
        nome, v = min(quedas, key=lambda x: x[1])
        obs.append({
            "tipo": "queda",
            "texto": f"{nome} caiu {pct(v)}% em relação a {nome_ant}.",
            "pergunta": f"Quais os 10 produtos mais vendidos em {rotulo}?",
        })

    if sem_giro > 0:
        plural = "produtos venderam" if sem_giro > 1 else "produto vendeu"
        obs.append({
            "tipo": "atencao",
            "texto": f"{sem_giro} {plural} nos 3 meses anteriores e ficou sem saída em {nome_mes}."
            if sem_giro == 1
            else f"{sem_giro} {plural} nos 3 meses anteriores e ficaram sem saída em {nome_mes}.",
            "pergunta": f"Quais produtos não venderam em {rotulo}?",
        })

    if dias_semana:
        melhor, pior = dias_semana
        obs.append({
            "tipo": "padrao",
            "texto": (
                f"{DIAS_SEMANA[melhor].capitalize()} teve a melhor média diária; "
                f"{DIAS_SEMANA[pior]}, a mais fraca."
            ),
            "pergunta": None,
        })

    if canais and canais[0]["pct"] >= 40:
        principal = canais[0]
        obs.append({
            "tipo": "padrao",
            "texto": f"{principal['nome']} respondeu por {pct(principal['pct'])}% do faturamento.",
            "pergunta": f"Quanto vendi por canal em {rotulo}?",
        })

    return obs[:MAX_OBSERVACOES]


def gerar_resumo_texto(
    *,
    ano: int,
    mes: int,
    kpi_atual: dict[str, float],
    kpi_anterior: dict[str, float],
    categorias: list[dict[str, Any]],
    top_produtos: list[dict[str, Any]],
) -> list[str]:
    """Dois parágrafos curtos montados só com os números calculados."""
    fat = kpi_atual["faturamento"]
    vendas = kpi_atual["vendas"]
    if not vendas:
        return [f"Não houve vendas registradas em {rotulo_mes(ano, mes)}."]

    ticket = fat / vendas
    _, mes_ant = mes_anterior(ano, mes)
    nome_ant = MESES[mes_ant - 1]

    qtd = f"{vendas:,}".replace(",", ".")
    primeiro = (
        f"Em {rotulo_mes(ano, mes)}, a loja faturou {moeda(fat)} em {qtd} "
        f"{'venda' if vendas == 1 else 'vendas'}, com ticket médio de {moeda(ticket)}"
    )
    var_fat = variacao(fat, kpi_anterior["faturamento"])
    if var_fat is None:
        primeiro += "."
    elif abs(var_fat) < 0.5:
        primeiro += f", praticamente o mesmo de {nome_ant}."
    else:
        sentido = "acima" if var_fat > 0 else "abaixo"
        primeiro += f": {pct(var_fat)}% {sentido} de {nome_ant}."

    paragrafos = [primeiro]

    partes = []
    if categorias:
        c = categorias[0]
        partes.append(f"a categoria líder foi {c['nome']}, com {pct(c['pct'])}% do faturamento")
    if top_produtos:
        p = top_produtos[0]
        partes.append(f"o produto que mais faturou foi {p['nome']} ({moeda(p['valor'])})")
    if partes:
        frase = ", e ".join(partes)
        paragrafos.append(frase[0].upper() + frase[1:] + ".")

    var_ticket = variacao(ticket, (kpi_anterior["faturamento"] / kpi_anterior["vendas"]) if kpi_anterior["vendas"] else None)
    var_vendas = variacao(vendas, kpi_anterior["vendas"])
    if var_ticket is not None and var_vendas is not None and var_fat is not None and abs(var_fat) >= 0.5:
        if abs(var_vendas) >= abs(var_ticket):
            origem = "do número de vendas" if var_vendas * var_fat > 0 else "do ticket médio"
        else:
            origem = "do ticket médio" if var_ticket * var_fat > 0 else "do número de vendas"
        movimento = "alta" if var_fat > 0 else "queda"
        paragrafos.append(f"A {movimento} veio principalmente {origem}.")

    return paragrafos


# --------------------------------------------------------------------- #
# Montagem                                                              #
# --------------------------------------------------------------------- #
def montar_resumo(
    conn: psycopg.Connection,
    empresa_id: str,
    ano: int | None = None,
    mes: int | None = None,
    hoje: date | None = None,
) -> dict[str, Any]:
    # "Hoje" no fuso da loja, não no do servidor (o Render roda em UTC).
    hoje = hoje or datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    meses_brutos = conn.execute(SQL_MESES, {"empresa_id": empresa_id}).fetchall()
    if not meses_brutos:
        raise HTTPException(
            status_code=404,
            detail={
                "tipo": "sem_resultado",
                "mensagem": "Ainda não há vendas neste conjunto de dados. Importe uma planilha para ver o panorama.",
            },
        )
    meses = [(int(a), int(m)) for a, m, _ in meses_brutos]
    fat_por_mes = {(int(a), int(m)): _num(v) for a, m, v in meses_brutos}

    if ano is None or mes is None:
        ano, mes = escolher_mes(meses, hoje)

    inicio, fim = limites_mes(ano, mes)
    ano_ant, mes_ant = mes_anterior(ano, mes)
    ant_inicio, _ = limites_mes(ano_ant, mes_ant)
    tri_inicio, _ = limites_mes(*mes_anterior(ano, mes, 3))
    base = {"empresa_id": empresa_id, "inicio": inicio, "fim": fim}

    kpi_atual = _kpis(conn, empresa_id, inicio, fim)
    kpi_anterior = _kpis(conn, empresa_id, ant_inicio, inicio)

    por_dia = {int(d): _num(v) for d, v in conn.execute(SQL_DIARIO, base).fetchall()}
    dias_no_mes = calendar.monthrange(ano, mes)[1]
    serie_diaria = [{"dia": d, "valor": round(por_dia.get(d, 0.0), 2)} for d in range(1, dias_no_mes + 1)]

    serie_mensal = []
    for passos in range(11, -1, -1):
        a, m = mes_anterior(ano, mes, passos)
        serie_mensal.append({
            "ano": a, "mes": m, "rotulo": rotulo_curto(a, m),
            "valor": round(fat_por_mes.get((a, m), 0.0), 2),
        })

    categorias = _fatias(conn.execute(SQL_CATEGORIAS, base).fetchall())
    canais = _fatias(conn.execute(SQL_CANAIS, base).fetchall(), nome_canal)

    produtos = [
        (nome, _num(a), _num(b))
        for nome, a, b in conn.execute(SQL_PRODUTOS, {**base, "ant_inicio": ant_inicio}).fetchall()
    ]
    total_fat = kpi_atual["faturamento"]
    top_produtos = [
        {
            "nome": nome,
            "valor": round(a, 2),
            "pct": round(a / total_fat * 100, 1) if total_fat else 0.0,
            "variacao_pct": variacao(a, b),
        }
        for nome, a, b in sorted(produtos, key=lambda p: p[1], reverse=True)[:TOP_PRODUTOS]
        if a > 0
    ]

    sem_giro = int(conn.execute(SQL_SEM_GIRO, {**base, "tri_inicio": tri_inicio}).fetchone()[0])

    ticket = kpi_atual["faturamento"] / kpi_atual["vendas"] if kpi_atual["vendas"] else 0.0
    ticket_ant = kpi_anterior["faturamento"] / kpi_anterior["vendas"] if kpi_anterior["vendas"] else None

    kpis = [
        {"chave": "faturamento", "rotulo": "Faturamento", "valor": round(kpi_atual["faturamento"], 2),
         "formato": "moeda", "variacao_pct": variacao(kpi_atual["faturamento"], kpi_anterior["faturamento"])},
        {"chave": "ticket_medio", "rotulo": "Ticket médio", "valor": round(ticket, 2),
         "formato": "moeda", "variacao_pct": variacao(ticket, ticket_ant)},
        {"chave": "vendas", "rotulo": "Vendas", "valor": kpi_atual["vendas"],
         "formato": "numero", "variacao_pct": variacao(kpi_atual["vendas"], kpi_anterior["vendas"])},
        {"chave": "itens", "rotulo": "Itens vendidos", "valor": kpi_atual["itens"],
         "formato": "numero", "variacao_pct": variacao(kpi_atual["itens"], kpi_anterior["itens"])},
        {"chave": "clientes", "rotulo": "Clientes", "valor": kpi_atual["clientes"],
         "formato": "numero", "variacao_pct": variacao(kpi_atual["clientes"], kpi_anterior["clientes"])},
    ]

    observacoes = gerar_observacoes(
        ano=ano, mes=mes,
        kpi_atual=kpi_atual, kpi_anterior=kpi_anterior,
        produtos=produtos, sem_giro=sem_giro, canais=canais,
        dias_semana=melhor_e_pior_dia_semana(ano, mes, por_dia),
    )
    resumo_texto = gerar_resumo_texto(
        ano=ano, mes=mes, kpi_atual=kpi_atual, kpi_anterior=kpi_anterior,
        categorias=categorias, top_produtos=top_produtos,
    )

    return {
        "periodo": {
            "ano": ano, "mes": mes, "rotulo": rotulo_mes(ano, mes),
            "inicio": inicio.isoformat(), "fim": date.fromordinal(fim.toordinal() - 1).isoformat(),
        },
        "periodo_anterior": {"ano": ano_ant, "mes": mes_ant, "rotulo": rotulo_mes(ano_ant, mes_ant)},
        "meses_disponiveis": [
            {"ano": a, "mes": m, "rotulo": rotulo_mes(a, m)} for a, m in meses[:36]
        ],
        "kpis": kpis,
        "serie_diaria": serie_diaria,
        "serie_mensal": serie_mensal,
        "categorias": categorias,
        "canais": canais,
        "top_produtos": top_produtos,
        "observacoes": observacoes,
        "resumo_texto": resumo_texto,
        "total_registros": kpi_atual["registros"],
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }
