"""Auditoria best-effort: falha ao gravar vira aviso no log, não erro."""

import contextlib
import logging

from app.auditoria import registrar_consulta
from app.models import Interpretacao

INTERP = Interpretacao(intencao="ticket_medio", confianca=0.9, entidades={}, texto_original="x")


class _Conexao:
    def __init__(self, erro=None):
        self.erro, self.savepoints, self.inseriu = erro, 0, False

    @contextlib.contextmanager
    def transaction(self):
        self.savepoints += 1
        yield

    def execute(self, *_a):
        if self.erro:
            raise self.erro
        self.inseriu = True


def test_grava_dentro_de_um_savepoint():
    conn = _Conexao()
    assert registrar_consulta(conn, "emp", INTERP, 12) is True
    assert conn.savepoints == 1 and conn.inseriu


def test_falha_nao_derruba_e_fica_no_log(caplog):
    conn = _Conexao(erro=RuntimeError("sem permissão"))
    with caplog.at_level(logging.WARNING, logger="intellix.auditoria"):
        assert registrar_consulta(conn, "emp", INTERP, 12) is False
    assert "falha ao gravar log_consulta" in caplog.text
