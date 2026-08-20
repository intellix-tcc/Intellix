import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_connection, get_empresa_id
from app.fallbacks import verificar_confianca
from app.models import Pergunta, ResultSet
from app.nlu.regras import RuleBasedNLU
from app.sql.executor import executar_template

app = FastAPI(title="Intellix API")

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

nlu = RuleBasedNLU()  # tomada: troca para o modelo treinado na semana 9 (B11)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ResultSet)
def chat(pergunta: Pergunta) -> ResultSet:
    interpretacao = nlu.parse(pergunta.pergunta)
    verificar_confianca(interpretacao)

    with get_connection() as conn:
        return executar_template(interpretacao, get_empresa_id(), conn)
