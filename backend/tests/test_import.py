"""Testes da importação de planilha que rodam sem banco.

Cobrem o leitor (mapeamento de colunas, sinônimos, validação do arquivo) e os
conversores de tipo do ETL. A carga no Postgres em si (dim/fato) precisa de
DATABASE_URL e fica para o ambiente integrado (ver docs/plano-ingestao-dados.md).
"""

import io

import pytest
from app.importacao import etl
from app.importacao.leitor_excel import (
    ErroImportacao,
    ler_planilha,
    mapear_coluna,
    normalizar,
)
from openpyxl import Workbook


def _xlsx(linhas: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for linha in linhas:
        ws.append(linha)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---- mapeamento de colunas ----

def test_normalizar_tira_acento_e_espaco():
    assert normalizar(" Preço Unitário ") == "preco_unitario"
    assert normalizar("QTD") == "qtd"


def test_mapeia_coluna_direta_e_sinonimo():
    assert mapear_coluna("data_venda") == "data_venda"
    assert mapear_coluna("Data da Venda") == "data_venda"
    assert mapear_coluna("qtd") == "quantidade"
    assert mapear_coluna("total") == "valor_total"
    assert mapear_coluna("coluna qualquer") is None


# ---- leitor ----

def test_le_planilha_valida():
    conteudo = _xlsx([
        ["data_venda", "produto", "quantidade", "valor_total"],
        ["2026-03-05", "Tênis", 1, 279.90],
    ])
    r = ler_planilha(conteudo, "vendas.xlsx")
    assert r["total_linhas"] == 1
    assert "data_venda" in r["colunas_encontradas"]
    assert r["linhas"][0]["produto"] == "Tênis"


def test_coluna_obrigatoria_faltando():
    conteudo = _xlsx([
        ["produto", "quantidade", "valor_total"],  # sem data_venda
        ["Tênis", 1, 279.90],
    ])
    with pytest.raises(ErroImportacao, match="data_venda"):
        ler_planilha(conteudo, "vendas.xlsx")


def test_precisa_de_algum_valor():
    conteudo = _xlsx([
        ["data_venda", "produto", "quantidade"],  # sem unitário nem total
        ["2026-03-05", "Tênis", 1],
    ])
    with pytest.raises(ErroImportacao, match="valor_total"):
        ler_planilha(conteudo, "vendas.xlsx")


def test_rejeita_xls_antigo():
    with pytest.raises(ErroImportacao, match=".xlsx"):
        ler_planilha(b"qualquer", "planilha.xls")


def test_rejeita_arquivo_nao_excel():
    with pytest.raises(ErroImportacao):
        ler_planilha(b"isto nao e um zip", "fake.xlsx")


def test_colunas_extras_sao_listadas():
    conteudo = _xlsx([
        ["data_venda", "produto", "quantidade", "valor_total", "observacao"],
        ["2026-03-05", "Tênis", 1, 279.90, "primeira compra"],
    ])
    r = ler_planilha(conteudo, "vendas.xlsx")
    assert "observacao" in r["extras"]


# ---- conversores do ETL ----

def test_parse_numero_pt_br():
    assert etl._parse_numero("1.234,56") == 1234.56
    assert etl._parse_numero("279,90") == 279.90
    assert etl._parse_numero("R$ 49.90") == 49.90
    assert etl._parse_numero(49.9) == 49.9
    assert etl._parse_numero("") is None


def test_parse_data_formatos():
    from datetime import date, datetime, timezone

    assert etl._parse_data("2026-03-05") == date(2026, 3, 5)
    assert etl._parse_data("05/03/2026") == date(2026, 3, 5)
    assert etl._parse_data(datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc)) == date(2026, 3, 5)
    assert etl._parse_data("data ruim") is None


def test_parse_int_arredonda():
    assert etl._parse_int("2") == 2
    assert etl._parse_int(3.0) == 3
    assert etl._parse_int(None) is None


# ---- número da linha, teto de linhas e tamanho (sem banco) ----

def test_numero_da_linha_e_o_do_excel_mesmo_com_linha_vazia_no_meio():
    conteudo = _xlsx([
        ["data_venda", "produto", "quantidade", "valor_total"],
        ["2024-03-05", "A", 1, 10],
        [None, None, None, None],          # linha 3 em branco
        ["2024-03-06", "B", 1, 20],        # é a linha 4 no Excel
    ])
    r = ler_planilha(conteudo, "vendas.xlsx")
    assert [linha["_linha"] for linha in r["linhas"]] == [2, 4]


def test_planilha_acima_do_teto_de_linhas_e_recusada(monkeypatch):
    from app.importacao import leitor_excel

    monkeypatch.setattr(leitor_excel, "LIMITE_LINHAS", 3)
    linhas = [["data_venda", "produto", "quantidade", "valor_total"]]
    linhas += [["2024-03-05", f"P{i}", 1, 10] for i in range(4)]
    with pytest.raises(ErroImportacao, match="mais de 3 linhas"):
        ler_planilha(_xlsx(linhas), "vendas.xlsx")
    # exatamente no teto ainda passa
    assert ler_planilha(_xlsx(linhas[:4]), "vendas.xlsx")["total_linhas"] == 3


def test_upload_acima_do_limite_e_recusado_antes_de_ler(monkeypatch):
    from app import main
    from fastapi.testclient import TestClient

    monkeypatch.setenv("LIMITE_REQUISICOES", "0")
    monkeypatch.setattr(main, "TAMANHO_MAX_MB", 0)  # qualquer byte passa do limite
    r = TestClient(main.app).post("/import", files={"arquivo": ("v.xlsx", b"PK\x03\x04xx")})
    assert r.status_code == 422
    assert r.json()["detail"]["tipo"] == "planilha_invalida"
