#!/usr/bin/env python3
"""
avaliar_ineditas.py — Avaliação de GENERALIZAÇÃO em perguntas inéditas.

Atende ao parecer da banca final, F01 ("testes de generalização e conjuntos
reutilizados") e ao item nº 1 da defesa ("consulta inédita com cálculo
conferível"). As 100 perguntas de validação têm sobreposição com o treino e
guiaram ajustes, então não medem generalização. Este conjunto (`docs/
perguntas_ineditas.jsonl`) é redigido **fora dos moldes de treino e das 100**,
com formulações e vocabulário diferentes, e cada pergunta traz um GABARITO: a
intenção esperada e os parâmetros para recomputar o valor certo de forma
independente (mesmo oráculo em Python de `scripts/gabarito_numerico.py`).

Congelamento (F01): o relatório fixa o commit e o SHA-256 do modelo usados, para
que a medição seja atribuível a um estado exato. Os pesos, o limiar (0,70), as
regras e o banco semeado não mudam durante a bateria.

Separa, por pergunta, três níveis (parecer: técnico × semântico × numérico):
  - TÉCNICO   — o sistema respondeu no formato esperado (200/422/404 certo);
  - SEMÂNTICO — a intenção/decisão foi a esperada (consulta certa ou recusa certa);
  - NUMÉRICO  — o valor conferível bate com o oráculo (faturamento, ticket,
                contagem, líder de ranking, variação...).

Reporta a taxa por intenção, o comportamento nas recusas e um intervalo de
confiança de Wilson (95%) adequado ao tamanho pequeno da amostra.

Modos:
  app  (padrão) — ponta a ponta via FastAPI TestClient (NLU + SQL + resposta).
                  Precisa de DATABASE_URL (banco semeado) e do modelo (torch).
  nlu            — só a classificação (ModeloTreinadoNLU.parse), sem banco.
                  Mede a generalização da INTENÇÃO; não conclui valor.

Uso:
    DATABASE_URL=postgresql://... NLU_BACKEND=modelo \\
    EMPRESA_ID=00000000-0000-0000-0000-000000000001 \\
        python scripts/avaliar_ineditas.py --saida docs/evidencias
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "database"))

from scripts.gabarito_numerico import (  # noqa: E402  oráculo independente
    carregar_oraculo, no_periodo, soma, vendas_distintas,
)

ARQ = RAIZ / "docs" / "perguntas_ineditas.jsonl"
LIMIAR = 0.70

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


# --------------------------------------------------------------------------- #
# Oráculo: valor esperado por tipo de verificação                              #
# --------------------------------------------------------------------------- #
def _argmax_grupo(linhas, campo):
    agg = defaultdict(lambda: Decimal("0.00"))
    for ln in linhas:
        agg[ln[campo]] += ln["valor_total"]
    return max(agg.items(), key=lambda kv: kv[1])[0] if agg else None


def esperado(check, params, orac):
    p = params
    # filtros implícitos na pergunta (canal, categoria, vendedor...) entram no
    # oráculo também, para conferir exatamente o mesmo recorte que o sistema fez.
    _FILT = ("produto", "categoria", "vendedor", "cliente", "canal", "forma_pagamento")
    filtros_fixos = {k: p[k] for k in _FILT if k in p}

    def base(k_ini="ini", k_fim="fim", **extra):
        return no_periodo(orac, p[k_ini], p[k_fim], **{**filtros_fixos, **extra})
    if check == "faturamento":
        return soma(base())
    if check == "ticket":
        b = base()
        return (soma(b) / vendas_distintas(b)).quantize(Decimal("0.01"))
    if check == "quantidade":
        return vendas_distintas(base())
    if check == "faturamento_vendedor":
        return soma(base())
    if check == "top_produto":
        return _argmax_grupo(base(), "produto")
    if check == "top_cliente":
        return _argmax_grupo(base(), "cliente")
    if check == "top_canal":
        return _argmax_grupo(base(), "canal")
    if check == "top_categoria":
        return _argmax_grupo(base(), "categoria")
    if check == "top_pagamento":
        return _argmax_grupo(base(), "pagamento")
    if check == "variacao":
        atual, ant = soma(base()), soma(base("ini2", "fim2"))
        return ((atual - ant) / ant * 100).quantize(Decimal("0.01"))
    if check == "comparacao":
        return (soma(base()), soma(base("ini2", "fim2")))
    if check == "sem_saida":
        import seed as seedmod
        todos = {n for _c, itens in seedmod.CATALOGO.items() for (n, _pr) in itens}
        return sorted(todos - {ln["produto"] for ln in base()})
    return None


# --------------------------------------------------------------------------- #
# Obtido: valor extraído da resposta do /chat                                  #
# --------------------------------------------------------------------------- #
def _col(d, nome):
    cols = d.get("colunas") or []
    return cols.index(nome) if nome in cols else None


def _soma_col(d, nome):
    i = _col(d, nome)
    return sum((Decimal(str(r[i])) for r in d["linhas"]), Decimal("0.00")) if i is not None else None


def obtido(check, d):
    if check in ("faturamento",):
        return _soma_col(d, "faturamento")
    if check == "quantidade":
        return int(_soma_col(d, "quantidade_vendas"))
    if check == "ticket":
        i = _col(d, "ticket_medio")
        return Decimal(str(d["linhas"][0][i])).quantize(Decimal("0.01"))
    if check == "faturamento_vendedor":
        i = _col(d, "faturamento")
        return Decimal(str(d["linhas"][0][i]))
    if check == "top_produto":
        return d["linhas"][0][_col(d, "produto")]
    if check == "top_cliente":
        return d["linhas"][0][_col(d, "cliente")]
    if check == "top_canal":
        return d["linhas"][0][_col(d, "canal")]
    if check == "top_categoria":
        return d["linhas"][0][_col(d, "categoria")]
    if check == "top_pagamento":
        return d["linhas"][0][_col(d, "forma_pagamento")]
    if check == "variacao":
        return Decimal(str(d["linhas"][0][_col(d, "variacao_percentual")])).quantize(Decimal("0.01"))
    if check == "comparacao":
        i = _col(d, "faturamento")
        return tuple(Decimal(str(r[i])) for r in d["linhas"])
    if check == "sem_saida":
        return sorted(r[_col(d, "produto")] for r in d["linhas"])
    return None


def confere_valor(check, esp, obt) -> bool:
    if esp is None or obt is None:
        return False
    if check in ("faturamento", "ticket", "faturamento_vendedor"):
        return abs(Decimal(str(obt)) - Decimal(str(esp))) <= Decimal("0.05")
    if check == "variacao":
        return abs(Decimal(str(obt)) - Decimal(str(esp))) <= Decimal("0.1")
    if check == "quantidade":
        return int(obt) == int(esp)
    if check == "comparacao":
        return all(abs(Decimal(str(o)) - Decimal(str(e))) <= Decimal("0.05") for o, e in zip(obt, esp))
    if check == "sem_saida":
        return list(obt) == list(esp)
    return obt == esp  # top_* (nome)


# --------------------------------------------------------------------------- #
# Wilson 95%                                                                   #
# --------------------------------------------------------------------------- #
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den
    return (max(0.0, c - h), min(1.0, c + h))


# --------------------------------------------------------------------------- #
class R:
    def __init__(self, q):
        self.__dict__.update(q)
        self.tecnico = self.semantico = self.numerico = False
        self.obt_int = "-"
        self.detalhe = ""
    REFUSAL = {"recusa", "param_faltando", "sem_resultado"}


def _git(*a):
    try:
        return subprocess.check_output(["git", "-C", str(RAIZ), *a], text=True).strip()
    except Exception:
        return "-"


def _sha_modelo():
    p = RAIZ / "backend" / "app" / "nlu" / "intellix_nlu_v1.2.0.pt"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def carregar(arq: Path = ARQ):
    return [json.loads(l) for l in Path(arq).read_text(encoding="utf-8").splitlines() if l.strip()]


def avaliar_app(perguntas):
    import warnings
    warnings.filterwarnings("ignore")
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    orac = carregar_oraculo()
    out = []
    for q in perguntas:
        r = R(q)
        resp = c.post("/chat", json={"pergunta": q["pergunta"]})
        st = resp.status_code
        d = resp.json()
        tipo = (d.get("detail") or {}).get("tipo", "") if isinstance(d.get("detail"), dict) else ""
        if q["check"] == "recusa":
            r.tecnico = st == 422
            r.semantico = st == 422 and tipo == "baixa_confianca"
            r.numerico = r.semantico
            r.obt_int = f"{st}/{tipo or '-'}"
            r.detalhe = "recusou por baixa confiança" if r.semantico else f"deveria recusar; veio {st}/{tipo}"
        elif q["check"] == "param_faltando":
            r.tecnico = r.semantico = r.numerico = st == 422
            r.obt_int = f"{st}/{tipo or '-'}"
            r.detalhe = "pediu parâmetro (422)" if r.semantico else f"esperado 422; veio {st}"
        elif q["check"] == "sem_resultado":
            r.tecnico = r.semantico = r.numerico = (st == 404 and tipo == "sem_resultado")
            r.obt_int = f"{st}/{tipo or '-'}"
            r.detalhe = "404 sem_resultado" if r.semantico else f"esperado 404; veio {st}/{tipo}"
        else:
            r.tecnico = st == 200
            titulo_base = (d.get("titulo") or "").split(" · ")[0]
            r.obt_int = TITULO_PARA_INTENCAO.get(titulo_base, f"({st})")
            r.semantico = st == 200 and r.obt_int == q["intencao"]
            if r.semantico:
                esp = esperado(q["check"], q["params"], orac)
                try:
                    obt = obtido(q["check"], d)
                except Exception as e:  # noqa: BLE001
                    obt = None
                    r.detalhe = f"erro ao extrair valor: {type(e).__name__}"
                r.numerico = confere_valor(q["check"], esp, obt)
                r.detalhe = f"esp={esp} obt={obt}" if not r.detalhe else r.detalhe
            else:
                r.detalhe = f"intenção {r.obt_int} ≠ {q['intencao']}"
        out.append(r)
    return out


def avaliar_nlu(perguntas):
    import warnings
    warnings.filterwarnings("ignore")
    from app.nlu.adaptador_modelo import ModeloTreinadoNLU
    nlu = ModeloTreinadoNLU()
    out = []
    for q in perguntas:
        r = R(q)
        if q["check"] in ("param_faltando", "sem_resultado"):
            r.detalhe = "depende do executor/banco (só no modo app)"
            r.tecnico = r.semantico = r.numerico = None
            out.append(r)
            continue
        i = nlu.parse(q["pergunta"])
        aceita = i.intencao is not None and i.confianca >= LIMIAR
        r.obt_int = f"{i.intencao} ({i.confianca:.2f})"
        if q["check"] == "recusa":
            r.tecnico = r.semantico = r.numerico = not aceita
            r.detalhe = "rejeitada (conf < 0,70)" if not aceita else "aceita indevidamente"
        else:
            r.tecnico = True
            r.semantico = aceita and i.intencao == q["intencao"]
            r.numerico = None  # valor não é medido no modo nlu
            r.detalhe = "intenção certa" if r.semantico else f"obteve {i.intencao}"
        out.append(r)
    return out


def _sim(v):
    return "—" if v is None else ("✅" if v else "❌")


def relatorio_md(res, modo, alvo):
    agora = dt.datetime.now().astimezone().strftime("%d/%m/%Y %H:%M (UTC%z)")
    aplicaveis = [r for r in res if not (r.semantico is None and r.numerico is None)]
    respondiveis = [r for r in aplicaveis if r.check not in R.REFUSAL]
    recusas = [r for r in aplicaveis if r.check in R.REFUSAL]
    n = len(aplicaveis)
    # acerto combinado: semântico para todas; numérico quando aplicável
    acerto = [r for r in aplicaveis if (r.numerico if r.numerico is not None else r.semantico)]
    k = len(acerto)
    lo, hi = wilson(k, n)
    sem_ok = sum(bool(r.semantico) for r in aplicaveis)
    num_aplic = [r for r in res if r.numerico is not None and r.check not in R.REFUSAL]
    num_ok = sum(bool(r.numerico) for r in num_aplic)

    L = [
        "# Avaliação de generalização — perguntas inéditas",
        "",
        "Conjunto redigido fora dos moldes de treino e das 100 perguntas, com",
        "gabarito de intenção e de valor (parecer da banca final, F01 e item nº 1 da",
        "defesa). Gerado por `scripts/avaliar_ineditas.py`.",
        "",
        f"- **Data:** {agora}  ·  **modo:** `{modo}`  ·  **alvo:** {alvo}",
        f"- **Congelamento:** commit `{_git('rev-parse', '--short', 'HEAD')}` · "
        f"modelo `intellix_nlu_v1.2.0.pt` SHA-256 `{_sha_modelo()[:16]}…` · limiar {LIMIAR}",
        f"- **Perguntas:** {n} ({len(respondiveis)} respondíveis + {len(recusas)} de recusa)",
        "",
        "## Resumo",
        "",
        "| Nível | Métrica |",
        "|---|---|",
        f"| Semântico (intenção/decisão certa) | {sem_ok}/{n} ({100*sem_ok/n:.1f}%) |",
        f"| Numérico (valor confere, quando aplicável) | {num_ok}/{len(num_aplic)}"
        + (f" ({100*num_ok/len(num_aplic):.1f}%)" if num_aplic else "") + " |",
        f"| **Acerto combinado** | **{k}/{n} ({100*k/n:.1f}%)** · IC95% Wilson "
        f"[{100*lo:.1f}% – {100*hi:.1f}%] |",
        "",
        "> O intervalo de Wilson é largo de propósito: a amostra é pequena. Ele",
        "> expressa a incerteza honesta sobre a generalização, não um ponto único.",
        "",
        "## Por pergunta",
        "",
        "| ID | Intenção esperada | Téc | Sem | Num | Obtido / detalhe |",
        "|---|---|:-:|:-:|:-:|---|",
    ]
    for r in res:
        L.append(f"| {r.id} | `{r.intencao}` | {_sim(r.tecnico)} | {_sim(r.semantico)} | "
                 f"{_sim(r.numerico)} | {r.detalhe} |")

    # por intenção
    porint = defaultdict(lambda: [0, 0])
    for r in respondiveis:
        porint[r.intencao][1] += 1
        if (r.numerico if r.numerico is not None else r.semantico):
            porint[r.intencao][0] += 1
    L += ["", "## Por intenção (respondíveis)", "", "| Intenção | Acerto |", "|---|---:|"]
    for intencao, (a, t) in sorted(porint.items()):
        L.append(f"| `{intencao}` | {a}/{t} |")

    # recusas
    rec_ok = sum(bool(r.semantico) for r in recusas)
    L += [
        "",
        "## Comportamento nas recusas",
        "",
        f"{rec_ok}/{len(recusas)} recusas corretas (fora de escopo → baixa confiança; "
        "parâmetro ausente → 422; fora do período dos dados → 404).",
        "",
        "## Limite honesto (método)",
        "",
        "- As perguntas foram redigidas pela equipe de desenvolvimento evitando os",
        "  moldes de treino; para rigor máximo na defesa, **some perguntas coletadas",
        "  de pessoas de fora** da equipe e reexecute — o avaliador aceita qualquer",
        "  `perguntas_ineditas.jsonl`.",
        "- O gabarito de valor é recomputado em Python puro (independente do SQL).",
        "- As 100 perguntas seguem como **regressão** (`avaliar_100_perguntas.py`), não",
        "  como prova de generalização.",
        "",
        "## Reproduzir",
        "",
        "```bash",
        "DATABASE_URL=postgresql://... NLU_BACKEND=modelo \\",
        "EMPRESA_ID=00000000-0000-0000-0000-000000000001 \\",
        "    python scripts/avaliar_ineditas.py --modo app --saida docs/evidencias",
        "python scripts/avaliar_ineditas.py --modo nlu   # só a intenção",
        "```",
        "",
    ]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Avaliação de generalização em perguntas inéditas (F01).")
    ap.add_argument("--modo", choices=["app", "nlu"], default="app")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--arquivo", default=str(ARQ),
                    help="conjunto .jsonl a avaliar (padrão: perguntas_ineditas.jsonl)")
    args = ap.parse_args()

    perguntas = carregar(args.arquivo)
    if args.modo == "app":
        if not os.environ.get("DATABASE_URL"):
            sys.exit("modo app precisa de DATABASE_URL (banco semeado) e NLU_BACKEND=modelo.")
        res = avaliar_app(perguntas)
        alvo = "FastAPI TestClient (ponta a ponta)"
    else:
        res = avaliar_nlu(perguntas)
        alvo = "ModeloTreinadoNLU (classificação)"

    print(f"\n{'ID':4} {'TÉC':3} {'SEM':3} {'NUM':3}  INTENÇÃO / DETALHE")
    for r in res:
        print(f"{r.id:4} {_sim(r.tecnico):>3} {_sim(r.semantico):>3} {_sim(r.numerico):>3}  "
              f"{r.intencao} — {r.detalhe}")
    aplic = [r for r in res if not (r.semantico is None and r.numerico is None)]
    n = len(aplic)
    k = sum(1 for r in aplic if (r.numerico if r.numerico is not None else r.semantico))
    lo, hi = wilson(k, n)
    print(f"\nAcerto combinado: {k}/{n} ({100*k/n:.1f}%)  IC95% [{100*lo:.1f}% – {100*hi:.1f}%]")

    if args.saida:
        destino = Path(args.saida)
        destino.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        arq = destino / f"avaliacao_ineditas_{args.modo}_{stamp}.md"
        arq.write_text(relatorio_md(res, args.modo, alvo), encoding="utf-8")
        print(f"Relatório: {arq}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
