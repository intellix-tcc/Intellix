"""Histórico de conversas por conta (migration 008).

As conversas do chat eram guardadas só no navegador. Aqui a conta logada
lista, salva (cria ou atualiza) e apaga as suas, para reencontrá-las em outro
aparelho. As três operações passam por funções do banco (listar_conversas,
salvar_conversa, excluir_conversa) que SEMPRE filtram pelo dono — com o RLS da
migration 006, o usuário da aplicação não lê nem grava a conversa de outra
pessoa.

O id do dono vem SEMPRE do token validado (app/auth.py), nunca do pedido. O
id da conversa é gerado pelo frontend (o mesmo que ele já usa no localStorage),
então salvar é um upsert: cria se não existe, atualiza se for do dono.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


def _iso(valor: Any) -> str | None:
    return valor.isoformat() if valor is not None else None


def _uuid_valido(valor: str) -> bool:
    try:
        uuid.UUID(str(valor))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def _data(valor: str | None) -> datetime | None:
    """ISO -> datetime; None (ou inválida) deixa o banco usar now()."""
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None


def listar(conn: psycopg.Connection, dono_id: str) -> list[dict[str, Any]]:
    linhas = conn.execute("select * from listar_conversas(%s)", (dono_id,)).fetchall()
    return [
        {
            "id": str(id_),
            "titulo": titulo,
            "mensagens": mensagens,
            "criadoEm": _iso(criada_em),
            "atualizadoEm": _iso(atualizada_em),
        }
        for id_, titulo, mensagens, criada_em, atualizada_em in linhas
    ]


def salvar(
    conn: psycopg.Connection,
    conversa_id: str,
    dono_id: str,
    titulo: str,
    mensagens: list[Any],
    criada_em: str | None = None,
) -> str | None:
    """Cria ou atualiza a conversa. Devolve o id quando grava; None quando o id
    é de outra pessoa (o chamador responde 404, sem revelar que o id existe)."""
    if not _uuid_valido(conversa_id):
        return None
    linha = conn.execute(
        "select salvar_conversa(%s, %s, %s, %s, %s)",
        (conversa_id, dono_id, titulo, Jsonb(mensagens), _data(criada_em)),
    ).fetchone()
    return str(linha[0]) if linha and linha[0] else None


def excluir(conn: psycopg.Connection, conversa_id: str, dono_id: str) -> bool:
    """True se apagou; False se o id não existe, é inválido ou é de outra
    pessoa (o chamador responde 404 nos três casos, sem distinguir)."""
    if not _uuid_valido(conversa_id):
        return False
    linha = conn.execute(
        "select excluir_conversa(%s, %s)", (conversa_id, dono_id)
    ).fetchone()
    return bool(linha and linha[0])
