"""Data de referência ("hoje") do /chat: períodos relativos partem da data
atual, limitada à última venda do dataset. Sem banco."""

from datetime import date

from app.nlu import regras as R
from app.nlu.adaptador_modelo import _dois_periodos, _periodo_relativo
from app.periodo_dataset import referencia_do_dataset, tem_ano_explicito

HOJE = date(2026, 11, 5)


def test_referencia_e_hoje_quando_os_dados_vao_ate_depois():
    assert referencia_do_dataset(date(2026, 12, 31), HOJE) == HOJE


def test_referencia_e_a_ultima_venda_numa_planilha_antiga():
    assert referencia_do_dataset(date(2025, 6, 30), HOJE) == date(2025, 6, 30)


def test_dataset_vazio_usa_a_referencia_fixa():
    assert referencia_do_dataset(None, HOJE) == R.DATA_REFERENCIA


def test_ano_passado_e_mes_passado_partem_de_hoje():
    with R.usar_referencia(HOJE):
        assert _periodo_relativo("quanto vendi no ano passado") == {
            "periodo_inicio": "2025-01-01", "periodo_fim": "2025-12-31"}
        assert _periodo_relativo("quanto vendi no mês passado") == {
            "periodo_inicio": "2026-10-01", "periodo_fim": "2026-10-31"}
        assert _periodo_relativo("e esse mês?") == {
            "periodo_inicio": "2026-11-01", "periodo_fim": "2026-11-30"}


def test_ultimo_trimestre_e_o_ultimo_completo():
    with R.usar_referencia(HOJE):  # novembro: o 4º trimestre está em andamento
        assert _periodo_relativo("no último trimestre") == {
            "periodo_inicio": "2026-07-01", "periodo_fim": "2026-09-30"}
    with R.usar_referencia(date(2026, 2, 10)):  # vira o ano
        assert _periodo_relativo("no último trimestre")["periodo_inicio"] == "2025-10-01"


def test_mes_e_esse_ano_sem_ano_citado_ficam_no_ano_de_hoje():
    with R.usar_referencia(HOJE):
        assert R._extrai_periodo("quanto faturei em março")["periodo_inicio"] == "2026-03-01"
        assert R._extrai_periodo("quanto faturei", ano_completo_se_ausente=True)["periodo_inicio"] == "2026-01-01"


def test_comparacao_com_o_ano_passado_parte_de_hoje():
    with R.usar_referencia(HOJE):
        atual_ini, _, anterior_ini, _ = _dois_periodos("quanto cresci em relação ao ano passado")
        assert (atual_ini, anterior_ini) == ("2026-01-01", "2025-01-01")
        atual_ini, _, anterior_ini, _ = _dois_periodos("compare esse mês com o mês passado")
        assert (atual_ini, anterior_ini) == ("2026-11-01", "2026-10-01")


def test_ano_citado_vale_sempre():
    with R.usar_referencia(HOJE):
        assert R._extrai_periodo("quanto faturei em março de 2024")["periodo_inicio"] == "2024-03-01"


def test_referencia_volta_ao_padrao_fora_do_bloco():
    with R.usar_referencia(HOJE):
        pass
    assert R.referencia() == R.DATA_REFERENCIA


def test_tem_ano_explicito():
    assert tem_ano_explicito("quanto faturei em 2026")
    assert not tem_ano_explicito("quanto faturei esse ano")
