"""Regras do panorama (app/resumo.py) -- funções puras, sem banco."""

from datetime import date

from app.resumo import (
    escolher_mes,
    gerar_observacoes,
    gerar_resumo_texto,
    limites_mes,
    melhor_e_pior_dia_semana,
    mes_anterior,
    moeda,
    nome_canal,
    variacao,
)


def kpi(fat, vendas, itens=0, clientes=0):
    return {"faturamento": fat, "vendas": vendas, "itens": itens, "produtos": 0,
            "clientes": clientes, "registros": 0}


def test_mes_anterior_atravessa_o_ano():
    assert mes_anterior(2026, 1) == (2025, 12)
    assert mes_anterior(2026, 3, 3) == (2025, 12)
    assert mes_anterior(2025, 12, -1) == (2026, 1)


def test_limites_mes_fim_exclusivo():
    assert limites_mes(2024, 2) == (date(2024, 2, 1), date(2024, 3, 1))
    assert limites_mes(2024, 12) == (date(2024, 12, 1), date(2025, 1, 1))


def test_escolher_mes_ignora_meses_futuros():
    meses = [(2026, 12), (2026, 11), (2026, 10)]
    assert escolher_mes(meses, date(2026, 11, 5)) == (2026, 11)
    # tudo no futuro: fica com o mais próximo de hoje
    assert escolher_mes([(2030, 2), (2030, 1)], date(2026, 1, 1)) == (2030, 1)


def test_variacao_sem_base_e_none():
    assert variacao(100, 0) is None
    assert variacao(100, None) is None
    assert variacao(110, 100) == 10.0
    assert variacao(90, 100) == -10.0


def test_moeda_no_formato_brasileiro():
    assert moeda(1234567.5) == "R$ 1.234.567,50"
    assert moeda(0) == "R$ 0,00"


def test_nome_canal():
    assert nome_canal("whatsapp") == "WhatsApp"
    assert nome_canal("loja_fisica") == "Loja fisica"
    assert nome_canal(None) == "Não informado"


def test_dia_semana_conta_dia_sem_venda_como_zero():
    # março/2024 começa numa sexta. Só sextas vendem.
    por_dia = {1: 100.0, 8: 100.0, 15: 100.0, 22: 100.0, 29: 100.0}
    melhor, _ = melhor_e_pior_dia_semana(2024, 3, por_dia)
    assert melhor == 4  # sexta
    assert melhor_e_pior_dia_semana(2024, 3, {}) is None


def test_observacao_de_faturamento_so_acima_do_limiar():
    base = {"ano": 2024, "mes": 3, "produtos": [], "sem_giro": 0, "canais": [], "dias_semana": None}
    obs = gerar_observacoes(kpi_atual=kpi(110, 10), kpi_anterior=kpi(100, 10), **base)
    assert obs[0]["tipo"] == "alta"
    assert "10% acima de fevereiro" in obs[0]["texto"]
    assert obs[0]["pergunta"] == "Quanto faturei em março de 2024?"

    obs = gerar_observacoes(kpi_atual=kpi(101, 10), kpi_anterior=kpi(100, 10), **base)
    assert obs == []


def test_produto_com_base_pequena_nao_vira_destaque():
    # "Brinde" saiu de 1 para 50 (+4900%), mas era 0,1% do mês anterior.
    produtos = [("Brinde", 50.0, 1.0), ("Tênis", 600.0, 400.0)]
    obs = gerar_observacoes(
        ano=2024, mes=3, kpi_atual=kpi(1000, 10), kpi_anterior=kpi(1000, 10),
        produtos=produtos, sem_giro=0, canais=[], dias_semana=None,
    )
    textos = " ".join(o["texto"] for o in obs)
    assert "Brinde" not in textos
    assert "Tênis cresceu 50%" in textos


def test_observacao_sem_giro_e_canal():
    obs = gerar_observacoes(
        ano=2024, mes=3, kpi_atual=kpi(100, 1), kpi_anterior=kpi(100, 1),
        produtos=[], sem_giro=3,
        canais=[{"nome": "Loja", "valor": 60, "pct": 60.0}],
        dias_semana=None,
    )
    assert obs[0]["tipo"] == "atencao"
    assert obs[0]["texto"].startswith("3 produtos venderam")
    assert obs[0]["pergunta"] == "Quais produtos não venderam em março de 2024?"
    assert obs[1]["texto"] == "Loja respondeu por 60% do faturamento."


def test_resumo_texto_explica_origem_da_variacao():
    texto = gerar_resumo_texto(
        ano=2024, mes=3,
        kpi_atual=kpi(1200.0, 12), kpi_anterior=kpi(1000.0, 10),
        categorias=[{"nome": "Calçados", "valor": 600, "pct": 50.0}],
        top_produtos=[{"nome": "Tênis", "valor": 400.0, "pct": 33.3, "variacao_pct": None}],
    )
    assert texto[0].startswith("Em março de 2024, a loja faturou R$ 1.200,00 em 12 vendas")
    assert "20% acima de fevereiro" in texto[0]
    assert "Calçados" in texto[1] and "Tênis" in texto[1]
    assert texto[2] == "A alta veio principalmente do número de vendas."


def test_resumo_texto_sem_vendas():
    texto = gerar_resumo_texto(
        ano=2019, mes=3, kpi_atual=kpi(0, 0), kpi_anterior=kpi(0, 0),
        categorias=[], top_produtos=[],
    )
    assert texto == ["Não houve vendas registradas em março de 2019."]
