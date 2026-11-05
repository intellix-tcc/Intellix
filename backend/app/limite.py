"""Limite de requisições por cliente (rate limit), em memória.

Protege o plano gratuito do Render e do Supabase contra abuso e contra loops
acidentais do frontend. Janela deslizante por (cliente, rota): o cliente é o
IP de origem (no Render, o primeiro de X-Forwarded-For).

Em memória de propósito: o backend roda num processo só, e um Redis seria
infraestrutura nova para um TCC. Se um dia houver várias instâncias, cada uma
conta separado (o limite efetivo multiplica), o que continua seguro.

Limites por variável de ambiente (pedidos por janela):
  LIMITE_CHAT=30      por minuto   (/chat)
  LIMITE_RESUMO=60    por minuto   (/resumo)
  LIMITE_IMPORT=10    por hora     (/import)
  LIMITE_REQUISICOES=0 desliga tudo (útil em teste de carga local)
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


def cliente(request: Request) -> str:
    encaminhado = request.headers.get("x-forwarded-for", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


class Janela:
    """Contador de janela deslizante, seguro para threads."""

    def __init__(self) -> None:
        self._eventos: dict[tuple[str, str], deque[float]] = {}
        self._trava = threading.Lock()

    def registrar(self, chave: tuple[str, str], limite: int, janela: int, agora: float | None = None) -> int:
        """Registra um pedido. Devolve 0 se permitido, ou os segundos até liberar."""
        agora = time.monotonic() if agora is None else agora
        with self._trava:
            fila = self._eventos.setdefault(chave, deque())
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
