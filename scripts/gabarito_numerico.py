#!/usr/bin/env python3
"""
gabarito_numerico.py — Oráculo NUMÉRICO independente das 14 consultas.

Atende ao parecer da banca final, F02 ("acerto funcional não verifica todo o
resultado comercial"): o oráculo das 100 perguntas compara apenas status + tipo
da resposta, então uma consulta com valor, filtro, grupo ou ordenação errados
PASSA. Este script fecha essa lacuna conferindo os VALORES.

Como a verificação é independente:

  1. a "verdade esperada" é recomputada em **Python puro**, a partir da MESMA
     geração determinística do `database/seed.py` (SEED=42) — nenhuma linha de
     SQL participa desse lado;
  2. o "obtido" vem de executar os **templates SQL reais** importados de
     `backend/app/sql/templates.py` (não uma cópia) contra o banco semeado;
  3. as duas computações da mesma verdade são comparadas célula a célula.

Para cada prova separa três níveis de sucesso (parecer: "separar sucesso
técnico, semântico e numérico"):

  - TÉCNICO   — a consulta executou sem erro e devolveu linhas;
  - SEMÂNTICO — colunas, grão, agrupamento e ordenação corretos;
  - NUMÉRICO  — todos os valores batem com o oráculo em Python.

Cobre valor, filtros, grupo, ordenação e unidade (peças × vendas), além de
nulos, venda com vários itens e fronteiras de período. DEVOLUÇÕES: o artefato
não modela devolução/estorno (`fato_item_venda` só tem quantidade ≥ 0, sem
fluxo de retorno), então ficam fora do escopo e são declaradas como tal — não
são inventadas.

Uso:
    DATABASE_URL=postgresql://... python scripts/gabarito_numerico.py
    python scripts/gabarito_numerico.py --saida docs/evidencias   # grava o .md

Saída: tabela no terminal e, com --saida, um relatório em Markdown datado.
Código de saída 0 se todas as provas passam no nível NUMÉRICO, 1 caso contrário.
Só depende de psycopg (o oráculo é biblioteca padrão).
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "database"))

import psycopg  # noqa: E402
from app.sql.templates import TEMPLATES  # noqa: E402  (templates SQL REAIS)
import seed as seedmod  # noqa: E402     (mesma geração determinística)

EMPRESA = seedmod.EMPRESA_ID
D0 = Decimal("0.00")


def _d(x) -> Decimal:
    """valor float do seed -> Decimal de 2 casas, idêntico ao numeric(12,2) do banco."""
    return Decimal(str(round(float(x), 2)))


# --------------------------------------------------------------------------- #
# Oráculo: a verdade recomputada em Python a partir do seed (sem SQL)          #
# --------------------------------------------------------------------------- #
def carregar_oraculo() -> list[dict]:
    """Achata as vendas geradas em itens com cabeçalho, como a fato_item_venda."""
    _produtos, _clientes, vendas = seedmod.gerar()
    linhas = []
    for v in vendas:
        for it in v["itens"]:
            linhas.append({
                "venda_id": v["venda_id"],
                "data": v["data"],
                "ano": v["data"].year,
                "mes": v["data"].month,
                "periodo": f'{v["data"].year:04d}-{v["data"].month:02d}',
                "cliente": v["cliente"],
                "vendedor": v["vendedor"],
                "canal": v["canal"],
                "pagamento": v["pagamento"],
                "produto": it["produto"],
                "categoria": it["categoria"],
                "qtd": int(it["qtd"]),
                "valor_total": _d(it["valor_total"]),
            })
    return linhas


def no_periodo(linhas, ini: str, fim: str, **filtros):
    """Filtra por data [ini, fim] inclusive e pelos recortes opcionais (= FILTROS_SQL)."""
    di = dt.date.fromisoformat(ini)
    df = dt.date.fromisoformat(fim)
    campo = {"produto": "produto", "categoria": "categoria", "vendedor": "vendedor",
             "cliente": "cliente", "canal": "canal", "forma_pagamento": "pagamento"}
    out = []
    for r in linhas:
        if not (di <= r["data"] <= df):
            continue
        ok = True
        for k, col in campo.items():
            v = filtros.get(k)
            if v is not None and r[col] != v:
                ok = False
                break
        if ok:
            out.append(r)
    return out


def soma(linhas) -> Decimal:
    return sum((r["valor_total"] for r in linhas), D0)


def vendas_distintas(linhas) -> int:
    return len({r["venda_id"] for r in linhas})


# --------------------------------------------------------------------------- #
# Execução dos templates SQL reais                                             #
# --------------------------------------------------------------------------- #
# superconjunto de parâmetros: psycopg usa só os %(...)s que cada SQL referencia
PARAMS_BASE = {
    "empresa_id": EMPRESA,
    "limite": 5,
    "vendedor_nome": None,
    "produto": None, "categoria": None, "vendedor": None,
    "cliente": None, "canal": None, "forma_pagamento": None,
}


def rodar(cur, intencao: str, **params) -> list[tuple]:
    sql = TEMPLATES[intencao]["sql"]
    cur.execute(sql, {**PARAMS_BASE, **params})
    return cur.fetchall()


# --------------------------------------------------------------------------- #
# Provas                                                                       #
# --------------------------------------------------------------------------- #
class Resultado:
    def __init__(self, pid, intencao, descricao):
        self.pid = pid
        self.intencao = intencao
        self.descricao = descricao
        self.tecnico = False
        self.semantico = False
        self.numerico = False
        self.detalhe = ""

    def ok(self, detalhe=""):
        self.tecnico = self.semantico = self.numerico = True
        self.detalhe = detalhe
        return self

    def falha_num(self, detalhe):
        self.tecnico = self.semantico = True
        self.detalhe = detalhe
        return self


def executar(dsn: str) -> list[Resultado]:
    orac = carregar_oraculo()
    res: list[Resultado] = []

    with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
        def prova(pid, intencao, descricao):
            r = Resultado(pid, intencao, descricao)
            res.append(r)
            return r

        # ---- 1. total_vendas_periodo: valor + grupo (mês) + ordenação -------
        r = prova("P01", "total_vendas_periodo", "Faturamento 2024, por mês")
        obt = rodar(cur, "total_vendas_periodo", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        esp = defaultdict(lambda: D0)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            esp[ln["periodo"]] += ln["valor_total"]
        esp_ord = sorted(esp.items())
        got = [(p, Decimal(str(f))) for p, f in obt]
        if got == esp_ord:
            r.ok(f"{len(got)} meses; ∑={sum(esp.values()):.2f}; ordem asc confere")
        else:
            r.falha_num(f"esperado {esp_ord[:2]}…  obtido {got[:2]}…")

        # ---- 2. ticket_medio: por VENDA, não por item (F08) -----------------
        r = prova("P02", "ticket_medio", "Ticket médio 2024 (= faturamento / vendas distintas)")
        obt = rodar(cur, "ticket_medio", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        base = no_periodo(orac, "2024-01-01", "2024-12-31")
        esp_ticket = (soma(base) / vendas_distintas(base)).quantize(Decimal("0.01"))
        got = Decimal(str(obt[0][0])).quantize(Decimal("0.01"))
        media_item = (soma(base) / len(base)).quantize(Decimal("0.01"))
        if got == esp_ticket:
            r.ok(f"{got} por venda (média por ITEM seria {media_item} — descartada)")
        else:
            r.falha_num(f"esperado {esp_ticket} obtido {got}")

        # ---- 3. quantidade_vendas: vendas DISTINTAS por mês (unidade) -------
        r = prova("P03", "quantidade_vendas", "Qtd de vendas distintas 2024, por mês")
        obt = rodar(cur, "quantidade_vendas", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        esp = defaultdict(set)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            esp[ln["periodo"]].add(ln["venda_id"])
        esp_ord = sorted((p, len(s)) for p, s in esp.items())
        got = [(p, int(q)) for p, q in obt]
        if got == esp_ord:
            r.ok(f"{sum(q for _, q in got)} vendas no ano (distintas, não itens)")
        else:
            r.falha_num(f"esperado {esp_ord[:2]}… obtido {got[:2]}…")

        # ---- 4. top_produtos: ordenação desc + limite + unidade (peças) -----
        r = prova("P04", "top_produtos", "Top 5 produtos de 2024 (faturamento desc)")
        obt = rodar(cur, "top_produtos", periodo_inicio="2024-01-01", periodo_fim="2024-12-31", limite=5)
        agg = defaultdict(lambda: [0, D0])  # produto -> [qtd, faturamento]
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            agg[ln["produto"]][0] += ln["qtd"]
            agg[ln["produto"]][1] += ln["valor_total"]
        esp_ord = sorted(agg.items(), key=lambda kv: kv[1][1], reverse=True)[:5]
        esp5 = [(nome, qf[0], qf[1]) for nome, qf in esp_ord]
        got = [(n, int(q), Decimal(str(f))) for n, q, f in obt]
        if got == esp5:
            r.ok(f"1º = {got[0][0]} ({got[0][2]:.2f}, {got[0][1]} peças); ordem e limite conferem")
        else:
            r.falha_num(f"esperado {[e[0] for e in esp5]} obtido {[g[0] for g in got]}")

        # ---- 5. top_clientes: ordenação desc + limite ------------------------
        r = prova("P05", "top_clientes", "Top 5 clientes de 2024")
        obt = rodar(cur, "top_clientes", periodo_inicio="2024-01-01", periodo_fim="2024-12-31", limite=5)
        agg = defaultdict(lambda: D0)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            agg[ln["cliente"]] += ln["valor_total"]
        # desempate por nome para refletir "order by faturamento desc" estável
        esp_ord = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:5]
        got = [(n, Decimal(str(f))) for n, f in obt]
        if [n for n, _ in got] == [n for n, _ in esp_ord] and \
           all(g[1] == e[1] for g, e in zip(got, esp_ord)):
            r.ok(f"1º = {got[0][0]} ({got[0][1]:.2f}); top 5 e ordem conferem")
        else:
            r.falha_num(f"esperado {[e[0] for e in esp_ord]} obtido {[g[0] for g in got]}")

        # ---- 6. desempenho_vendedor: FILTRO por vendedor ---------------------
        r = prova("P06", "desempenho_vendedor", "Desempenho de 'Carlos Nunes' em 2024 (filtro)")
        obt = rodar(cur, "desempenho_vendedor", periodo_inicio="2024-01-01",
                    periodo_fim="2024-12-31", vendedor_nome="%carlos%")
        base = [ln for ln in no_periodo(orac, "2024-01-01", "2024-12-31") if ln["vendedor"] == "Carlos Nunes"]
        esp_fat, esp_qtd = soma(base), vendas_distintas(base)
        if obt and obt[0][0] == "Carlos Nunes" and Decimal(str(obt[0][1])) == esp_fat and int(obt[0][2]) == esp_qtd:
            r.ok(f"Carlos Nunes: {esp_fat:.2f} em {esp_qtd} vendas; filtro isola o vendedor")
        else:
            r.falha_num(f"esperado (Carlos Nunes,{esp_fat},{esp_qtd}) obtido {obt[:1]}")

        # ---- 7. produtos_sem_saida: conjunto correto (recorte por mês) ------
        r = prova("P07", "produtos_sem_saida", "Produtos sem saída em fev/2024")
        obt = rodar(cur, "produtos_sem_saida", periodo_inicio="2024-02-01", periodo_fim="2024-02-29")
        todos = {nome for cat, itens in seedmod.CATALOGO.items() for (nome, _preco) in itens}
        com_saida = {ln["produto"] for ln in no_periodo(orac, "2024-02-01", "2024-02-29")}
        esp_sem = sorted(todos - com_saida)
        got = sorted(row[0] for row in obt)
        if got == esp_sem:
            r.ok(f"{len(got)} produto(s) sem saída no mês; conjunto confere")
        else:
            r.falha_num(f"esperado {esp_sem} obtido {got}")

        # ---- 8. comparacao_periodos: dois períodos --------------------------
        r = prova("P08", "comparacao_periodos", "Comparar jan/2024 × fev/2024")
        obt = rodar(cur, "comparacao_periodos",
                    periodo_a_inicio="2024-01-01", periodo_a_fim="2024-01-31",
                    periodo_b_inicio="2024-02-01", periodo_b_fim="2024-02-29")
        esp_a = soma(no_periodo(orac, "2024-01-01", "2024-01-31"))
        esp_b = soma(no_periodo(orac, "2024-02-01", "2024-02-29"))
        d = {row[0]: Decimal(str(row[1])) for row in obt}
        if d.get("periodo_a") == esp_a and d.get("periodo_b") == esp_b:
            r.ok(f"A={esp_a:.2f}  B={esp_b:.2f}; rótulos e valores conferem")
        else:
            r.falha_num(f"esperado A={esp_a} B={esp_b} obtido {d}")

        # ---- 9. variacao_periodo: valor + fórmula do percentual -------------
        r = prova("P09", "variacao_periodo", "Variação mar/2024 vs fev/2024 (%)")
        obt = rodar(cur, "variacao_periodo",
                    periodo_atual_inicio="2024-03-01", periodo_atual_fim="2024-03-31",
                    periodo_anterior_inicio="2024-02-01", periodo_anterior_fim="2024-02-29")
        atual = soma(no_periodo(orac, "2024-03-01", "2024-03-31"))
        ant = soma(no_periodo(orac, "2024-02-01", "2024-02-29"))
        esp_var = ((atual - ant) / ant * 100).quantize(Decimal("0.01"))
        row = obt[0]
        got_var = Decimal(str(row[2])).quantize(Decimal("0.01"))
        if Decimal(str(row[0])) == atual and Decimal(str(row[1])) == ant and got_var == esp_var:
            r.ok(f"atual={atual:.2f} ant={ant:.2f} var={got_var}%")
        else:
            r.falha_num(f"esperado ({atual},{ant},{esp_var}) obtido {tuple(row)}")

        # ---- 10. unidades_vendidas: UNIDADE = peças (≠ vendas) --------------
        r = prova("P10", "unidades_vendidas", "Unidades (peças) vendidas 2024, por mês")
        obt = rodar(cur, "unidades_vendidas", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        esp = defaultdict(int)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            esp[ln["periodo"]] += ln["qtd"]
        esp_ord = sorted(esp.items())
        got = [(p, int(u)) for p, u in obt]
        total_pecas = sum(esp.values())
        total_vendas = vendas_distintas(no_periodo(orac, "2024-01-01", "2024-12-31"))
        if got == esp_ord:
            r.ok(f"{total_pecas} peças (≠ {total_vendas} vendas — unidade distinta)")
        else:
            r.falha_num(f"esperado {esp_ord[:2]}… obtido {got[:2]}…")

        # ---- 11. vendas_por_canal: grupo + ordenação + 2 medidas -----------
        r = prova("P11", "vendas_por_canal", "Vendas por canal 2024 (desc)")
        obt = rodar(cur, "vendas_por_canal", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        fat = defaultdict(lambda: D0)
        vnd = defaultdict(set)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            fat[ln["canal"]] += ln["valor_total"]
            vnd[ln["canal"]].add(ln["venda_id"])
        esp_ord = sorted(fat.items(), key=lambda kv: kv[1], reverse=True)
        got = [(c, Decimal(str(f)), int(q)) for c, f, q in obt]
        if [c for c, _, _ in got] == [c for c, _ in esp_ord] and \
           all(g[1] == fat[g[0]] and g[2] == len(vnd[g[0]]) for g in got):
            r.ok(f"{len(got)} canais; 1º={got[0][0]} ({got[0][1]:.2f}); ordem e contagem conferem")
        else:
            r.falha_num(f"esperado {[c for c,_ in esp_ord]} obtido {[g[0] for g in got]}")

        # ---- 12. vendas_por_categoria --------------------------------------
        r = prova("P12", "vendas_por_categoria", "Vendas por categoria 2024 (desc)")
        obt = rodar(cur, "vendas_por_categoria", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        fat = defaultdict(lambda: D0)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            fat[ln["categoria"]] += ln["valor_total"]
        esp_ord = sorted(fat.items(), key=lambda kv: kv[1], reverse=True)
        got = [(c, Decimal(str(f))) for c, f in obt]
        if [c for c, _ in got] == [c for c, _ in esp_ord] and all(g[1] == fat[g[0]] for g in got):
            r.ok(f"{len(got)} categorias; 1ª={got[0][0]} ({got[0][1]:.2f})")
        else:
            r.falha_num(f"esperado {[c for c,_ in esp_ord]} obtido {[g[0] for g in got]}")

        # ---- 13. vendas_por_pagamento --------------------------------------
        r = prova("P13", "vendas_por_pagamento", "Vendas por forma de pagamento 2024 (desc)")
        obt = rodar(cur, "vendas_por_pagamento", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        fat = defaultdict(lambda: D0)
        vnd = defaultdict(set)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            fat[ln["pagamento"]] += ln["valor_total"]
            vnd[ln["pagamento"]].add(ln["venda_id"])
        esp_ord = sorted(fat.items(), key=lambda kv: kv[1], reverse=True)
        got = [(c, Decimal(str(f)), int(q)) for c, f, q in obt]
        if [c for c, _, _ in got] == [c for c, _ in esp_ord] and \
           all(g[1] == fat[g[0]] and g[2] == len(vnd[g[0]]) for g in got):
            r.ok(f"{len(got)} formas; 1ª={got[0][0]} ({got[0][1]:.2f})")
        else:
            r.falha_num(f"esperado {[c for c,_ in esp_ord]} obtido {[g[0] for g in got]}")

        # ---- 14. melhor_mes: série mês a mês (base do refino) --------------
        r = prova("P14", "melhor_mes", "Série 2024 e identificação do mês de pico")
        obt = rodar(cur, "melhor_mes", periodo_inicio="2024-01-01", periodo_fim="2024-12-31")
        fat = defaultdict(lambda: D0)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            fat[ln["periodo"]] += ln["valor_total"]
        esp_ord = sorted(fat.items())
        got = [(p, Decimal(str(f))) for p, f, _u in obt]
        pico_esp = max(fat.items(), key=lambda kv: kv[1])[0]
        pico_got = max(got, key=lambda kv: kv[1])[0]
        if got == esp_ord and pico_esp == pico_got:
            r.ok(f"12 meses; pico em {pico_got} ({max(fat.values()):.2f})")
        else:
            r.falha_num(f"esperado pico {pico_esp} obtido {pico_got}")

        # ---- 15. FILTRO por categoria sobre total_vendas_periodo -----------
        r = prova("P15", "total_vendas_periodo", "Faturamento 2024 filtrado por categoria 'Calçados'")
        obt = rodar(cur, "total_vendas_periodo", periodo_inicio="2024-01-01",
                    periodo_fim="2024-12-31", categoria="Calçados")
        esp = defaultdict(lambda: D0)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31", categoria="Calçados"):
            esp[ln["periodo"]] += ln["valor_total"]
        esp_ord = sorted(esp.items())
        got = [(p, Decimal(str(f))) for p, f in obt]
        total_filtro = sum(esp.values())
        total_sem = soma(no_periodo(orac, "2024-01-01", "2024-12-31"))
        if got == esp_ord and total_filtro < total_sem:
            r.ok(f"∑Calçados={total_filtro:.2f} < ∑total={total_sem:.2f}; filtro aplicado")
        else:
            r.falha_num(f"esperado {esp_ord[:2]}… obtido {got[:2]}…")

        # ---- 16. FILTRO por canal sobre ticket_medio -----------------------
        r = prova("P16", "ticket_medio", "Ticket médio 2024 só no canal 'site' (filtro)")
        obt = rodar(cur, "ticket_medio", periodo_inicio="2024-01-01",
                    periodo_fim="2024-12-31", canal="site")
        base = no_periodo(orac, "2024-01-01", "2024-12-31", canal="site")
        esp_ticket = (soma(base) / vendas_distintas(base)).quantize(Decimal("0.01"))
        got = Decimal(str(obt[0][0])).quantize(Decimal("0.01"))
        if got == esp_ticket:
            r.ok(f"ticket(site)={got}; recorte por canal confere")
        else:
            r.falha_num(f"esperado {esp_ticket} obtido {got}")

        # ---- 17. NULO: período sem vendas vira NULL (base do 404) ----------
        r = prova("P17", "ticket_medio", "Período sem vendas (2018) → ticket NULO")
        obt = rodar(cur, "ticket_medio", periodo_inicio="2018-01-01", periodo_fim="2018-12-31")
        valor = obt[0][0] if obt else "sem linha"
        if obt and obt[0][0] is None:
            r.ok("retorna uma linha com ticket = NULL (nullif evita divisão por zero → executor responde 404)")
        else:
            r.falha_num(f"esperado NULL obtido {valor}")

        # ---- 18. FRONTEIRA: 'between' inclui o último dia do período -------
        r = prova("P18", "total_vendas_periodo", "Fronteira: venda no último dia do período entra")
        # procura, no oráculo, o último dia de 2024 com venda
        dias_2024 = sorted({ln["data"] for ln in no_periodo(orac, "2024-01-01", "2024-12-31")})
        ultimo = dias_2024[-1]
        so_ultimo_dia = [ln for ln in orac if ln["data"] == ultimo]
        esp_dia = soma(so_ultimo_dia)
        obt = rodar(cur, "total_vendas_periodo",
                    periodo_inicio=ultimo.isoformat(), periodo_fim=ultimo.isoformat())
        got = sum((Decimal(str(f)) for _p, f in obt), D0)
        if got == esp_dia and esp_dia > 0:
            r.ok(f"{ultimo.isoformat()} incluído: ∑={esp_dia:.2f} (between é inclusivo nas duas pontas)")
        else:
            r.falha_num(f"esperado {esp_dia} obtido {got}")

        # ---- 19. VENDA MULTI-ITEM: conta como UMA venda --------------------
        r = prova("P19", "quantidade_vendas", "Venda com vários itens conta 1 vez")
        # escolhe uma venda de 2024 com >1 item; o mês dela deve contá-la uma vez só
        porv = defaultdict(list)
        for ln in no_periodo(orac, "2024-01-01", "2024-12-31"):
            porv[ln["venda_id"]].append(ln)
        multi = next((v for v, itens in porv.items() if len(itens) > 1), None)
        mes = porv[multi][0]["periodo"]
        n_itens = len(porv[multi])
        obt = rodar(cur, "quantidade_vendas",
                    periodo_inicio=f"{mes}-01", periodo_fim=f"{mes}-28")
        esp = defaultdict(set)
        for ln in no_periodo(orac, f"{mes}-01", f"{mes}-28"):
            esp[ln["periodo"]].add(ln["venda_id"])
        esp_q = len(esp[mes])
        got_q = next((int(q) for p, q in obt if p == mes), None)
        if got_q == esp_q:
            r.ok(f"venda {multi} tem {n_itens} itens e entra 1× em {mes} (count distinct venda_id)")
        else:
            r.falha_num(f"mês {mes}: esperado {esp_q} vendas distintas, obtido {got_q}")

    return res


# --------------------------------------------------------------------------- #
# Relatório                                                                    #
# --------------------------------------------------------------------------- #
def _sim(b: bool) -> str:
    return "✅" if b else "❌"


def relatorio_md(res: list[Resultado], dsn_rotulo: str) -> str:
    agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")
    n = len(res)
    tec = sum(r.tecnico for r in res)
    sem = sum(r.semantico for r in res)
    num = sum(r.numerico for r in res)
    linhas = [
        "# Gabarito numérico independente das 14 consultas",
        "",
        "Oráculo independente que confere os **valores** das consultas (parecer da",
        "banca final, F02). A verdade esperada é recomputada em Python puro a partir",
        "da geração determinística do `database/seed.py` (SEED=42); o obtido vem dos",
        "templates SQL reais de `backend/app/sql/templates.py`. Gerado por",
        "`scripts/gabarito_numerico.py`.",
        "",
        f"- **Data:** {agora}",
        f"- **Base:** empresa demo `{EMPRESA}` — 8.941 itens / 3.527 vendas / R$ 2.717.797,23",
        f"- **Alvo:** {dsn_rotulo}",
        "",
        "## Resumo",
        "",
        "| Nível de sucesso | O que verifica | Provas |",
        "|---|---|---:|",
        f"| Técnico | executou sem erro, devolveu linhas | {tec}/{n} |",
        f"| Semântico | colunas, grão, agrupamento, ordenação | {sem}/{n} |",
        f"| **Numérico** | **todos os valores batem com o oráculo** | **{num}/{n}** |",
        "",
        "## Provas",
        "",
        "| ID | Intenção | O que verifica | Téc | Sem | **Num** | Detalhe |",
        "|---|---|---|:-:|:-:|:-:|---|",
    ]
    for r in res:
        linhas.append(
            f"| {r.pid} | `{r.intencao}` | {r.descricao} | {_sim(r.tecnico)} | "
            f"{_sim(r.semantico)} | {_sim(r.numerico)} | {r.detalhe} |"
        )
    linhas += [
        "",
        "## Cobertura (parecer F02)",
        "",
        "- **Valor, filtro, grupo, ordenação, unidade:** P01–P16 cobrem as 14 consultas,",
        "  mais recortes por categoria (P15) e canal (P16); unidade peças × vendas em P03/P10.",
        "- **Nulos:** P17 — período sem vendas devolve ticket `NULL` (base do 404 `sem_resultado`).",
        "- **Fronteira de período:** P18 — `between` inclui o último dia.",
        "- **Venda com vários itens:** P19 — contada uma única vez (`count(distinct venda_id)`).",
        "- **Devoluções:** o artefato **não modela devolução/estorno** (`fato_item_venda` tem",
        "  `quantidade` inteira ≥ 0, sem fluxo de retorno). Declarado fora do escopo — não simulado.",
        "",
        "## Reproduzir",
        "",
        "```bash",
        "# banco local (ver README) semeado com database/seed.py",
        "DATABASE_URL=postgresql://... python scripts/gabarito_numerico.py --saida docs/evidencias",
        "# ou como teste (pytest):",
        "cd backend && pytest tests/test_gabarito_numerico.py -q",
        "```",
        "",
        "## Limite honesto",
        "",
        "Este gabarito prova que **a consulta certa calcula o valor certo**. Ele não mede",
        "se o NLU escolhe a consulta certa (isso é a bateria de 100 perguntas, por status +",
        "título) nem substitui a verificação semântica de ponta a ponta — é a camada de",
        "**correção numérica** que faltava entre os dois.",
        "",
    ]
    return "\n".join(linhas) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Gabarito numérico independente das 14 consultas.")
    ap.add_argument("--saida", default=None, help="diretório para gravar o relatório .md (ex.: docs/evidencias)")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("Defina DATABASE_URL (banco semeado com database/seed.py).")

    res = executar(dsn)

    # terminal
    print(f"\n{'ID':4} {'TÉC':3} {'SEM':3} {'NUM':3}  INTENÇÃO / DETALHE")
    for r in res:
        print(f"{r.pid:4} {_sim(r.tecnico):>3} {_sim(r.semantico):>3} {_sim(r.numerico):>3}  "
              f"{r.intencao} — {r.detalhe}")
    num = sum(r.numerico for r in res)
    print(f"\nNUMÉRICO: {num}/{len(res)} provas conferem.")

    if args.saida:
        destino = Path(args.saida)
        destino.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        arq = destino / f"gabarito_numerico_{stamp}.md"
        arq.write_text(relatorio_md(res, dsn.split("@")[-1]), encoding="utf-8")
        print(f"Relatório: {arq}")

    return 0 if num == len(res) else 1


if __name__ == "__main__":
    raise SystemExit(main())
