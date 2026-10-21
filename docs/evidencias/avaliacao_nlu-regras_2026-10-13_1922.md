# Avaliação das 100 perguntas — modo `nlu-regras`

- **Data:** 13/10/2026 19:22 (UTC-0300)
- **Alvo:** NLU `regras` (sem servidor, sem banco)
- **Ambiente do executor:** Linux 6.18.44-fc-v114 · Python 3.11.15
- **Perguntas avaliadas:** 90

## Taxa de acerto por categoria

| # | Categoria | Perguntas | Acertos | Taxa de acerto |
|---|---|---:|---:|---:|
| 1 | total_vendas_periodo | 7 | 5 | 71.4% |
| 2 | top_produtos | 7 | 6 | 85.7% |
| 3 | ticket_medio | 7 | 6 | 85.7% |
| 4 | quantidade_vendas | 7 | 0 | 0.0% |
| 5 | top_clientes | 7 | 0 | 0.0% |
| 6 | desempenho_vendedor | 7 | 0 | 0.0% |
| 7 | produtos_sem_saida | 7 | 0 | 0.0% |
| 8 | comparacao_periodos | 7 | 0 | 0.0% |
| 9 | variacao_periodo | 7 | 0 | 0.0% |
| 10 | vendas_por_canal | 7 | 0 | 0.0% |
| 11 | vendas_por_categoria | 7 | 0 | 0.0% |
| 12 | vendas_por_pagamento | 7 | 0 | 0.0% |
| 13 | fora_de_escopo | 6 | 6 | 100.0% |
| | **Total** | **90** | **23** | **25.6%** |

## Latência

| Mediana | p95 | Máxima | Média | Abaixo de 3 s |
|---:|---:|---:|---:|---:|
| 0 ms | 0 ms | 0 ms | 0 ms | 90/90 (100.0%) |

## Erros

| n | Pergunta | Esperado | Obtido | Status |
|---:|---|---|---|---|
| 4 | Quanto vendi no mês passado? | total_vendas_periodo | total_vendas_periodo (0.60) | - |
| 5 | Qual o faturamento total desse ano? | total_vendas_periodo | total_vendas_periodo (0.60) | - |
| 11 | Quais produtos mais venderam em 2024? | top_produtos | None (0.00) | - |
| 18 | Qual o valor médio das vendas em março de 2024? | ticket_medio | None (0.00) | - |
| 22 | Quantas vendas eu fiz em março? | quantidade_vendas | None (0.00) | - |
| 23 | Quantas vendas tiveram em 2024? | quantidade_vendas | None (0.00) | - |
| 24 | Quantas vendas foram feitas em março de 2024? | quantidade_vendas | None (0.00) | - |
| 25 | Qual a quantidade de vendas do último mês? | quantidade_vendas | None (0.00) | - |
| 26 | Quantas vendas a loja fez esse ano? | quantidade_vendas | None (0.00) | - |
| 27 | Número de vendas em janeiro de 2024? | quantidade_vendas | None (0.00) | - |
| 28 | Quantas vendas eu tive no primeiro trimestre? | quantidade_vendas | None (0.00) | - |
| 29 | Quais os clientes que mais compraram? | top_clientes | None (0.00) | - |
| 30 | Quem são os 5 clientes que mais compraram em 2024? | top_clientes | None (0.00) | - |
| 31 | Top 10 clientes do ano? | top_clientes | None (0.00) | - |
| 32 | Quais clientes mais gastaram em março de 2024? | top_clientes | None (0.00) | - |
| 33 | Meus melhores clientes desse ano? | top_clientes | None (0.00) | - |
| 34 | Quem comprou mais em janeiro de 2024? | top_clientes | None (0.00) | - |
| 35 | Ranking de clientes por faturamento? | top_clientes | total_vendas_periodo (0.60) | - |
| 36 | Como foi o desempenho da Fernanda em março? | desempenho_vendedor | None (0.00) | - |
| 37 | Quanto o vendedor João vendeu em 2024? | desempenho_vendedor | None (0.00) | - |
| 38 | Desempenho de vendas da Maria em janeiro de 2024? | desempenho_vendedor | None (0.00) | - |
| 39 | Como está o vendedor Carlos esse ano? | desempenho_vendedor | None (0.00) | - |
| 40 | Quanto a vendedora Ana faturou em março de 2024? | desempenho_vendedor | total_vendas_periodo (0.93) | - |
| 41 | Performance do time de vendas em fevereiro? | desempenho_vendedor | None (0.00) | - |
| 42 | Quem vendeu mais entre os vendedores? | desempenho_vendedor | None (0.00) | - |
| 43 | Quais produtos não venderam em março? | produtos_sem_saida | None (0.00) | - |
| 44 | Quais produtos ficaram parados esse ano? | produtos_sem_saida | None (0.00) | - |
| 45 | Produtos sem venda em 2024? | produtos_sem_saida | None (0.00) | - |
| 46 | O que não saiu do estoque no último mês? | produtos_sem_saida | None (0.00) | - |
| 47 | Quais itens não tiveram saída em janeiro de 2024? | produtos_sem_saida | None (0.00) | - |
| 48 | Produtos parados no ano? | produtos_sem_saida | None (0.00) | - |
| 49 | Quais produtos estão encalhados? | produtos_sem_saida | None (0.00) | - |
| 50 | Compare o faturamento de março com abril de 2024. | comparacao_periodos | total_vendas_periodo (0.93) | - |
| 51 | Como foi o faturamento de 2023 comparado com 2024? | comparacao_periodos | total_vendas_periodo (0.93) | - |
| 52 | Compare as vendas do primeiro trimestre com o segundo. | comparacao_periodos | None (0.00) | - |
| 53 | Faturamento de janeiro versus fevereiro de 2024? | comparacao_periodos | total_vendas_periodo (0.93) | - |
| 54 | Compare esse mês com o mês passado. | comparacao_periodos | None (0.00) | - |
| 55 | Como as vendas de 2024 se comparam com 2023? | comparacao_periodos | None (0.00) | - |
| 56 | Compare o desempenho de março e junho. | comparacao_periodos | None (0.00) | - |
| 57 | Qual foi a variação do faturamento em relação ao mês anterior? | variacao_periodo | total_vendas_periodo (0.60) | - |
| 58 | Quanto cresceu o faturamento de março para abril de 2024? | variacao_periodo | total_vendas_periodo (0.93) | - |
| 59 | Qual a variação percentual das vendas esse ano? | variacao_periodo | None (0.00) | - |
| 60 | As vendas cresceram ou caíram em relação ao ano passado? | variacao_periodo | None (0.00) | - |
| 61 | Qual o crescimento do faturamento em março de 2024? | variacao_periodo | total_vendas_periodo (0.93) | - |
| 62 | Quanto caiu o faturamento comparado ao mês anterior? | variacao_periodo | total_vendas_periodo (0.60) | - |
| 63 | Qual a variação de vendas entre os trimestres? | variacao_periodo | None (0.00) | - |
| 64 | Quanto vendi por canal em março de 2024? | vendas_por_canal | total_vendas_periodo (0.93) | - |
| 65 | Qual canal vendeu mais esse ano? | vendas_por_canal | None (0.00) | - |
| 66 | Vendas por canal de venda em 2024? | vendas_por_canal | None (0.00) | - |
| 67 | Como estão as vendas online comparadas às vendas físicas? | vendas_por_canal | None (0.00) | - |
| 68 | Qual o faturamento por canal no último mês? | vendas_por_canal | total_vendas_periodo (0.60) | - |
| 69 | Quais canais mais venderam em janeiro de 2024? | vendas_por_canal | None (0.00) | - |
| 70 | Desempenho de vendas por canal esse trimestre? | vendas_por_canal | None (0.00) | - |
| 71 | Quais categorias mais venderam em 2024? | vendas_por_categoria | None (0.00) | - |
| 72 | Faturamento por categoria de produto em março? | vendas_por_categoria | total_vendas_periodo (0.93) | - |
| 73 | Qual categoria vendeu mais esse ano? | vendas_por_categoria | None (0.00) | - |
| 74 | Vendas por categoria no último mês? | vendas_por_categoria | None (0.00) | - |
| 75 | Quais categorias tiveram queda de vendas? | vendas_por_categoria | None (0.00) | - |
| 76 | Desempenho das categorias em janeiro de 2024? | vendas_por_categoria | None (0.00) | - |
| 77 | Qual categoria de produto é mais lucrativa? | vendas_por_categoria | None (0.00) | - |
| 78 | Quais formas de pagamento mais usadas em março? | vendas_por_pagamento | None (0.00) | - |
| 79 | Vendas por forma de pagamento em 2024? | vendas_por_pagamento | None (0.00) | - |
| 80 | Quanto foi pago no cartão em março de 2024? | vendas_por_pagamento | None (0.00) | - |
| 81 | Qual forma de pagamento é mais usada pelos clientes? | vendas_por_pagamento | None (0.00) | - |
| 82 | Faturamento por método de pagamento esse ano? | vendas_por_pagamento | total_vendas_periodo (0.60) | - |
| 83 | Quantas vendas no pix em janeiro de 2024? | vendas_por_pagamento | None (0.00) | - |
| 84 | Como estão distribuídas as formas de pagamento das vendas? | vendas_por_pagamento | None (0.00) | - |
