# Avaliação de generalização — perguntas inéditas

Conjunto redigido fora dos moldes de treino e das 100 perguntas, com
gabarito de intenção e de valor (parecer da banca final, F01 e item nº 1 da
defesa). Gerado por `scripts/avaliar_ineditas.py`.

- **Data:** 17/11/2026 15:13 (UTC+0000)  ·  **modo:** `nlu`  ·  **alvo:** ModeloTreinadoNLU (classificação)
- **Congelamento:** commit `7cff7aa` · modelo `intellix_nlu_v1.2.0.pt` SHA-256 `ea30338e9626f4b6…` · limiar 0.7
- **Perguntas:** 26 (24 respondíveis + 2 de recusa)

## Resumo

| Nível | Métrica |
|---|---|
| Semântico (intenção/decisão certa) | 10/26 (38.5%) |
| Numérico (valor confere, quando aplicável) | 0/0 |
| **Acerto combinado** | **10/26 (38.5%)** · IC95% Wilson [22.4% – 57.5%] |

> O intervalo de Wilson é largo de propósito: a amostra é pequena. Ele
> expressa a incerteza honesta sobre a generalização, não um ponto único.

## Por pergunta

| ID | Intenção esperada | Téc | Sem | Num | Obtido / detalhe |
|---|---|:-:|:-:|:-:|---|
| I01 | `total_vendas_periodo` | ✅ | ❌ | — | obteve variacao_periodo |
| I02 | `total_vendas_periodo` | ✅ | ❌ | — | obteve produtos_sem_saida |
| I03 | `top_produtos` | ✅ | ❌ | — | obteve quantidade_vendas |
| I04 | `top_produtos` | ✅ | ❌ | — | obteve variacao_periodo |
| I05 | `ticket_medio` | ✅ | ✅ | — | intenção certa |
| I06 | `ticket_medio` | ✅ | ✅ | — | intenção certa |
| I07 | `quantidade_vendas` | ✅ | ✅ | — | intenção certa |
| I08 | `quantidade_vendas` | ✅ | ✅ | — | intenção certa |
| I09 | `top_clientes` | ✅ | ❌ | — | obteve desempenho_vendedor |
| I10 | `top_clientes` | ✅ | ❌ | — | obteve quantidade_vendas |
| I11 | `desempenho_vendedor` | ✅ | ✅ | — | intenção certa |
| I12 | `desempenho_vendedor` | ✅ | ❌ | — | obteve total_vendas_periodo |
| I13 | `produtos_sem_saida` | ✅ | ❌ | — | obteve quantidade_vendas |
| I14 | `produtos_sem_saida` | ✅ | ✅ | — | intenção certa |
| I15 | `comparacao_periodos` | ✅ | ❌ | — | obteve total_vendas_periodo |
| I16 | `comparacao_periodos` | ✅ | ❌ | — | obteve comparacao_periodos |
| I17 | `variacao_periodo` | ✅ | ✅ | — | intenção certa |
| I18 | `variacao_periodo` | ✅ | ❌ | — | obteve comparacao_periodos |
| I19 | `vendas_por_canal` | ✅ | ✅ | — | intenção certa |
| I20 | `vendas_por_canal` | ✅ | ❌ | — | obteve comparacao_periodos |
| I21 | `vendas_por_categoria` | ✅ | ❌ | — | obteve top_produtos |
| I22 | `vendas_por_categoria` | ✅ | ❌ | — | obteve quantidade_vendas |
| I23 | `vendas_por_pagamento` | ✅ | ❌ | — | obteve quantidade_vendas |
| I24 | `vendas_por_pagamento` | ✅ | ❌ | — | obteve top_clientes |
| I25 | `fora_de_escopo` | ✅ | ✅ | ✅ | rejeitada (conf < 0,70) |
| I26 | `fora_de_escopo` | ✅ | ✅ | ✅ | rejeitada (conf < 0,70) |
| I27 | `parametro_faltando` | — | — | — | depende do executor/banco (só no modo app) |
| I28 | `parametro_faltando` | — | — | — | depende do executor/banco (só no modo app) |
| I29 | `sem_resultado` | — | — | — | depende do executor/banco (só no modo app) |
| I30 | `sem_resultado` | — | — | — | depende do executor/banco (só no modo app) |

## Por intenção (respondíveis)

| Intenção | Acerto |
|---|---:|
| `comparacao_periodos` | 0/2 |
| `desempenho_vendedor` | 1/2 |
| `produtos_sem_saida` | 1/2 |
| `quantidade_vendas` | 2/2 |
| `ticket_medio` | 2/2 |
| `top_clientes` | 0/2 |
| `top_produtos` | 0/2 |
| `total_vendas_periodo` | 0/2 |
| `variacao_periodo` | 1/2 |
| `vendas_por_canal` | 1/2 |
| `vendas_por_categoria` | 0/2 |
| `vendas_por_pagamento` | 0/2 |

## Comportamento nas recusas

2/2 recusas corretas (fora de escopo → baixa confiança; parâmetro ausente → 422; fora do período dos dados → 404).

## Limite honesto (método)

- As perguntas foram redigidas pela equipe de desenvolvimento evitando os
  moldes de treino; para rigor máximo na defesa, **some perguntas coletadas
  de pessoas de fora** da equipe e reexecute — o avaliador aceita qualquer
  `perguntas_ineditas.jsonl`.
- O gabarito de valor é recomputado em Python puro (independente do SQL).
- As 100 perguntas seguem como **regressão** (`avaliar_100_perguntas.py`), não
  como prova de generalização.

## Reproduzir

```bash
DATABASE_URL=postgresql://... NLU_BACKEND=modelo \
EMPRESA_ID=00000000-0000-0000-0000-000000000001 \
    python scripts/avaliar_ineditas.py --modo app --saida docs/evidencias
python scripts/avaliar_ineditas.py --modo nlu   # só a intenção
```

