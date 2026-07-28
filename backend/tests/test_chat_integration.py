import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="precisa de backend/.env com DATABASE_URL (Bloco 2)",
)

client = TestClient(app)


def test_chat_total_vendas_periodo():
    r = client.post("/chat", json={"pergunta": "quanto faturei em março de 2024"})
    assert r.status_code == 200
    dados = r.json()
    assert dados["tipo_visualizacao"] == "numero"
    assert dados["colunas"] == ["periodo", "faturamento"]
    assert dados["linhas"][0][0] == "2024-03"
    assert isinstance(dados["linhas"][0][1], float)


def test_chat_top_produtos_sem_periodo_explicito():
    # Mesma pergunta que ja esta nos exemplos do frontend (App.jsx), sem mes/ano.
    r = client.post("/chat", json={"pergunta": "Quais os 5 produtos mais vendidos?"})
    assert r.status_code == 200
    dados = r.json()
    assert dados["tipo_visualizacao"] == "barra"
    assert len(dados["linhas"]) <= 5


def test_chat_baixa_confianca_nao_toca_banco():
    r = client.post("/chat", json={"pergunta": "qual a capital da França"})
    assert r.status_code == 422
    assert r.json()["detail"]["tipo"] == "baixa_confianca"


def test_chat_sem_resultado():
    # 2020 e um ano suportado pelo NLU (regex so reconhece 20xx), mas os
    # dados seedados comecam em 2023 -- garante zero linhas de verdade.
    r = client.post("/chat", json={"pergunta": "quanto faturei em janeiro de 2020"})
    assert r.status_code == 404
    assert r.json()["detail"]["tipo"] == "sem_resultado"


def test_valores_decimais_viram_float_serializavel():
    r = client.post("/chat", json={"pergunta": "qual o ticket médio em março de 2024"})
    assert r.status_code == 200
    valor = r.json()["linhas"][0][0]
    assert isinstance(valor, float)
