# Avaliação de generalização — perguntas inéditas

Conjunto redigido fora dos moldes de treino e das 100 perguntas, com
gabarito de intenção e de valor (parecer da banca final, F01 e item nº 1 da
defesa). Gerado por `scripts/avaliar_ineditas.py`.

- **Data:** 18/11/2026 23:55 (UTC+0000)  ·  **modo:** `app`  ·  **alvo:** FastAPI TestClient (ponta a ponta)
- **Congelamento:** commit `4338282` · modelo `intellix_nlu_v1.2.0.pt` SHA-256 `ea30338e9626f4b6…` · limiar 0.7
- **Perguntas:** 30 (24 respondíveis + 6 de recusa)

## Resumo

| Nível | Métrica |
|---|---|
| Semântico (intenção/decisão certa) | 27/30 (90.0%) |
| Numérico (valor confere, quando aplicável) | 21/24 (87.5%) |
| **Acerto combinado** | **27/30 (90.0%)** · IC95% Wilson [74.4% – 96.5%] |

> O intervalo de Wilson é largo de propósito: a amostra é pequena. Ele
> expressa a incerteza honesta sobre a generalização, não um ponto único.

## Por pergunta

| ID | Intenção esperada | Téc | Sem | Num | Obtido / detalhe |
|---|---|:-:|:-:|:-:|---|
| R01 | `total_vendas_periodo` | ✅ | ❌ | ❌ | intenção variacao_periodo ≠ total_vendas_periodo |
| R02 | `total_vendas_periodo` | ✅ | ✅ | ✅ | esp=681130.94 obt=681130.94 |
| R03 | `top_produtos` | ✅ | ✅ | ✅ | esp=Smartwatch obt=Smartwatch |
| R04 | `top_produtos` | ✅ | ✅ | ✅ | esp=Smartwatch obt=Smartwatch |
| R05 | `ticket_medio` | ✅ | ✅ | ✅ | esp=770.51 obt=770.51 |
| R06 | `ticket_medio` | ✅ | ✅ | ✅ | esp=770.51 obt=770.51 |
| R07 | `quantidade_vendas` | ✅ | ✅ | ✅ | esp=57 obt=57 |
| R08 | `quantidade_vendas` | ❌ | ❌ | ❌ | intenção (422) ≠ quantidade_vendas |
| R09 | `top_clientes` | ✅ | ✅ | ✅ | esp=Ana Ribeiro obt=Ana Ribeiro |
| R10 | `top_clientes` | ✅ | ✅ | ✅ | esp=Isabela Ferreira obt=Isabela Ferreira |
| R11 | `desempenho_vendedor` | ✅ | ✅ | ✅ | esp=101487.15 obt=101487.15 |
| R12 | `desempenho_vendedor` | ✅ | ✅ | ✅ | esp=124385.32 obt=124385.32 |
| R13 | `produtos_sem_saida` | ✅ | ✅ | ✅ | esp=['Batom matte', 'Bota couro', 'Caixa de som portátil', 'Creme hidratante', 'Kit organizador', 'Power bank', 'Vestido casual'] obt=['Batom matte', 'Bota couro', 'Caixa de som portátil', 'Creme hidratante', 'Kit organizador', 'Power bank', 'Vestido casual'] |
| R14 | `produtos_sem_saida` | ✅ | ✅ | ✅ | esp=[] obt=[] |
| R15 | `comparacao_periodos` | ❌ | ❌ | ❌ | intenção (422) ≠ comparacao_periodos |
| R16 | `comparacao_periodos` | ✅ | ✅ | ✅ | esp=(Decimal('681130.94'), Decimal('648875.81')) obt=(Decimal('681130.94'), Decimal('648875.81')) |
| R17 | `variacao_periodo` | ✅ | ✅ | ✅ | esp=9.81 obt=9.81 |
| R18 | `variacao_periodo` | ✅ | ✅ | ✅ | esp=4.97 obt=4.97 |
| R19 | `vendas_por_canal` | ✅ | ✅ | ✅ | esp=loja obt=loja |
| R20 | `vendas_por_canal` | ✅ | ✅ | ✅ | esp=loja obt=loja |
| R21 | `vendas_por_categoria` | ✅ | ✅ | ✅ | esp=Eletrônicos obt=Eletrônicos |
| R22 | `vendas_por_categoria` | ✅ | ✅ | ✅ | esp=Eletrônicos obt=Eletrônicos |
| R23 | `vendas_por_pagamento` | ✅ | ✅ | ✅ | esp=pix obt=pix |
| R24 | `vendas_por_pagamento` | ✅ | ✅ | ✅ | esp=pix obt=pix |
| R25 | `fora_de_escopo` | ✅ | ✅ | ✅ | recusou por baixa confiança |
| R26 | `fora_de_escopo` | ✅ | ✅ | ✅ | recusou por baixa confiança |
| R27 | `parametro_faltando` | ✅ | ✅ | ✅ | pediu parâmetro (422) |
| R28 | `parametro_faltando` | ✅ | ✅ | ✅ | pediu parâmetro (422) |
| R29 | `sem_resultado` | ✅ | ✅ | ✅ | 404 sem_resultado |
| R30 | `sem_resultado` | ✅ | ✅ | ✅ | 404 sem_resultado |

## Por intenção (respondíveis)

| Intenção | Acerto |
|---|---:|
| `comparacao_periodos` | 1/2 |
| `desempenho_vendedor` | 2/2 |
| `produtos_sem_saida` | 2/2 |
| `quantidade_vendas` | 1/2 |
| `ticket_medio` | 2/2 |
| `top_clientes` | 2/2 |
| `top_produtos` | 2/2 |
| `total_vendas_periodo` | 1/2 |
| `variacao_periodo` | 2/2 |
| `vendas_por_canal` | 2/2 |
| `vendas_por_categoria` | 2/2 |
| `vendas_por_pagamento` | 2/2 |

## Comportamento nas recusas

6/6 recusas corretas (fora de escopo → baixa confiança; parâmetro ausente → 422; fora do período dos dados → 404).

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

