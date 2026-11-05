"""Evolução mensal das respostas de um mês só (app/sql/evolucao.py)."""

from app.sql.evolucao import mes_unico, meses_ate, preencher


def test_mes_unico_reconhece_mes_inteiro():
    assert mes_unico({"periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31"}) == (2024, 3)
    assert mes_unico({"periodo_inicio": "2024-02-01", "periodo_fim": "2024-02-29"}) == (2024, 2)


def test_mes_unico_recusa_ano_trimestre_e_faltando():
    assert mes_unico({"periodo_inicio": "2024-01-01", "periodo_fim": "2024-12-31"}) is None
    assert mes_unico({"periodo_inicio": "2024-01-01", "periodo_fim": "2024-03-31"}) is None
    assert mes_unico({"periodo_inicio": "2024-03-05", "periodo_fim": "2024-03-31"}) is None
    assert mes_unico({}) is None


def test_meses_ate_atravessa_o_ano():
    rotulos = meses_ate(2026, 3)
    assert len(rotulos) == 12
    assert rotulos[0] == "2025-04"
    assert rotulos[-1] == "2026-03"


def test_preencher_coloca_zero_nos_meses_sem_venda():
    assert preencher(["2024-01", "2024-02"], {"2024-02": 10.5}) == [["2024-01", 0.0], ["2024-02", 10.5]]
