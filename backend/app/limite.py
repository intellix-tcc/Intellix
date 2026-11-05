"""Limite de requisições por cliente (rate limit), em memória.

Protege o plano gratuito do Render e do Supabase contra abuso e contra loops
acidentais do frontend. Janela deslizante por (cliente, rota): o cliente é o
IP de origem, lido do X-Forwarded-For pela DIREITA (ver `cliente`).

Em memória de propósito: o backend roda num processo só, e um Redis seria
infraestrutura nova para um TCC. Se um dia houver várias instâncias, cada uma
conta separado (o limite efetivo multiplica), o que continua seguro.

Limites por variável de ambiente (pedidos por janela):
  LIMITE_CHAT=30      por minuto   (/chat)
  LIMITE_RESUMO=60    por minuto   (/resumo)
  LIMITE_IMPORT=10    por hora     (/import)
  LIMITE_REQUISICOES=0 desliga tudo (útil em teste de carga local)
  PROXIES_CONFIAVEIS=1 quantos proxies nossos ficam na frente do app (Render: 1)
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# rota -> (variável de ambiente, padrão, janela em segundos, mensagem)
REGRAS: dict[str, tuple[str, int, int, str]] = {
    "/chat": (
        "LIMITE_CHAT", 30, 60,
        "Muitas perguntas em pouco tempo. Espere alguns segundos e tente de novo.",
    ),
    "/resumo": (
        "LIMITE_RESUMO", 60, 60,
        "Muitas atualizações do panorama em pouco tempo. Espere alguns segundos.",
    ),
    "/import": (
        "LIMITE_IMPORT", 10, 3600,
        "Muitas importações na última hora. Espere um pouco antes de enviar outra planilha.",
    ),
}


def _limite(var: str, padrao: int) -> int:
    try:
        return int(os.environ.get(var, padrao))
    except ValueError:
        return padrao


def _ligado() -> bool:
    return os.environ.get("LIMITE_REQUISICOES", "1").strip() not in ("0", "false", "nao", "não")


def _proxies_confiaveis() -> int:
    try:
        return max(0, int(os.environ.get("PROXIES_CONFIAVEIS", "1")))
    except ValueError:
        return 1


def cliente(request: Request) -> str:
    """IP de quem fez o pedido.

    Cada proxy ACRESCENTA ao fim do X-Forwarded-For o IP que viu. O começo da
    lista vem de quem fez o pedido e pode ser inventado: com o primeiro item,
    bastava mandar um X-Forwarded-For diferente a cada pedido para nunca cair
    no limite. Por isso a leitura é pela direita: com N proxies nossos na
    frente (PROXIES_CONFIAVEIS, Render = 1), o cliente é o N-ésimo a partir do
    fim, o último valor que um proxy nosso escreveu.
    """
    confiaveis = _proxies_confiaveis()
    ips = [ip.strip() for ip in request.headers.get("x-forwarded-for", "").split(",") if ip.strip()]
    if confiaveis and ips:
        return ips[-confiaveis] if len(ips) >= confiaveis else ips[0]
    return request.client.host if request.client else "desconhecido"


class Janela:
    """Contador de janela deslizante, seguro para threads.

    Clientes que pararam de mandar pedidos são apagados a cada
    `INTERVALO_LIMPEZA` segundos; sem isso o dicionário só crescia (um IP
    novo por visitante, para sempre) e a memória do Render ia junto.
    """

    INTERVALO_LIMPEZA = 60.0

    def __init__(self) -> None:
        self._eventos: dict[tuple[str, str], tuple[int, deque[float]]] = {}
        self._trava = threading.Lock()
        self._ultima_limpeza = 0.0

    def __len__(self) -> int:
        return len(self._eventos)

    def _limpar(self, agora: float) -> None:
        self._ultima_limpeza = agora
        vencidas = [
            chave for chave, (janela, fila) in self._eventos.items()
            if not fila or agora - fila[-1] >= janela
        ]
        for chave in vencidas:
            del self._eventos[chave]

    def registrar(self, chave: tuple[str, str], limite: int, janela: int, agora: float | None = None) -> int:
        """Registra um pedido. Devolve 0 se permitido, ou os segundos até liberar."""
        agora = time.monotonic() if agora is None else agora
        with self._trava:
            if agora - self._ultima_limpeza >= self.INTERVALO_LIMPEZA:
                self._limpar(agora)
            _, fila = self._eventos.setdefault(chave, (janela, deque()))
            while fila and agora - fila[0] >= janela:
                fila.popleft()
            if len(fila) >= limite:
                return max(1, int(janela - (agora - fila[0])) + 1)
            fila.append(agora)
            return 0


_janela = Janela()


class LimiteDeRequisicoes(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        regra = REGRAS.get(request.url.path)
        if regra and request.method != "OPTIONS" and _ligado():
            var, padrao, janela, mensagem = regra
            limite = _limite(var, padrao)
            if limite > 0:
                espera = _janela.registrar((cliente(request), request.url.path), limite, janela)
                if espera:
                    return JSONResponse(
                        status_code=429,
                        headers={"Retry-After": str(espera)},
                        content={"detail": {"tipo": "limite_requisicoes", "mensagem": mensagem}},
                    )
        return await call_next(request)
