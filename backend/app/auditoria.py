"""Auditoria de consultas — escreve em log_consulta (seção 7.7 do TCC;
feedback TC2 F09, que apontou a tabela existente porém sem escrita).

Registra cada consulta que chegou a executar um template: empresa, pergunta,
intenção, entidades, confiança, template e tempo. É **best-effort**: uma falha
ao auditar nunca derruba a resposta ao usuário.

O insert roda num savepoint (`conn.transaction()` dentro da transação do
/chat): se ele falhar, só o savepoint é desfeito e a transação segue sã. Antes
o erro era engolido sem log e, no Postgres, deixava a transação abortada; a
falha não aparecia em lugar nenhum, embora o TCC afirme que toda consulta é
registrada. Agora vai um aviso para o log do servidor.
"""

import logging

import psycopg
from psycopg.types.json import Jsonb

from app.models import Interpretacao

log = logging.getLogger("intellix.auditoria")


def registrar_consulta(
    conn: psycopg.Connection, empresa_id: str, interp: Interpretacao, tempo_ms: int
) -> bool:
    """True se registrou; False (com aviso no log) se a gravação falhou."""
    try:
        with conn.transaction():
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
        return True
    except Exception:  # best-effort: qualquer falha vira aviso, nunca erro ao usuário
        log.warning("auditoria: falha ao gravar log_consulta (empresa %s)", empresa_id, exc_info=True)
        return False
