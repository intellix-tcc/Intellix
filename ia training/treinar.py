# -*- coding: utf-8 -*-
"""
treinar.py — treino LOCAL do NLU, reproduzindo o Intellix_NLU_Colab.ipynb sem
Google Drive nem upload manual. Serve para re-treinar na máquina (CPU) depois
de editar moldes.py e rodar gerar_dataset.py.

    python treinar.py                       # treina e salva v1.1.0 ao lado
    python treinar.py --saida modelo.pt     # caminho de saída
    python treinar.py --versao 1.1.0        # rótulo da versão

Para garantir que o treino usa EXATAMENTE a mesma rede e o mesmo tokenizador do
backend (regra crítica do projeto), importa ModeloNLU e tokenizar de
backend/app/nlu/modelo_nlu.py em vez de redefini-los aqui.

Hiperparâmetros idênticos ao notebook: Adam lr 1e-3, ALPHA 0.5, 40 épocas,
early stopping (paciência 6), batch 32, grad clip 5. Split 70/15/15
estratificado por intenção (semente 42), sem sklearn.
"""

import argparse
import copy
import json
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
# Mesma rede e mesmo tokenizador do backend -> paridade treino/inferência.
from app.nlu.modelo_nlu import ModeloNLU, tokenizar  # noqa: E402

SEMENTE = 42
ALPHA = 0.5          # peso entre intenção e entidades
EPOCAS = 40
PACIENCIA = 6
LR = 1e-3
BATCH = 32
IGNORAR = -100
DATASET = Path(__file__).resolve().parent / "dados" / "dataset.jsonl"
# Ordem das tags idêntica à do notebook (19 = O + B/I de 9 tipos).
TIPOS = ["PERIODO", "DATA", "PRODUTO", "CATEGORIA", "CLIENTE",
         "VENDEDOR", "CANAL", "PAGAMENTO", "NUMERO"]


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def split_estratificado(dados, prop_treino=0.70):
    """Split por intenção (mantém a proporção de cada classe), semente fixa."""
    rnd = random.Random(SEMENTE)
    por_intencao = {}
    for d in dados:
        por_intencao.setdefault(d["intencao"], []).append(d)
    treino, validacao = [], []
    for lista in por_intencao.values():
        rnd.shuffle(lista)
        corte = int(len(lista) * prop_treino)
        treino += lista[:corte]
        validacao += lista[corte:]
    rnd.shuffle(treino)
    rnd.shuffle(validacao)
    return treino, validacao


def construir_mapas(treino, dados):
    contagem = Counter(tok for ex in treino for tok in ex["tokens"])
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for palavra, n in contagem.most_common():
        if n >= 2:  # palavra que aparece 1x só vira <UNK>
            vocab[palavra] = len(vocab)
    intencoes = sorted({d["intencao"] for d in dados})
    intent2id = {nome: i for i, nome in enumerate(intencoes)}
    tag2id = {"O": 0}
    for t in TIPOS:
        tag2id[f"B-{t}"] = len(tag2id)
        tag2id[f"I-{t}"] = len(tag2id)
    assert len(intent2id) == 14 and len(tag2id) == 19
    return vocab, intent2id, tag2id


class DatasetNLU(Dataset):
    def __init__(self, exemplos, vocab, intent2id, tag2id):
        self.ex, self.vocab, self.intent2id, self.tag2id = exemplos, vocab, intent2id, tag2id

    def __len__(self):
        return len(self.ex)

    def __getitem__(self, i):
        ex = self.ex[i]
        ids_tokens = [self.vocab.get(t, self.vocab["<UNK>"]) for t in ex["tokens"]]
        ids_tags = [self.tag2id[t] for t in ex["tags"]]
        return ids_tokens, ids_tags, self.intent2id[ex["intencao"]]


def juntar_lote(lote):
    tokens, tags, intencoes = zip(*lote)
    maior = max(len(t) for t in tokens)
    x = [t + [0] * (maior - len(t)) for t in tokens]
    yt = [t + [IGNORAR] * (maior - len(t)) for t in tags]
    return torch.tensor(x), torch.tensor(yt), torch.tensor(intencoes)


def acuracia(modelo, loader, dispositivo):
    modelo.eval()
    certos = total = 0
    with torch.no_grad():
        for x, _, yi in loader:
            x, yi = x.to(dispositivo), yi.to(dispositivo)
            logits_i, _ = modelo(x)
            certos += (logits_i.argmax(1) == yi).sum().item()
            total += yi.size(0)
    return certos / total


def main():
    ap = argparse.ArgumentParser(description="Treino local do Intellix NLU.")
    ap.add_argument("--saida", default=None, help="caminho do .pt de saída")
    ap.add_argument("--versao", default="1.1.0")
    args = ap.parse_args()

    torch.manual_seed(SEMENTE)
    random.seed(SEMENTE)
    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"dispositivo: {dispositivo}")

    dados = carregar(DATASET)
    ruins = [d for d in dados if len(d["tokens"]) != len(d["tags"])]
    assert not ruins, f"{len(ruins)} exemplos com tokens/tags desalinhados!"
    treino, validacao = split_estratificado(dados)
    vocab, intent2id, tag2id = construir_mapas(treino, dados)
    print(f"treino={len(treino)} validacao={len(validacao)} vocab={len(vocab)}")

    def loader(d, embaralhar):
        return DataLoader(DatasetNLU(d, vocab, intent2id, tag2id), batch_size=BATCH,
                          shuffle=embaralhar, collate_fn=juntar_lote)
    loader_treino, loader_val = loader(treino, True), loader(validacao, False)

    modelo = ModeloNLU(len(vocab), n_intencoes=len(intent2id), n_tags=len(tag2id)).to(dispositivo)
    otimizador = torch.optim.Adam(modelo.parameters(), lr=LR)
    perda_int = nn.CrossEntropyLoss()
    perda_tags = nn.CrossEntropyLoss(ignore_index=IGNORAR)

    melhor_acc, melhor_estado, sem_melhora, epocas_rodadas = 0.0, None, 0, 0
    for epoca in range(1, EPOCAS + 1):
        modelo.train()
        soma = 0.0
        for x, yt, yi in loader_treino:
            x, yt, yi = x.to(dispositivo), yt.to(dispositivo), yi.to(dispositivo)
            otimizador.zero_grad()
            logits_i, logits_t = modelo(x)
            erro = ALPHA * perda_int(logits_i, yi) + (1 - ALPHA) * perda_tags(
                logits_t.reshape(-1, len(tag2id)), yt.reshape(-1))
            erro.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 5.0)
            otimizador.step()
            soma += erro.item()
        epocas_rodadas = epoca
        acc_val = acuracia(modelo, loader_val, dispositivo)
        melhor = ""
        if acc_val > melhor_acc:
            melhor_acc, melhor_estado, sem_melhora, melhor = acc_val, copy.deepcopy(modelo.state_dict()), 0, " *melhor"
        else:
            sem_melhora += 1
        print(f"epoca {epoca:>2} | erro {soma/len(loader_treino):.4f} | val {acc_val:.3f}{melhor}")
        if sem_melhora >= PACIENCIA:
            print(f"early stopping: {PACIENCIA} epocas sem melhorar.")
            break

    modelo.load_state_dict(melhor_estado)
    print(f"melhor acuracia de validacao: {melhor_acc:.3f}")

    pacote = {
        "state_dict": modelo.state_dict(),
        "vocab": vocab,
        "intent2id": intent2id,
        "tag2id": tag2id,
        "config": {
            "arquitetura": "BiLSTM",
            "tam_vocab": len(vocab),
            "dim_emb": 100,
            "dim_oculta": 128,
            "dropout": 0.3,
            "n_intencoes": len(intent2id),
            "n_tags": len(tag2id),
        },
        "treino": {
            "alpha": ALPHA, "learning_rate": LR, "batch_size": BATCH,
            "epocas_rodadas": epocas_rodadas, "n_treino": len(treino),
            "n_validacao": len(validacao),
        },
        "metricas": {"acc_validacao": round(melhor_acc, 4)},
        "versao": args.versao,
        "data": datetime.now().isoformat(timespec="seconds"),
    }
    saida = Path(args.saida) if args.saida else Path(__file__).resolve().parent / f"intellix_nlu_v{args.versao}.pt"
    torch.save(pacote, saida)
    print(f"salvo em {saida}  ({saida.stat().st_size/1024**2:.1f} MB)")


if __name__ == "__main__":
    main()
