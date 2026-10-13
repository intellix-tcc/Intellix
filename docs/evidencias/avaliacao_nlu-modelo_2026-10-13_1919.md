# Avaliação das 100 perguntas — modo `nlu-modelo`

- **Data:** 13/10/2026 19:19 (UTC-0300)
- **Alvo:** NLU `modelo` (sem servidor, sem banco)
- **Ambiente do executor:** Windows 11 · Python 3.12.0
- **Perguntas avaliadas:** 90

## Taxa de acerto por categoria

| # | Categoria | Perguntas | Acertos | Taxa de acerto |
|---|---|---:|---:|---:|
| 1 | total_vendas_periodo | 7 | 5 | 71.4% |
| 2 | top_produtos | 7 | 7 | 100.0% |
| 3 | ticket_medio | 7 | 7 | 100.0% |
| 4 | quantidade_vendas | 7 | 6 | 85.7% |
| 5 | top_clientes | 7 | 6 | 85.7% |
| 6 | desempenho_vendedor | 7 | 4 | 57.1% |
| 7 | produtos_sem_saida | 7 | 7 | 100.0% |
| 8 | comparacao_periodos | 7 | 4 | 57.1% |
| 9 | variacao_periodo | 7 | 5 | 71.4% |
| 10 | vendas_por_canal | 7 | 5 | 71.4% |
| 11 | vendas_por_categoria | 7 | 4 | 57.1% |
| 12 | vendas_por_pagamento | 7 | 3 | 42.9% |
| 13 | fora_de_escopo | 6 | 4 | 66.7% |
| | **Total** | **90** | **67** | **74.4%** |

## Latência

| Mediana | p95 | Máxima | Média | Abaixo de 3 s |
|---:|---:|---:|---:|---:|
| 0 ms | 1 ms | 82 ms | 1 ms | 90/90 (100.0%) |

## Erros

| n | Pergunta | Esperado | Obtido | Status |
|---:|---|---|---|---|
| 4 | Quanto vendi no mês passado? | total_vendas_periodo | vendas_por_canal (0.57) | - |
| 7 | Faturamento de dezembro de 2023, por favor. | total_vendas_periodo | vendas_por_categoria (0.95) | - |
| 25 | Qual a quantidade de vendas do último mês? | quantidade_vendas | variacao_periodo (1.00) | - |
| 35 | Ranking de clientes por faturamento? | top_clientes | desempenho_vendedor (0.54) | - |
| 38 | Desempenho de vendas da Maria em janeiro de 2024? | desempenho_vendedor | variacao_periodo (0.93) | - |
| 40 | Quanto a vendedora Ana faturou em março de 2024? | desempenho_vendedor | variacao_periodo (0.93) | - |
| 41 | Performance do time de vendas em fevereiro? | desempenho_vendedor | vendas_por_canal (0.69) | - |
| 51 | Como foi o faturamento de 2023 comparado com 2024? | comparacao_periodos | total_vendas_periodo (0.93) | - |
| 53 | Faturamento de janeiro versus fevereiro de 2024? | comparacao_periodos | comparacao_periodos (0.42) | - |
| 55 | Como as vendas de 2024 se comparam com 2023? | comparacao_periodos | variacao_periodo (0.90) | - |
| 58 | Quanto cresceu o faturamento de março para abril de 2024? | variacao_periodo | total_vendas_periodo (0.91) | - |
| 62 | Quanto caiu o faturamento comparado ao mês anterior? | variacao_periodo | vendas_por_canal (0.97) | - |
| 67 | Como estão as vendas online comparadas às vendas físicas? | vendas_por_canal | vendas_por_categoria (0.75) | - |
| 69 | Quais canais mais venderam em janeiro de 2024? | vendas_por_canal | top_produtos (0.96) | - |
| 71 | Quais categorias mais venderam em 2024? | vendas_por_categoria | top_produtos (0.97) | - |
| 75 | Quais categorias tiveram queda de vendas? | vendas_por_categoria | produtos_sem_saida (0.77) | - |
| 76 | Desempenho das categorias em janeiro de 2024? | vendas_por_categoria | desempenho_vendedor (0.41) | - |
| 78 | Quais formas de pagamento mais usadas em março? | vendas_por_pagamento | top_produtos (0.67) | - |
| 82 | Faturamento por método de pagamento esse ano? | vendas_por_pagamento | comparacao_periodos (0.58) | - |
| 83 | Quantas vendas no pix em janeiro de 2024? | vendas_por_pagamento | quantidade_vendas (1.00) | - |
| 84 | Como estão distribuídas as formas de pagamento das vendas? | vendas_por_pagamento | vendas_por_categoria (0.93) | - |
| 85 | Qual a capital da França? | rejeitar (conf < 0,70) | variacao_periodo (0.92) | - |
| 88 | Me conta uma piada. | rejeitar (conf < 0,70) | produtos_sem_saida (0.85) | - |
