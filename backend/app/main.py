import os
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.acesso import resolver_empresa
from app.auth import Usuario, usuario_atual
from app.contexto import aplicar_contexto
from app.db import fechar_pool, get_connection
from app.fallbacks import verificar_confianca
from app.importacao.etl import importar
from app.importacao.leitor_excel import ErroImportacao
from app.limite import LimiteDeRequisicoes
from app.models import Pergunta, ResultSet
from app.nlu.regras import RuleBasedNLU
from app.periodo_dataset import ajustar_periodo, ano_referencia, tem_ano_explicito
from app.resumo import montar_resumo
from app.sql.executor import executar_template

# Usuário logado (ou None, com AUTH_OBRIGATORIA=false). Annotated é a forma
# recomendada pelo FastAPI para dependências, e não esbarra na regra B008 do
# ruff (chamada de função como valor padrão de argumento).
UsuarioAtual = Annotated[Usuario | None, Depends(usuario_atual)]

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

# Limite de requisições por cliente (app/limite.py). Adicionado ANTES do CORS
# de propósito: o último middleware adicionado é o mais externo, então o CORS
# envolve este e a resposta 429 também sai com os cabeçalhos de CORS (sem
# isso, o navegador mostraria "erro de rede" em vez da mensagem de limite).
app.add_middleware(LimiteDeRequisicoes)

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


# Exemplos de pergunta por intenção, para o frontend exibir sugestões e deixar
# claro o que o agente responde (melhoria: dizer o que ele sabe e o que não
# sabe). As 12 chaves batem com os títulos de sql/templates.py.
_EXEMPLOS_POR_INTENCAO: dict[str, list[str]] = {
    "total_vendas_periodo": ["Quanto faturei em março de 2024?", "Qual o faturamento de 2024?"],
    "top_produtos": ["Quais os 5 produtos mais vendidos?", "Top 3 produtos de março de 2024?"],
    "ticket_medio": ["Qual o ticket médio em 2024?", "Ticket médio de janeiro de 2024?"],
    "quantidade_vendas": ["Quantas vendas tiveram em março de 2024?", "Número de vendas em 2024?"],
    "top_clientes": ["Quais os 5 clientes que mais compraram em 2024?", "Top 10 clientes do ano?"],
    "desempenho_vendedor": ["Como foi o desempenho da Fernanda em março?", "Quanto o vendedor Carlos vendeu em 2024?"],
    "produtos_sem_saida": ["Quais produtos não venderam em 2024?", "Produtos parados em março de 2024?"],
    "comparacao_periodos": ["Compare o faturamento de março com abril de 2024.", "Vendas de 2023 versus 2024?"],
    "variacao_periodo": ["Qual a variação do faturamento de março para abril de 2024?", "Quanto cresceu em relação ao ano passado?"],
    "vendas_por_canal": ["Quanto vendi por canal em 2024?", "Qual canal vendeu mais esse ano?"],
    "vendas_por_categoria": ["Quais categorias mais venderam em 2024?", "Faturamento por categoria em março de 2024?"],
    "vendas_por_pagamento": ["Vendas por forma de pagamento em 2024?", "Quanto foi pago no pix em março de 2024?"],
}

_LIMITACOES = [
    "Só respondo sobre os dados de vendas carregados (base demo ou planilha importada).",
    "Não faço previsões nem recomendações — só o que já aconteceu nos dados.",
    "Não respondo perguntas fora de vendas (clima, geografia, conversas gerais).",
    "Preciso de um período claro (mês, ano ou trimestre) na maioria das perguntas.",
    "Busco vendedor, produto e cliente por nome; nomes que não existem na base retornam 'sem resultado'.",
]


@app.get("/capacidades")
def capacidades() -> dict:
    """O que o agente sabe responder (com exemplos) e o que está fora de
    escopo. Serve para o frontend montar sugestões e orientar o usuário."""
    from app.sql.templates import TEMPLATES

    intencoes = [
        {
            "chave": chave,
            "titulo": TEMPLATES[chave]["titulo"],
            "exemplos": exemplos,
        }
        for chave, exemplos in _EXEMPLOS_POR_INTENCAO.items()
        if chave in TEMPLATES
    ]
    return {
        "total_intencoes": len(intencoes),
        "intencoes": intencoes,
        "limitacoes": _LIMITACOES,
        "dica": "Inclua sempre um período (ex.: 'em março de 2024' ou 'em 2024').",
    }


@app.post("/chat", response_model=ResultSet)
def chat(pergunta: Pergunta, usuario: UsuarioAtual) -> ResultSet:
    interpretacao = nlu.parse(pergunta.pergunta)
    # Continuação da conversa: "e em abril?" depois de "faturamento em março?"
    # herda a intenção anterior quando o frontend reenvia o contexto.
    interpretacao = aplicar_contexto(interpretacao, pergunta.contexto, pergunta.pergunta)
    verificar_confianca(interpretacao)

    # O executor.py trata OperationalError que acontece DURANTE a consulta, mas a
    # conexao e adquirida aqui: com o banco fora, get_connection() estoura
    # PoolTimeout (subclasse de psycopg.OperationalError) antes de chegar ao
    # executor. Sem este try, viraria 500 cru em vez do 503 banco_indisponivel
    # (fallback da secao 7.6 do TCC). Mesmo tratamento que o /import ja faz.
    try:
        with get_connection() as conn:
            # Dataset do usuário (vindo de uma importação) ou a base demo.
            # Só o dono consulta um dataset importado (ver acesso.py).
            empresa = resolver_empresa(conn, pergunta.empresa_id, usuario)
            # Período por dataset: quando a pergunta NÃO cita um ano ("esse ano",
            # "mês passado", "em março"), usa o ano mais recente dos dados DESSE
            # dataset em vez do ANO_PADRAO fixo -- senão uma planilha de 2026
            # respondia "sem resultado" (ver app/periodo_dataset.py).
            if not tem_ano_explicito(pergunta.pergunta):
                interpretacao = ajustar_periodo(interpretacao, ano_referencia(conn, empresa))
            return executar_template(interpretacao, empresa, conn)
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "banco_indisponivel",
                "mensagem": "Serviço temporariamente indisponível. Tente novamente em instantes.",
            },
        )


@app.get("/resumo")
def resumo(
    usuario: UsuarioAtual,
    empresa_id: str | None = None,
    ano: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    mes: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> dict:
    """Panorama do mês para a tela Início (ver app/resumo.py). Sem ano/mês,
    usa o mês mais recente com dados. Mesmas regras de acesso do /chat."""
    try:
        with get_connection() as conn:
            empresa = resolver_empresa(conn, empresa_id, usuario)
            return montar_resumo(conn, empresa, ano, mes)
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "banco_indisponivel",
                "mensagem": "Serviço temporariamente indisponível. Tente novamente em instantes.",
            },
        )


@app.post("/import")
async def import_planilha(arquivo: UploadFile, usuario: UsuarioAtual) -> dict:
    """Recebe o .xlsx do frontend (campo `arquivo`), valida e carrega no star
    schema. A resposta traz linhas_lidas/validas/rejeitadas -- campos que o
    `frontend/src/paginas/Importar.jsx` já lê. Mesmo padrão de erro do
    executor.py: nada de stack trace do Postgres vaza para o cliente."""
    conteudo = await arquivo.read()
    try:
        with get_connection() as conn:
            # Cada importação cria o próprio dataset (empresa) e devolve o
            # empresa_id, que o frontend reenvia nas perguntas.
            # Com login, o dataset fica registrado em nome do usuário.
            return importar(
                conteudo,
                arquivo.filename or "planilha.xlsx",
                conn,
                dono_id=usuario.id if usuario else None,
            )
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
