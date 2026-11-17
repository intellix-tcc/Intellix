#!/usr/bin/env python3
"""
teste_carga_normal.py — Reteste do /chat em CONFIGURAÇÃO NORMAL (parecer da
banca final, F05).

O teste de carga anterior (`teste_carga.py`) desligou o limitador
(LIMITE_REQUISICOES=0) para medir a capacidade bruta. A banca observa que isso
não representa a operação normal e pede: repetir sob configuração normal, medir
partida fria e aquecida, duração maior, mistura de consultas e latência por
estado — **sem extrapolar vazão ou disponibilidade**.

Este script mede, contra uma API local com o **limitador LIGADO** (padrão,
/chat = 30 req/min por IP):

  1. Partida fria × quente — a 1ª pergunta (abre o pool de conexões) × a mediana
     das seguintes. Observação honesta: a "partida fria" de instância do Render
     (hibernação ~30 s, decisão 003) é propriedade da hospedagem e NÃO é
     reproduzível localmente; aqui medimos o caminho frio da aplicação.
  2. Latência por estado — mistura de consultas: 200 (consulta), 404
     (sem_resultado), 422 (baixa_confiança / parâmetro faltando), mediana e p95
     por estado, dentro do limite.
  3. Limitador ativo — um burst acima de 30/min no /chat devolve 429
     (`limite_requisicoes`): a proteção que o teste anterior havia desligado.

Não mede vazão máxima nem disponibilidade: são propriedades da hospedagem.

Uso (com a API local no ar; ver README):
    python scripts/teste_carga_normal.py --url http://127.0.0.1:8000 --saida docs/evidencias
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# mistura de consultas com estados esperados variados
BATERIA = [
    ("Quanto faturei em março de 2024?", "200"),
    ("Quais os 5 produtos mais vendidos em 2024?", "200"),
    ("Qual o ticket médio de 2024?", "200"),
    ("Quantas vendas eu fiz em dezembro de 2024?", "200"),
    ("Vendas por canal em 2024", "200"),
    ("Vendas por categoria em 2025", "200"),
    ("Qual o ticket médio de 2018?", "404"),          # fora do range -> sem_resultado
    ("Me conta uma piada.", "422"),                   # fora de escopo -> baixa_confianca
    ("Compare os períodos.", "422"),                  # parâmetro faltando
]


def perguntar(base, pergunta, timeout=60.0):
    corpo = json.dumps({"pergunta": pergunta}).encode("utf-8")
    req = urllib.request.Request(base + "/chat", data=corpo, method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, bruto = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, bruto = e.code, e.read()
    except (TimeoutError, urllib.error.URLError, OSError):
        status, bruto = 0, b"{}"
    ms = (time.perf_counter() - t0) * 1000
    try:
        tipo = (json.loads(bruto or b"{}").get("detail") or {}).get("tipo", "")
    except Exception:  # noqa: BLE001
        tipo = ""
    return status, tipo, round(ms, 1)


def estado(status, tipo):
    if status == 200:
        return "200 consulta"
    if status == 404:
        return "404 sem_resultado"
    if status == 422:
        return f"422 {tipo or '-'}"
    if status == 429:
        return "429 limite"
    return f"{status} {tipo or '-'}"


def main():
    ap = argparse.ArgumentParser(description="Reteste de carga em configuração normal (F05).")
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--aquecidas", type=int, default=24, help="perguntas na fase dentro do limite")
    ap.add_argument("--burst", type=int, default=35, help="perguntas no burst do limitador")
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()
    base = args.url.rstrip("/")

    try:
        urllib.request.urlopen(base + "/health", timeout=120).read()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"API indisponível em {base}/health: {e}")

    # ---- 1. partida fria × quente + 2. latência por estado -------------------
    # a 1ª pergunta abre o pool (caminho frio da aplicação)
    s0, t0, fria = perguntar(base, BATERIA[0][0])
    por_estado: dict[str, list[float]] = {estado(s0, t0): [fria]}
    quentes = []
    for i in range(args.aquecidas):
        p, _esp = BATERIA[(i + 1) % len(BATERIA)]
        s, t, ms = perguntar(base, p)
        if s == 429:
            # bateu no limite antes da hora: ainda assim registramos
            por_estado.setdefault("429 limite", []).append(ms)
            continue
        quentes.append(ms)
        por_estado.setdefault(estado(s, t), []).append(ms)

    # ---- 3. limitador ativo: espera a janela limpar e dá um burst ------------
    print("Aguardando 62 s para a janela do limitador limpar...")
    time.sleep(62)
    burst = [perguntar(base, "Quanto faturei em março de 2024?") for _ in range(args.burst)]
    b200 = sum(1 for s, _t, _ms in burst if s == 200)
    b429 = sum(1 for s, _t, _ms in burst if s == 429)

    # ---- relatório -----------------------------------------------------------
    med_quente = round(statistics.median(quentes)) if quentes else 0
    agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")

    def linha_estado(nome, vs):
        vs = sorted(vs)
        p95 = vs[min(len(vs) - 1, max(0, round(0.95 * len(vs)) - 1))] if vs else 0
        med = statistics.median(vs) if vs else 0
        return f"| {nome} | {len(vs)} | {med:.0f} ms | {p95:.0f} ms | {max(vs):.0f} ms |"

    L = [
        f"# Reteste de carga do /chat em configuração normal — {agora}",
        "",
        f"- **Alvo:** `{base}` (local)  ·  **limitador:** LIGADO (/chat = 30/min por IP)",
        "- **Escopo:** caracterização sob config normal; **não** mede vazão máxima nem",
        "  disponibilidade (propriedades da hospedagem — ver decisão 003 sobre a hibernação do Render).",
        "",
        "## 1. Partida fria × quente (caminho da aplicação)",
        "",
        f"- **Fria** (1ª pergunta, abre o pool de conexões): **{fria:.0f} ms**",
        f"- **Quente** (mediana de {len(quentes)} seguintes): **{med_quente} ms**",
        "",
        "> A partida fria de *instância* do Render (hibernação ~30 s) não é reproduzível",
        "> localmente; aqui está o caminho frio da aplicação (abertura do pool).",
        "",
        "## 2. Latência por estado (mistura de consultas)",
        "",
        "| Estado | N | Mediana | p95 | Máx |",
        "|---|---:|---:|---:|---:|",
    ]
    for nome in sorted(por_estado):
        if nome != "429 limite":
            L.append(linha_estado(nome, por_estado[nome]))
    L += [
        "",
        "## 3. Limitador ativo (a proteção que o teste anterior desligou)",
        "",
        f"Burst de {args.burst} perguntas /chat do mesmo IP em poucos segundos:",
        "",
        f"- **{b200}** responderam **200** (dentro do limite de 30/min);",
        f"- **{b429}** responderam **429 `limite_requisicoes`** (bloqueadas pela proteção).",
        "",
        "Em operação normal, um cliente é limitado a 30 perguntas/min por IP; o teste de",
        "capacidade (`teste_carga.py`) desliga isso de propósito e, por isso, não",
        "representa a operação normal — é a leitura que o parecer pedia para separar.",
        "",
        "## Reproduzir",
        "",
        "```bash",
        "cd backend && NLU_BACKEND=modelo AUTH_OBRIGATORIA=false \\",
        "  EMPRESA_ID=00000000-0000-0000-0000-000000000001 DATABASE_URL=postgresql://... \\",
        "  uvicorn app.main:app --port 8000 &",
        "python scripts/teste_carga_normal.py --url http://127.0.0.1:8000 --saida docs/evidencias",
        "```",
        "",
    ]
    md = "\n".join(L) + "\n"
    print("\n" + md)
    if args.saida:
        destino = Path(args.saida)
        destino.mkdir(parents=True, exist_ok=True)
        arq = destino / f"teste_carga_normal_{dt.datetime.now():%Y-%m-%d_%H%M}.md"
        arq.write_text(md, encoding="utf-8")
        print("Arquivo:", arq)


if __name__ == "__main__":
    main()
