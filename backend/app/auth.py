"""Autenticação: valida o token de acesso (JWT) emitido pelo Supabase Auth.

Quem cadastra, faz login, recupera senha e guarda o hash das senhas é o
Supabase Auth: o frontend fala direto com ele e recebe um token de acesso.
O backend não vê senha nenhuma. Ele só confere, a cada requisição, se o
token que veio no cabeçalho `Authorization: Bearer <token>` foi assinado pelo
Supabase do projeto, não expirou e é de um usuário logado. Do token sai o
`id` do usuário, que decide de quais datasets ele é dono (ver acesso.py).

Dois formatos de assinatura são aceitos, porque o Supabase tem os dois:
  - chaves assimétricas (ES256/RS256), o padrão dos projetos novos: a chave
    pública vem do endpoint JWKS do projeto e fica em cache;
  - segredo compartilhado (HS256), o formato legado: exige
    SUPABASE_JWT_SECRET no ambiente.

Variáveis de ambiente:
  SUPABASE_URL          https://<ref>.supabase.co  (obrigatória para validar)
  SUPABASE_JWT_SECRET   só para projetos com o segredo legado (HS256)
  AUTH_OBRIGATORIA      "true" para recusar requisições sem login. Começa
                        "false" para o deploy do backend não quebrar o
                        frontend antigo; vira "true" quando o frontend novo
                        estiver no ar.
"""

import logging
import os
import threading
from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException

_AUDIENCIA = "authenticated"
_ALGORITMOS_ASSIMETRICOS = ("ES256", "RS256")

# Relógios de servidores nunca batem ao segundo: sem folga, um token recém-
# emitido pelo Supabase pode chegar "do futuro" e ser recusado.
_FOLGA_RELOGIO_S = 30

log = logging.getLogger("intellix.auth")

_jwks: jwt.PyJWKClient | None = None
_trava = threading.Lock()


@dataclass(frozen=True)
class Usuario:
    id: str
    email: str | None = None


def auth_obrigatoria() -> bool:
    return os.environ.get("AUTH_OBRIGATORIA", "false").strip().lower() in ("1", "true", "sim")


def _supabase_url() -> str:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    if not url:
        # Erro de configuração do servidor, não do usuário.
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "autenticacao_indisponivel",
                "mensagem": "Login temporariamente indisponível. Tente novamente em instantes.",
            },
        )
    return url


def _cliente_jwks() -> jwt.PyJWKClient:
    global _jwks
    if _jwks is None:
        with _trava:
            if _jwks is None:
                _jwks = jwt.PyJWKClient(
                    f"{_supabase_url()}/auth/v1/.well-known/jwks.json",
                    cache_keys=True,
                    lifespan=3600,
                    timeout=5,
                )
    return _jwks


def _nao_autenticado(mensagem: str = "Faça login para continuar.", tipo: str = "nao_autenticado"):
    return HTTPException(
        status_code=401,
        detail={"tipo": tipo, "mensagem": mensagem},
        headers={"WWW-Authenticate": "Bearer"},
    )


def validar_token(token: str) -> Usuario:
    """Devolve o usuário do token ou levanta 401. Nunca devolve um usuário
    sem a assinatura conferida."""
    try:
        alg = jwt.get_unverified_header(token).get("alg")
        if alg == "HS256":
            segredo = os.environ.get("SUPABASE_JWT_SECRET")
            if not segredo:
                log.warning(
                    "token recusado: assinado com HS256 (segredo legado), mas "
                    "SUPABASE_JWT_SECRET nao esta configurado"
                )
                raise _nao_autenticado()
            chave = segredo
        elif alg in _ALGORITMOS_ASSIMETRICOS:
            chave = _cliente_jwks().get_signing_key_from_jwt(token).key
        else:
            # inclui alg "none": nunca aceitar token sem assinatura
            log.warning("token recusado: algoritmo %r nao aceito", alg)
            raise _nao_autenticado()

        claims = jwt.decode(
            token,
            chave,
            algorithms=[alg],
            audience=_AUDIENCIA,
            issuer=f"{_supabase_url()}/auth/v1",
            # "iat" (hora de emissão) não é conferido: se o relógio deste
            # servidor estiver atrasado, um token recém-emitido parece vir do
            # futuro e seria recusado. A segurança vem da assinatura e do
            # "exp" (validade), que continuam conferidos.
            options={"require": ["exp", "sub", "aud", "iss"], "verify_iat": False},
            leeway=_FOLGA_RELOGIO_S,
        )
    except jwt.ExpiredSignatureError:
        raise _nao_autenticado("Sua sessão expirou. Entre de novo.", "sessao_expirada")
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "autenticacao_indisponivel",
                "mensagem": "Login temporariamente indisponível. Tente novamente em instantes.",
            },
        )
    except jwt.PyJWTError as e:
        # O motivo vai só para o log do servidor (nunca o token); o usuário
        # recebe a mensagem genérica.
        log.warning("token recusado: %s: %s", type(e).__name__, e)
        raise _nao_autenticado()

    if claims.get("role") != "authenticated":
        # token "anon" (chave pública do projeto) não é login de ninguém
        log.warning("token recusado: role=%r", claims.get("role"))
        raise _nao_autenticado()
    return Usuario(id=claims["sub"], email=claims.get("email"))


def usuario_atual(authorization: str | None = Header(default=None)) -> Usuario | None:
    """Dependência do FastAPI. Sem cabeçalho: None, ou 401 se o login for
    obrigatório. Com cabeçalho: o token TEM de ser válido, mesmo com o login
    opcional -- token inválido nunca é tratado como "anônimo"."""
    if not authorization:
        if auth_obrigatoria():
            raise _nao_autenticado()
        return None
    esquema, _, token = authorization.partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        raise _nao_autenticado()
    return validar_token(token.strip())
