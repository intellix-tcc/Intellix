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


def _resolver_entidades(intencao: str, texto: str, entidades_modelo: dict) -> dict:
    # ---- intenções de DOIS períodos ----------------------------------
    if intencao in _DOIS_PERIODOS:
        meses = _meses_em_ordem(texto)
        ano_m = re.search(r"\b(20\d{2})\b", texto)
        ano = int(ano_m.group(1)) if ano_m else R.ANO_PADRAO
        if len(meses) < 2:
            return {}  # falha segura -> executor devolve 422 parametro_faltando
        a_ini, a_fim = R._periodo_do_mes(meses[0], ano)
        b_ini, b_fim = R._periodo_do_mes(meses[1], ano)
        k = _DOIS_PERIODOS[intencao]
        # 1o mês citado = período A / atual; 2o = período B / anterior.
        # (ver AVISO no chat: a ordem de variacao_periodo precisa de decisão
        #  do time — confirme com exemplos reais do modelo.)
        return {k[0]: a_ini, k[1]: a_fim, k[2]: b_ini, k[3]: b_fim}

    # ---- intenções de UM período -------------------------------------
    entidades = R._extrai_periodo(texto, ano_completo_se_ausente=True)

    if intencao in _COM_LIMITE:
        entidades["limite"] = R._extrai_limite(texto)

    if intencao == "desempenho_vendedor":
        nome = _nome_vendedor(entidades_modelo)
        if nome:
            # templates.py espera o % do ILIKE já montado pela NLU
            entidades["vendedor_nome"] = f"%{nome}%"

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

        entidades = _resolver_entidades(r["intencao"], texto.lower(), r["entidades"])
        return Interpretacao(
            intencao=r["intencao"],
            confianca=r["confianca"],
            entidades=entidades,
            texto_original=texto,
        )
