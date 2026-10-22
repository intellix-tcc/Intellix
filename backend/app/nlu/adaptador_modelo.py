"""Adaptador que pluga o modelo treinado no contrato NLUService (base.py).

Divisão de trabalho:
  - o MODELO (ModeloIntellix.prever) decide a INTENÇÃO — é o forte dele,
    cobre as 12 intenções (o RuleBasedNLU só cobre 3);
  - as REGRAS determinísticas (reaproveitadas de regras.py) RESOLVEM os
    slots que os templates exigem (mês -> datas ISO, limite, vendedor_nome).

Por que resolver slot com regra e não com as entidades cruas do modelo?
Porque "março -> 2024-03-01..2024-03-31" é determinístico e o regras.py já
faz certo; o BIO tagging do modelo (F1 ~0.85) é mais ruidoso. Assim o
Interpretacao continua idêntico ao contrato (docs/contratos.md, seção 1) —
nada muda para quem consome a NLU.

Falha segura: quando não dá para resolver os obrigatórios (ex.: uma
comparação sem dois meses claros), devolve entidades incompletas de
propósito — o executor.py responde 422 "parametro_faltando" e o usuário é
convidado a reformular, em vez de rodar um SQL errado.
"""

import os
import re

from app.models import Interpretacao
from app.nlu import regras as R
from app.nlu.modelo_nlu import ModeloIntellix

# Intenções que exigem DOIS períodos, e os nomes de parâmetro de cada uma
# (conferidos contra os "obrigatorios" em sql/templates.py).
_DOIS_PERIODOS = {
    "comparacao_periodos": (
        "periodo_a_inicio", "periodo_a_fim",
        "periodo_b_inicio", "periodo_b_fim",
    ),
    "variacao_periodo": (
        "periodo_atual_inicio", "periodo_atual_fim",
        "periodo_anterior_inicio", "periodo_anterior_fim",
    ),
}

_COM_LIMITE = {"top_produtos", "top_clientes"}


def _meses_em_ordem(texto: str) -> list[int]:
    """Todos os meses citados, na ordem em que aparecem no texto."""
    achados = []
    for nome_mes, numero_mes in R.MESES.items():
        for m in re.finditer(rf"\b{nome_mes}\b", texto):
            achados.append((m.start(), numero_mes))
    achados.sort()
    # remove repetição do mesmo mês (ex.: citado duas vezes)
    vistos, ordenados = set(), []
    for _, num in achados:
        if num not in vistos:
            vistos.add(num)
            ordenados.append(num)
    return ordenados


def _nome_vendedor(entidades_modelo: dict) -> str | None:
    v = entidades_modelo.get("VENDEDOR")
    if isinstance(v, list):
        v = v[0] if v else None
    return v


# ---- item 4: resolução de DOIS períodos (relativos, anos, trimestres) -------
# O modelo acerta a intenção (comparacao_periodos / variacao_periodo), mas os
# templates exigem quatro datas ISO. Antes só resolvíamos quando a frase citava
# dois meses por extenso; "mês anterior", "ano passado", "esse mês", trimestres
# e comparação entre anos ("2023 com 2024") ficavam sem resolução e viravam 422
# (variacao_periodo caiu 0/7 na API). Aqui cobrimos essas formas.

def _anos_distintos(texto: str) -> list[int]:
    """Anos de 4 dígitos citados, sem repetir, na ordem em que aparecem."""
    vistos, ordem = set(), []
    for m in re.finditer(r"\b(20\d{2})\b", texto):
        ano = int(m.group(1))
        if ano not in vistos:
            vistos.add(ano)
            ordem.append(ano)
    return ordem


def _trimestres(texto: str) -> list[int]:
    """Números de trimestre (1..4) citados. 'primeiro trimestre com o segundo'
    -> [1, 2] (o 'segundo' aparece com o 'trimestre' elíptico)."""
    if "trimestre" not in texto:
        return []
    achados = []
    for palavra, n in (("primeiro", 1), ("segundo", 2), ("terceiro", 3), ("quarto", 4)):
        for m in re.finditer(rf"\b{palavra}\b", texto):
            achados.append((m.start(), n))
    for m in re.finditer(r"\b([1-4])[ºo]?\s*trimestre", texto):
        achados.append((m.start(), int(m.group(1))))
    achados.sort()
    vistos, ordenados = set(), []
    for _, n in achados:
        if n not in vistos:
            vistos.add(n)
            ordenados.append(n)
    return ordenados


def _ordenar(p: tuple[str, str], q: tuple[str, str]) -> tuple[str, str, str, str]:
    """Ordena dois períodos por data: o mais recente vira 'atual'/A, o mais
    antigo vira 'anterior'/B. Para variacao_periodo a variação fica no sentido
    anterior -> atual; para comparacao_periodos a ordem de A/B é apenas visual."""
    atual, anterior = (p, q) if p[0] >= q[0] else (q, p)
    return (atual[0], atual[1], anterior[0], anterior[1])


def _dois_periodos(texto: str) -> tuple[str, str, str, str] | None:
    """Resolve (atual_inicio, atual_fim, anterior_inicio, anterior_fim) ou None
    quando a frase não dá para montar dois períodos (falha segura -> 422)."""
    ano_m = re.search(r"\b(20\d{2})\b", texto)
    ano = int(ano_m.group(1)) if ano_m else R.ANO_PADRAO

    # 1) dois anos distintos: "2023 comparado com 2024"
    anos = _anos_distintos(texto)
    if len(anos) >= 2:
        return _ordenar(R._ano_inteiro(anos[0]), R._ano_inteiro(anos[1]))

    # 2) dois meses por extenso: "março com abril", "janeiro versus fevereiro"
    meses = _meses_em_ordem(texto)
    if len(meses) >= 2:
        return _ordenar(R._periodo_do_mes(meses[0], ano), R._periodo_do_mes(meses[1], ano))

    # 3) dois trimestres: "primeiro trimestre com o segundo"
    tris = _trimestres(texto)
    if len(tris) >= 2:
        return _ordenar(R._trimestre(tris[0], ano), R._trimestre(tris[1], ano))

    # 4) mês relativo: "esse mês com o mês passado", "em relação ao mês anterior"
    if re.search(r"\bm[eê]s\s+(passad|anterior)", texto) or "último mês" in texto or "ultimo mes" in texto:
        return _ordenar(R._mes_relativo(0), R._mes_relativo(-1))

    # 5) ano relativo: "em relação ao ano passado", "variação ... esse ano"
    if re.search(r"\bano\s+(passad|anterior)", texto) or re.search(r"\b(es[st]e|des[st]e)\s+ano\b", texto):
        return _ordenar(R._ano_inteiro(R.ANO_PADRAO - 1), R._ano_inteiro(R.ANO_PADRAO))

    # 6) trimestres genéricos: "variação de vendas entre os trimestres"
    if "trimestre" in texto:
        return _ordenar(R._trimestre(3, R.ANO_PADRAO), R._trimestre(4, R.ANO_PADRAO))

    # 7) um único mês por extenso: "crescimento em março de 2024" -> mês vs anterior
    if len(meses) == 1:
        atual = R._periodo_do_mes(meses[0], ano)
        anterior_mes = meses[0] - 1 or 12
        anterior_ano = ano if meses[0] > 1 else ano - 1
        return _ordenar(R._periodo_do_mes(anterior_mes, anterior_ano), atual)

    return None


# ---- item 6: filtro de domínio antes de aceitar a classificação -------------
# Um classificador fechado em 12 classes sempre escolhe uma delas, e às vezes
# com confiança alta ("capital da França" saiu como variacao_periodo a 0,92).
# Exigimos ao menos um termo do domínio (venda, faturamento, produto...) antes
# de aceitar — o mesmo efeito que já protege o baseline de regras.
_TERMOS_DOMINIO = re.compile(
    r"vend|fatur|produt|client|ticket|receita|pedid|categoria|"
    r"canai|canal|pagament|pix|cart[aã]o|boleto|dinheiro|d[eé]bito|cr[eé]dito|"
    r"estoque|encalhad|parad|sa[ií]da|giro|compr|gast|loja|lucr|desempenho|"
    r"per[ií]odo|varia[cç]|cresc|unidad|transa[cç]|nota",
    re.IGNORECASE,
)


def _tem_termo_dominio(texto: str) -> bool:
    return bool(_TERMOS_DOMINIO.search(texto))


# ---- item 5: vendedor sem nome em perguntas de ranking/agregadas ------------
# "Quem vendeu mais?" não traz nome, mas pede o ranking de todos; já "Como foi o
# desempenho do vendedor?" (singular, sem nome) é ambíguo e deve pedir o nome.
_SINAIS_TODOS_VENDEDORES = re.compile(
    r"\bquem\b|\bmelhor(es)?\b|\bmais\b|\branking\b|\btop\b|\btodos\b|"
    r"\bcada\b|\btime\b|\bequipe\b|vendedores|\bdestaque\b|\bcampe",
    re.IGNORECASE,
)


def _pede_todos_vendedores(texto: str) -> bool:
    return bool(_SINAIS_TODOS_VENDEDORES.search(texto))


def _resolver_entidades(intencao: str, texto: str, entidades_modelo: dict) -> dict:
    # ---- intenções de DOIS períodos ----------------------------------
    if intencao in _DOIS_PERIODOS:
        par = _dois_periodos(texto)
        if par is None:
            return {}  # falha segura -> executor devolve 422 parametro_faltando
        k = _DOIS_PERIODOS[intencao]
        return {k[0]: par[0], k[1]: par[1], k[2]: par[2], k[3]: par[3]}

    # ---- intenções de UM período -------------------------------------
    entidades = R._extrai_periodo(texto, ano_completo_se_ausente=True)

    if intencao in _COM_LIMITE:
        entidades["limite"] = R._extrai_limite(texto)

    if intencao == "desempenho_vendedor":
        nome = _nome_vendedor(entidades_modelo)
        if nome:
            # templates.py espera o % do ILIKE já montado pela NLU
            entidades["vendedor_nome"] = f"%{nome}%"
        elif _pede_todos_vendedores(texto):
            # sem nome, mas pergunta por ranking/todos -> lista todos (ILIKE '%')
            entidades["vendedor_nome"] = "%"
        # senão: sem vendedor_nome -> executor pede o nome (422 parametro_faltando)

    return entidades


class ModeloTreinadoNLU:
    """Implementa NLUService (base.py) usando o .pt treinado."""

    def __init__(self, caminho_pt: str | None = None):
        if caminho_pt is None:
            base = os.path.dirname(__file__)
            caminho_pt = os.path.join(base, "intellix_nlu_v1.0.0.pt")
        self._modelo = ModeloIntellix(caminho_pt)

    def parse(self, texto: str) -> Interpretacao:
        r = self._modelo.prever(texto)

        # fallback do modelo (baixa confiança) ou nada reconhecido:
        # devolve confiança baixa e deixa o verificar_confianca/executor cuidarem.
        if r["fallback"] or r["intencao"] is None:
            return Interpretacao(
                intencao=r["intencao"],
                confianca=r["confianca"],
                entidades={},
                texto_original=texto,
            )

        # item 6: mesmo confiante, rejeita se a frase não tem termo do domínio.
        # O executor/verificar_confianca tratam como baixa_confianca (422).
        if not _tem_termo_dominio(texto):
            return Interpretacao(
                intencao=None,
                confianca=0.0,
                entidades={},
                texto_original=texto,
            )

        entidades = _resolver_entidades(r["intencao"], texto.lower(), r["entidades"])
        return Interpretacao(
            intencao=r["intencao"],
            confianca=r["confianca"],
            entidades=entidades,
            texto_original=texto,
        )
