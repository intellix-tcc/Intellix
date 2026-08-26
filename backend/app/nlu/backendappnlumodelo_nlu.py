# -*- coding: utf-8 -*-
"""
modelo_nlu.py — Módulo de inferência do Intellix NLU (para o backend)

ISTO É TUDO QUE O BACKEND PRECISA para usar o modelo. Um arquivo só.

COMO USAR (no FastAPI, por exemplo):
------------------------------------
    from modelo_nlu import ModeloIntellix

    # carrega uma vez, quando a aplicação sobe (NÃO a cada requisição!)
    nlu = ModeloIntellix("intellix_nlu_v1.0.0.pt")

    # a cada pergunta do usuário:
    resultado = nlu.prever("quanto faturei em março")
    # -> {
    #      "intencao": "total_vendas_periodo",
    #      "confianca": 0.98,
    #      "entidades": {"PERIODO": "março"},
    #      "fallback": False
    #    }

    if resultado["fallback"]:
        responder("Não entendi bem. Pode reformular?")
    else:
        sql = montar_sql(resultado["intencao"], resultado["entidades"])

DEPENDÊNCIAS: só torch. (pip install torch)

⚠️ REGRA CRÍTICA: a função tokenizar() DESTE arquivo é IDÊNTICA à usada no
treino (gerar_dataset.py). Nunca altere uma sem alterar a outra. Se os dois
tokenizadores divergirem, o modelo funciona nos testes e falha em produção,
e é um bug que leva dias para achar. Idealmente, os dois deveriam importar
esta mesma função — mas mantemos uma cópia aqui para o backend não depender
do código de treino.
"""

import re
import unicodedata

import torch
import torch.nn as nn


# =============================================================================
# 1. TOKENIZADOR  (cópia EXATA do gerar_dataset.py — não divergir!)
# =============================================================================

_ABREVIACOES = {
    "qnt": "quanto", "qto": "quanto", "qtd": "quantidade",
    "qtas": "quantas", "qts": "quantos", "vlr": "valor",
    "tkt": "ticket", "fat": "faturamento", "pq": "porque",
    "vc": "você", "q": "que", "pra": "para", "pro": "para o",
}


def normalizar(texto: str) -> str:
    """Padroniza o texto. NÃO tira acento — acento importa em português."""
    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)
    texto = unicodedata.normalize("NFC", texto)
    palavras = [_ABREVIACOES.get(p, p) for p in texto.split()]
    return " ".join(palavras)


def tokenizar(texto: str) -> list:
    """Quebra a frase em tokens, separando pontuação.

        "quanto faturei em março?" -> ['quanto','faturei','em','março','?']
    """
    return re.findall(r"\w+|[^\w\s]", normalizar(texto), re.UNICODE)


# =============================================================================
# 2. A CLASSE DO MODELO  (idêntica à do treino)
# =============================================================================

class ModeloNLU(nn.Module):
    """Rede BiLSTM com duas cabeças: intenção (frase) e entidades (por token)."""

    def __init__(self, tam_vocab, n_intencoes=12, n_tags=19,
                 dim_emb=100, dim_oculta=128, dropout=0.3):
        super().__init__()
        self.emb = nn.Embedding(tam_vocab, dim_emb, padding_idx=0)
        self.lstm = nn.LSTM(dim_emb, dim_oculta, batch_first=True,
                            bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.cabeca_intencao = nn.Linear(dim_oculta * 2, n_intencoes)
        self.cabeca_tags = nn.Linear(dim_oculta * 2, n_tags)

    def forward(self, x):
        mascara = (x != 0).unsqueeze(-1).float()
        e = self.dropout(self.emb(x))
        saidas, _ = self.lstm(e)
        frase = (saidas * mascara).sum(1) / mascara.sum(1).clamp(min=1)
        frase = self.dropout(frase)
        return self.cabeca_intencao(frase), self.cabeca_tags(saidas)


# =============================================================================
# 3. O WRAPPER DE INFERÊNCIA  (é isto que o backend usa)
# =============================================================================

class ModeloIntellix:
    """Carrega o .pt e responde perguntas. Thread-safe para leitura."""

    def __init__(self, caminho_pt: str, limiar_confianca: float = 0.70):
        """
        caminho_pt: caminho do arquivo .pt salvo no treino
        limiar_confianca: abaixo disto, retorna fallback (seção 7.6 do doc)
        """
        # weights_only=False porque o pacote tem vocab e dicionários, não só pesos
        pacote = torch.load(caminho_pt, map_location="cpu", weights_only=False)

        self.vocab = pacote["vocab"]
        self.intent2id = pacote["intent2id"]
        self.tag2id = pacote["tag2id"]
        self.id2intent = {i: n for n, i in self.intent2id.items()}
        self.id2tag = {i: t for t, i in self.tag2id.items()}
        self.limiar = limiar_confianca
        self.versao = pacote.get("versao", "desconhecida")
        self.metricas = pacote.get("metricas", {})

        cfg = pacote["config"]
        self.modelo = ModeloNLU(
            tam_vocab=cfg["tam_vocab"],
            n_intencoes=cfg["n_intencoes"],
            n_tags=cfg["n_tags"],
            dim_emb=cfg["dim_emb"],
            dim_oculta=cfg["dim_oculta"],
            dropout=cfg["dropout"],
        )
        self.modelo.load_state_dict(pacote["state_dict"])
        self.modelo.eval()

    def _agrupar_entidades(self, tokens, tags):
        """Junta B-X I-X I-X num dicionário {TIPO: "texto"}.

        Se o mesmo tipo aparecer duas vezes (ex: dois períodos numa
        comparação), guarda como lista.
        """
        bruto = []
        atual, tipo = [], None
        for tok, tag in zip(tokens, tags):
            if tag.startswith("B-"):
                if atual:
                    bruto.append((tipo, " ".join(atual)))
                atual, tipo = [tok], tag[2:]
            elif tag.startswith("I-") and tipo == tag[2:]:
                atual.append(tok)
            else:
                if atual:
                    bruto.append((tipo, " ".join(atual)))
                atual, tipo = [], None
        if atual:
            bruto.append((tipo, " ".join(atual)))

        # monta o dicionário; vira lista quando o tipo se repete
        entidades = {}
        for tp, valor in bruto:
            if tp in entidades:
                if isinstance(entidades[tp], list):
                    entidades[tp].append(valor)
                else:
                    entidades[tp] = [entidades[tp], valor]
            else:
                entidades[tp] = valor
        return entidades

    def prever(self, pergunta: str) -> dict:
        """Recebe uma frase, devolve intenção + entidades + fallback."""
        tokens = tokenizar(pergunta)
        if not tokens:
            return {"intencao": None, "confianca": 0.0,
                    "entidades": {}, "fallback": True,
                    "motivo": "frase vazia"}

        x = torch.tensor([[self.vocab.get(t, self.vocab["<UNK>"]) for t in tokens]])
        with torch.no_grad():
            logits_i, logits_t = self.modelo(x)

        probs = torch.softmax(logits_i, dim=1)[0]
        conf, idx = probs.max(0)
        conf = conf.item()

        tags = [self.id2tag[i] for i in logits_t.argmax(-1)[0].tolist()]
        entidades = self._agrupar_entidades(tokens, tags)

        fallback = conf < self.limiar
        return {
            "intencao": self.id2intent[idx.item()],
            "confianca": round(conf, 4),
            "entidades": entidades,
            "fallback": fallback,
            "motivo": "baixa confiança" if fallback else None,
        }

    def prever_lote(self, perguntas: list) -> list:
        """Versão para várias perguntas de uma vez."""
        return [self.prever(p) for p in perguntas]


# =============================================================================
# 4. TESTE RÁPIDO — rode "python modelo_nlu.py caminho/do/modelo.pt"
# =============================================================================

if __name__ == "__main__":
    import sys
    caminho = sys.argv[1] if len(sys.argv) > 1 else "intellix_nlu_v1.0.0.pt"

    print(f"Carregando {caminho}...")
    nlu = ModeloIntellix(caminho)
    print(f"Versão do modelo: {nlu.versao}")
    print(f"Métricas: {nlu.metricas}\n")

    exemplos = [
        "quanto faturei em março",
        "quais os 5 produtos mais vendidos em abril",
        "o pix tá vendendo mais que o cartão?",
        "vendi mais em março ou em abril",
        "quanto o carlos vendeu esse mês",
        "qual a capital da França?",   # deve dar fallback
    ]
    for p in exemplos:
        r = nlu.prever(p)
        if r["fallback"]:
            print(f">> {p!r}\n   FALLBACK (conf {r['confianca']}) -> pedir reformulação\n")
        else:
            print(f">> {p!r}\n   intencao: {r['intencao']} (conf {r['confianca']})")
            print(f"   entidades: {r['entidades']}\n")
