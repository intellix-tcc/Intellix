"""Fallback de baixa confianca (secao 7.6 do TCC), o unico dos 6 que da
para escrever e testar sem banco com a Interpretacao atual.

Os outros dois fallbacks "sem banco" da tabela -- intencoes empatadas e
duas intencoes na mesma frase -- exigem que o NLU devolva as intencoes
candidatas ranqueadas, e Interpretacao hoje so carrega uma. Ficam para
quando esse formato for definido junto com o Dev A (B9/B11).

Os tres fallbacks restantes ("banco fora do ar", "consulta sem
resultado", "produto inexistente") dependem de uma consulta real ao
Postgres e ficam para quando o banco estiver disponivel (Bloco 2).
"""

from fastapi import HTTPException

from app.models import Interpretacao

CONFIANCA_MINIMA = 0.70

EXEMPLOS_PADRAO = [
    "Quanto faturei em março?",
    "Quais os 5 produtos mais vendidos?",
]


def verificar_confianca(interp: Interpretacao) -> None:
    """Levanta 422 quando a interpretacao nao e confiavel o bastante para
    virar uma consulta. O NLU nao "adivinha" -- pede reformulacao."""
    if interp.confianca < CONFIANCA_MINIMA:
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "baixa_confianca",
                "mensagem": "Não entendi a pergunta. Tente reformular.",
                "exemplos": EXEMPLOS_PADRAO,
            },
        )
