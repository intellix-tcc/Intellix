# -*- coding: utf-8 -*-
"""
ablacao_nlu.py — mede a contribuição de cada parte da resolução de intenção e
entidades (feedback TC2 F04: "fazer ablação NLU ... para identificar a
contribuição efetiva" e "não presumir que a cabeça de entidades está
desconectada sem conferir o código").

Fato do código (ver backend/app/nlu/adaptador_modelo.py): a INTENÇÃO vem do
modelo; os SLOTS (período -> datas ISO, limite) vêm das REGRAS determinísticas;
o nome do VENDEDOR usa a entidade BIO do modelo e, como reserva, uma heurística
de regex. As etiquetas BIO do modelo NÃO resolvem período (texto "março" não é
uma data ISO) — por isso o período é das regras.

Configurações avaliadas (todas offline, sem banco):
  B  regras            intenção e slots só por regras (RuleBasedNLU baseline)
  A  modelo (atual)    intenção=modelo; slots=regras + entidade BIO + heurística
  C  modelo sem BIO    intenção=modelo; slots=regras + heurística (ignora o BIO)
  D  modelo só regras  intenção=modelo; slots só por regras (sem BIO e sem heur.)

Diferenças:  A−C = contribuição da cabeça de entidades (BIO) do modelo
             C−D = contribuição da heurística de nome
Métrica: "intenção+slots" = intenção correta E todos os parâmetros obrigatórios
do template preenchidos (ou seja, chegaria ao SQL em vez de um 422).
"""

import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ / "scripts"))

from avaliar_100_perguntas import ler_perguntas, ARQ_PERGUNTAS, FORA_DE_ESCOPO, PARAM_FALTANDO, SEM_RESULTADO, CONFIANCA_MINIMA  # noqa: E402
from app.nlu import adaptador_modelo as AD  # noqa: E402
from app.nlu.modelo_nlu import ModeloIntellix  # noqa: E402
from app.nlu.regras import RuleBasedNLU  # noqa: E402
from app.sql.templates import TEMPLATES  # noqa: E402


def _completa(intencao, entidades) -> bool:
    """A intenção existe e todos os obrigatórios do template foram preenchidos."""
    t = TEMPLATES.get(intencao)
    return bool(t) and all(p in entidades for p in t["obrigatorios"])


def resolver_modelo(prev, texto, usar_bio: bool, usar_heuristica: bool):
    """Reproduz o adaptador, podendo desligar o BIO do modelo e/ou a heurística,
    para a ablação. Devolve (intencao, entidades)."""
    if prev["fallback"] or prev["intencao"] is None:
        return None, {}
    if not AD._tem_termo_dominio(texto):
        return None, {}
    entidades_modelo = prev["entidades"] if usar_bio else {}
    heur_orig = AD._nome_por_heuristica
    if not usar_heuristica:
        AD._nome_por_heuristica = lambda _t: None
    try:
        ent = AD._resolver_entidades(prev["intencao"], texto.lower(), entidades_modelo, texto)
    finally:
        AD._nome_por_heuristica = heur_orig
    return prev["intencao"], ent


def main():
    modelo = ModeloIntellix(str(RAIZ / "backend/app/nlu/intellix_nlu_v1.1.0.pt"))
    regras = RuleBasedNLU()
    perguntas = [p for p in ler_perguntas(ARQ_PERGUNTAS)
                 if p["categoria"] not in (FORA_DE_ESCOPO, PARAM_FALTANDO, SEM_RESULTADO)]

    configs = ["B regras", "A modelo (atual)", "C modelo sem BIO", "D modelo so regras"]
    acertos = {c: {"int": 0, "intslot": 0} for c in configs}
    por_cat = {c: defaultdict(lambda: [0, 0]) for c in configs}  # cat -> [intslot_ok, total]

    for p in perguntas:
        cat, texto = p["categoria"], p["pergunta"]
        prev = modelo.prever(texto)

        # B: regras puras
        rb = regras.parse(texto)
        resultados = {
            "B regras": (rb.intencao if rb.confianca >= CONFIANCA_MINIMA else None, rb.entidades),
            "A modelo (atual)": resolver_modelo(prev, texto, usar_bio=True, usar_heuristica=True),
            "C modelo sem BIO": resolver_modelo(prev, texto, usar_bio=False, usar_heuristica=True),
            "D modelo so regras": resolver_modelo(prev, texto, usar_bio=False, usar_heuristica=False),
        }
        for c, (intencao, ent) in resultados.items():
            int_ok = intencao == cat
            intslot_ok = int_ok and _completa(intencao, ent)
            acertos[c]["int"] += int_ok
            acertos[c]["intslot"] += intslot_ok
            d = por_cat[c][cat]
            d[1] += 1
            d[0] += intslot_ok

    n = len(perguntas)
    linhas = ["# Ablação do NLU (TC2 F04)", "",
              f"- Perguntas (12 intenções): {n}",
              f"- Modelo: intellix_nlu_v1.1.0.pt", "",
              "## Contribuição de cada parte", "",
              "| Config | Intenção | Intenção+slots |", "|---|---:|---:|"]
    for c in configs:
        a = acertos[c]
        linhas.append(f"| {c} | {100*a['int']/n:.1f}% | {100*a['intslot']/n:.1f}% |")
    difAC = 100 * (acertos["A modelo (atual)"]["intslot"] - acertos["C modelo sem BIO"]["intslot"]) / n
    difCD = 100 * (acertos["C modelo sem BIO"]["intslot"] - acertos["D modelo so regras"]["intslot"]) / n
    linhas += ["",
               f"**A − C = {difAC:+.1f} pp** → contribuição da cabeça de entidades (BIO) do modelo.",
               f"**C − D = {difCD:+.1f} pp** → contribuição da heurística de nome do vendedor.",
               "",
               "## desempenho_vendedor (onde o BIO/heurística atuam)", "",
               "| Config | Intenção+slots (desempenho_vendedor) |", "|---|---:|"]
    for c in configs:
        ok, tot = por_cat[c]["desempenho_vendedor"]
        linhas.append(f"| {c} | {ok}/{tot} |")
    md = "\n".join(linhas) + "\n"

    saida = RAIZ / "docs" / "evidencias"
    saida.mkdir(parents=True, exist_ok=True)
    import datetime as dt
    destino = saida / f"ablacao_nlu_{dt.datetime.now():%Y-%m-%d_%H%M}.md"
    destino.write_text(md, encoding="utf-8")
    print(md)
    print("Arquivo:", destino)


if __name__ == "__main__":
    main()
