#!/usr/bin/env python3
"""
avaliar_100_perguntas.py — executa as 100 perguntas de validação funcional
(docs/perguntas_validacao.md) e consolida a taxa de acerto por categoria e a
latência. Atende a crítica nº 2 da orientação: "executar as cem perguntas,
consolidando taxa funcional, latência e verificação de objetivos".

Dois modos:

  api  (padrão) — envia cada pergunta para POST /chat de uma API no ar e
        avalia status HTTP + categoria obtida. É o teste ponta a ponta.
            python scripts/avaliar_100_perguntas.py --url http://127.0.0.1:8000
            python scripts/avaliar_100_perguntas.py --url https://intellix-api.onrender.com

  nlu  — avalia só a classificação, importando o NLU direto (sem servidor e
        sem banco). Serve para comparar regras x modelo.
            python scripts/avaliar_100_perguntas.py --modo nlu --backend regras
            python scripts/avaliar_100_perguntas.py --modo nlu --backend modelo

Critério de acerto (modo api):
  * categorias 1-12: HTTP 200 e título da resposta igual ao do template
    esperado (cada template de backend/app/sql/templates.py tem título único);
  * 13 (fora de escopo): HTTP 422 tipo "baixa_confianca";
  * 14 (parâmetro faltando / ambíguo): HTTP 422 (qualquer tipo);
  * 15 (sem resultado): HTTP 404 tipo "sem_resultado".

Saídas (em --saida, padrão docs/evidencias/): CSV com uma linha por pergunta e
um resumo em Markdown com a Tabela 1 preenchida. Só usa a biblioteca padrão.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import platform
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ_PERGUNTAS = RAIZ / "docs" / "perguntas_validacao.md"
META_LATENCIA_MS = 3000          # meta do TCC: resposta em menos de 3 s
CONFIANCA_MINIMA = 0.70          # mesmo limiar de backend/app/fallbacks.py

# título único de cada template (backend/app/sql/templates.py)
TITULOS = {
    "total_vendas_periodo": "Faturamento no período",
    "top_produtos": "Produtos mais vendidos",
    "ticket_medio": "Ticket médio",
    "quantidade_vendas": "Quantidade de vendas no período",
    "top_clientes": "Clientes que mais compraram",
    "desempenho_vendedor": "Desempenho do vendedor",
    "produtos_sem_saida": "Produtos sem saída no período",
    "comparacao_periodos": "Comparação entre períodos",
    "variacao_periodo": "Variação entre períodos",
    "vendas_por_canal": "Vendas por canal",
    "vendas_por_categoria": "Vendas por categoria",
    "vendas_por_pagamento": "Vendas por forma de pagamento",
}
TITULO_PARA_INTENCAO = {v: k for k, v in TITULOS.items()}

FORA_DE_ESCOPO, PARAM_FALTANDO, SEM_RESULTADO = "fora_de_escopo", "parametro_faltando", "sem_resultado"


# --------------------------------------------------------------------------- #
# Leitura das perguntas                                                        #
# --------------------------------------------------------------------------- #
def ler_perguntas(caminho: Path) -> list[dict]:
    """Devolve [{n, secao, categoria, pergunta}] a partir do Markdown."""
    perguntas, secao, categoria = [], None, None
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(\d+)\.\s+(.*)$", linha)
        if m:
            secao, titulo = int(m.group(1)), m.group(2).strip()
            if secao <= 12:
                categoria = titulo.split()[0]            # "total_vendas_periodo — ..." -> chave
            elif secao == 13:
                categoria = FORA_DE_ESCOPO
            elif secao == 14:
                categoria = PARAM_FALTANDO
            elif secao == 15:
                categoria = SEM_RESULTADO
            continue
        if linha.startswith("## "):                      # ex.: "## Tabela 1" encerra a lista
            secao = None
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", linha)
        if m and secao is not None:
            texto = re.sub(r"\*\(.*?\)\*", "", m.group(2)).strip()   # tira notas em itálico
            perguntas.append({"n": int(m.group(1)), "secao": secao,
                              "categoria": categoria, "pergunta": texto})
    return perguntas


# --------------------------------------------------------------------------- #
# Modo API                                                                     #
# --------------------------------------------------------------------------- #
def _post(url: str, pergunta: str, timeout: float) -> tuple[int, dict, float]:
    corpo = json.dumps({"pergunta": pergunta}).encode("utf-8")
    req = urllib.request.Request(url, data=corpo, method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, bruto = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, bruto = e.code, e.read()
    ms = (time.perf_counter() - t0) * 1000
    try:
        dados = json.loads(bruto.decode("utf-8") or "{}")
    except ValueError:
        dados = {"bruto": bruto[:200].decode("utf-8", "replace")}
    return status, dados, ms


def avaliar_api(perguntas: list[dict], base: str, timeout: float) -> list[dict]:
    base = base.rstrip("/")
    # aquece a instância (no Render free a 1ª chamada pode levar ~50 s)
    try:
        urllib.request.urlopen(base + "/health", timeout=120).read()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"API indisponível em {base}/health: {e}")

    resultados = []
    for p in perguntas:
        status, dados, ms = _post(base + "/chat", p["pergunta"], timeout)
        detalhe = dados.get("detail") if isinstance(dados.get("detail"), dict) else {}
        tipo_erro = detalhe.get("tipo", "")
        obtido = TITULO_PARA_INTENCAO.get(dados.get("titulo", ""), "") if status == 200 else tipo_erro

        cat = p["categoria"]
        if cat in TITULOS:
            esperado = f"200 / {cat}"
            acerto = status == 200 and obtido == cat
        elif cat == FORA_DE_ESCOPO:
            esperado = "422 / baixa_confianca"
            acerto = status == 422 and tipo_erro == "baixa_confianca"
        elif cat == PARAM_FALTANDO:
            esperado = "422"
            acerto = status == 422
        else:
            esperado = "404 / sem_resultado"
            acerto = status == 404 and tipo_erro == "sem_resultado"

        resultados.append({**p, "esperado": esperado, "status": status,
                           "obtido": obtido or "-", "acerto": acerto,
                           "latencia_ms": round(ms, 1)})
        print(f"{p['n']:3d} {'OK ' if acerto else 'ERR'} {status} {ms:7.0f} ms  {p['pergunta'][:60]}")
    return resultados


# --------------------------------------------------------------------------- #
# Modo NLU (sem servidor, sem banco)                                           #
# --------------------------------------------------------------------------- #
def avaliar_nlu(perguntas: list[dict], backend: str) -> list[dict]:
    sys.path.insert(0, str(RAIZ / "backend"))
    if backend == "modelo":
        from app.nlu.adaptador_modelo import ModeloTreinadoNLU
        nlu = ModeloTreinadoNLU()
    else:
        from app.nlu.regras import RuleBasedNLU
        nlu = RuleBasedNLU()

    resultados = []
    for p in perguntas:
        cat = p["categoria"]
        if cat in (PARAM_FALTANDO, SEM_RESULTADO):
            continue  # dependem do executor e do banco: só o modo api avalia
        t0 = time.perf_counter()
        i = nlu.parse(p["pergunta"])
        ms = (time.perf_counter() - t0) * 1000
        aceita = i.intencao is not None and i.confianca >= CONFIANCA_MINIMA
        if cat == FORA_DE_ESCOPO:
            esperado, acerto = "rejeitar (conf < 0,70)", not aceita
        else:
            esperado, acerto = cat, aceita and i.intencao == cat
        resultados.append({**p, "esperado": esperado, "status": "-",
                           "obtido": f"{i.intencao} ({i.confianca:.2f})",
                           "acerto": acerto, "latencia_ms": round(ms, 2)})
    return resultados


# --------------------------------------------------------------------------- #
# Relatório                                                                    #
# --------------------------------------------------------------------------- #
def _pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "-"


def resumo_md(resultados: list[dict], modo: str, alvo: str) -> str:
    ordem, rot = [], {}
    for r in resultados:
        if r["secao"] not in rot:
            ordem.append(r["secao"])
            rot[r["secao"]] = r["categoria"]
    linhas = ["| # | Categoria | Perguntas | Acertos | Taxa de acerto |", "|---|---|---:|---:|---:|"]
    tot_n = tot_a = 0
    for s in ordem:
        grupo = [r for r in resultados if r["secao"] == s]
        a = sum(r["acerto"] for r in grupo)
        tot_n, tot_a = tot_n + len(grupo), tot_a + a
        linhas.append(f"| {s} | {rot[s]} | {len(grupo)} | {a} | {_pct(a, len(grupo))} |")
    linhas.append(f"| | **Total** | **{tot_n}** | **{tot_a}** | **{_pct(tot_a, tot_n)}** |")

    lat = sorted(r["latencia_ms"] for r in resultados)
    p95 = lat[max(0, int(round(0.95 * len(lat))) - 1)] if lat else 0
    abaixo = sum(x < META_LATENCIA_MS for x in lat)
    agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")

    partes = [
        f"# Avaliação das 100 perguntas — modo `{modo}`",
        "",
        f"- **Data:** {agora}",
        f"- **Alvo:** {alvo}",
        f"- **Ambiente do executor:** {platform.system()} {platform.release()} · Python {platform.python_version()}",
        f"- **Perguntas avaliadas:** {tot_n}",
        "",
        "## Taxa de acerto por categoria",
        "",
        *linhas,
        "",
        "## Latência",
        "",
        "| Mediana | p95 | Máxima | Média | Abaixo de 3 s |",
        "|---:|---:|---:|---:|---:|",
        f"| {statistics.median(lat):.0f} ms | {p95:.0f} ms | {max(lat):.0f} ms | "
        f"{statistics.mean(lat):.0f} ms | {abaixo}/{len(lat)} ({_pct(abaixo, len(lat))}) |" if lat else "| - | - | - | - | - |",
        "",
        "## Erros",
        "",
    ]
    erros = [r for r in resultados if not r["acerto"]]
    if erros:
        partes += ["| n | Pergunta | Esperado | Obtido | Status |", "|---:|---|---|---|---|"]
        partes += [f"| {r['n']} | {r['pergunta']} | {r['esperado']} | {r['obtido']} | {r['status']} |" for r in erros]
    else:
        partes.append("Nenhum.")
    return "\n".join(partes) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Avalia as 100 perguntas de validação.")
    ap.add_argument("--modo", choices=["api", "nlu"], default="api")
    ap.add_argument("--url", default="http://127.0.0.1:8000", help="base da API (modo api)")
    ap.add_argument("--backend", choices=["regras", "modelo"], default="regras", help="NLU (modo nlu)")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--saida", default=str(RAIZ / "docs" / "evidencias"))
    args = ap.parse_args()

    perguntas = ler_perguntas(ARQ_PERGUNTAS)
    if len(perguntas) != 100:
        print(f"aviso: {len(perguntas)} perguntas lidas (esperado 100)")

    if args.modo == "api":
        resultados, alvo, rotulo = avaliar_api(perguntas, args.url, args.timeout), args.url, "api"
    else:
        resultados = avaliar_nlu(perguntas, args.backend)
        alvo, rotulo = f"NLU `{args.backend}` (sem servidor, sem banco)", f"nlu-{args.backend}"

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    base = saida / f"avaliacao_{rotulo}_{stamp}"
    with open(f"{base}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "secao", "categoria", "pergunta", "esperado",
                                          "status", "obtido", "acerto", "latencia_ms"])
        w.writeheader()
        w.writerows(resultados)
    md = resumo_md(resultados, rotulo, alvo)
    Path(f"{base}.md").write_text(md, encoding="utf-8")
    print("\n" + md)
    print(f"Arquivos: {base}.csv  e  {base}.md")


if __name__ == "__main__":
    main()
