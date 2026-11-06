"""Respostas do executor que não dependem do banco real.

- "produtos sem saída" com lista vazia: é resposta (200), não falta de dados;
- valor impossível num parâmetro (DataError do Postgres): 422, nunca 500;
- contexto reenviado pelo navegador: só passa o que é seguro usar no SQL.
"""

import psycopg
import pytest
from app.models import Contexto, Interpretacao, sanear_entidades
from app.sql.executor import executar_template
from fastapi import HTTPException


class _Coluna:
    def __init__(self, nome):
        self.name = nome


class _Cursor:
    def __init__(self, colunas, linhas, erro=None):
        self.description = [_Coluna(c) for c in colunas]
        self._linhas, self._erro = linhas, erro

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, parametros):
        if self._erro:
            raise self._erro

    def fetchall(self):
        return self._linhas


class _Conexao:
    def __init__(self, colunas, linhas, erro=None):
        self._cursor = _Cursor(colunas, linhas, erro)

    def cursor(self):
        return self._cursor


def _interp(intencao, **entidades):
    return Interpretacao(intencao=intencao, confianca=0.95, entidades=entidades, texto_original="x")


PERIODO = {"periodo_inicio": "2024-01-01", "periodo_fim": "2024-12-31"}


def test_produtos_sem_saida_vazio_responde_200_com_mensagem():
    r = executar_template(
        _interp("produtos_sem_saida", **PERIODO), "emp", _Conexao(["produto", "categoria"], [])
    )
    assert r.linhas == []
    assert r.titulo == "Produtos sem saída no período"  # o avaliador reconhece a intenção pelo título
    assert r.intencao == "produtos_sem_saida"
    assert "Nenhum ficou parado" in r.mensagem


def test_produtos_sem_saida_vazio_cita_a_categoria():
    r = executar_template(
        _interp("produtos_sem_saida", categoria="Calçados", **PERIODO),
        "emp",
        _Conexao(["produto", "categoria"], []),
    )
    assert r.mensagem.startswith("Todos os produtos da categoria Calçados")


def test_outras_intencoes_sem_linhas_continuam_404():
    with pytest.raises(HTTPException) as e:
        executar_template(_interp("top_clientes", limite=5, **PERIODO), "emp", _Conexao(["cliente"], []))
    assert e.value.status_code == 404


def test_valor_impossivel_no_parametro_vira_422_e_nao_500():
    erro = psycopg.errors.InvalidDatetimeFormat("invalid input syntax for type date")
    with pytest.raises(HTTPException) as e:
        executar_template(_interp("ticket_medio", **PERIODO), "emp", _Conexao(["ticket_medio"], [], erro))
    assert e.value.status_code == 422
    assert e.value.detail["tipo"] == "parametro_invalido"


def test_contexto_descarta_valores_inseguros():
    limpo = sanear_entidades({
        "periodo_inicio": "2024-13-45",          # data impossível
        "periodo_fim": "2024-12-31",             # válida
        "limite": -1,                            # fora de 1..100
        "vendedor_nome": "%fernanda%",           # texto comum
        "produto": {"$ne": 1},                   # objeto
        "categoria": ["a", "b"],                 # lista
        "Chave Estranha": "x",                   # chave fora do padrão
        "canal": "  site  ",
    })
    assert limpo == {"periodo_fim": "2024-12-31", "vendedor_nome": "%fernanda%", "canal": "site"}


def test_contexto_aceita_o_que_a_propria_api_devolve():
    ctx = Contexto(intencao="top_produtos", entidades={"limite": 5, **PERIODO, "categoria": "Calçados"})
    assert ctx.entidades == {"limite": 5, **PERIODO, "categoria": "Calçados"}


def test_contexto_limite_em_texto_vira_numero():
    assert sanear_entidades({"limite": "10"}) == {"limite": 10}
    assert sanear_entidades({"limite": "500"}) == {}
