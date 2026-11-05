"""Ano de referência por dataset (app/periodo_dataset.py): perguntas sem ano
explícito deslocam o período do ANO_PADRAO para o ano do dataset. Sem banco."""

from app.models import Interpretacao
from app.nlu.regras import ANO_PADRAO
from app.periodo_dataset import ajustar_periodo, tem_ano_explicito


def _interp(entidades: dict) -> Interpretacao:
    return Interpretacao(
        intencao="total_vendas_periodo", confianca=0.9,
        entidades=entidades, texto_original="x",
    )


def test_desloca_o_ano_para_o_do_dataset():
    i = _interp({"periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31"})
    out = ajustar_periodo(i, 2026)
    assert out.entidades["periodo_inicio"] == "2026-03-01"
    assert out.entidades["periodo_fim"] == "2026-03-31"


def test_desloca_os_dois_periodos_de_uma_comparacao():
    i = _interp({
        "periodo_a_inicio": "2024-03-01", "periodo_a_fim": "2024-03-31",
        "periodo_b_inicio": "2024-04-01", "periodo_b_fim": "2024-04-30",
    })
    out = ajustar_periodo(i, 2025)
    assert out.entidades["periodo_a_inicio"] == "2025-03-01"
    assert out.entidades["periodo_b_fim"] == "2025-04-30"


def test_nao_desloca_quando_ano_ref_e_o_padrao():
    i = _interp({"periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31"})
    out = ajustar_periodo(i, ANO_PADRAO)
    assert out.entidades["periodo_inicio"] == "2024-03-01"


def test_clampa_29_de_fevereiro_em_ano_nao_bissexto():
    # 2024 é bissexto (29/02); 2025 não é -> 28/02
    i = _interp({"periodo_inicio": "2024-02-01", "periodo_fim": "2024-02-29"})
    out = ajustar_periodo(i, 2025)
    assert out.entidades["periodo_fim"] == "2025-02-28"


def test_nao_mexe_em_periodo_de_outro_ano():
    # período que não é do ANO_PADRAO (usuário citou 2023) fica como está
    i = _interp({"periodo_inicio": "2023-03-01", "periodo_fim": "2023-03-31"})
    out = ajustar_periodo(i, 2026)
    assert out.entidades["periodo_inicio"] == "2023-03-01"


def test_tem_ano_explicito():
    assert tem_ano_explicito("quanto faturei em 2026")
    assert not tem_ano_explicito("quanto faturei esse ano")
