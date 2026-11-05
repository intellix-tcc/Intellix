"""Auditoria de consultas — escreve em log_consulta (seção 7.7 do TCC;
feedback TC2 F09, que apontou a tabela existente porém sem escrita).

Registra cada consulta que chegou a executar um template: empresa, pergunta,
intenção, entidades, confiança, template e tempo. É **best-effort**: uma falha
ao auditar nunca derruba a resposta ao usuário (o insert vai na mesma conexão/
transação do /chat, que faz commit ao sair do `with`).
"""

import contextlib

import psycopg
from psycopg.types.json import Jsonb

from app.models import Interpretacao


def registrar_consulta(
    conn: psycopg.Connection, empresa_id: str, interp: Interpretacao, tempo_ms: int
) -> None:
    # best-effort: uma falha ao auditar nunca derruba a resposta ao usuário.
    with contextlib.suppress(Exception):
        conn.execute(
            "insert into log_consulta "
            "(empresa_id, pergunta, intencao, entidades, confianca, template_sql, "
            " parametros, tempo_ms) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                empresa_id,
                interp.texto_original,
                interp.intencao,
                Jsonb(interp.entidades),
                interp.confianca,
                interp.intencao,  # chave do template usado (ver sql/templates.py)
                Jsonb(interp.entidades),
                tempo_ms,
            ),
        )
