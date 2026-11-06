import re
from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator

_CHAVE_VALIDA = re.compile(r"^[a-z_]{1,40}$")
_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_CHAVES = 30
_MAX_TEXTO = 200
_LIMITE_MAX = 100


def _data_valida(valor: Any) -> str | None:
    if not isinstance(valor, str) or not _DATA_ISO.match(valor):
        return None
    try:
        date.fromisoformat(valor)
    except ValueError:
        return None
    return valor


def _limite_valido(valor: Any) -> int | None:
    if isinstance(valor, bool):
        return None
    if isinstance(valor, str) and valor.strip().isdigit():
        valor = int(valor.strip())
    if isinstance(valor, int) and 1 <= valor <= _LIMITE_MAX:
        return valor
    return None


def sanear_entidades(bruto: Any) -> dict[str, Any]:
    """Filtra os parâmetros que o navegador reenvia no contexto da conversa.

    Esses valores voltam do cliente e vão para o SQL (sempre como parâmetro,
    nunca no texto da consulta). Uma data malformada ou um limite negativo
    virava erro 500 no Postgres; listas e objetos nem chegavam a ser
    adaptados. O que não passa aqui é descartado: se faltar algo obrigatório,
    o executor pede o dado (422 parametro_faltando), como numa pergunta nova.
    """
    if not isinstance(bruto, dict):
        return {}
    limpo: dict[str, Any] = {}
    for chave, valor in list(bruto.items())[:_MAX_CHAVES]:
        if not isinstance(chave, str) or not _CHAVE_VALIDA.match(chave):
            continue
        if chave.startswith("periodo_"):
            valor = _data_valida(valor)
        elif chave == "limite":
            valor = _limite_valido(valor)
        elif isinstance(valor, str):
            valor = valor.strip()[:_MAX_TEXTO] or None
        elif isinstance(valor, bool) or not isinstance(valor, (int, float)):
            valor = None
        if valor is not None:
            limpo[chave] = valor
    return limpo


class Interpretacao(BaseModel):
    """O que o NLU (regras ou modelo) devolve. Fronteira A -> B."""

    intencao: str | None
    confianca: float
    entidades: dict[str, Any] = {}
    texto_original: str
    # Trechos que o modelo marcou na frase (tags BIO), crus: {"PRODUTO": "botas de couro"}.
    # Não vão para o SQL; servem de pista para app/filtros.py achar o valor no catálogo.
    entidades_modelo: dict[str, Any] = {}


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
    # Frase pronta para quando a resposta certa é uma lista vazia (ex.: nenhum
    # produto parado no período). Opcional: ausente na resposta comum.
    mensagem: str | None = None


class Contexto(BaseModel):
    """Resumo da resposta anterior, reenviado pelo frontend para dar
    continuidade à conversa (ver app/contexto.py). `intencao` e `entidades`
    saem do ResultSet anterior (campos `intencao` e `parametros`)."""

    intencao: str | None = Field(default=None, max_length=40)
    entidades: dict[str, Any] = {}

    @field_validator("entidades", mode="before")
    @classmethod
    def _sanear(cls, valor: Any) -> dict[str, Any]:
        return sanear_entidades(valor)


class ConversaPayload(BaseModel):
    """Corpo do PUT /conversas/{id}: a conversa inteira como o frontend a
    mantém (título + mensagens). O id vem na URL; o dono, do token. Aceita
    tanto `criadoEm` (nome do objeto no frontend) quanto `criado_em`."""

    model_config = {"populate_by_name": True}

    titulo: str = Field(min_length=1, max_length=200)
    # Mensagens no formato do frontend (tipo + texto/dados). Teto de 200 por
    # conversa: o bastante para uma conversa real, e um limite para o corpo não
    # crescer sem fim. O conteúdo não é interpretado aqui — vai como JSONB.
    mensagens: list[dict[str, Any]] = Field(default_factory=list, max_length=200)
    criado_em: str | None = Field(default=None, alias="criadoEm")


class Pergunta(BaseModel):
    # Mesmo limite do campo da tela (500 caracteres): uma pergunta de vendas
    # não precisa de mais, e texto gigante só serviria para gastar CPU do NLU.
    pergunta: str = Field(min_length=1, max_length=500)
    # Dataset a consultar. Quando o usuário importa uma planilha, o /import
    # cria uma empresa própria e devolve o id; o frontend o reenvia aqui para
    # as perguntas caírem sobre os dados importados, não sobre a base demo.
    # Ausente (None) = base de demonstração (EMPRESA_ID fixo).
    empresa_id: str | None = None
    # Contexto da pergunta anterior, para resolver frases elípticas como
    # "e em abril?". Ausente (None) = pergunta tratada isoladamente.
    contexto: Contexto | None = None
