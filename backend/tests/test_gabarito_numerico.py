"""Gabarito NUMÉRICO independente das 14 consultas (parecer banca final, F02).

Executa `scripts/gabarito_numerico.py` contra o banco apontado por DATABASE_URL
e exige que TODAS as provas passem no nível numérico. A verdade esperada é
recomputada em Python puro a partir da geração determinística do seed; o obtido
vem dos templates SQL reais. Ver o cabeçalho do script para o método.

Pré-requisito: banco semeado com `database/seed.py` (empresa demo completa).
Se a base não estiver semeada, o teste é PULADO com instrução — não falha.
"""
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="precisa de DATABASE_URL apontando para um banco semeado (ver README)",
)


def _base_semeada(dsn) -> bool:
    import psycopg
    from scripts.gabarito_numerico import EMPRESA
    with psycopg.connect(dsn, prepare_threshold=None) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from fato_item_venda where empresa_id=%s", (EMPRESA,))
        return cur.fetchone()[0] == 8941


def test_gabarito_numerico_14_consultas():
    from scripts.gabarito_numerico import executar

    dsn = os.environ["DATABASE_URL"]
    if not _base_semeada(dsn):
        pytest.skip("empresa demo não semeada (8.941 itens). Rode: python database/seed.py")

    res = executar(dsn)
    falhas = [f"{r.pid} {r.intencao}: {r.detalhe}" for r in res if not r.numerico]
    assert not falhas, "provas numéricas falharam:\n" + "\n".join(falhas)
    # garante que a cobertura não encolheu silenciosamente
    assert len(res) >= 19, f"esperava >= 19 provas, havia {len(res)}"
