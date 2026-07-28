"""Executa o template SQL escolhido pelo NLU e devolve um ResultSet.

Os 3 fallbacks que precisam de banco (secao 7.6 do TCC) moram aqui:
parametro obrigatorio ausente, banco fora do ar e consulta sem resultado.
Nenhum deles deixa o Postgres/psycopg vazar stack trace para o cliente.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import psycopg
from fastapi import HTTPException

from app.fallbacks import EXEMPLOS_PADRAO
from app.models import Interpretacao, ResultSet
from app.sql.templates import TEMPLATES


def _para_json(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


def executar_template(interp: Interpretacao, empresa_id: str, conn: psycopg.Connection) -> ResultSet:
    template = TEMPLATES.get(interp.intencao)
    if template is None:
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "baixa_confianca",
                "mensagem": "Não entendi a pergunta. Tente reformular.",
                "exemplos": EXEMPLOS_PADRAO,
            },
        )

    faltando = [p for p in template["obrigatorios"] if p not in interp.entidades]
    if faltando:
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "parametro_faltando",
                "mensagem": "Não consegui identificar todos os dados da pergunta. Tente reformular.",
                "exemplos": EXEMPLOS_PADRAO,
            },
        )

    parametros = {**interp.entidades, "empresa_id": empresa_id}

    try:
        with conn.cursor() as cur:
            cur.execute(template["sql"], parametros)
            colunas = [d.name for d in cur.description]
            linhas_brutas = cur.fetchall()
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "banco_indisponivel",
                "mensagem": "Serviço temporariamente indisponível. Tente novamente em instantes.",
            },
        )

    if not linhas_brutas:
        raise HTTPException(
            status_code=404,
            detail={
                "tipo": "sem_resultado",
                "mensagem": "Não há registros para o período ou filtro informado.",
            },
        )

    linhas = [[_para_json(valor) for valor in linha] for linha in linhas_brutas]

    return ResultSet(
        titulo=template["titulo"],
        colunas=colunas,
        linhas=linhas,
        tipo_visualizacao=template["visual"],
        parametros=interp.entidades,
        confianca=interp.confianca,
        gerado_em=datetime.now(timezone.utc).isoformat(),
    )
