# Conjunto de dados do modelo 1.0.0 (recriado)

- **Data:** 06/11/2026 19:59
- **Gerador:** `ia training/gerar_dataset.py` e `moldes.py` do commit `55613ea` (semente fixa)
- **Modelo comparado:** `ia training/modelos/intellix_nlu_v1.0.0_2026-09-08.pt` (treinado em 2026-09-08T22:42:00)
- **Script:** `ia training/reproduzir_dataset_v1.0.0.py`

## Prova de identidade

Divisão do notebook de treino (70/15/15, estratificada por intenção, `random_state=42`) e vocabulário
com frequência mínima 2 no subconjunto de treino:

| | Recriado | Gravado no modelo 1.0.0 |
|---|---:|---:|
| Exemplos de treino | 3360 | 3360 |
| Vocabulário (com `<PAD>` e `<UNK>`) | 404 | 404 |
| Vocabulários idênticos | sim | |

## Estatísticas (seção 5.2 do TCC)

- Exemplos: **4800**; intenções: 12; etiquetas usadas: 19
- Tamanho das frases: mínimo 2, média **7.3**, máximo 14 tokens

### Exemplos por intenção (Tabela 2)

| Intenção | Exemplos |
|---|---:|
| comparacao_periodos | 400 |
| desempenho_vendedor | 400 |
| produtos_sem_saida | 400 |
| quantidade_vendas | 400 |
| ticket_medio | 400 |
| top_clientes | 400 |
| top_produtos | 400 |
| total_vendas_periodo | 400 |
| variacao_periodo | 400 |
| vendas_por_canal | 400 |
| vendas_por_categoria | 400 |
| vendas_por_pagamento | 400 |

### Etiquetas de entidade (Tabela 3)

| Entidade | Início (B) | Continuação (I) |
|---|---:|---:|
| PERIODO | 4654 | 4568 |
| CANAL | 457 | 124 |
| PAGAMENTO | 440 | 245 |
| CATEGORIA | 296 | 48 |
| VENDEDOR | 292 | 118 |
| NUMERO | 235 | 64 |
| CLIENTE | 188 | 120 |
| PRODUTO | 187 | 145 |
| DATA | 54 | 194 |

Razão entre a entidade mais frequente e a segunda: 10.2 vezes.

## Teste real: palavras fora do vocabulário

39 de 236 palavras distintas do `teste_manual.jsonl` (16.5%)
não estão no vocabulário do modelo 1.0.0:

alguma, ao, aí, bombando, bombaram, coisa, dando, desse, difícil, empacada, encalhada, fala, fiéis, fregueses, gasta, giro, grana, jeito, lidera, media, mercadoria, mercadorias, nenhum, oi, pagando, paradas, pegando, poeira, prateleira, saindo, seção, subindo, teve, ultimamente, uma, usa, vendem, vender, vendidas
