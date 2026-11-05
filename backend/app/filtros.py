"""Filtros de detalhe: produto, categoria, vendedor, cliente, canal e forma de
pagamento citados na pergunta.

"Quantas botas de couro vendemos em 2026?" tem a mesma intenção de "quantas
unidades vendemos em 2026?"; muda só o recorte. O modelo já marca esse trecho
(entidades PRODUTO, CATEGORIA, CLIENTE, VENDEDOR, CANAL e PAGAMENTO, da cabeça
de tags), mas os templates só filtravam por período, então o detalhe se perdia
e a resposta saía para a loja inteira.

Aqui o trecho vira um valor que EXISTE no dataset consultado: o catálogo
(nomes de produto, categorias, vendedores, clientes, canais e formas de
pagamento dessa empresa) é comparado com a pergunta. É a mesma divisão de
trabalho do adaptador_modelo.py: o modelo diz o QUE a pessoa quer e onde está
o detalhe; a resolução contra os dados é determinística. Comparar com o
catálogo também resolve o que o modelo não tem como saber sozinho: "botas de
couro" é o produto "Bota couro" desta loja.

Segurança: o valor resolvido é sempre um texto copiado do próprio banco e vai
para o SQL como parâmetro (%(produto)s), nunca concatenado.
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from dataclasses import dataclass, field

import psycopg

from app.models import Interpretacao

# Chaves de filtro em Interpretacao.entidades, na ordem em que aparecem no título.
FILTROS = ("produto", "categoria", "vendedor", "cliente", "canal", "forma_pagamento")

# Produto e categoria recortam a mesma dimensão: quem cita um novo substitui os dois.
GRUPOS = {"produto": "item", "categoria": "item"}

# Entidade do modelo (tag BIO) -> filtro.
_ENTIDADE_DO_MODELO = {
    "PRODUTO": "produto",
    "CATEGORIA": "categoria",
    "VENDEDOR": "vendedor",
    "CLIENTE": "cliente",
    "CANAL": "canal",
    "PAGAMENTO": "forma_pagamento",
}

_PALAVRAS_VAZIAS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "em", "no", "na",
    "nos", "nas", "com", "para", "por", "pelo", "pela", "um", "uma", "ao", "aos",
}

# Palavras do próprio vocabulário de vendas que não podem, sozinhas, apontar
# um item do catálogo (um produto chamado "Kit vendas" não deve casar com
# "quantas vendas").
_NUNCA_SOZINHA = {
    "venda", "vendi", "vendeu", "vendemo", "produto", "item", "total", "mai",
    "ano", "me", "mes", "dia", "semana", "loja", "valor", "quanto", "quanta",
    "qual", "quai", "kit", "categoria", "cliente", "vendedor", "canal",
}

# Canal e pagamento: sinônimos do jeito que se fala, por valor normalizado do
# banco. Valores que não estão aqui (planilhas importadas) casam pelo próprio nome.
_SINONIMOS = {
    "canal": {
        "loja": ["loja fisica", "loja"],
        "site": ["site", "ecommerce", "e commerce", "loja online", "internet"],
        "whatsapp": ["whatsapp", "whats", "zap"],
        "marketplace": ["marketplace", "mercado livre", "shopee"],
    },
    "forma_pagamento": {
        "pix": ["pix"],
        "cartao_credito": ["cartao de credito", "credito"],
        "cartao_debito": ["cartao de debito", "debito"],
        "dinheiro": ["dinheiro", "especie"],
        "boleto": ["boleto"],
    },
}

# Uma palavra comum que só vale como canal/pagamento depois de uma dessas
# ("na loja", "pelo site", "em dinheiro"). "Quanto dinheiro entrou" ou "a loja
# faturou" não filtram nada.
_AMBIGUAS = {"loja", "site", "dinheiro", "internet", "app"}
_PISTAS = {"no", "na", "nos", "nas", "pelo", "pela", "pelos", "pelas", "via", "em", "canal", "com"}


def sem_acento(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def palavras(texto: str) -> list[str]:
    """Minúsculas, sem acento, só letras e números: 'Botas de couro?' -> ['botas','de','couro']."""
    return re.findall(r"[a-z0-9]+", sem_acento(texto.lower()))


def _singular(p: str) -> str:
    # Plural simples do português: botas -> bota, óculos -> oculo (dos dois
    # lados da comparação, então "Óculos" do banco e "óculos" da frase batem).
    return p[:-1] if len(p) > 3 and p.endswith("s") else p


def chaves(texto: str) -> list[str]:
    """Palavras com conteúdo, no singular: 'Cinto de couro' -> ['cinto', 'couro']."""
    return [_singular(p) for p in palavras(texto) if p not in _PALAVRAS_VAZIAS]


@dataclass
class Item:
    valor: str  # exatamente como está no banco
    chaves: tuple[str, ...]


@dataclass
class Catalogo:
    produto: list[Item] = field(default_factory=list)
    categoria: list[Item] = field(default_factory=list)
    vendedor: list[Item] = field(default_factory=list)
    cliente: list[Item] = field(default_factory=list)
    canal: list[str] = field(default_factory=list)
    forma_pagamento: list[str] = field(default_factory=list)


_CONSULTAS_CATALOGO = {
    "produto": "select distinct nome from dim_produto where empresa_id = %s",
    "categoria": "select distinct categoria from dim_produto where empresa_id = %s and categoria is not null",
    "vendedor": "select distinct nome from dim_vendedor where empresa_id = %s",
    "cliente": "select distinct nome from dim_cliente where empresa_id = %s",
    "canal": "select distinct canal from fato_item_venda where empresa_id = %s and canal is not null",
    "forma_pagamento": (
        "select distinct forma_pagamento from fato_item_venda "
        "where empresa_id = %s and forma_pagamento is not null"
    ),
}

# Cache por empresa: o catálogo muda só quando uma planilha é importada, e
# cada importação cria uma empresa nova. 10 minutos cobre a base demo editada.
_CACHE: dict[str, tuple[float, Catalogo]] = {}
_TRAVA = threading.Lock()
_VALIDADE = 600.0


def carregar_catalogo(conn: psycopg.Connection, empresa_id: str) -> Catalogo:
    agora = time.monotonic()
    with _TRAVA:
        em_cache = _CACHE.get(empresa_id)
    if em_cache and agora - em_cache[0] < _VALIDADE:
        return em_cache[1]

    cat = Catalogo()
    with conn.cursor() as cur:
        for dim, sql in _CONSULTAS_CATALOGO.items():
            cur.execute(sql, (empresa_id,))
            valores = [str(v) for (v,) in cur.fetchall() if v]
            if dim in ("canal", "forma_pagamento"):
                setattr(cat, dim, valores)
            else:
                setattr(cat, dim, [Item(v, tuple(chaves(v))) for v in valores if chaves(v)])
    with _TRAVA:
        _CACHE[empresa_id] = (agora, cat)
    return cat


# ---------------------------------------------------------------- casamento --

def _melhor_item(itens: list[Item], alvo: list[str], *, so_nome_completo: bool = False,
                 primeira_palavra: str | None = None) -> str | None:
    """Item do catálogo que a frase cita.

    Pontuação = quantas palavras do nome aparecem na frase; a primeira palavra
    do nome (o "núcleo": bota, cinto, caixa) tem de estar entre elas. Vence o
    maior número de palavras; empate é ambíguo e não filtra (melhor responder
    sem recorte do que com o recorte errado). Uma palavra só vale quando o
    núcleo é único no catálogo ("botas" -> Bota couro; "kit" é de vários).
    """
    presentes = set(alvo)
    candidatos: list[tuple[int, float, str]] = []
    for item in itens:
        nucleo = item.chaves[0]
        if nucleo not in presentes:
            continue
        acertos = sum(1 for c in item.chaves if c in presentes)
        if so_nome_completo and acertos < len(item.chaves):
            continue
        if acertos == 1 and len(item.chaves) > 1:
            # só o núcleo: precisa ser único e não ser palavra do domínio
            if nucleo in _NUNCA_SOZINHA or len(nucleo) < 4:
                continue
            if sum(1 for o in itens if o.chaves[0] == nucleo) > 1:
                continue
        if len(item.chaves) == 1 and (nucleo in _NUNCA_SOZINHA or len(nucleo) < 3):
            continue
        if primeira_palavra and len(item.chaves) == 1 and primeira_palavra == nucleo:
            # "Beleza, e em 2025?": a interjeição não é a categoria Beleza
            continue
        candidatos.append((acertos, acertos / len(item.chaves), item.valor))
    if not candidatos:
        return None
    candidatos.sort(reverse=True)
    if len(candidatos) > 1 and candidatos[0][:2] == candidatos[1][:2]:
        return None
    return candidatos[0][2]


def _contem_sequencia(alvo: list[str], seq: list[str]) -> int:
    """Posição onde `seq` aparece seguida em `alvo`, ou -1."""
    n = len(seq)
    for i in range(len(alvo) - n + 1):
        if alvo[i:i + n] == seq:
            return i
    return -1


def _valor_fixo(dim: str, valores: list[str], alvo: list[str]) -> str | None:
    """Canal ou forma de pagamento citado (com sinônimos e a regra das pistas)."""
    sinonimos = _SINONIMOS.get(dim, {})
    achados: list[tuple[int, str]] = []
    for valor in valores:
        chave = "_".join(palavras(valor))
        formas = sinonimos.get(chave) or [" ".join(palavras(valor.replace("_", " ")))]
        for forma in formas:
            seq = [_singular(p) for p in forma.split()]
            pos = _contem_sequencia(alvo, seq)
            if pos < 0:
                continue
            if len(seq) == 1 and seq[0] in _AMBIGUAS and (pos == 0 or alvo[pos - 1] not in _PISTAS):
                continue
            achados.append((len(seq), valor))
            break
    if not achados:
        return None
    achados.sort(reverse=True)
    if len(achados) > 1 and achados[0][0] == achados[1][0]:
        return None
    return achados[0][1]


def extrair_filtros(texto: str, catalogo: Catalogo, entidades_modelo: dict | None = None) -> dict[str, str]:
    """Filtros que a pergunta cita, já com o valor exato do banco."""
    # Para canal/pagamento a ordem e as palavras vazias importam ("na loja").
    alvo_seq = [_singular(p) for p in palavras(texto)]
    alvo = chaves(texto)
    filtros: dict[str, str] = {}

    # 1º o trecho que o modelo marcou; se ele não marcou ou não casou, a frase toda.
    trechos: dict[str, list[str]] = {}
    for tipo, valor in (entidades_modelo or {}).items():
        dim = _ENTIDADE_DO_MODELO.get(tipo)
        if not dim:
            continue
        for v in valor if isinstance(valor, list) else [valor]:
            trechos.setdefault(dim, []).append(str(v))

    for dim in ("produto", "categoria", "vendedor", "cliente"):
        itens = getattr(catalogo, dim)
        achado = None
        for trecho in trechos.get(dim, []):
            achado = _melhor_item(itens, chaves(trecho))
            if achado:
                break
        if not achado:
            achado = _melhor_item(
                itens, alvo,
                # cliente só pelo nome completo: os primeiros nomes se repetem
                # entre clientes e vendedores ("Amanda").
                so_nome_completo=(dim == "cliente"),
                primeira_palavra=alvo_seq[0] if dim == "categoria" and alvo_seq else None,
            )
        if achado:
            filtros[dim] = achado

    # Um nome que casou como vendedor não é também cliente.
    if "cliente" in filtros and filtros.get("vendedor") == filtros["cliente"]:
        del filtros["cliente"]

    for dim in ("canal", "forma_pagamento"):
        achado = _valor_fixo(dim, getattr(catalogo, dim), alvo_seq)
        if achado:
            filtros[dim] = achado

    return filtros


def aplicar_filtros(interp: Interpretacao, texto: str, catalogo: Catalogo) -> Interpretacao:
    """Acrescenta à interpretação os filtros citados na pergunta."""
    filtros = extrair_filtros(texto, catalogo, interp.entidades_modelo)
    if not filtros:
        return interp
    return interp.model_copy(update={"entidades": {**interp.entidades, **filtros}})


def descrever(entidades: dict, intencao: str | None = None) -> str:
    """'Bota couro · canal Site' — o recorte, para o título da resposta."""
    partes = []
    for dim in FILTROS:
        v = entidades.get(dim)
        if not v:
            continue
        if dim == "produto":
            partes.append(str(v))
        elif dim == "categoria":
            partes.append(f"categoria {v}")
        elif dim == "vendedor":
            # "Desempenho do vendedor · Fernanda Dias" (sem repetir "vendedor")
            partes.append(str(v) if intencao == "desempenho_vendedor" else f"vendedor(a) {v}")
        elif dim == "cliente":
            partes.append(f"cliente {v}")
        elif dim == "canal":
            partes.append(f"canal {'WhatsApp' if v.lower() == 'whatsapp' else v.capitalize()}")
        else:
            nomes = {"pix": "Pix", "cartao_credito": "cartão de crédito",
                     "cartao_debito": "cartão de débito", "dinheiro": "dinheiro", "boleto": "boleto"}
            partes.append(f"pagamento em {nomes.get(v, v)}")
    return " · ".join(partes)
