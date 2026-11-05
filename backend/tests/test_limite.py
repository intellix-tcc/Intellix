"""Limite de requisições (app/limite.py) e tamanho máximo da pergunta."""

from app.limite import Janela
from app.main import app
from fastapi.testclient import TestClient


def test_janela_bloqueia_acima_do_limite_e_libera_depois():
    j = Janela()
    chave = ("1.2.3.4", "/chat")
    assert all(j.registrar(chave, 3, 60, agora=0.0) == 0 for _ in range(3))
    espera = j.registrar(chave, 3, 60, agora=10.0)
    assert espera > 0  # quarto pedido no mesmo minuto: bloqueado
    assert j.registrar(chave, 3, 60, agora=61.0) == 0  # janela passou


def test_janela_conta_cada_cliente_separado():
    j = Janela()
    assert j.registrar(("a", "/chat"), 1, 60, agora=0.0) == 0
    assert j.registrar(("b", "/chat"), 1, 60, agora=0.0) == 0
    assert j.registrar(("a", "/chat"), 1, 60, agora=1.0) > 0


def test_chat_responde_429_com_mensagem_e_retry_after(monkeypatch):
    monkeypatch.setenv("LIMITE_CHAT", "2")
    client = TestClient(app)
    cabecalho = {"x-forwarded-for": "203.0.113.77"}
    # pergunta fora de escopo: não toca no banco (422), mas conta no limite
    for _ in range(2):
        assert client.post("/chat", json={"pergunta": "qual a capital da França"}, headers=cabecalho).status_code != 429
    r = client.post("/chat", json={"pergunta": "qual a capital da França"}, headers=cabecalho)
    assert r.status_code == 429
    assert r.json()["detail"]["tipo"] == "limite_requisicoes"
    assert int(r.headers["retry-after"]) >= 1


def test_pergunta_maior_que_500_caracteres_e_recusada():
    client = TestClient(app)
    r = client.post("/chat", json={"pergunta": "x" * 501}, headers={"x-forwarded-for": "203.0.113.90"})
    assert r.status_code == 422
