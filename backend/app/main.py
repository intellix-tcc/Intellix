import os
import time
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.acesso import resolver_empresa
from app.auditoria import registrar_consulta
from app.auth import Usuario, usuario_atual
from app.contexto import aplicar_contexto
from app.conversas import excluir as excluir_conversa
from app.conversas import listar as listar_conversas
from app.conversas import salvar as salvar_conversa
from app.db import fechar_pool, get_connection
from app.fallbacks import CONFIANCA_MINIMA, verificar_confianca
from app.filtros import aplicar_filtros, carregar_catalogo, sem_acento
from app.importacao.etl import importar
from app.importacao.leitor_excel import TAMANHO_MAX_MB, ErroImportacao
from app.limite import LimiteDeRequisicoes
from app.models import ConversaPayload, Pergunta, ResultSet
from app.nlu.regras import RuleBasedNLU, usar_referencia
from app.periodo_dataset import data_referencia, tem_ano_explicito
from app.planilhas import excluir as excluir_planilha
from app.planilhas import listar as listar_planilhas
from app.refino import pede_refino, refinar
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
    "unidades_vendidas": ["Quantas botas de couro vendemos em 2025?", "Quantos itens vendi em março de 2024?"],
    "melhor_mes": ["Qual foi o melhor mês de 2025?", "Em que mês mais vendemos smartwatch em 2025?"],
}

_LIMITACOES = [
    "Só respondo sobre os dados de vendas carregados (base demo ou planilha importada).",
    "Não faço previsões nem recomendações — só o que já aconteceu nos dados.",
    "Não respondo perguntas fora de vendas (clima, geografia, conversas gerais).",
    "Sem período na pergunta, uso o da conversa (ou o ano mais recente dos dados).",
    (
        "Filtro por produto, categoria, vendedor, cliente, canal e pagamento pelo nome do "
        "cadastro; nome que não existe na base é ignorado."
    ),
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
    inicio = time.perf_counter()
    texto = pergunta.pergunta
    # 1. O modelo (ou o baseline de regras) lê a frase: intenção, confiança e
    #    os trechos que marcou (período, produto, vendedor...).
    interpretacao = nlu.parse(texto)
    # Sem confiança e sem conversa anterior não há o que completar: pede para
    # reformular sem nem abrir conexão com o banco.
    if (
        pergunta.contexto is None
        and (not interpretacao.intencao or interpretacao.confianca < CONFIANCA_MINIMA)
        and not pede_refino(sem_acento(texto.lower()))
    ):
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
            # "Hoje" desse dataset: a data atual, limitada à última venda (ver
            # app/periodo_dataset.py). "Ano passado", "mês passado", "esse ano" e
            # um mês sem ano ("em março") saem dela.
            ref = data_referencia(conn, empresa)
            with usar_referencia(ref):
                # A leitura de antes do banco serviu só de triagem; sem ano na
                # frase, o período depende de "hoje", então a frase é lida de novo.
                if not tem_ano_explicito(texto):
                    interpretacao = nlu.parse(texto)
                # 2. Detalhes: o trecho que o modelo marcou ("botas de couro") vira
                #    o valor exato do catálogo desse dataset ("Bota couro").
                interpretacao = aplicar_filtros(interpretacao, texto, carregar_catalogo(conn, empresa))
                # 3. Conversa: "e de calçados?", "e em 2025?", "e qual mês vendeu
                #    mais?" completam a pergunta anterior (ver app/contexto.py).
                interpretacao = aplicar_contexto(interpretacao, pergunta.contexto, texto, ref.year)
                # 4. Refino: mês de maior venda, unidades, total de um recorte.
                interpretacao = refinar(interpretacao, texto)
            verificar_confianca(interpretacao)
            resultado = executar_template(interpretacao, empresa, conn)
            # Auditoria (F09): registra a consulta que de fato executou. É
            # best-effort e vai na mesma transação (commit ao sair do `with`).
            registrar_consulta(conn, empresa, interpretacao,
                               round((time.perf_counter() - inicio) * 1000))
            return resultado
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
    # Lê no máximo 1 byte além do limite: o suficiente para saber que passou,
    # sem trazer para a memória um arquivo de qualquer tamanho que alguém
    # mande direto para a API (o navegador já barra acima de 10 MB).
    limite_bytes = TAMANHO_MAX_MB * 1024 * 1024
    conteudo = await arquivo.read(limite_bytes + 1)
    if len(conteudo) > limite_bytes:
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "planilha_invalida",
                "mensagem": f"A planilha precisa ter no máximo {TAMANHO_MAX_MB} MB.",
            },
        )
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


# ---- Minhas planilhas (migration 007) ---------------------------------------
# Datasets importados pela conta logada. Exigem login mesmo com
# AUTH_OBRIGATORIA=false: sem usuário não há "minhas".


def _exigir_login(usuario: Usuario | None) -> Usuario:
    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail={"tipo": "nao_autenticado", "mensagem": "Entre na sua conta para ver suas planilhas."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def _banco_indisponivel() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "tipo": "banco_indisponivel",
            "mensagem": "Serviço temporariamente indisponível. Tente novamente em instantes.",
        },
    )


@app.get("/planilhas")
def minhas_planilhas(usuario: UsuarioAtual) -> dict:
    """Planilhas importadas pelo usuário, da mais recente para a mais antiga."""
    dono = _exigir_login(usuario)
    try:
        with get_connection() as conn:
            return {"planilhas": listar_planilhas(conn, dono.id)}
    except psycopg.OperationalError:
        raise _banco_indisponivel()


@app.delete("/planilhas/{empresa_id}")
def apagar_planilha(empresa_id: str, usuario: UsuarioAtual) -> dict:
    """Apaga um dataset importado pelo próprio usuário. De outra pessoa, da
    base demo ou inexistente: o mesmo 404 (não revela quais ids existem)."""
    dono = _exigir_login(usuario)
    try:
        with get_connection() as conn:
            if not excluir_planilha(conn, empresa_id, dono.id):
                raise HTTPException(
                    status_code=404,
                    detail={
                        "tipo": "dataset_nao_encontrado",
                        "mensagem": "Não encontrei essa planilha na sua conta.",
                    },
                )
            return {"excluida": True, "empresa_id": empresa_id}
    except psycopg.OperationalError:
        raise _banco_indisponivel()


# ---- Histórico de conversas (migration 008) ---------------------------------
# As conversas do chat da conta logada. Como "minhas planilhas", exigem login
# mesmo com AUTH_OBRIGATORIA=false: sem usuário não há "minhas".


def _conversa_nao_encontrada() -> HTTPException:
    # Mesma resposta para "não é sua" e "não existe": não revela ids de outros.
    return HTTPException(
        status_code=404,
        detail={
            "tipo": "conversa_nao_encontrada",
            "mensagem": "Não encontrei essa conversa na sua conta.",
        },
    )


@app.get("/conversas")
def minhas_conversas(usuario: UsuarioAtual) -> dict:
    """Conversas do usuário, da mais recente para a mais antiga."""
    dono = _exigir_login(usuario)
    try:
        with get_connection() as conn:
            return {"conversas": listar_conversas(conn, dono.id)}
    except psycopg.OperationalError:
        raise _banco_indisponivel()


@app.put("/conversas/{conversa_id}")
def gravar_conversa(conversa_id: str, payload: ConversaPayload, usuario: UsuarioAtual) -> dict:
    """Cria ou atualiza uma conversa da conta (o id é o mesmo do frontend).
    Id de outra pessoa, ou malformado: 404, sem sobrescrever nada."""
    dono = _exigir_login(usuario)
    try:
        with get_connection() as conn:
            salvo = salvar_conversa(
                conn, conversa_id, dono.id, payload.titulo, payload.mensagens, payload.criado_em
            )
            if not salvo:
                raise _conversa_nao_encontrada()
            return {"id": salvo}
    except psycopg.OperationalError:
        raise _banco_indisponivel()


@app.delete("/conversas/{conversa_id}")
def apagar_conversa(conversa_id: str, usuario: UsuarioAtual) -> dict:
    """Apaga uma conversa da própria conta. De outra pessoa ou inexistente: 404."""
    dono = _exigir_login(usuario)
    try:
        with get_connection() as conn:
            if not excluir_conversa(conn, conversa_id, dono.id):
                raise _conversa_nao_encontrada()
            return {"excluida": True, "id": conversa_id}
    except psycopg.OperationalError:
        raise _banco_indisponivel()
