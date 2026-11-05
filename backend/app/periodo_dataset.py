"""Ano de referência por dataset.

O /chat resolve "esse ano", "mês passado" ou um mês sem ano em cima do
ANO_PADRAO fixo (2024, em regras.py). Quando o usuário importa uma planilha de
2025/2026, essas perguntas caíam em 2024 -> sem_resultado, mesmo o modelo
acertando a intenção. Aqui, quando a pergunta NÃO cita um ano explícito,
deslocamos o ano do período resolvido para o **ano mais recente do dataset**.

Não toca na NLU: o modelo/regras continuam resolvendo com ANO_PADRAO, e este
ajuste roda depois, só no /chat, quando já se sabe qual dataset responder.
"""

import calendar
import re

import psycopg

from app.models import Interpretacao
from app.nlu.regras import ANO_PADRAO

# Chaves de período em Interpretacao.entidades (um período ou dois).
_SUFIXOS = ("_inicio", "_fim")
_ANO_EXPLICITO = re.compile(r"\b20\d{2}\b")


def tem_ano_explicito(texto: str) -> bool:
    """A pergunta cita um ano de 4 dígitos? (Se citar, respeitamos o ano dela.)"""
    return bool(_ANO_EXPLICITO.search(texto))


def ano_referencia(conn: psycopg.Connection, empresa_id: str) -> int:
    """Ano mais recente com dados nesse dataset; ANO_PADRAO se estiver vazio."""
    with conn.cursor() as cur:
        cur.execute(
            "select max(d.data) from fato_item_venda f "
            "join dim_data d on d.id = f.data_id where f.empresa_id = %s",
            (empresa_id,),
        )
        row = cur.fetchone()
    return row[0].year if row and row[0] else ANO_PADRAO


def _trocar_ano(iso: str, ano: int) -> str:
    """'2024-03-31' + 2026 -> '2026-03-31'. Clampa o dia ao fim do mês do ano
    alvo (29/02 de um ano bissexto vira 28/02 num ano comum)."""
    _, mes, dia = (int(x) for x in iso.split("-"))
    ultimo = calendar.monthrange(ano, mes)[1]
    return f"{ano:04d}-{mes:02d}-{min(dia, ultimo):02d}"


def ajustar_periodo(interp: Interpretacao, ano_ref: int) -> Interpretacao:
    """Desloca para `ano_ref` os períodos que ficaram no ANO_PADRAO. Só deve ser
    chamado quando a pergunta NÃO cita um ano (quem chama decide isso)."""
    if ano_ref == ANO_PADRAO:
        return interp
    alvo = str(ANO_PADRAO)
    novas = dict(interp.entidades)
    mudou = False
    for chave, valor in interp.entidades.items():
        if chave.endswith(_SUFIXOS) and isinstance(valor, str) and valor[:4] == alvo:
            novas[chave] = _trocar_ano(valor, ano_ref)
            mudou = True
    return interp.model_copy(update={"entidades": novas}) if mudou else interp
