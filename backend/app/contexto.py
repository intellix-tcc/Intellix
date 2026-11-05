"""Resolução de contexto conversacional (histórico) para o /chat.

O /chat é sem estado: cada pergunta chega sozinha. Mas o usuário conversa em
sequência, e a pergunta seguinte costuma trazer só o que mudou:

    "Qual o produto mais vendido em 2026?"
    "E de calçados?"                      -> mesma pergunta, só a categoria
    "Quantas botas de couro vendemos?"     -> outra pergunta, mesmo ano (2026)
    "E em 2025?"                           -> mesma pergunta, outro ano
    "E qual mês vendeu mais?"              -> outra pergunta, mesmas botas e ano

O frontend reenvia o contexto da resposta anterior (intenção + parâmetros:
período, filtros, limite). Aqui se decide o que herdar. Três situações:

  1. A frase NÃO se classificou sozinha (elíptica: "e de calçados?", "e em
     abril?", "e da Fernanda?"): herda a intenção anterior e todos os
     parâmetros, trocando só o que a frase trouxe de novo (período ou filtro).
     Se ela não trouxe nada reconhecível, não herda (segue para o 422 de
     reformulação, em vez de chutar).
  2. A frase se classificou e é uma CONTINUAÇÃO ("e o ticket médio?", "e
     quantas unidades?", "desse produto", "nesse período"): vale a intenção
     nova, mas herda período e filtros que ela não trocou.
  3. A frase se classificou e é uma pergunta NOVA: vale tudo dela; só o
     período, se ela não citar nenhum, continua o da conversa ("quantas botas
     vendemos no ano?" logo depois de uma pergunta sobre 2026 é sobre 2026).

Determinístico e o mesmo para os dois backends de NLU (regras e modelo): a
resolução de slots continua em app/nlu/adaptador_modelo._resolver_entidades.
"""

import re

from app.fallbacks import CONFIANCA_MINIMA
from app.filtros import FILTROS, GRUPOS, sem_acento
from app.models import Contexto, Interpretacao
from app.nlu import regras as R
from app.nlu.adaptador_modelo import _resolver_entidades
from app.periodo_dataset import _trocar_ano, tem_ano_explicito
from app.refino import QUEBRA_POR, pede_refino

# A frase cita um período? ("e em abril?", "e em 2023?", "e no último
# trimestre?", "e no mês passado?", "esse ano")
_MESES = "|".join(R.MESES.keys())
_TEM_PERIODO = re.compile(
    rf"\b(?:{_MESES})\b|\b20\d{{2}}\b|\btrimestre\b|\bsemestre\b"
    r"|[úu]ltim|passad|anterior|\b(?:n|d)?es[st]e\s+(?:m[eê]s|ano)\b|\bm[eê]s\s+atual\b",
    re.IGNORECASE,
)

# "no ano", "do ano", "o ano todo": o ano da conversa, inteiro.
_ANO_DA_CONVERSA = re.compile(r"\b(?:n|d)o\s+ano\b(?!\s+(?:passado|anterior))|\bano\s+(?:todo|inteiro)\b")

# Continuação: começa com "e"/"agora"/"e se", ou aponta para trás.
_CONTINUACAO = re.compile(
    r"^\s*(?:e|e\s+se|agora|tamb[eé]m|mas)\b"
    r"|\b(?:des[st][ea]|nes[st][ea]|del[ea]|dis[st]o|mesm[oa])\b",
    re.IGNORECASE,
)

_PERIODO_UNICO = ("periodo_inicio", "periodo_fim")


def _chaves_de_periodo(ent: dict) -> dict:
    return {k: v for k, v in ent.items() if k.startswith("periodo_")}


def _ano_do_contexto(ent: dict) -> int | None:
    """Ano do período anterior, quando ele cabe num ano só."""
    ini, fim = str(ent.get("periodo_inicio", "")), str(ent.get("periodo_fim", ""))
    if len(ini) >= 4 and ini[:4] == fim[:4] and ini[:4].isdigit():
        return int(ini[:4])
    return None


# "mês passado", "último trimestre", "esse ano": relativos a hoje, não à conversa.
_RELATIVO = re.compile(r"passad|anterior|[úu]ltim|\b(?:n|d)?es[st][ea]\b|\batual\b", re.IGNORECASE)


def _periodo_novo(intencao: str, texto: str, ctx_ent: dict, ano_ref: int | None) -> dict:
    """Período que a frase cita, resolvido para a intenção. Sem ano na frase,
    um mês ou trimestre por nome fica no ano da conversa ("e em abril?" depois
    de 2025 = abril de 2025); um período relativo ("e no mês passado?") parte
    de hoje (R.referencia())."""
    novas = _chaves_de_periodo(_resolver_entidades(intencao, texto.lower(), {}, texto))
    if novas and not tem_ano_explicito(texto) and not _RELATIVO.search(texto):
        ano = _ano_do_contexto(ctx_ent)
        atual = str(R.ano_atual())
        if ano:
            novas = {
                k: _trocar_ano(v, ano) if isinstance(v, str) and v[:4] == atual else v
                for k, v in novas.items()
            }
    return novas


def _ano_inteiro(ctx_ent: dict, ano_ref: int | None) -> dict:
    ano = _ano_do_contexto(ctx_ent) or ano_ref or R.ano_atual()
    return {"periodo_inicio": f"{ano}-01-01", "periodo_fim": f"{ano}-12-31"}


def _filtros_herdados(ctx_ent: dict, novos: dict) -> dict:
    """Filtros da conversa que a frase não trocou. Produto e categoria são o
    mesmo recorte: citar uma categoria nova descarta o produto anterior."""
    grupos_novos = {GRUPOS.get(k, k) for k in novos}
    return {k: v for k, v in ctx_ent.items() if k in FILTROS and GRUPOS.get(k, k) not in grupos_novos}


def _um_periodo(ent: dict) -> bool:
    return all(k in ent for k in _PERIODO_UNICO)


def aplicar_contexto(
    interp: Interpretacao, contexto: Contexto | None, texto: str, ano_ref: int | None = None
) -> Interpretacao:
    """Devolve a interpretação completada pelo contexto da conversa (ver o
    docstring do módulo). Sem contexto, devolve `interp` inalterada."""
    if contexto is None or not contexto.intencao:
        return interp

    ctx_ent = dict(contexto.entidades or {})
    t = sem_acento(texto.lower())
    cita_periodo = bool(_TEM_PERIODO.search(texto))
    ano_da_conversa = bool(_ANO_DA_CONVERSA.search(t)) and not cita_periodo
    filtros_novos = {k: v for k, v in interp.entidades.items() if k in FILTROS}
    confiante = bool(interp.intencao) and interp.confianca >= CONFIANCA_MINIMA
    continuacao = bool(_CONTINUACAO.search(texto))
    # "E no pix?" depois de "quantas botas em 2026?": o modelo lê "vendas por
    # pagamento", mas a pessoa só trocou o recorte. Quebra pela mesma dimensão
    # que a frase acabou de filtrar, numa continuação, é só recorte novo.
    if confiante and continuacao and any(
        k in filtros_novos for k in QUEBRA_POR.get(interp.intencao or "", ())
    ):
        confiante = False

    # ---- 1. frase elíptica: herda a intenção anterior --------------------
    if not confiante:
        intencao = contexto.intencao
        novas: dict = {}
        if cita_periodo:
            novas = _periodo_novo(intencao, texto, ctx_ent, ano_ref)
        elif ano_da_conversa and _um_periodo(ctx_ent):
            novas = _ano_inteiro(ctx_ent, ano_ref)
        if not novas and not filtros_novos and not pede_refino(t):
            return interp  # nada de novo reconhecível -> 422, sem chutar
        entidades = {
            **{k: v for k, v in ctx_ent.items() if k not in FILTROS},
            **_filtros_herdados(ctx_ent, filtros_novos),
            **novas,
            **filtros_novos,
        }
        return Interpretacao(
            intencao=intencao,
            confianca=max(interp.confianca, CONFIANCA_MINIMA),
            entidades=entidades,
            texto_original=interp.texto_original,
            entidades_modelo=interp.entidades_modelo,
        )

    entidades = dict(interp.entidades)

    # Período: a frase não citou nenhum -> o da conversa (quando o formato
    # serve: um período para um período). "no ano" -> o ano da conversa inteiro.
    if not cita_periodo and _um_periodo(interp.entidades):
        if ano_da_conversa:
            entidades.update(_ano_inteiro(ctx_ent, ano_ref))
        elif _um_periodo(ctx_ent):
            entidades.update({k: ctx_ent[k] for k in _PERIODO_UNICO})

    # ---- 2. continuação: herda também os filtros -------------------------
    if continuacao:
        entidades = {**_filtros_herdados(ctx_ent, filtros_novos), **entidades}

    if entidades == interp.entidades:
        return interp
    return interp.model_copy(update={"entidades": entidades})
