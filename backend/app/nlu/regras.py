import calendar
import re
from datetime import date

from app.models import Interpretacao

# Ano de referencia dos dados de exemplo/seed. Quando o usuario nao
# menciona o ano ("quanto faturei em marco"), assumimos este.
ANO_PADRAO = 2024

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

CONFIANCA_MINIMA = 0.70


def _periodo_do_mes(mes: int, ano: int) -> tuple[str, str]:
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, 1).isoformat(), date(ano, mes, ultimo_dia).isoformat()


def _extrai_periodo(texto: str, ano_completo_se_ausente: bool = False) -> dict[str, str]:
    for nome_mes, numero_mes in MESES.items():
        if re.search(rf"\b{nome_mes}\b", texto):
            ano_encontrado = re.search(r"\b(20\d{2})\b", texto)
            ano = int(ano_encontrado.group(1)) if ano_encontrado else ANO_PADRAO
            inicio, fim = _periodo_do_mes(numero_mes, ano)
            return {"periodo_inicio": inicio, "periodo_fim": fim}

    ano_encontrado = re.search(r"\b(20\d{2})\b", texto)
    if ano_encontrado:
        ano = ano_encontrado.group(1)
        return {"periodo_inicio": f"{ano}-01-01", "periodo_fim": f"{ano}-12-31"}

    if ano_completo_se_ausente:
        return {"periodo_inicio": f"{ANO_PADRAO}-01-01", "periodo_fim": f"{ANO_PADRAO}-12-31"}

    return {}


def _extrai_limite(texto: str, padrao: int = 5) -> int:
    numero = re.search(r"\b(\d{1,2})\b", texto)
    return int(numero.group(1)) if numero else padrao


class RuleBasedNLU:
    """Baseline por regras (secao 7.4 do TCC). Sem dependencias externas,
    sem banco. Serve tanto de primeiro ponto do comparativo do capitulo 8
    quanto de seguro de vida: NLU_BACKEND=regras no painel do Render volta
    o sistema ao ar se o modelo treinado quebrar.
    """

    def parse(self, texto: str) -> Interpretacao:
        t = texto.lower().strip()

        if re.search(r"fatur|quanto vendi", t):
            entidades = _extrai_periodo(t)
            confianca = 0.93 if entidades else 0.60
            return Interpretacao(
                intencao="total_vendas_periodo",
                confianca=confianca,
                entidades=entidades,
                texto_original=texto,
            )

        if re.search(r"produtos? mais vendid|top\s*\d*\s*produtos", t):
            entidades = {"limite": _extrai_limite(t)}
            entidades.update(_extrai_periodo(t, ano_completo_se_ausente=True))
            return Interpretacao(
                intencao="top_produtos",
                confianca=0.90,
                entidades=entidades,
                texto_original=texto,
            )

        if "ticket" in t:
            entidades = _extrai_periodo(t, ano_completo_se_ausente=True)
            return Interpretacao(
                intencao="ticket_medio",
                confianca=0.85,
                entidades=entidades,
                texto_original=texto,
            )

        return Interpretacao(
            intencao=None,
            confianca=0.0,
            entidades={},
            texto_original=texto,
        )
