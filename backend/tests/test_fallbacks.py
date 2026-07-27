import pytest
from fastapi import HTTPException

from app.fallbacks import verificar_confianca
from app.models import Interpretacao


def test_confianca_baixa_levanta_422():
    interp = Interpretacao(intencao=None, confianca=0.0, texto_original="oi")
    with pytest.raises(HTTPException) as exc:
        verificar_confianca(interp)
    assert exc.value.status_code == 422
    assert exc.value.detail["tipo"] == "baixa_confianca"


def test_confianca_suficiente_nao_levanta():
    interp = Interpretacao(
        intencao="total_vendas_periodo", confianca=0.93, texto_original="quanto faturei em março"
    )
    verificar_confianca(interp)  # nao deve levantar
