import os

import psycopg
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.db import fechar_pool, get_connection, get_empresa_id
from app.fallbacks import verificar_confianca
from app.importacao.etl import importar
from app.importacao.leitor_excel import ErroImportacao
from app.models import Pergunta, ResultSet
from app.nlu.regras import RuleBasedNLU
from app.sql.executor import executar_template

app = FastAPI(title="Intellix API")
app.add_event_handler("shutdown", fechar_pool)  # devolve as conexões do pool ao desligar

# Origens padrão: dev local + a URL estável de produção da Vercel.
# 5173 e 5174: o Vite sobe na primeira porta livre — com dois `npm run dev`
# ao mesmo tempo (comum durante o trabalho no frontend), o segundo cai na
# 5174, e sem isso aqui a Dev D toma erro de CORS sem entender por quê.
# CORS_ORIGINS (lista separada por vírgula, configurada no painel do Render)
# acrescenta outras sem precisar de novo deploy de código — era o que o
# .env.example já declarava mas o app não lia.
ORIGENS_PADRAO = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://intellix-lilac.vercel.app",
]
ORIGENS_EXTRA = [
    origem.strip()
    for origem in os.environ.get("CORS_ORIGINS", "").split(",")
    if origem.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PADRAO + ORIGENS_EXTRA,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _criar_nlu():
    """Interruptor NLU_BACKEND (ver regras.py). 'regras' = baseline/seguro de
    vida; 'modelo' = rede treinada. Import do torch é preguiçoso: só ocorre
    com NLU_BACKEND=modelo, para o baseline não pagar RAM à toa."""
    backend = os.environ.get("NLU_BACKEND", "regras").lower()
    if backend == "modelo":
        from app.nlu.adaptador_modelo import ModeloTreinadoNLU
        return ModeloTreinadoNLU()
    return RuleBasedNLU()


nlu = _criar_nlu()  # B11: definir NLU_BACKEND=modelo no Render ativa a rede


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ResultSet)
def chat(pergunta: Pergunta) -> ResultSet:
    interpretacao = nlu.parse(pergunta.pergunta)
    verificar_confianca(interpretacao)

    # Dataset do usuário (vindo de uma importação) ou a base demo por padrão.
    empresa = pergunta.empresa_id or get_empresa_id()
    # O executor.py trata OperationalError que acontece DURANTE a consulta, mas a
    # conexao e adquirida aqui: com o banco fora, get_connection() estoura
    # PoolTimeout (subclasse de psycopg.OperationalError) antes de chegar ao
    # executor. Sem este try, viraria 500 cru em vez do 503 banco_indisponivel
    # (fallback da secao 7.6 do TCC). Mesmo tratamento que o /import ja faz.
    try:
        with get_connection() as conn:
            return executar_template(interpretacao, empresa, conn)
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "banco_indisponivel",
                "mensagem": "Serviço temporariamente indisponível. Tente novamente em instantes.",
            },
        )


@app.post("/import")
async def import_planilha(arquivo: UploadFile) -> dict:
    """Recebe o .xlsx do frontend (campo `arquivo`), valida e carrega no star
    schema. A resposta traz linhas_lidas/validas/rejeitadas -- campos que o
    `frontend/src/paginas/Importar.jsx` já lê. Mesmo padrão de erro do
    executor.py: nada de stack trace do Postgres vaza para o cliente."""
    conteudo = await arquivo.read()
    try:
        with get_connection() as conn:
            # Cada importação cria o próprio dataset (empresa) e devolve o
            # empresa_id, que o frontend reenvia nas perguntas.
            return importar(conteudo, arquivo.filename or "planilha.xlsx", conn)
    except ErroImportacao as e:
        raise HTTPException(
            status_code=422,
            detail={"tipo": "planilha_invalida", "mensagem": e.mensagem},
        )
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "banco_indisponivel",
                "mensagem": "Serviço temporariamente indisponível. Tente novamente em instantes.",
            },
        )
