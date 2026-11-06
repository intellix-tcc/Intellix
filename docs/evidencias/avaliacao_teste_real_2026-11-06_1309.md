# Avaliação dos modelos no conjunto de teste real

- **Data:** 06/11/2026 13:09
- **Conjunto:** `ia training/teste_manual.jsonl` (120 frases escritas à mão, 10 por intenção; 7 delas também aparecem no treino do modelo 1.2.0, ver Observações)
- **Procedimento:** o mesmo do notebook de treino (tokens e tags do arquivo entram direto no modelo); intenção com scikit-learn, entidades por entidade completa com seqeval.
- **Script:** `ia training/avaliar_teste_real.py`

## Resumo

| Modelo | Acurácia de intenção | F1 de intenção (macro) | F1 de entidades (micro) | Precisão / revocação de entidades | Só frases conferidas: acurácia · F1 entidades |
|---|---:|---:|---:|---:|---:|
| 1.0.0 | **93,3%** | 0,932 | **0,803** | 0,742 / 0,876 | 94,9% · 0,868 (n=78) |
| 1.1.0 | **88,3%** | 0,881 | **0,873** | 0,835 / 0,914 | 91,0% · 0,910 (n=78) |
| 1.2.0 | **88,3%** | 0,887 | **0,831** | 0,762 / 0,914 | 89,7% · 0,889 (n=78) |

## Modelo 1.0.0

### Por intenção

| Intenção | Precisão | Revocação | F1 |
|---|---:|---:|---:|
| comparacao_periodos | 0,909 | 1,000 | 0,952 |
| desempenho_vendedor | 1,000 | 0,900 | 0,947 |
| produtos_sem_saida | 0,909 | 1,000 | 0,952 |
| quantidade_vendas | 1,000 | 1,000 | 1,000 |
| ticket_medio | 0,900 | 0,900 | 0,900 |
| top_clientes | 1,000 | 1,000 | 1,000 |
| top_produtos | 0,900 | 0,900 | 0,900 |
| total_vendas_periodo | 0,889 | 0,800 | 0,842 |
| variacao_periodo | 0,909 | 1,000 | 0,952 |
| vendas_por_canal | 0,900 | 0,900 | 0,900 |
| vendas_por_categoria | 1,000 | 0,800 | 0,889 |
| vendas_por_pagamento | 0,909 | 1,000 | 0,952 |

### Matriz de confusão (linhas = verdadeira, colunas = prevista)

| | comparacao | desempenho | produtos_s | quantidade | ticket_med | top_client | top_produt | total_vend | variacao_p | vendas_por | vendas_por | vendas_por |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| comparacao_periodos | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| desempenho_vendedor | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| produtos_sem_saida | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| quantidade_vendas | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ticket_medio | 0 | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| top_clientes | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| top_produtos | 0 | 0 | 1 | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| total_vendas_periodo | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 1 | 0 | 0 | 0 |
| variacao_periodo | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |
| vendas_por_canal | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 9 | 0 | 0 |
| vendas_por_categoria | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 8 | 1 |
| vendas_por_pagamento | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 |

### Frases com intenção errada (8)

| Frase | Verdadeira | Prevista |
|---|---|---|
| oi , quanto que eu vendi mês passado ? | total_vendas_periodo | comparacao_periodos |
| qual foi a grana que entrou ontem | total_vendas_periodo | variacao_periodo |
| quais produtos bombaram mês passado | top_produtos | produtos_sem_saida |
| quanto o pessoal gasta por compra em média | ticket_medio | vendas_por_canal |
| quanto a leticia faturou essa semana | desempenho_vendedor | total_vendas_periodo |
| de onde vem mais venda | vendas_por_canal | top_produtos |
| qual seção puxa mais venda | vendas_por_categoria | ticket_medio |
| me mostra o total por categoria | vendas_por_categoria | vendas_por_pagamento |

### Entidades (seqeval)

```
              precision    recall  f1-score   support

       CANAL      0.750     0.643     0.692        14
   CATEGORIA      0.667     0.800     0.727         5
     CLIENTE      1.000     1.000     1.000         2
        DATA      1.000     1.000     1.000         1
      NUMERO      0.600     1.000     0.750         3
   PAGAMENTO      0.923     1.000     0.960        12
     PERIODO      0.750     0.934     0.832        61
    VENDEDOR      0.444     0.571     0.500         7

   micro avg      0.742     0.876     0.803       105
   macro avg      0.767     0.869     0.808       105
weighted avg      0.748     0.876     0.803       105
```

## Modelo 1.1.0

### Por intenção

| Intenção | Precisão | Revocação | F1 |
|---|---:|---:|---:|
| comparacao_periodos | 1,000 | 0,900 | 0,947 |
| desempenho_vendedor | 0,900 | 0,900 | 0,900 |
| produtos_sem_saida | 0,727 | 0,800 | 0,762 |
| quantidade_vendas | 1,000 | 1,000 | 1,000 |
| ticket_medio | 0,900 | 0,900 | 0,900 |
| top_clientes | 0,833 | 1,000 | 0,909 |
| top_produtos | 1,000 | 0,600 | 0,750 |
| total_vendas_periodo | 0,818 | 0,900 | 0,857 |
| variacao_periodo | 0,900 | 0,900 | 0,900 |
| vendas_por_canal | 0,909 | 1,000 | 0,952 |
| vendas_por_categoria | 0,700 | 0,700 | 0,700 |
| vendas_por_pagamento | 1,000 | 1,000 | 1,000 |

### Matriz de confusão (linhas = verdadeira, colunas = prevista)

| | comparacao | desempenho | produtos_s | quantidade | ticket_med | top_client | top_produt | total_vend | variacao_p | vendas_por | vendas_por | vendas_por |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| comparacao_periodos | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| desempenho_vendedor | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| produtos_sem_saida | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| quantidade_vendas | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ticket_medio | 0 | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| top_clientes | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| top_produtos | 0 | 0 | 3 | 0 | 0 | 1 | 6 | 0 | 0 | 0 | 0 | 0 |
| total_vendas_periodo | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 1 | 0 | 0 | 0 |
| variacao_periodo | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 9 | 0 | 0 | 0 |
| vendas_por_canal | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 |
| vendas_por_categoria | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 7 | 0 |
| vendas_por_pagamento | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 |

### Frases com intenção errada (14)

| Frase | Verdadeira | Prevista |
|---|---|---|
| qual foi a grana que entrou ontem | total_vendas_periodo | variacao_periodo |
| o que tá bombando de venda | top_produtos | produtos_sem_saida |
| quais produtos bombaram mês passado | top_produtos | produtos_sem_saida |
| top 10 mercadorias mais vendidas | top_produtos | top_clientes |
| qual produto lidera as vendas | top_produtos | produtos_sem_saida |
| media de gasto por cliente | ticket_medio | vendas_por_categoria |
| onde vendi mais , na loja ou no site | comparacao_periodos | vendas_por_canal |
| quanto a leticia faturou essa semana | desempenho_vendedor | total_vendas_periodo |
| tem alguma coisa encalhada no estoque | produtos_sem_saida | vendas_por_categoria |
| tem mercadoria empacada ? | produtos_sem_saida | vendas_por_categoria |
| roupas tão vendendo bem ? | vendas_por_categoria | desempenho_vendedor |
| qual seção puxa mais venda | vendas_por_categoria | top_clientes |
| me mostra o total por categoria | vendas_por_categoria | ticket_medio |
| quanto cresci esse mês | variacao_periodo | total_vendas_periodo |

### Entidades (seqeval)

```
              precision    recall  f1-score   support

       CANAL      0.786     0.786     0.786        14
   CATEGORIA      0.833     1.000     0.909         5
     CLIENTE      1.000     1.000     1.000         2
        DATA      1.000     1.000     1.000         1
      NUMERO      1.000     1.000     1.000         3
   PAGAMENTO      1.000     0.917     0.957        12
     PERIODO      0.829     0.951     0.885        61
    VENDEDOR      0.625     0.714     0.667         7

   micro avg      0.835     0.914     0.873       105
   macro avg      0.884     0.921     0.900       105
weighted avg      0.839     0.914     0.873       105
```

## Modelo 1.2.0

### Por intenção

| Intenção | Precisão | Revocação | F1 |
|---|---:|---:|---:|
| comparacao_periodos | 0,889 | 0,800 | 0,842 |
| desempenho_vendedor | 0,909 | 1,000 | 0,952 |
| produtos_sem_saida | 0,909 | 1,000 | 0,952 |
| quantidade_vendas | 0,909 | 1,000 | 0,952 |
| ticket_medio | 1,000 | 0,900 | 0,947 |
| top_clientes | 1,000 | 0,900 | 0,947 |
| top_produtos | 1,000 | 0,900 | 0,947 |
| total_vendas_periodo | 0,538 | 0,700 | 0,609 |
| variacao_periodo | 0,800 | 0,800 | 0,800 |
| vendas_por_canal | 0,900 | 0,900 | 0,900 |
| vendas_por_categoria | 0,889 | 0,800 | 0,842 |
| vendas_por_pagamento | 1,000 | 0,900 | 0,947 |

### Matriz de confusão (linhas = verdadeira, colunas = prevista)

| | comparacao | desempenho | produtos_s | quantidade | ticket_med | top_client | top_produt | total_vend | variacao_p | vendas_por | vendas_por | vendas_por |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| comparacao_periodos | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| desempenho_vendedor | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| produtos_sem_saida | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| quantidade_vendas | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ticket_medio | 0 | 0 | 0 | 1 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| top_clientes | 0 | 0 | 0 | 0 | 0 | 9 | 0 | 1 | 0 | 0 | 0 | 0 |
| top_produtos | 0 | 0 | 1 | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| total_vendas_periodo | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 2 | 0 | 0 | 0 |
| variacao_periodo | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 8 | 0 | 0 | 0 |
| vendas_por_canal | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 1 | 0 |
| vendas_por_categoria | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 8 | 0 |
| vendas_por_pagamento | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 9 |

### Frases com intenção errada (14)

| Frase | Verdadeira | Prevista |
|---|---|---|
| oi , quanto que eu vendi mês passado ? | total_vendas_periodo | comparacao_periodos |
| me diz aí o total que entrou em março | total_vendas_periodo | variacao_periodo |
| qual foi a grana que entrou ontem | total_vendas_periodo | variacao_periodo |
| quais produtos bombaram mês passado | top_produtos | produtos_sem_saida |
| media de gasto por cliente | ticket_medio | quantidade_vendas |
| onde vendi mais , na loja ou no site | comparacao_periodos | vendas_por_canal |
| qual trimestre foi melhor | comparacao_periodos | total_vendas_periodo |
| de onde vem mais venda | vendas_por_canal | vendas_por_categoria |
| quanto entrou de pix esse mês | vendas_por_pagamento | total_vendas_periodo |
| quanto a maria já gastou no total | top_clientes | total_vendas_periodo |
| qual seção puxa mais venda | vendas_por_categoria | total_vendas_periodo |
| me mostra o total por categoria | vendas_por_categoria | total_vendas_periodo |
| minhas vendas tão subindo ? | variacao_periodo | desempenho_vendedor |
| quanto cresci esse mês | variacao_periodo | total_vendas_periodo |

### Entidades (seqeval)

```
              precision    recall  f1-score   support

       CANAL      0.867     0.929     0.897        14
   CATEGORIA      0.833     1.000     0.909         5
     CLIENTE      0.667     1.000     0.800         2
        DATA      1.000     1.000     1.000         1
      NUMERO      0.750     1.000     0.857         3
   PAGAMENTO      1.000     0.833     0.909        12
     PERIODO      0.766     0.967     0.855        61
     PRODUTO      0.000     0.000     0.000         0
    VENDEDOR      0.429     0.429     0.429         7

   micro avg      0.762     0.914     0.831       105
   macro avg      0.701     0.795     0.740       105
weighted avg      0.787     0.914     0.841       105
```

## Observações

- **Reprodução do TCC (modelo 1.0.0):** a acurácia de intenção reproduz exatamente os
  93,3% do TCC, com as mesmas 8 frases erradas analisadas na seção 5.5.5. O F1 de
  entidades medido aqui é 0,803; o valor gravado no próprio arquivo do modelo na época
  do treino é 0,838. A diferença está só nas entidades, então o mais provável é que
  as anotações de entidades deste arquivo tenham sido revisadas depois do treino (42
  frases estão marcadas `revisar: true`). Com `mode="strict"` do seqeval, o F1 é 0,829.
- **Anotações a corrigir:** em 3 frases a etiqueta de vendedor está no artigo
  ("**a** fernanda", "**o** carlos", "**a** juliana": `B-VENDEDOR` no artigo e
  `I-VENDEDOR` no nome), o que penaliza todos os modelos nas entidades.
- **Frases do teste que também aparecem no treino:** o gerador de dados tem semente
  fixa (`gerar_dataset.py`), então o treino pode ser regenerado. 7 das 120 frases de
  teste aparecem idênticas no treino do modelo 1.2.0 (frases curtas como "quais
  produtos tão parados", que os moldes também produzem). Sem essas 7, a acurácia de
  intenção do 1.2.0 é 88,5% (100 de 113), praticamente igual aos 88,3% com elas.
- **Modelos 1.1.0 e 1.2.0 x conjunto de validação:** nas 100 perguntas de validação,
  a classificação isolada subiu de 74,4% (1.0.0) para 92,2% (1.2.0); neste conjunto
  independente, a acurácia caiu de 93,3% para 88,3%. Os retreinos usaram formulações
  parecidas com as que falhavam na validação, o que melhorou aquele repertório, mas
  não a generalização para frases novas.
- O modelo 1.0.0 não está mais no repositório; foi recuperado do histórico do git
  (commit anterior a `22f0d17`, arquivo `backend/app/nlu/intellix_nlu_v1.0.0.pt`).
