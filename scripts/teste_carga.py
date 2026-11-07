#!/usr/bin/env python3
"""
teste_carga.py — mede quantas perguntas simultâneas a API aguenta.

Atende à crítica do parecer do TC2 (F11/F12): a capacidade de requisições
simultâneas de uma instância "não foi medida". Este script mede, por nível de
concorrência (1, 2, 5, 10, 20 usuários ao mesmo tempo, por padrão):

  * vazão (perguntas respondidas por segundo);
  * tempo de resposta (mediana, p95 e máximo);
  * erros, separados por tipo: 429 (limite de requisições), 503 (banco
    indisponível / pool esgotado), outros 5xx e tempo esgotado.

Uso (com o login obrigatório, como em produção):
    python scripts/teste_carga.py --url https://intellix-backend-3fu4.onrender.com --email voce@exemplo.com

ATENÇÃO: o /chat limita 30 perguntas por minuto por IP. Para medir a
capacidade, e não o limitador, o limite precisa estar desligado durante o
teste (LIMITE_REQUISICOES=0 no Render) e religado logo depois. Se o script
receber 429 já no primeiro nível, ele para e avisa.

Proteções: aquece a instância antes (/health), para quando a taxa de erro de
um nível passa de 50% e não sobe mais de nível. Cada pergunta respondida grava
uma linha em log_consulta (auditoria), como qualquer uso normal.

Saída (em --saida, padrão docs/evidencias/): CSV com uma linha por pergunta e
um resumo em Markdown. Só usa a biblioteca padrão.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Perguntas válidas que consultam o banco (base de demonstração), variadas
# para não medir só uma consulta. Todas devem responder 200.
PERGUNTAS = [
    "Quanto faturei em março de 2024?",
    "Quais os 5 produtos mais vendidos em 2024?",
    "Qual o ticket médio de 2024?",
    "Quantas vendas eu fiz em dezembro de 2024?",
    "Vendas por canal em 2024",
    "Vendas por categoria em 2025",
]


def perguntar(base: str, pergunta: str, token: str, timeout: float) -> dict:
    corpo = json.dumps({"pergunta": pergunta}).encode("utf-8")
    cab = {"Content-Type": "application/json"}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(base + "/chat", data=corpo, method="POST", headers=cab)
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except (TimeoutError, urllib.error.URLError, OSError):
        status = 0  # tempo esgotado ou conexão recusada
    return {
        "pergunta": pergunta,
        "status": status,
        "ms": round((time.perf_counter() - inicio) * 1000, 1),
    }


def rodar_nivel(
    base: str, usuarios: int, total: int, token: str, timeout: float
) -> tuple[list[dict], float]:
    """`usuarios` perguntas em voo ao mesmo tempo, até completar `total`."""
    lista = [PERGUNTAS[i % len(PERGUNTAS)] for i in range(total)]
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=usuarios) as ex:
        res = list(ex.map(lambda p: perguntar(base, p, token, timeout), lista))
    return res, time.perf_counter() - inicio


def _p(valores: list[float], q: float) -> float:
    if not valores:
        return 0.0
    v = sorted(valores)
    return v[min(len(v) - 1, max(0, round(q * len(v)) - 1))]


def resumir(usuarios: int, res: list[dict], duracao: float) -> dict:
    ok = [r["ms"] for r in res if r["status"] == 200]

    def cont(criterio) -> int:
        return sum(1 for r in res if criterio(r["status"]))

    return {
        "usuarios": usuarios,
        "pedidos": len(res),
        "ok": len(ok),
        "vazao_ok_s": round(len(ok) / duracao, 2) if duracao else 0,
        "mediana_ms": round(statistics.median(ok)) if ok else 0,
        "p95_ms": round(_p(ok, 0.95)),
        "max_ms": round(max(ok)) if ok else 0,
        "e429": cont(lambda s: s == 429),
        "e503": cont(lambda s: s == 503),
        "e5xx": cont(lambda s: s >= 500 and s != 503),
        "e_outros": cont(lambda s: s not in (200, 429, 503) and s < 500 and s != 0),
        "timeout": cont(lambda s: s == 0),
        "duracao_s": round(duracao, 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Teste de carga do /chat.")
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument(
        "--email", default=None, help="conta do Intellix; a senha é pedida no terminal"
    )
    ap.add_argument(
        "--niveis",
        default="1,2,5,10,20",
        help="usuários simultâneos, separados por vírgula",
    )
    ap.add_argument("--por-nivel", type=int, default=40, help="perguntas por nível")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--saida", default=str(RAIZ / "docs" / "evidencias"))
    args = ap.parse_args()

    base = args.url.rstrip("/")
    niveis = [int(n) for n in args.niveis.split(",") if n.strip()]
    if args.email:
        # mesmo login do script das 100 perguntas (senha pedida no terminal)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from avaliar_100_perguntas import obter_token

        token = obter_token(args.email)
    else:
        token = os.environ.get("INTELLIX_TOKEN", "")

    print(f"Aquecendo {base} ...")
    try:
        urllib.request.urlopen(base + "/health", timeout=120).read()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"API indisponível em {base}/health: {e}")
    aquecimento = perguntar(base, PERGUNTAS[0], token, args.timeout)
    if aquecimento["status"] == 401:
        sys.exit(
            "A API exige login (HTTP 401). Rode com --email ou defina INTELLIX_TOKEN."
        )
    if aquecimento["status"] != 200:
        sys.exit(
            f"A pergunta de aquecimento respondeu HTTP {aquecimento['status']}; confira antes de testar."
        )

    detalhes, linhas = [], []
    for n in niveis:
        print(f"\nNível {n} usuário(s) simultâneo(s), {args.por_nivel} perguntas ...")
        res, dur = rodar_nivel(base, n, args.por_nivel, token, args.timeout)
        r = resumir(n, res, dur)
        linhas.append(r)
        detalhes += [{**x, "usuarios": n} for x in res]
        print(
            f"  ok {r['ok']}/{r['pedidos']}  vazão {r['vazao_ok_s']}/s  mediana {r['mediana_ms']} ms"
            f"  p95 {r['p95_ms']} ms  429={r['e429']} 503={r['e503']} 5xx={r['e5xx']} timeout={r['timeout']}"
        )
        if n == niveis[0] and r["e429"]:
            print(
                "\nO limite de requisições está ligado (HTTP 429): o teste mediria o limitador, não a"
                " capacidade. Defina LIMITE_REQUISICOES=0 no Render, rode de novo e religue depois."
            )
            break
        if r["ok"] < r["pedidos"] / 2:
            print(
                "  Mais da metade falhou: parando aqui para não sobrecarregar o serviço."
            )
            break
        time.sleep(5)  # deixa o servidor respirar entre os níveis

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().astimezone().strftime("%Y-%m-%d_%H%M")
    arq = saida / f"teste_carga_{stamp}"
    with open(f"{arq}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["usuarios", "pergunta", "status", "ms"])
        w.writeheader()
        w.writerows(detalhes)

    agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")
    md = [
        f"# Teste de carga do /chat — {agora}",
        "",
        f"- **Alvo:** `{base}`",
        (
            f"- **Perguntas por nível:** {args.por_nivel}, alternando {len(PERGUNTAS)} perguntas válidas"
            " que consultam o banco"
        ),
        "- **Cronômetro:** do envio do pedido ao fim da resposta, no cliente (inclui a rede até o servidor)",
        "- **Aquecimento:** /health e uma pergunta antes do primeiro nível (sem partida fria)",
        "",
        (
            "| Usuários simultâneos | Respondidas | Vazão (resp./s) | Mediana | p95 | Máximo"
            " | 429 | 503 | Outros 5xx | Tempo esgotado |"
        ),
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in linhas:
        md.append(
            f"| {r['usuarios']} | {r['ok']}/{r['pedidos']} | {r['vazao_ok_s']} | {r['mediana_ms']} ms"
            f" | {r['p95_ms']} ms | {r['max_ms']} ms | {r['e429']} | {r['e503']} | {r['e5xx']}"
            f" | {r['timeout']} |"
        )
    md += ["", f"Detalhe por pergunta: `{arq.name}.csv`.", ""]
    Path(f"{arq}.md").write_text("\n".join(md), encoding="utf-8")
    print("\n" + "\n".join(md))
    print(f"Arquivos: {arq}.csv  e  {arq}.md")


if __name__ == "__main__":
    main()
