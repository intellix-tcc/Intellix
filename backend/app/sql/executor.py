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
from app.filtros import FILTROS, descrever
from app.models import Interpretacao, ResultSet
from app.sql.evolucao import evolucao_mensal, preencher
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


_MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _nome_mes(periodo: str) -> str:
    ano, mes = periodo.split("-")
    return f"{_MESES[int(mes) - 1]} de {ano}"


def _meses_entre(primeiro: str, ultimo: str) -> list[str]:
    a0, m0 = (int(x) for x in primeiro.split("-"))
    a1, m1 = (int(x) for x in ultimo.split("-"))
    return [f"{t // 12:04d}-{t % 12 + 1:02d}" for t in range(a0 * 12 + m0 - 1, a1 * 12 + m1)]


def _melhor_mes(colunas: list[str], linhas: list[list[Any]], entidades: dict) -> tuple:
    """Da série mês a mês, o mês de maior (ou menor) faturamento/unidades.
    Responde com esse mês e devolve a série inteira como evolução, com ele em
    destaque: a pessoa vê o mês e o quanto ele se destacou dos outros."""
    metrica = entidades.get("metrica") if entidades.get("metrica") in colunas else "faturamento"
    i = colunas.index(metrica)
    com_valor = [linha for linha in linhas if linha[i]]
    escolha = (min if entidades.get("sentido") == "menor" else max)(com_valor or linhas, key=lambda li: li[i])
    serie = {str(linha[0]): float(linha[i] or 0) for linha in linhas}
    rotulos = _meses_entre(str(linhas[0][0]), str(linhas[-1][0]))
    evolucao = None
    if len(rotulos) >= 2:
        evolucao = {
            "titulo": "Unidades vendidas mês a mês" if metrica == "unidades" else "Faturamento mês a mês",
            "colunas": ["periodo", metrica],
            "linhas": preencher(rotulos, serie),
            "destaque": str(escolha[0]),
        }
    menor = entidades.get("sentido") == "menor"
    if evolucao:
        evolucao["legenda"] = f"o mês com {'menos' if menor else 'mais'} vendas"
    if metrica == "unidades":
        titulo = f"Mês com {'menos' if menor else 'mais'} unidades vendidas: {_nome_mes(str(escolha[0]))}"
    else:
        titulo = f"Mês de {'menor' if menor else 'maior'} faturamento: {_nome_mes(str(escolha[0]))}"
    return ["periodo", metrica], [[escolha[0], escolha[i]]], titulo, evolucao


def _sem_produtos_parados(template: dict, colunas: list[str], interp: Interpretacao) -> ResultSet:
    """Resposta de "produtos sem saída" quando todos venderam: 200, lista vazia
    e a frase que explica. O título é o do template (com o recorte), como nas
    demais respostas."""
    recorte = descrever(interp.entidades, interp.intencao)
    categoria = interp.entidades.get("categoria")
    quem = f"Todos os produtos da categoria {categoria}" if categoria else "Todos os produtos"
    # recorte da venda (canal, pagamento, vendedor, cliente): "...no período, com canal Site"
    recorte_venda = descrever({k: v for k, v in interp.entidades.items() if k != "categoria"},
                              interp.intencao)
    if recorte_venda:
        quem = f"{quem} ({recorte_venda})"
    return ResultSet(
        titulo=f"{template['titulo']} · {recorte}" if recorte else template["titulo"],
        colunas=colunas,
        linhas=[],
        tipo_visualizacao="tabela",
        parametros=interp.entidades,
        confianca=interp.confianca,
        gerado_em=datetime.now(timezone.utc).isoformat(),
        intencao=interp.intencao,
        mensagem=f"{quem} tiveram pelo menos uma venda no período. Nenhum ficou parado.",
    )


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

    # Filtros ausentes vão como NULL (= sem recorte; ver FILTROS_SQL em templates.py).
    parametros = {**{k: None for k in FILTROS}, **interp.entidades, "empresa_id": empresa_id}

    try:
        with conn.cursor() as cur:
            cur.execute(template["sql"], parametros)
            colunas = [d.name for d in cur.description]
            linhas_brutas = cur.fetchall()
    except psycopg.DataError:
        # Parâmetro com valor impossível (data malformada, limite negativo):
        # pede para reformular em vez de devolver 500. Os valores vêm da NLU
        # ou do contexto reenviado pelo navegador (ver models.Contexto).
        raise HTTPException(
            status_code=422,
            detail={
                "tipo": "parametro_invalido",
                "mensagem": "Não consegui usar algum dado da pergunta. Tente reformular.",
                "exemplos": EXEMPLOS_PADRAO,
            },
        )
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
    # "Quais produtos não venderam?": lista vazia é a RESPOSTA (nenhum produto
    # parado), não falta de dados. Antes caía no 404 abaixo e o usuário lia
    # "não há registros" justamente quando tudo tinha vendido (5 dos 17 erros
    # da reavaliação de 05/11/2026 eram isso).
    if interp.intencao == "produtos_sem_saida" and not linhas_brutas:
        return _sem_produtos_parados(template, colunas, interp)

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
    titulo = template["titulo"]
    evolucao = None
    if interp.intencao == "melhor_mes":
        colunas, linhas, titulo, evolucao = _melhor_mes(colunas, linhas, interp.entidades)

    # Faturamento e quantidade de vendas já vêm um mês por linha. Com mais de
    # um mês (ex.: "quanto faturei em 2024?"), a resposta é uma evolução no
    # tempo: vira gráfico de linha. Antes saía como "numero" e a tela mostrava
    # só o primeiro mês.
    visual = template["visual"]
    if visual == "numero" and len(linhas) > 1 and colunas and colunas[0] == "periodo":
        visual = "linha"
        # Mês sem venda não volta do GROUP BY; com recorte (um produto) isso é
        # comum, e a linha do gráfico pularia o mês. Completa com 0.
        por_mes = {str(linha[0]): linha for linha in linhas}
        zeros = [0] * (len(colunas) - 1)
        linhas = [por_mes.get(m, [m, *zeros]) for m in _meses_entre(str(linhas[0][0]), str(linhas[-1][0]))]

    # Um mês só: junta a evolução dos 12 meses até ele. É complemento — se
    # falhar, a resposta principal sai do mesmo jeito.
    if evolucao is None and len(linhas) == 1:
        try:
            evolucao = evolucao_mensal(interp.intencao, interp.entidades, empresa_id, conn)
        except psycopg.Error:
            evolucao = None

    # O recorte entra no título: "Unidades vendidas · Bota couro".
    recorte = descrever(interp.entidades, interp.intencao)
    if recorte:
        titulo = f"{titulo} · {recorte}"

    return ResultSet(
        titulo=titulo,
        colunas=colunas,
        linhas=linhas,
        tipo_visualizacao=visual,
        parametros=interp.entidades,
        confianca=interp.confianca,
        gerado_em=datetime.now(timezone.utc).isoformat(),
        intencao=interp.intencao,
        evolucao=evolucao,
    )
