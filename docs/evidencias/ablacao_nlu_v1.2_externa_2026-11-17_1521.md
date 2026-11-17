# Ablação do NLU na v1.2.0 — corpus externo, oráculo numérico (F03)

Repete a ablação (`ablacao_nlu.py`) na **versão 1.2.0**, sobre o conjunto
**inédito** (`docs/perguntas_ineditas.jsonl`, externo ao treino e às 100), com
**oráculo numérico**: cada aceito é executado e o valor conferido. Gerado por
`ia training/ablacao_nlu_externa.py`.

- **Data:** 17/11/2026 15:21 (UTC+0000)
- **Modelo:** `intellix_nlu_v1.2.0.pt` · **perguntas respondíveis:** 24

## Cobertura e risco por configuração

| Config | Aceitos | Valor certo | **Risco** (aceito errado) | Recusados |
|---|---:|---:|---:|---:|
| B regras | 1/24 | 1/24 | **0/24** | 23/24 |
| A modelo (atual) | 8/24 | 7/24 | **1/24** | 16/24 |
| C modelo sem BIO | 8/24 | 7/24 | **1/24** | 16/24 |
| D modelo só regras | 7/24 | 6/24 | **1/24** | 17/24 |

**A − C = +0 acerto(s) de valor** → contribuição da cabeça de entidades (BIO).
**C − D = +1 acerto(s) de valor** → contribuição da heurística de nome.

## Onde BIO/heurística atuam: desempenho_vendedor

| Config | Vendedor aceito | Vendedor com valor certo |
|---|---:|---:|
| B regras | 0 | 0 |
| A modelo (atual) | 1 | 1 |
| C modelo sem BIO | 1 | 1 |
| D modelo só regras | 0 | 0 |

## Conclusão (manter a cabeça de entidades?)

No corpus externo e com oráculo numérico, a cabeça BIO adiciona **+0**
acerto(s) de valor sobre a configuração sem BIO. A resolução de slots (período,
limite) é determinística (regras) e independe do BIO; o nome do vendedor é
recuperado pela heurística de regex. Logo, a cabeça de entidades se justifica
**por finalidade de pesquisa / robustez**, não por ganho operacional demonstrado
neste conjunto — conforme o ponto do parecer (F03). As 100 perguntas seguem como
regressão; este conjunto mede generalização.

