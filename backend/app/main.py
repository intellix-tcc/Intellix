from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_connection, get_empresa_id
from app.fallbacks import verificar_confianca
from app.models import Pergunta, ResultSet
from app.nlu.regras import RuleBasedNLU
from app.sql.executor import executar_template

app = FastAPI(title="Intellix API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",                          # dev local do frontend
        "https://intellix-454e8bjo3-intellix3.vercel.app", # produção na Vercel
    ],
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
