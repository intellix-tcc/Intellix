"""Autenticação (app/auth.py) e regra de acesso aos datasets (app/acesso.py).

Nenhum teste aqui usa rede nem banco: os tokens são assinados com chaves
geradas na hora, e o "JWKS" do Supabase é substituído por um dublê.
"""

import time
import uuid

import jwt
import pytest
from app import acesso, auth
from app.main import app
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from fastapi.testclient import TestClient

URL = "https://projeto-teste.supabase.co"
SEGREDO = "segredo-de-teste-com-pelo-menos-32-bytes!!"
USUARIO_ID = str(uuid.uuid4())

CHAVE_PRIVADA = ec.generate_private_key(ec.SECP256R1())
CHAVE_PUBLICA = CHAVE_PRIVADA.public_key()


class _ChaveFalsa:
    key = CHAVE_PUBLICA


class _JwksFalso:
    def get_signing_key_from_jwt(self, token):
        return _ChaveFalsa()


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SEGREDO)
    monkeypatch.setenv("AUTH_OBRIGATORIA", "false")
    monkeypatch.setenv("EMPRESA_ID", "00000000-0000-0000-0000-000000000001")
    monkeypatch.setattr(auth, "_cliente_jwks", lambda: _JwksFalso())


def _claims(**extra):
    agora = int(time.time())
    base = {
        "sub": USUARIO_ID,
        "email": "ana@exemplo.com",
        "aud": "authenticated",
        "role": "authenticated",
        "iss": f"{URL}/auth/v1",
        "iat": agora,
        "exp": agora + 3600,
    }
    base.update(extra)
    return base


def token_es256(**extra):
    return jwt.encode(_claims(**extra), CHAVE_PRIVADA, algorithm="ES256")


def token_hs256(**extra):
    return jwt.encode(_claims(**extra), SEGREDO, algorithm="HS256")


# ---- validar_token -----------------------------------------------------------


def test_token_assimetrico_valido():
    u = auth.validar_token(token_es256())
    assert u.id == USUARIO_ID
    assert u.email == "ana@exemplo.com"


def test_token_legado_hs256_valido():
    assert auth.validar_token(token_hs256()).id == USUARIO_ID


def _codigo_401(token):
    with pytest.raises(HTTPException) as e:
        auth.validar_token(token)
    assert e.value.status_code == 401
    return e.value.detail["tipo"]


def test_token_expirado():
    assert _codigo_401(token_es256(exp=int(time.time()) - 10)) == "sessao_expirada"


def test_token_assinado_por_outra_chave():
    outra = ec.generate_private_key(ec.SECP256R1())
    _codigo_401(jwt.encode(_claims(), outra, algorithm="ES256"))


def test_token_de_outro_projeto():
    _codigo_401(token_es256(iss="https://outro-projeto.supabase.co/auth/v1"))


def test_token_anon_nao_e_login():
    _codigo_401(token_es256(role="anon", aud="authenticated"))


def test_token_sem_assinatura_e_recusado():
    sem_assinatura = jwt.encode(_claims(), key=None, algorithm="none")
    _codigo_401(sem_assinatura)


def test_hs256_sem_segredo_configurado(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET")
    _codigo_401(token_hs256())


def test_lixo_no_lugar_do_token():
    _codigo_401("isto-nao-e-um-jwt")


# ---- dependência usuario_atual ----------------------------------------------


def test_sem_cabecalho_com_login_opcional():
    assert auth.usuario_atual(None) is None


def test_sem_cabecalho_com_login_obrigatorio(monkeypatch):
    monkeypatch.setenv("AUTH_OBRIGATORIA", "true")
    with pytest.raises(HTTPException) as e:
        auth.usuario_atual(None)
    assert e.value.status_code == 401


def test_token_invalido_nunca_vira_anonimo():
    # mesmo com login opcional, um token ruim é recusado, não ignorado
    with pytest.raises(HTTPException):
        auth.usuario_atual("Bearer isto-nao-e-um-jwt")


def test_esquema_errado_no_cabecalho():
    with pytest.raises(HTTPException):
        auth.usuario_atual(f"Basic {token_es256()}")


def test_cabecalho_valido():
    assert auth.usuario_atual(f"Bearer {token_es256()}").id == USUARIO_ID


# ---- endpoints ---------------------------------------------------------------

cliente = TestClient(app)


def test_chat_exige_login_quando_obrigatorio(monkeypatch):
    monkeypatch.setenv("AUTH_OBRIGATORIA", "true")
    r = cliente.post("/chat", json={"pergunta": "quanto faturei em março de 2024"})
    assert r.status_code == 401
    assert r.json()["detail"]["tipo"] == "nao_autenticado"


def test_import_exige_login_quando_obrigatorio(monkeypatch):
    monkeypatch.setenv("AUTH_OBRIGATORIA", "true")
    r = cliente.post("/import", files={"arquivo": ("x.xlsx", b"nada", "application/octet-stream")})
    assert r.status_code == 401


def test_health_continua_aberto(monkeypatch):
    monkeypatch.setenv("AUTH_OBRIGATORIA", "true")
    assert cliente.get("/health").status_code == 200


# ---- resolver_empresa (quem consulta qual dataset) ---------------------------


class _ConexaoFalsa:
    """Responde ao `select dono_id from empresa where id = %s`."""

    def __init__(self, donos: dict):
        self.donos = donos

    def execute(self, sql, params):
        empresa_id = params[0]
        linha = (self.donos[empresa_id],) if empresa_id in self.donos else None
        return type("Cursor", (), {"fetchone": lambda _self: linha})()


ANA = auth.Usuario(id=USUARIO_ID)
BRUNO = auth.Usuario(id=str(uuid.uuid4()))
DATASET_DA_ANA = str(uuid.uuid4())
DATASET_SEM_DONO = str(uuid.uuid4())
CONN = _ConexaoFalsa({DATASET_DA_ANA: USUARIO_ID, DATASET_SEM_DONO: None})


def _status_404(empresa_id, usuario):
    with pytest.raises(HTTPException) as e:
        acesso.resolver_empresa(CONN, empresa_id, usuario)
    assert e.value.status_code == 404
    assert e.value.detail["tipo"] == "dataset_nao_encontrado"


def test_sem_empresa_id_usa_demo():
    assert acesso.resolver_empresa(CONN, None, None) == "00000000-0000-0000-0000-000000000001"


def test_dono_consulta_o_proprio_dataset():
    assert acesso.resolver_empresa(CONN, DATASET_DA_ANA, ANA) == DATASET_DA_ANA


def test_outro_usuario_nao_ve_dataset_alheio():
    _status_404(DATASET_DA_ANA, BRUNO)


def test_anonimo_nao_ve_dataset_com_dono():
    _status_404(DATASET_DA_ANA, None)


def test_dataset_inexistente_e_alheio_dao_a_mesma_resposta():
    _status_404(str(uuid.uuid4()), ANA)


def test_id_malformado_nao_vira_erro_500():
    _status_404("'; drop table empresa; --", ANA)


def test_dataset_sem_dono_so_com_login_opcional(monkeypatch):
    assert acesso.resolver_empresa(CONN, DATASET_SEM_DONO, None) == DATASET_SEM_DONO
    monkeypatch.setenv("AUTH_OBRIGATORIA", "true")
    _status_404(DATASET_SEM_DONO, ANA)
