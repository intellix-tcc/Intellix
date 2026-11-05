"""Data de referência ("hoje") por dataset.

"Ano passado", "mês passado", "esse ano" e um mês sem ano ("em março") são
relativos a hoje. O /chat resolve esses períodos a partir de:

    referência = a data de hoje, limitada à última venda do dataset

Na base demo (vendas até dezembro de 2026), em 5 de novembro de 2026: "ano
passado" = 2025, "mês passado" = outubro de 2026, "esse ano" = 2026.

O limite pela última venda existe para planilhas antigas: um arquivo com
vendas só até junho de 2025 responde "mês passado" com maio de 2025 e "esse
ano" com 2025, em vez de devolver "sem resultado" para tudo que é recente.

Antes, tudo partia de 2024 (ANO_PADRAO) e um ajuste trocava só o ano: "ano
passado" virava 2023 mesmo em 2026. A referência agora entra na própria
resolução (regras.usar_referencia), então o cálculo já sai certo.
"""

import calendar
import re
from datetime import date, datetime, timedelta, timezone

import psycopg

from app.nlu.regras import DATA_REFERENCIA

# Horário de Brasília (sem horário de verão desde 2019): perto da meia-noite,
# o "hoje" do usuário não vira o dia seguinte por causa do UTC do servidor.
_BRASILIA = timezone(timedelta(hours=-3))
_ANO_EXPLICITO = re.compile(r"\b20\d{2}\b")


def tem_ano_explicito(texto: str) -> bool:
    """A pergunta cita um ano de 4 dígitos? (Se citar, respeitamos o ano dela.)"""
    return bool(_ANO_EXPLICITO.search(texto))


def referencia_do_dataset(ultima_venda: date | None, hoje: date | None = None) -> date:
    """Hoje, limitado à última venda do dataset (sem vendas: DATA_REFERENCIA)."""
    if ultima_venda is None:
        return DATA_REFERENCIA
    return min(hoje or datetime.now(_BRASILIA).date(), ultima_venda)


def data_referencia(conn: psycopg.Connection, empresa_id: str) -> date:
    with conn.cursor() as cur:
        cur.execute(
            "select max(d.data) from fato_item_venda f "
            "join dim_data d on d.id = f.data_id where f.empresa_id = %s",
            (empresa_id,),
        )
        row = cur.fetchone()
    return referencia_do_dataset(row[0] if row else None)


def _trocar_ano(iso: str, ano: int) -> str:
    """'2024-03-31' + 2026 -> '2026-03-31'. Clampa o dia ao fim do mês do ano
    alvo (29/02 de um ano bissexto vira 28/02 num ano comum)."""
    _, mes, dia = (int(x) for x in iso.split("-"))
    ultimo = calendar.monthrange(ano, mes)[1]
    return f"{ano:04d}-{mes:02d}-{min(dia, ultimo):02d}"
