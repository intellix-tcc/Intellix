"""Confirma qual NLU está ativo conforme a variável NLU_BACKEND.

Feedback TC2 F11: "não se confirma ... se todas as verificações usaram o modelo
treinado em vez do substituto por regras". Este teste torna isso explícito e
automático: a instância criada em app.main tem de bater com a configuração.
Sem banco.
"""

import os

from app.main import nlu


def test_nlu_ativo_reflete_a_configuracao():
    backend = os.environ.get("NLU_BACKEND", "regras").strip().lower()
    nome = type(nlu).__name__
    if backend == "modelo":
        assert nome == "ModeloTreinadoNLU", (
            "NLU_BACKEND=modelo mas o NLU ativo não é o modelo treinado"
        )
    else:
        assert nome == "RuleBasedNLU", (
            f"NLU_BACKEND={backend!r} deveria ativar o baseline de regras"
        )
