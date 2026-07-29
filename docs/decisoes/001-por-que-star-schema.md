# ADR 001 — Esquema estrela (star schema) em vez de modelo normalizado

- **Status:** aceito
- **Data:** (preencher no dia em que rodarem o 001_schema.sql)
- **Decisores:** equipe Intellix

## Contexto

A carga de trabalho do Intellix é essencialmente analítica: somas de faturamento,
contagens, médias e rankings sobre dados de vendas. As perguntas suportadas
("quanto faturei em março?", "quais os 5 produtos mais vendidos?", "faturamento por
categoria") são agregações, não transações ponto a ponto.

Dois modelos de dados eram candidatos:

1. **Normalizado até 3FN** (o da disciplina de banco), ótimo para inserções e
   integridade referencial, mas exige muitos `join` nas consultas analíticas.
2. **Esquema estrela**, com uma tabela de fato central de medidas numéricas cercada
   por dimensões descritivas.

## Decisão

Adotamos o **esquema estrela**. A tabela de fato `fato_item_venda` tem grão de
**um item de uma venda** e guarda apenas medidas (quantidade, valor unitário,
desconto, valor total). Ao redor ficam `dim_data`, `dim_produto`, `dim_cliente` e
`dim_vendedor`. `canal` e `forma_pagamento` entram como dimensões degeneradas
(atributos na própria fato, por baixa cardinalidade).

Optamos por **estrela** e não **floco de neve** (snowflake): a hierarquia
produto → categoria fica como atributo dentro de `dim_produto`, sem uma
`dim_categoria` separada.

## Justificativa

- **Menos `join`, consultas mais rápidas e templates SQL mais legíveis** — casa com a
  meta de resposta < 3s e com a geração de SQL restrita a templates.
- **O grão "item de venda" preserva capacidades** que o grão "venda" perderia, como
  "produtos mais vendidos" e "faturamento por categoria".
- **Volume moderado** do público-alvo (pequenas empresas) não impõe a pressão de
  armazenamento que justificaria normalizar as dimensões.

## Consequências

- **Positivas:** desempenho de leitura, simplicidade dos templates, aderência ao tipo
  de pergunta do domínio.
- **Negativas (aceitas de propósito):** redundância controlada — o nome da categoria
  se repete entre produtos da mesma categoria. É o preço do desempenho de leitura.
- Cargas e mudanças de esquema são feitas por **migrations `.sql` numeradas e
  versionadas** (`db/migrations/`), garantindo rastreabilidade.

## Referência

Kimball, Ralph; Ross, Margy. *The Data Warehouse Toolkit*. 3. ed. Wiley, 2013.
