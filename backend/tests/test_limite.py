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


def _pedido(xff: str | None, ip_conexao: str = "10.0.0.1"):
    from starlette.requests import Request

    cabecalhos = [(b"x-forwarded-for", xff.encode())] if xff is not None else []
    return Request({"type": "http", "headers": cabecalhos, "client": (ip_conexao, 1234)})


def test_cliente_usa_o_ip_que_o_proxy_escreveu_nao_o_inventado(monkeypatch):
    from app.limite import cliente

    monkeypatch.delenv("PROXIES_CONFIAVEIS", raising=False)  # padrão: 1 (Render)
    # o cliente mandou "1.1.1.1" por conta própria; o Render acrescentou o IP real
    assert cliente(_pedido("1.1.1.1, 198.51.100.7")) == "198.51.100.7"
    assert cliente(_pedido("198.51.100.7")) == "198.51.100.7"


def test_trocar_o_x_forwarded_for_nao_escapa_do_limite(monkeypatch):
    monkeypatch.setenv("LIMITE_CHAT", "2")
    client = TestClient(app)
    respostas = [
        client.post(
            "/chat",
            json={"pergunta": "qual a capital da França"},
            headers={"x-forwarded-for": f"9.9.9.{i}, 203.0.113.55"},
        ).status_code
        for i in range(3)
    ]
    assert respostas[-1] == 429


def test_proxies_confiaveis_configuravel(monkeypatch):
    from app.limite import cliente

    monkeypatch.setenv("PROXIES_CONFIAVEIS", "2")  # ex.: Cloudflare + Render
    assert cliente(_pedido("1.1.1.1, 198.51.100.7, 172.16.0.9")) == "198.51.100.7"
    monkeypatch.setenv("PROXIES_CONFIAVEIS", "0")  # sem proxy: IP da conexão
    assert cliente(_pedido("1.1.1.1", ip_conexao="192.0.2.4")) == "192.0.2.4"


def test_janela_apaga_clientes_inativos():
    j = Janela()
    for i in range(100):
        j.registrar((f"10.0.0.{i}", "/chat"), 5, 60, agora=0.0)
    assert len(j) == 100
    # passou a janela de todos: a próxima limpeza tira os 100
    j.registrar(("novo", "/chat"), 5, 60, agora=Janela.INTERVALO_LIMPEZA + 61)
    assert len(j) == 1


def test_limpeza_respeita_a_janela_de_cada_rota():
    j = Janela()
    j.registrar(("a", "/import"), 10, 3600, agora=0.0)
    j.registrar(("a", "/chat"), 30, 60, agora=0.0)
    j.registrar(("b", "/chat"), 30, 60, agora=120.0)  # limpa: /chat venceu, /import não
    assert len(j) == 2
    for _ in range(9):
        assert j.registrar(("a", "/import"), 10, 3600, agora=130.0) == 0
    assert j.registrar(("a", "/import"), 10, 3600, agora=131.0) > 0  # contagem preservada
