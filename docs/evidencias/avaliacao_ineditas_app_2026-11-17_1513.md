# Avaliação de generalização — perguntas inéditas

Conjunto redigido fora dos moldes de treino e das 100 perguntas, com
gabarito de intenção e de valor (parecer da banca final, F01 e item nº 1 da
defesa). Gerado por `scripts/avaliar_ineditas.py`.

- **Data:** 17/11/2026 15:13 (UTC+0000)  ·  **modo:** `app`  ·  **alvo:** FastAPI TestClient (ponta a ponta)
- **Congelamento:** commit `7cff7aa` · modelo `intellix_nlu_v1.2.0.pt` SHA-256 `ea30338e9626f4b6…` · limiar 0.7
- **Perguntas:** 30 (24 respondíveis + 6 de recusa)

## Resumo

| Nível | Métrica |
|---|---|
| Semântico (intenção/decisão certa) | 13/30 (43.3%) |
| Numérico (valor confere, quando aplicável) | 8/24 (33.3%) |
| **Acerto combinado** | **13/30 (43.3%)** · IC95% Wilson [27.4% – 60.8%] |

> O intervalo de Wilson é largo de propósito: a amostra é pequena. Ele
> expressa a incerteza honesta sobre a generalização, não um ponto único.

## Por pergunta

| ID | Intenção esperada | Téc | Sem | Num | Obtido / detalhe |
|---|---|:-:|:-:|:-:|---|
| I01 | `total_vendas_periodo` | ✅ | ❌ | ❌ | intenção variacao_periodo ≠ total_vendas_periodo |
| I02 | `total_vendas_periodo` | ❌ | ❌ | ❌ | intenção (422) ≠ total_vendas_periodo |
| I03 | `top_produtos` | ✅ | ❌ | ❌ | intenção (200) ≠ top_produtos |
| I04 | `top_produtos` | ❌ | ❌ | ❌ | intenção (422) ≠ top_produtos |
| I05 | `ticket_medio` | ✅ | ✅ | ✅ | esp=770.51 obt=770.51 |
| I06 | `ticket_medio` | ✅ | ✅ | ✅ | esp=790.68 obt=790.68 |
| I07 | `quantidade_vendas` | ✅ | ✅ | ✅ | esp=59 obt=59 |
| I08 | `quantidade_vendas` | ✅ | ✅ | ✅ | esp=884 obt=884 |
| I09 | `top_clientes` | ❌ | ❌ | ❌ | intenção (422) ≠ top_clientes |
| I10 | `top_clientes` | ✅ | ❌ | ❌ | intenção quantidade_vendas ≠ top_clientes |
| I11 | `desempenho_vendedor` | ✅ | ✅ | ✅ | esp=101487.15 obt=101487.15 |
| I12 | `desempenho_vendedor` | ✅ | ❌ | ❌ | intenção total_vendas_periodo ≠ desempenho_vendedor |
| I13 | `produtos_sem_saida` | ❌ | ❌ | ❌ | intenção (422) ≠ produtos_sem_saida |
| I14 | `produtos_sem_saida` | ✅ | ✅ | ✅ | esp=[] obt=[] |
| I15 | `comparacao_periodos` | ❌ | ❌ | ❌ | intenção (422) ≠ comparacao_periodos |
| I16 | `comparacao_periodos` | ❌ | ❌ | ❌ | intenção (422) ≠ comparacao_periodos |
| I17 | `variacao_periodo` | ✅ | ✅ | ✅ | esp=9.81 obt=9.81 |
| I18 | `variacao_periodo` | ✅ | ❌ | ❌ | intenção comparacao_periodos ≠ variacao_periodo |
| I19 | `vendas_por_canal` | ✅ | ✅ | ✅ | esp=loja obt=loja |
| I20 | `vendas_por_canal` | ❌ | ❌ | ❌ | intenção (422) ≠ vendas_por_canal |
| I21 | `vendas_por_categoria` | ✅ | ❌ | ❌ | intenção top_produtos ≠ vendas_por_categoria |
| I22 | `vendas_por_categoria` | ❌ | ❌ | ❌ | intenção (422) ≠ vendas_por_categoria |
| I23 | `vendas_por_pagamento` | ✅ | ❌ | ❌ | intenção quantidade_vendas ≠ vendas_por_pagamento |
| I24 | `vendas_por_pagamento` | ✅ | ❌ | ❌ | intenção top_clientes ≠ vendas_por_pagamento |
| I25 | `fora_de_escopo` | ✅ | ✅ | ✅ | recusou por baixa confiança |
| I26 | `fora_de_escopo` | ✅ | ✅ | ✅ | recusou por baixa confiança |
| I27 | `parametro_faltando` | ✅ | ✅ | ✅ | pediu parâmetro (422) |
| I28 | `parametro_faltando` | ✅ | ✅ | ✅ | pediu parâmetro (422) |
| I29 | `sem_resultado` | ❌ | ❌ | ❌ | esperado 404; veio 422/baixa_confianca |
| I30 | `sem_resultado` | ✅ | ✅ | ✅ | 404 sem_resultado |

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

5/6 recusas corretas (fora de escopo → baixa confiança; parâmetro ausente → 422; fora do período dos dados → 404).

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

