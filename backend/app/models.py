from typing import Any

from pydantic import BaseModel


class Interpretacao(BaseModel):
    """O que o NLU (regras ou modelo) devolve. Fronteira A -> B."""

    intencao: str | None
    confianca: float
    entidades: dict[str, Any] = {}
    texto_original: str


class ResultSet(BaseModel):
    """O que o backend devolve para o frontend. Fronteira B -> D.

    Passa por aqui TUDO: tela, Excel e PDF. Valores numericos ficam como
    numero (ex.: 48231.50), nunca formatados como texto (ex.: "R$ 48.231,50").
    """

    titulo: str
    colunas: list[str]
    linhas: list[list[Any]]
    tipo_visualizacao: str  # numero | tabela | barra | linha | pizza
    parametros: dict[str, Any] = {}
    confianca: float = 1.0
    gerado_em: str
    # Chave do template que respondeu (ver app/sql/templates.py). O frontend
    # usa para sugerir a próxima pergunta; opcional para não quebrar quem
    # já consome o contrato.
    intencao: str | None = None
    # Resposta de um mês só (faturamento, quantidade de vendas, ticket médio):
    # a mesma métrica nos 12 meses até ele, para o frontend mostrar a
    # evolução com o mês em destaque. Ver app/sql/evolucao.py. (Não confundir
    # com Pergunta.contexto, que é o contexto conversacional da pergunta.)
    evolucao: dict[str, Any] | None = None


class Contexto(BaseModel):
    """Resumo da resposta anterior, reenviado pelo frontend para dar
    continuidade à conversa (ver app/contexto.py). `intencao` e `entidades`
    saem do ResultSet anterior (campos `intencao` e `parametros`)."""

    intencao: str | None = None
    entidades: dict[str, Any] = {}


class Pergunta(BaseModel):
    pergunta: str
    # Dataset a consultar. Quando o usuário importa uma planilha, o /import
    # cria uma empresa própria e devolve o id; o frontend o reenvia aqui para
    # as perguntas caírem sobre os dados importados, não sobre a base demo.
    # Ausente (None) = base de demonstração (EMPRESA_ID fixo).
    empresa_id: str | None = None
    # Contexto da pergunta anterior, para resolver frases elípticas como
    # "e em abril?". Ausente (None) = pergunta tratada isoladamente.
    contexto: Contexto | None = None
