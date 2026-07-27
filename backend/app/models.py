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


class Pergunta(BaseModel):
    pergunta: str
