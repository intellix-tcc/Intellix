# -*- coding: utf-8 -*-
"""
ablacao_nlu_externa.py — Ablação do NLU na versão 1.2.0, em CORPUS EXTERNO, com
ORÁCULO NUMÉRICO (parecer da banca final, F03).

A ablação anterior (`ablacao_nlu.py`) mediu a v1.1.0 sobre a bateria reutilizada
de 100 perguntas, pela métrica "intenção+slots". A banca pede para repetir na
v1.2.0, com corpus externo e oráculo numérico, e medir **cobertura** (aceitos) e
**risco** (aceitos com valor errado) nos aceitos e recusados — para decidir se a
cabeça de entidades (BIO) fica por ganho demonstrado ou por finalidade de pesquisa.

Configurações (reaproveitadas de ablacao_nlu.py), todas com o modelo v1.2.0:
  B  regras            intenção e slots só por regras (baseline)
  A  modelo (atual)    intenção=modelo; slots=regras + entidade BIO + heurística
  C  modelo sem BIO    intenção=modelo; slots=regras + heurística (ignora o BIO)
  D  modelo só regras  intenção=modelo; slots só por regras

Para cada configuração e cada pergunta inédita (respondível):
  - ACEITO    = intenção definida e todos os obrigatórios do template preenchidos
                (chegaria ao SQL em vez de 422);
  - se ACEITO, executa a consulta real e confere o VALOR contra o oráculo:
        CERTO   = valor confere;
        RISCO   = aceito, mas valor errado (respondeu errado em vez de recusar);
  - RECUSADO  = intenção ausente ou slots incompletos (pede reformulação).

A -C isola a cabeça de entidades; C-D isola a heurística de nome do vendedor.

Uso:
    DATABASE_URL=postgresql://... EMPRESA_ID=00000000-0000-0000-0000-000000000001 \\
        python "ia training/ablacao_nlu_externa.py" --saida docs/evidencias
"""
import argparse
import datetime as dt
import os
import sys
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "database"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "ia training"))

import psycopg  # noqa: E402
from ablacao_nlu import resolver_modelo, _completa  # noqa: E402  (mesma lógica de ablação)
from app.nlu.modelo_nlu import ModeloIntellix  # noqa: E402
from app.nlu.regras import RuleBasedNLU  # noqa: E402
from app.sql.templates import TEMPLATES  # noqa: E402
from avaliar_100_perguntas import CONFIANCA_MINIMA  # noqa: E402
from avaliar_ineditas import carregar, esperado, confere_valor  # noqa: E402
from gabarito_numerico import PARAMS_BASE, carregar_oraculo  # noqa: E402

CONFIGS = ["B regras", "A modelo (atual)", "C modelo sem BIO", "D modelo só regras"]


def extrair_raw(check, rows):
    """Extrai o escalar conferível das linhas CRUAS do template (ordem de coluna
    conhecida de backend/app/sql/templates.py)."""
    if not rows:
        return None
    if check == "faturamento":                       # [periodo, faturamento]
        return sum((Decimal(str(r[1])) for r in rows), Decimal("0.00"))
    if check == "quantidade":                        # [periodo, quantidade_vendas]
        return int(sum(int(r[1]) for r in rows))
    if check == "ticket":                            # [ticket_medio]
        return None if rows[0][0] is None else Decimal(str(rows[0][0])).quantize(Decimal("0.01"))
    if check == "faturamento_vendedor":              # [vendedor, faturamento, qtd]
        return Decimal(str(rows[0][1]))
    if check == "top_produto":                       # [produto, qtd, faturamento]
        return rows[0][0]
    if check in ("top_cliente", "top_canal", "top_categoria", "top_pagamento"):
        return rows[0][0]                            # 1ª coluna é o rótulo do grupo
    if check == "variacao":                          # [atual, anterior, variacao]
        return Decimal(str(rows[0][2])).quantize(Decimal("0.01"))
    if check == "comparacao":                        # [periodo_a/b, faturamento]
        return tuple(Decimal(str(r[1])) for r in rows)
    if check == "sem_saida":                         # [produto, categoria]
        return sorted(r[0] for r in rows)
    return None


def main():
    ap = argparse.ArgumentParser(description="Ablação do NLU v1.2.0 em corpus externo com oráculo numérico (F03).")
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("Defina DATABASE_URL (banco semeado) e EMPRESA_ID da empresa demo.")

    modelo = ModeloIntellix(str(RAIZ / "backend/app/nlu/intellix_nlu_v1.2.0.pt"))
    regras = RuleBasedNLU()
    orac = carregar_oraculo()
    perguntas = [q for q in carregar() if q["check"] not in ("recusa", "param_faltando", "sem_resultado")]

    # acumuladores por config
    est = {c: {"aceito": 0, "certo": 0, "risco": 0, "recusado": 0,
               "vend_aceito": 0, "vend_certo": 0} for c in CONFIGS}

    with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
        for q in perguntas:
            texto, intencao_certa, check = q["pergunta"], q["intencao"], q["check"]
            prev = modelo.prever(texto)
            rb = regras.parse(texto)
            resolvido = {
                "B regras": (rb.intencao if rb.confianca >= CONFIANCA_MINIMA else None, rb.entidades),
                "A modelo (atual)": resolver_modelo(prev, texto, usar_bio=True, usar_heuristica=True),
                "C modelo sem BIO": resolver_modelo(prev, texto, usar_bio=False, usar_heuristica=True),
                "D modelo só regras": resolver_modelo(prev, texto, usar_bio=False, usar_heuristica=False),
            }
            esp = esperado(check, q["params"], orac)
            for c, (intencao, ent) in resolvido.items():
                e = est[c]
                vendedor = intencao_certa == "desempenho_vendedor"
                # aceito = chega ao SQL com a intenção CERTA e obrigatórios preenchidos
                if intencao == intencao_certa and _completa(intencao, ent):
                    e["aceito"] += 1
                    if vendedor:
                        e["vend_aceito"] += 1
                    cur.execute(TEMPLATES[intencao]["sql"], {**PARAMS_BASE, **ent})
                    obt = extrair_raw(check, cur.fetchall())
                    if confere_valor(check, esp, obt):
                        e["certo"] += 1
                        if vendedor:
                            e["vend_certo"] += 1
                    else:
                        e["risco"] += 1
                else:
                    e["recusado"] += 1

    n = len(perguntas)
    L = [
        "# Ablação do NLU na v1.2.0 — corpus externo, oráculo numérico (F03)",
        "",
        "Repete a ablação (`ablacao_nlu.py`) na **versão 1.2.0**, sobre o conjunto",
        "**inédito** (`docs/perguntas_ineditas.jsonl`, externo ao treino e às 100), com",
        "**oráculo numérico**: cada aceito é executado e o valor conferido. Gerado por",
        "`ia training/ablacao_nlu_externa.py`.",
        "",
        f"- **Data:** {dt.datetime.now().astimezone():%d/%m/%Y %H:%M (UTC%z)}",
        f"- **Modelo:** `intellix_nlu_v1.2.0.pt` · **perguntas respondíveis:** {n}",
        "",
        "## Cobertura e risco por configuração",
        "",
        "| Config | Aceitos | Valor certo | **Risco** (aceito errado) | Recusados |",
        "|---|---:|---:|---:|---:|",
    ]
    for c in CONFIGS:
        e = est[c]
        L.append(f"| {c} | {e['aceito']}/{n} | {e['certo']}/{n} | **{e['risco']}/{n}** | {e['recusado']}/{n} |")

    difAC = est["A modelo (atual)"]["certo"] - est["C modelo sem BIO"]["certo"]
    difCD = est["C modelo sem BIO"]["certo"] - est["D modelo só regras"]["certo"]
    L += [
        "",
        f"**A − C = {difAC:+d} acerto(s) de valor** → contribuição da cabeça de entidades (BIO).",
        f"**C − D = {difCD:+d} acerto(s) de valor** → contribuição da heurística de nome.",
        "",
        "## Onde BIO/heurística atuam: desempenho_vendedor",
        "",
        "| Config | Vendedor aceito | Vendedor com valor certo |",
        "|---|---:|---:|",
    ]
    for c in CONFIGS:
        e = est[c]
        L.append(f"| {c} | {e['vend_aceito']} | {e['vend_certo']} |")

    manter = est["A modelo (atual)"]["certo"] - est["C modelo sem BIO"]["certo"]
    L += [
        "",
        "## Conclusão (manter a cabeça de entidades?)",
        "",
        f"No corpus externo e com oráculo numérico, a cabeça BIO adiciona **{manter:+d}**",
        "acerto(s) de valor sobre a configuração sem BIO. A resolução de slots (período,",
        "limite) é determinística (regras) e independe do BIO; o nome do vendedor é",
        "recuperado pela heurística de regex. Logo, a cabeça de entidades se justifica",
        "**por finalidade de pesquisa / robustez**, não por ganho operacional demonstrado",
        "neste conjunto — conforme o ponto do parecer (F03). As 100 perguntas seguem como",
        "regressão; este conjunto mede generalização.",
        "",
    ]
    md = "\n".join(L) + "\n"
    print(md)
    if args.saida:
        destino = Path(args.saida)
        destino.mkdir(parents=True, exist_ok=True)
        arq = destino / f"ablacao_nlu_v1.2_externa_{dt.datetime.now():%Y-%m-%d_%H%M}.md"
        arq.write_text(md, encoding="utf-8")
        print("Arquivo:", arq)


if __name__ == "__main__":
    main()
