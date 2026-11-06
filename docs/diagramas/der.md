# DER — modelo de dados implantado (TC2 F07)

Gerado por introspecção do banco real (`scripts/gerar_der.py`), não um
diagrama de software. DDL versionado em `database/migrations/` (001 em diante;
as migrations 006 e 007 não mudam tabelas, só permissões, RLS e funções, então
o diagrama continua o mesmo).

- **Grão da fato (`fato_item_venda`): um ITEM de venda** (produto dentro de
  uma venda). `quantidade_vendas` usa `count(distinct venda_id)`; o ticket
  médio = faturamento / vendas distintas (ver sql/templates.py).
- **`empresa.dono_id`** referencia `auth.users` (gerido pelo Supabase, em
  outro schema), por isso essa relação não é desenhada aqui. Não há
  tabela `usuario` própria do projeto.

```mermaid
erDiagram
  empresa {
    uuid id PK
    text nome
    timestamptz criada_em
    uuid dono_id
  }
  dim_data {
    bigint id PK
    date data
    smallint dia
    smallint mes
    smallint trimestre
    smallint ano
  }
  dim_produto {
    bigint id PK
    uuid empresa_id FK
    text nome
    text nome_norm
    text categoria
  }
  dim_cliente {
    bigint id PK
    uuid empresa_id FK
    text nome
    text nome_norm
    text segmento
  }
  dim_vendedor {
    bigint id PK
    uuid empresa_id FK
    text nome
    text nome_norm
  }
  importacao {
    uuid id PK
    uuid empresa_id FK
    text nome_arquivo
    text hash_arquivo
    text status
    int linhas_lidas
    int linhas_validas
    int linhas_rejeitadas
    timestamptz criada_em
  }
  staging_venda {
    bigint id PK
    uuid importacao_id FK
    uuid empresa_id FK
    int linha_origem
    text data_venda
    text produto
    text categoria
    text cliente
    text vendedor
    text canal
    text forma_pagamento
    text quantidade
    text valor_unitario
    text desconto
    text valor_total
    text erros
  }
  fato_item_venda {
    bigint id PK
    uuid empresa_id FK
    text venda_id
    bigint data_id FK
    bigint produto_id FK
    bigint cliente_id FK
    bigint vendedor_id FK
    text canal
    text forma_pagamento
    int quantidade
    numeric valor_unitario
    numeric desconto
    numeric valor_total
    uuid origem_importacao FK
  }
  log_consulta {
    bigint id PK
    uuid empresa_id FK
    timestamptz criado_em
    text pergunta
    text intencao
    jsonb entidades
    numeric confianca
    text template_sql
    jsonb parametros
    int tempo_ms
  }
  empresa ||--o{ dim_produto : empresa_id
  empresa ||--o{ dim_cliente : empresa_id
  empresa ||--o{ dim_vendedor : empresa_id
  empresa ||--o{ importacao : empresa_id
  empresa ||--o{ staging_venda : empresa_id
  importacao ||--o{ staging_venda : importacao_id
  dim_cliente ||--o{ fato_item_venda : cliente_id
  dim_data ||--o{ fato_item_venda : data_id
  empresa ||--o{ fato_item_venda : empresa_id
  importacao ||--o{ fato_item_venda : origem_importacao
  dim_produto ||--o{ fato_item_venda : produto_id
  dim_vendedor ||--o{ fato_item_venda : vendedor_id
  empresa ||--o{ log_consulta : empresa_id
```

## Chaves e unicidade

| Tabela | PK | Unicidade |
|---|---|---|
| empresa | id | — |
| dim_data | id | (data) |
| dim_produto | id | (empresa_id, nome_norm) |
| dim_cliente | id | (empresa_id, nome_norm) |
| dim_vendedor | id | (empresa_id, nome_norm) |
| importacao | id | (empresa_id, hash_arquivo) |
| staging_venda | id | — |
| fato_item_venda | id | (empresa_id, venda_id, produto_id) |
| log_consulta | id | — |

## Figura do documento (TCC, Figura 4)

`der.png` é a imagem usada na Figura 4 do TCC. Foi gerada a partir do mesmo
Mermaid acima, convertido para Graphviz (`der.dot`) para caber em uma página A4
em formato retrato. Para regenerar:

```bash
dot -Tpng -Gdpi=300 docs/diagramas/der.dot -o docs/diagramas/der.png
```
