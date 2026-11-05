import os

import pytest
from app.main import app
from fastapi.testclient import TestClient

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


def test_resumo_do_mes_com_dados():
    r = client.get("/resumo", params={"ano": 2024, "mes": 3})
    assert r.status_code == 200
    dados = r.json()
    assert dados["periodo"]["rotulo"] == "março de 2024"
    assert dados["periodo"]["parcial"] is False
    assert len(dados["serie_diaria"]) == 31
    assert len(dados["serie_mensal"]) == 12
    assert dados["kpis"][0]["chave"] == "faturamento"
    assert isinstance(dados["kpis"][0]["valor"], float)


def test_resumo_mes_invalido():
    assert client.get("/resumo", params={"mes": 13}).status_code == 422


def test_faturamento_de_um_ano_vira_serie_mensal_em_linha():
    r = client.post("/chat", json={"pergunta": "quanto faturei em 2024"})
    assert r.status_code == 200
    dados = r.json()
    assert dados["tipo_visualizacao"] == "linha"
    assert len(dados["linhas"]) == 12
    assert [linha[0] for linha in dados["linhas"]][:2] == ["2024-01", "2024-02"]


def test_faturamento_de_um_mes_traz_evolucao_de_12_meses():
    r = client.post("/chat", json={"pergunta": "quanto faturei em março de 2024"})
    assert r.status_code == 200
    ctx = r.json()["evolucao"]
    assert ctx["destaque"] == "2024-03"
    assert len(ctx["linhas"]) == 12
    assert ctx["linhas"][-1][0] == "2024-03"
    # o valor destacado é o mesmo da resposta principal
    assert abs(ctx["linhas"][-1][1] - r.json()["linhas"][0][1]) < 0.01


# ---- detalhes (filtros do catálogo), refino e contexto, com o banco ---------

def _perguntar(pergunta, anterior=None):
    corpo = {"pergunta": pergunta}
    if anterior is not None:
        corpo["contexto"] = {"intencao": anterior["intencao"], "entidades": anterior["parametros"]}
    return client.post("/chat", json=corpo)


def test_produto_citado_vira_filtro_com_o_nome_do_cadastro():
    r = _perguntar("quanto vendi de botas de couro em 2025")
    assert r.status_code == 200
    dados = r.json()
    assert dados["parametros"]["produto"] == "Bota couro"
    assert dados["titulo"].endswith("· Bota couro")
    loja = _perguntar("quanto vendi em 2025").json()
    # o recorte é uma parte do total da loja, mês a mês
    assert sum(v for _, v in dados["linhas"]) < sum(v for _, v in loja["linhas"])
    assert len(dados["linhas"]) == 12  # meses sem venda do produto entram com 0


def test_mes_que_mais_vendeu_um_produto():
    r = _perguntar("qual foi o mês que mais vendeu bota couro em 2025?")
    assert r.status_code == 200
    dados = r.json()
    assert dados["intencao"] == "melhor_mes"
    assert dados["colunas"] == ["periodo", "unidades"]
    melhor = dados["linhas"][0]
    serie = dados["evolucao"]["linhas"]
    assert dados["evolucao"]["destaque"] == melhor[0]
    assert melhor[1] == max(v for _, v in serie)


def test_conversa_troca_so_o_recorte_e_depois_so_o_periodo():
    top = _perguntar("top 5 produtos de 2025").json()
    calcados = _perguntar("e de calçados?", top)
    assert calcados.status_code == 200
    c = calcados.json()
    assert c["intencao"] == "top_produtos"
    assert c["parametros"]["categoria"] == "Calçados"
    assert c["parametros"]["periodo_inicio"] == "2025-01-01"
    outro_ano = _perguntar("e em 2024?", c).json()
    assert outro_ano["parametros"]["categoria"] == "Calçados"
    assert outro_ano["parametros"]["periodo_inicio"] == "2024-01-01"


def test_nome_que_nao_existe_no_cadastro_nao_filtra():
    r = _perguntar("quanto vendi de patinete em 2025")
    assert r.status_code == 200
    assert "produto" not in r.json()["parametros"]
