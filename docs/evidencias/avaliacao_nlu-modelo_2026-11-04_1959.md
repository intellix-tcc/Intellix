# Avaliação das 100 perguntas — modo `nlu-modelo`

- **Data:** 04/11/2026 19:59 (UTC-0300)
- **Alvo:** NLU `modelo` (sem servidor, sem banco)
- **Ambiente do executor:** Windows 10 · Python 3.11.5
- **Perguntas avaliadas:** 90

## Taxa de acerto por categoria

| # | Categoria | Perguntas | Acertos | Taxa de acerto |
|---|---|---:|---:|---:|
| 1 | total_vendas_periodo | 7 | 5 | 71.4% |
| 2 | top_produtos | 7 | 6 | 85.7% |
| 3 | ticket_medio | 7 | 7 | 100.0% |
| 4 | quantidade_vendas | 7 | 6 | 85.7% |
| 5 | top_clientes | 7 | 6 | 85.7% |
| 6 | desempenho_vendedor | 7 | 4 | 57.1% |
| 7 | produtos_sem_saida | 7 | 7 | 100.0% |
| 8 | comparacao_periodos | 7 | 3 | 42.9% |
| 9 | variacao_periodo | 7 | 5 | 71.4% |
| 10 | vendas_por_canal | 7 | 5 | 71.4% |
| 11 | vendas_por_categoria | 7 | 7 | 100.0% |
| 12 | vendas_por_pagamento | 7 | 5 | 71.4% |
| 13 | fora_de_escopo | 6 | 6 | 100.0% |
| | **Total** | **90** | **72** | **80.0%** |

## Latência

| Mediana | p95 | Máxima | Média | Abaixo de 3 s |
|---:|---:|---:|---:|---:|
| 2 ms | 4 ms | 10 ms | 2 ms | 90/90 (100.0%) |

## Erros

| n | Pergunta | Esperado | Obtido | Status |
|---:|---|---|---|---|
| 4 | Quanto vendi no mês passado? | total_vendas_periodo | vendas_por_canal (0.92) | - |
| 7 | Faturamento de dezembro de 2023, por favor. | total_vendas_periodo | vendas_por_categoria (0.87) | - |
| 14 | Top produtos de fevereiro de 2024? | top_produtos | top_produtos (0.66) | - |
| 25 | Qual a quantidade de vendas do último mês? | quantidade_vendas | variacao_periodo (0.65) | - |
| 35 | Ranking de clientes por faturamento? | top_clientes | top_clientes (0.70) | - |
| 38 | Desempenho de vendas da Maria em janeiro de 2024? | desempenho_vendedor | desempenho_vendedor (0.66) | - |
| 40 | Quanto a vendedora Ana faturou em março de 2024? | desempenho_vendedor | total_vendas_periodo (0.69) | - |
| 41 | Performance do time de vendas em fevereiro? | desempenho_vendedor | quantidade_vendas (0.82) | - |
| 51 | Como foi o faturamento de 2023 comparado com 2024? | comparacao_periodos | total_vendas_periodo (0.98) | - |
| 52 | Compare as vendas do primeiro trimestre com o segundo. | comparacao_periodos | comparacao_periodos (0.57) | - |
| 54 | Compare esse mês com o mês passado. | comparacao_periodos | None (0.00) | - |
| 55 | Como as vendas de 2024 se comparam com 2023? | comparacao_periodos | comparacao_periodos (0.48) | - |
| 58 | Quanto cresceu o faturamento de março para abril de 2024? | variacao_periodo | total_vendas_periodo (0.98) | - |
| 62 | Quanto caiu o faturamento comparado ao mês anterior? | variacao_periodo | total_vendas_periodo (0.50) | - |
| 67 | Como estão as vendas online comparadas às vendas físicas? | vendas_por_canal | vendas_por_categoria (0.42) | - |
| 69 | Quais canais mais venderam em janeiro de 2024? | vendas_por_canal | top_produtos (0.96) | - |
| 78 | Quais formas de pagamento mais usadas em março? | vendas_por_pagamento | produtos_sem_saida (0.52) | - |
| 83 | Quantas vendas no pix em janeiro de 2024? | vendas_por_pagamento | quantidade_vendas (0.99) | - |
