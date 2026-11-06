"""Minhas planilhas: os datasets importados pela conta (migration 007).

Cada importação cria um dataset próprio com o `dono_id` de quem importou.
Aqui o usuário logado lista os seus e apaga o que não quer mais. As duas
operações passam por funções do banco (listar_planilhas, excluir_planilha)
que sempre filtram pelo dono: com o RLS da migration 006, o usuário da
aplicação não enxerga outras empresas nem apaga vendas por conta própria.

O id do dono vem SEMPRE do token validado (app/auth.py), nunca do pedido.
"""

from __future__ import annotations

import uuid
from typing import Any

import psycopg


def _iso(valor: Any) -> str | None:
    return valor.isoformat() if valor is not None else None


def listar(conn: psycopg.Connection, dono_id: str) -> list[dict[str, Any]]:
    linhas = conn.execute("select * from listar_planilhas(%s)", (dono_id,)).fetchall()
    return [
        {
            "empresa_id": str(empresa_id),
            "nome_arquivo": nome_arquivo,
            "importada_em": _iso(importada_em),
            "linhas_validas": linhas_validas,
            "linhas_rejeitadas": linhas_rejeitadas,
            "primeira_venda": _iso(primeira),
            "ultima_venda": _iso(ultima),
        }
        for empresa_id, nome_arquivo, importada_em, linhas_validas, linhas_rejeitadas, primeira, ultima in linhas
    ]


def excluir(conn: psycopg.Connection, empresa_id: str, dono_id: str) -> bool:
    """True se apagou; False se o id não existe, é inválido ou é de outra
    pessoa (o chamador responde 404 nos três casos, sem distinguir)."""
    try:
        uuid.UUID(empresa_id)
    except ValueError:
        return False
    linha = conn.execute("select excluir_planilha(%s, %s)", (empresa_id, dono_id)).fetchone()
    return bool(linha and linha[0])
