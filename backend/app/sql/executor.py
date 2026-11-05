"""Executa o template SQL escolhido pelo NLU e devolve um ResultSet.

Os 3 fallbacks que precisam de banco (secao 7.6 do TCC) moram aqui:
parametro obrigatorio ausente, banco fora do ar e consulta sem resultado.
Nenhum deles deixa o Postgres/psycopg vazar stack trace para o cliente.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import psycopg
from fastapi import HTTPException

from app.fallbacks import EXEMPLOS_PADRAO
from app.models import Interpretacao, ResultSet
from app.sql.templates import TEMPLATES

# Pergunta de esclarecimento por parametro obrigatorio ausente. Em vez do
# generico "nao entendi, reformule", o backend diz exatamente o que faltou e
# da um exemplo de como completar (melhoria: perguntar quando o contexto esta
# incompleto). A chave e o prefixo do parametro para cobrir periodo_a_inicio,
# periodo_atual_inicio etc. com uma unica entrada.
_PERGUNTA_POR_PARAMETRO: list[tuple[str, str]] = [
    ("vendedor_nome", "sobre qual vendedor(a)? (ex.: \"desempenho da Fernanda em março\")"),
    ("limite", "quantos itens no ranking? (ex.: \"top 5 produtos\")"),
    ("periodo_a", "quais são os dois períodos a comparar? (ex.: \"março com abril de 2024\")"),
    ("periodo_b", "quais são os dois períodos a comparar? (ex.: \"março com abril de 2024\")"),
    ("periodo_atual", "em relação a qual período anterior? (ex.: \"de março para abril de 2024\")"),
    ("periodo_anterior", "em relação a qual período anterior? (ex.: \"de março para abril de 2024\")"),
    ("periodo", "de qual período? (ex.: \"em março de 2024\" ou \"em 2024\")"),
]


def _esclarecer(faltando: list[str]) -> str:
    """Monta uma pergunta de esclarecimento a partir dos parametros ausentes,
    sem repetir a mesma pergunta (ex.: periodo_a_inicio e periodo_a_fim viram
    uma pergunta so)."""
    perguntas: list[str] = []
    for param in faltando:
        for prefixo, texto in _PERGUNTA_POR_PARAMETRO:
            if param.startswith(prefixo) and texto not in perguntas:
                perguntas.append(texto)
                break
    if not perguntas:
        return "Não consegui identificar todos os dados da pergunta. Tente reformular."
    return "Quase lá — só preciso saber " + "; ".join(perguntas) + "."


def _para_json(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


def executar_template(interp: Interpretacao, empresa_id: str, conn: psycopg.Connection) -> ResultSet:
    template = TEMPLATES.get(interp.intencao)
    if template is None:
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "baixa_confianca",
                "mensagem": "Não entendi a pergunta. Tente reformular.",
                "exemplos": EXEMPLOS_PADRAO,
            },
        )

    faltando = [p for p in template["obrigatorios"] if p not in interp.entidades]
    if faltando:
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "parametro_faltando",
                "mensagem": _esclarecer(faltando),
                "faltando": faltando,
                "exemplos": EXEMPLOS_PADRAO,
            },
        )

    parametros = {**interp.entidades, "empresa_id": empresa_id}

    try:
        with conn.cursor() as cur:
            cur.execute(template["sql"], parametros)
            colunas = [d.name for d in cur.description]
            linhas_brutas = cur.fetchall()
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=503,
            detail={
                "tipo": "banco_indisponivel",
                "mensagem": "Serviço temporariamente indisponível. Tente novamente em instantes.",
            },
        )

    # Agregados sem GROUP BY (ex.: ticket_medio = avg(...)) SEMPRE devolvem uma
    # linha: quando nao ha dados no periodo, essa linha vem toda NULL. Sem este
    # tratamento, "ticket médio de 2018" (sem vendas) virava 200 com valor null
    # em vez de 404 sem_resultado. Uma linha unica 100% NULL conta como vazio.
    sem_dados = not linhas_brutas or (
        len(linhas_brutas) == 1 and all(v is None for v in linhas_brutas[0])
    )
    if sem_dados:
        raise HTTPException(
            status_code=404,
            detail={
                "tipo": "sem_resultado",
                "mensagem": "Não há registros para o período ou filtro informado.",
            },
        )

    linhas = [[_para_json(valor) for valor in linha] for linha in linhas_brutas]

    # Faturamento e quantidade de vendas já vêm um mês por linha. Com mais de
    # um mês (ex.: "quanto faturei em 2024?"), a resposta é uma evolução no
    # tempo: vira gráfico de linha. Antes saía como "numero" e a tela mostrava
    # só o primeiro mês.
    visual = template["visual"]
    if visual == "numero" and len(linhas) > 1 and colunas and colunas[0] == "periodo":
        visual = "linha"

    return ResultSet(
        titulo=template["titulo"],
        colunas=colunas,
        linhas=linhas,
        tipo_visualizacao=visual,
        parametros=interp.entidades,
        confianca=interp.confianca,
        gerado_em=datetime.now(timezone.utc).isoformat(),
        intencao=interp.intencao,
    )
