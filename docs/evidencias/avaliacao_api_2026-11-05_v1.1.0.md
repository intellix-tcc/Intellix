# Avaliação das 100 perguntas — modo `api`

- **Data:** 05/11/2026 16:20 (UTC+0000)
- **Alvo:** http://127.0.0.1:8001
- **Ambiente do executor:** Linux 6.18.44-fc-v236 · Python 3.13.18
- **Perguntas avaliadas:** 100

## Taxa de acerto por categoria

| # | Categoria | Perguntas | Acertos | Taxa de acerto |
|---|---|---:|---:|---:|
| 1 | total_vendas_periodo | 7 | 5 | 71.4% |
| 2 | top_produtos | 7 | 7 | 100.0% |
| 3 | ticket_medio | 7 | 7 | 100.0% |
| 4 | quantidade_vendas | 7 | 6 | 85.7% |
| 5 | top_clientes | 7 | 6 | 85.7% |
| 6 | desempenho_vendedor | 7 | 3 | 42.9% |
| 7 | produtos_sem_saida | 7 | 2 | 28.6% |
| 8 | comparacao_periodos | 7 | 5 | 71.4% |
| 9 | variacao_periodo | 7 | 7 | 100.0% |
| 10 | vendas_por_canal | 7 | 6 | 85.7% |
| 11 | vendas_por_categoria | 7 | 6 | 85.7% |
| 12 | vendas_por_pagamento | 7 | 4 | 57.1% |
| 13 | fora_de_escopo | 6 | 6 | 100.0% |
| 14 | parametro_faltando | 5 | 3 | 60.0% |
| 15 | sem_resultado | 5 | 4 | 80.0% |
| | **Total** | **100** | **77** | **77.0%** |

## Latência

| Mediana | p95 | Máxima | Média | Abaixo de 3 s |
|---:|---:|---:|---:|---:|
| 18 ms | 29 ms | 58 ms | 18 ms | 100/100 (100.0%) |

## Erros

| n | Pergunta | Esperado | Obtido | Status |
|---:|---|---|---|---|
| 4 | Quanto vendi no mês passado? | 200 / total_vendas_periodo | baixa_confianca | 422 |
| 7 | Faturamento de dezembro de 2023, por favor. | 200 / total_vendas_periodo | vendas_por_categoria | 200 |
| 25 | Qual a quantidade de vendas do último mês? | 200 / quantidade_vendas | variacao_periodo | 200 |
| 35 | Ranking de clientes por faturamento? | 200 / top_clientes | baixa_confianca | 422 |
| 37 | Quanto o vendedor João vendeu em 2024? | 200 / desempenho_vendedor | sem_resultado | 404 |
| 38 | Desempenho de vendas da Maria em janeiro de 2024? | 200 / desempenho_vendedor | variacao_periodo | 200 |
| 40 | Quanto a vendedora Ana faturou em março de 2024? | 200 / desempenho_vendedor | total_vendas_periodo | 200 |
| 41 | Performance do time de vendas em fevereiro? | 200 / desempenho_vendedor | variacao_periodo | 200 |
| 44 | Quais produtos ficaram parados esse ano? | 200 / produtos_sem_saida | sem_resultado | 404 |
| 45 | Produtos sem venda em 2024? | 200 / produtos_sem_saida | sem_resultado | 404 |
| 46 | O que não saiu do estoque no último mês? | 200 / produtos_sem_saida | sem_resultado | 404 |
| 48 | Produtos parados no ano? | 200 / produtos_sem_saida | sem_resultado | 404 |
| 49 | Quais produtos estão encalhados? | 200 / produtos_sem_saida | sem_resultado | 404 |
| 54 | Compare esse mês com o mês passado. | 200 / comparacao_periodos | baixa_confianca | 422 |
| 56 | Compare o desempenho de março e junho. | 200 / comparacao_periodos | parametro_faltando | 422 |
| 67 | Como estão as vendas online comparadas às vendas físicas? | 200 / vendas_por_canal | baixa_confianca | 422 |
| 76 | Desempenho das categorias em janeiro de 2024? | 200 / vendas_por_categoria | baixa_confianca | 422 |
| 78 | Quais formas de pagamento mais usadas em março? | 200 / vendas_por_pagamento | baixa_confianca | 422 |
| 83 | Quantas vendas no pix em janeiro de 2024? | 200 / vendas_por_pagamento | quantidade_vendas | 200 |
| 84 | Como estão distribuídas as formas de pagamento das vendas? | 200 / vendas_por_pagamento | vendas_por_categoria | 200 |
| 92 | Compare os períodos. | 422 | vendas_por_categoria | 200 |
| 94 | Quanto vendi? | 422 | total_vendas_periodo | 200 |
| 99 | Como foi o desempenho do vendedor "Roberto" em 2015? | 404 / sem_resultado | parametro_faltando | 422 |
