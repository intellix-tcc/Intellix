"""Quem pode consultar qual dataset (empresa).

Regras:
  - sem `empresa_id` no pedido: base de demonstração (EMPRESA_ID fixo),
    aberta a qualquer usuário;
  - com `empresa_id` de um dataset que tem dono: só o próprio dono;
  - com `empresa_id` de um dataset sem dono (importado antes do login
    existir): só enquanto AUTH_OBRIGATORIA estiver desligado.

Dataset de outra pessoa e dataset inexistente recebem a MESMA resposta
(404), para não revelar quais ids existem.
"""

import uuid

import psycopg
from fastapi import HTTPException

from app.auth import Usuario, auth_obrigatoria
from app.db import get_empresa_id


def _nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "tipo": "dataset_nao_encontrado",
            "mensagem": "Não encontrei esses dados. Importe a planilha de novo ou volte aos dados de exemplo.",
        },
    )


def resolver_empresa(
    conn: psycopg.Connection, empresa_id: str | None, usuario: Usuario | None
) -> str:
    demo = get_empresa_id()
    if not empresa_id or empresa_id == demo:
        return demo

    try:
        uuid.UUID(empresa_id)
    except ValueError:
        # sem isto, um id malformado virava erro do Postgres (500)
        raise _nao_encontrado()

    linha = conn.execute("select dono_id from empresa where id = %s", (empresa_id,)).fetchone()
    if linha is None:
        raise _nao_encontrado()

    dono = linha[0]
    if dono is None:
        if auth_obrigatoria():
            raise _nao_encontrado()
        return empresa_id

    if usuario is None or str(dono) != usuario.id:
        raise _nao_encontrado()
    return empresa_id
