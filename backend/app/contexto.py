"""Resolução de contexto conversacional (histórico) para o /chat.

O /chat é sem estado: cada pergunta chega sozinha. Mas o usuário conversa em
sequência — "Quanto faturei em março?" e, logo depois, "e em abril?". A
segunda frase é ELÍPTICA: não repete a intenção, só troca o período. Sozinha
ela cai em baixa_confianca (nem termo de domínio tem) e o usuário teria de
redigitar tudo.

Quando o frontend reenvia o contexto da resposta anterior (intenção +
entidades), aqui herdamos a intenção e trocamos só o slot que mudou. A regra é
deterministica e conservadora:
  - se a frase atual já se classificou com confiança, não mexe;
  - se não há contexto anterior, não mexe;
  - só herda quando a frase atual traz um PERÍODO novo (senão não dá para
    saber o que o usuário quer — melhor pedir reformulação do que chutar).
Vale para os dois backends de NLU (regras e modelo): a resolução de slots é a
mesma de sempre (app/nlu/adaptador_modelo._resolver_entidades, determinística).
"""

import re

from app.fallbacks import CONFIANCA_MINIMA
from app.models import Contexto, Interpretacao
from app.nlu import regras as R
from app.nlu.adaptador_modelo import _resolver_entidades

# A frase de follow-up precisa citar um período para herdarmos a intenção
# anterior: "e em abril?", "e em 2023?", "e no último trimestre?", "e no mês
# passado?". Sem período explícito, não herda.
_MESES = "|".join(R.MESES.keys())
_TEM_PERIODO = re.compile(
    rf"\b(?:{_MESES})\b|\b20\d{{2}}\b|\btrimestre\b|\bsemestre\b"
    r"|[úu]ltim|passad|anterior|\bes[st]e\s+(?:m[eê]s|ano)\b",
    re.IGNORECASE,
)


def aplicar_contexto(
    interp: Interpretacao, contexto: Contexto | None, texto: str
) -> Interpretacao:
    """Devolve a interpretação, herdando a intenção anterior quando a frase é
    uma continuação elíptica. Caso contrário devolve `interp` inalterada."""
    if contexto is None or not contexto.intencao:
        return interp
    # A frase atual já se bastou: nada a herdar.
    if interp.intencao and interp.confianca >= CONFIANCA_MINIMA:
        return interp
    # Sem período novo não dá para saber o que mudou -> deixa seguir (422).
    if not _TEM_PERIODO.search(texto):
        return interp

    novas = _resolver_entidades(contexto.intencao, texto.lower(), {}, texto)
    if not novas:
        return interp

    # Herda os slots anteriores; os recém-resolvidos (o período novo) vencem.
    entidades = {**contexto.entidades, **novas}
    return Interpretacao(
        intencao=contexto.intencao,
        confianca=max(interp.confianca, CONFIANCA_MINIMA),
        entidades=entidades,
        texto_original=interp.texto_original,
    )
