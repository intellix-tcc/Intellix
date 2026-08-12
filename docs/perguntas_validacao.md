# 100 perguntas de validação funcional (D14)

Base para a Tabela 1 do capítulo 8 (taxa de acerto por categoria). Não
depende do sistema completo — a lista está pronta antes do modelo real
existir; só falta rodar contra o sistema quando ele estiver no ar.

As 12 categorias batem com as 12 chaves de
[`backend/app/sql/templates.py`](../backend/app/sql/templates.py). Hoje
(ver [CLAUDE.md](../CLAUDE.md)) só `total_vendas_periodo`, `top_produtos`
e `ticket_medio` são reconhecidas pelo NLU de regras — as outras 9
categorias devem falhar até o Dev A/B implementarem o reconhecimento.
Isso é esperado: é justamente o que a taxa de acerto por categoria vai
expor.

Cada categoria tem 7 perguntas variando: com/sem ano explícito, "mês
passado"/"esse ano" (linguagem relativa), plural/singular, formal/informal.
As últimas 16 perguntas testam os fallbacks (seção 7.6 do TCC): fora de
escopo, parâmetro faltando, sem resultado.

## 1. total_vendas_periodo — faturamento

1. Quanto faturei em março?
2. Quanto faturei em março de 2024?
3. Qual foi o faturamento de 2024?
4. Quanto vendi no mês passado?
5. Qual o faturamento total desse ano?
6. Quanto a loja faturou em janeiro de 2024?
7. Faturamento de dezembro de 2023, por favor.

## 2. top_produtos

8. Quais os 5 produtos mais vendidos?
9. Quais os 10 produtos mais vendidos em março de 2024?
10. Top 3 produtos do ano?
11. Quais produtos mais venderam em 2024?
12. Me mostra os produtos mais vendidos.
13. Quais os produtos mais vendidos no último mês?
14. Top produtos de fevereiro de 2024?

## 3. ticket_medio

15. Qual o ticket médio em março?
16. Qual o ticket médio de 2024?
17. Qual foi o ticket médio esse ano?
18. Qual o valor médio das vendas em março de 2024?
19. Qual o ticket médio do mês passado?
20. Ticket médio de janeiro de 2024?
21. Qual o ticket médio geral?

## 4. quantidade_vendas

22. Quantas vendas eu fiz em março?
23. Quantas vendas tiveram em 2024?
24. Quantas vendas foram feitas em março de 2024?
25. Qual a quantidade de vendas do último mês?
26. Quantas vendas a loja fez esse ano?
27. Número de vendas em janeiro de 2024?
28. Quantas vendas eu tive no primeiro trimestre?

## 5. top_clientes

29. Quais os clientes que mais compraram?
30. Quem são os 5 clientes que mais compraram em 2024?
31. Top 10 clientes do ano?
32. Quais clientes mais gastaram em março de 2024?
33. Meus melhores clientes desse ano?
34. Quem comprou mais em janeiro de 2024?
35. Ranking de clientes por faturamento?

## 6. desempenho_vendedor

36. Como foi o desempenho da Fernanda em março?
37. Quanto o vendedor João vendeu em 2024?
38. Desempenho de vendas da Maria em janeiro de 2024?
39. Como está o vendedor Carlos esse ano?
40. Quanto a vendedora Ana faturou em março de 2024?
41. Performance do time de vendas em fevereiro?
42. Quem vendeu mais entre os vendedores?

## 7. produtos_sem_saida

43. Quais produtos não venderam em março?
44. Quais produtos ficaram parados esse ano?
45. Produtos sem venda em 2024?
46. O que não saiu do estoque no último mês?
47. Quais itens não tiveram saída em janeiro de 2024?
48. Produtos parados no ano?
49. Quais produtos estão encalhados?

## 8. comparacao_periodos

50. Compare o faturamento de março com abril de 2024.
51. Como foi o faturamento de 2023 comparado com 2024?
52. Compare as vendas do primeiro trimestre com o segundo.
53. Faturamento de janeiro versus fevereiro de 2024?
54. Compare esse mês com o mês passado.
55. Como as vendas de 2024 se comparam com 2023?
56. Compare o desempenho de março e junho.

## 9. variacao_periodo

57. Qual foi a variação do faturamento em relação ao mês anterior?
58. Quanto cresceu o faturamento de março para abril de 2024?
59. Qual a variação percentual das vendas esse ano?
60. As vendas cresceram ou caíram em relação ao ano passado?
61. Qual o crescimento do faturamento em março de 2024?
62. Quanto caiu o faturamento comparado ao mês anterior?
63. Qual a variação de vendas entre os trimestres?

## 10. vendas_por_canal

64. Quanto vendi por canal em março de 2024?
65. Qual canal vendeu mais esse ano?
66. Vendas por canal de venda em 2024?
67. Como estão as vendas online comparadas às vendas físicas?
68. Qual o faturamento por canal no último mês?
69. Quais canais mais venderam em janeiro de 2024?
70. Desempenho de vendas por canal esse trimestre?

## 11. vendas_por_categoria

71. Quais categorias mais venderam em 2024?
72. Faturamento por categoria de produto em março?
73. Qual categoria vendeu mais esse ano?
74. Vendas por categoria no último mês?
75. Quais categorias tiveram queda de vendas?
76. Desempenho das categorias em janeiro de 2024?
77. Qual categoria de produto é mais lucrativa?

## 12. vendas_por_pagamento

78. Quais formas de pagamento mais usadas em março?
79. Vendas por forma de pagamento em 2024?
80. Quanto foi pago no cartão em março de 2024?
81. Qual forma de pagamento é mais usada pelos clientes?
82. Faturamento por método de pagamento esse ano?
83. Quantas vendas no pix em janeiro de 2024?
84. Como estão distribuídas as formas de pagamento das vendas?

## 13. Fora de escopo (deve cair no fallback de baixa confiança, 422)

85. Qual a capital da França?
86. Que dia é hoje?
87. Como está o tempo hoje?
88. Me conta uma piada.
89. Qual o sentido da vida?
90. Quem descobriu o Brasil?

## 14. Parâmetro faltando / pedido ambíguo (422)

91. Como foi o desempenho do vendedor? *(sem nome)*
92. Compare os períodos. *(sem especificar quais)*
93. Qual a variação? *(sem período de referência)*
94. Quanto vendi? *(sem período)*
95. Mostra os dados de vendas. *(pedido vago, sem intenção clara)*

## 15. Sem resultado esperado (404 — fora do range dos dados seedados)

96. Quanto faturei em janeiro de 2020?
97. Quais produtos mais venderam em 2019?
98. Qual o ticket médio de 2018?
99. Como foi o desempenho do vendedor "Roberto" em 2015? *(provavelmente inexistente)*
100. Quantas vendas tivemos em 2030? *(data futura)*

---

## Tabela 1 — taxa de acerto por categoria (preencher ao rodar)

| # | Categoria | Perguntas | Acertos | Taxa de acerto |
|---|---|---|---|---|
| 1 | total_vendas_periodo | 7 | | |
| 2 | top_produtos | 7 | | |
| 3 | ticket_medio | 7 | | |
| 4 | quantidade_vendas | 7 | | |
| 5 | top_clientes | 7 | | |
| 6 | desempenho_vendedor | 7 | | |
| 7 | produtos_sem_saida | 7 | | |
| 8 | comparacao_periodos | 7 | | |
| 9 | variacao_periodo | 7 | | |
| 10 | vendas_por_canal | 7 | | |
| 11 | vendas_por_categoria | 7 | | |
| 12 | vendas_por_pagamento | 7 | | |
| 13 | Fora de escopo | 6 | | |
| 14 | Parâmetro faltando | 5 | | |
| 15 | Sem resultado | 5 | | |
| | **Total** | **100** | | |

"Acerto" = `tipo_visualizacao` e status HTTP batem com o esperado (não
precisa validar o valor exato, já que os dados seedados podem mudar).
