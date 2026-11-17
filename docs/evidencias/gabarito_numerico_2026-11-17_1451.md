# Gabarito numérico independente das 14 consultas

Oráculo independente que confere os **valores** das consultas (parecer da
banca final, F02). A verdade esperada é recomputada em Python puro a partir
da geração determinística do `database/seed.py` (SEED=42); o obtido vem dos
templates SQL reais de `backend/app/sql/templates.py`. Gerado por
`scripts/gabarito_numerico.py`.

- **Data:** 17/11/2026 14:51 (UTC+0000)
- **Base:** empresa demo `00000000-0000-0000-0000-000000000001` — 8.941 itens / 3.527 vendas / R$ 2.717.797,23
- **Alvo:** localhost:5432/intellix

## Resumo

| Nível de sucesso | O que verifica | Provas |
|---|---|---:|
| Técnico | executou sem erro, devolveu linhas | 19/19 |
| Semântico | colunas, grão, agrupamento, ordenação | 19/19 |
| **Numérico** | **todos os valores batem com o oráculo** | **19/19** |

## Provas

| ID | Intenção | O que verifica | Téc | Sem | **Num** | Detalhe |
|---|---|---|:-:|:-:|:-:|---|
| P01 | `total_vendas_periodo` | Faturamento 2024, por mês | ✅ | ✅ | ✅ | 12 meses; ∑=648875.81; ordem asc confere |
| P02 | `ticket_medio` | Ticket médio 2024 (= faturamento / vendas distintas) | ✅ | ✅ | ✅ | 749.28 por venda (média por ITEM seria 299.57 — descartada) |
| P03 | `quantidade_vendas` | Qtd de vendas distintas 2024, por mês | ✅ | ✅ | ✅ | 866 vendas no ano (distintas, não itens) |
| P04 | `top_produtos` | Top 5 produtos de 2024 (faturamento desc) | ✅ | ✅ | ✅ | 1º = Smartwatch (55608.43, 140 peças); ordem e limite conferem |
| P05 | `top_clientes` | Top 5 clientes de 2024 | ✅ | ✅ | ✅ | 1º = Bruno Costa (26688.11); top 5 e ordem conferem |
| P06 | `desempenho_vendedor` | Desempenho de 'Carlos Nunes' em 2024 (filtro) | ✅ | ✅ | ✅ | Carlos Nunes: 100664.85 em 141 vendas; filtro isola o vendedor |
| P07 | `produtos_sem_saida` | Produtos sem saída em fev/2024 | ✅ | ✅ | ✅ | 1 produto(s) sem saída no mês; conjunto confere |
| P08 | `comparacao_periodos` | Comparar jan/2024 × fev/2024 | ✅ | ✅ | ✅ | A=38174.92  B=35548.73; rótulos e valores conferem |
| P09 | `variacao_periodo` | Variação mar/2024 vs fev/2024 (%) | ✅ | ✅ | ✅ | atual=39275.59 ant=35548.73 var=10.48% |
| P10 | `unidades_vendidas` | Unidades (peças) vendidas 2024, por mês | ✅ | ✅ | ✅ | 5185 peças (≠ 866 vendas — unidade distinta) |
| P11 | `vendas_por_canal` | Vendas por canal 2024 (desc) | ✅ | ✅ | ✅ | 4 canais; 1º=loja (302107.93); ordem e contagem conferem |
| P12 | `vendas_por_categoria` | Vendas por categoria 2024 (desc) | ✅ | ✅ | ✅ | 8 categorias; 1ª=Eletrônicos (120898.02) |
| P13 | `vendas_por_pagamento` | Vendas por forma de pagamento 2024 (desc) | ✅ | ✅ | ✅ | 5 formas; 1ª=pix (211361.31) |
| P14 | `melhor_mes` | Série 2024 e identificação do mês de pico | ✅ | ✅ | ✅ | 12 meses; pico em 2024-12 (119044.59) |
| P15 | `total_vendas_periodo` | Faturamento 2024 filtrado por categoria 'Calçados' | ✅ | ✅ | ✅ | ∑Calçados=119635.40 < ∑total=648875.81; filtro aplicado |
| P16 | `ticket_medio` | Ticket médio 2024 só no canal 'site' (filtro) | ✅ | ✅ | ✅ | ticket(site)=767.44; recorte por canal confere |
| P17 | `ticket_medio` | Período sem vendas (2018) → ticket NULO | ✅ | ✅ | ✅ | retorna uma linha com ticket = NULL (nullif evita divisão por zero → executor responde 404) |
| P18 | `total_vendas_periodo` | Fronteira: venda no último dia do período entra | ✅ | ✅ | ✅ | 2024-12-31 incluído: ∑=3368.00 (between é inclusivo nas duas pontas) |
| P19 | `quantidade_vendas` | Venda com vários itens conta 1 vez | ✅ | ✅ | ✅ | venda V000000 tem 2 itens e entra 1× em 2024-12 (count distinct venda_id) |

## Cobertura (parecer F02)

- **Valor, filtro, grupo, ordenação, unidade:** P01–P16 cobrem as 14 consultas,
  mais recortes por categoria (P15) e canal (P16); unidade peças × vendas em P03/P10.
- **Nulos:** P17 — período sem vendas devolve ticket `NULL` (base do 404 `sem_resultado`).
- **Fronteira de período:** P18 — `between` inclui o último dia.
- **Venda com vários itens:** P19 — contada uma única vez (`count(distinct venda_id)`).
- **Devoluções:** o artefato **não modela devolução/estorno** (`fato_item_venda` tem
  `quantidade` inteira ≥ 0, sem fluxo de retorno). Declarado fora do escopo — não simulado.

## Reproduzir

```bash
# banco local (ver README) semeado com database/seed.py
DATABASE_URL=postgresql://... python scripts/gabarito_numerico.py --saida docs/evidencias
# ou como teste (pytest):
cd backend && pytest tests/test_gabarito_numerico.py -q
```

## Limite honesto

Este gabarito prova que **a consulta certa calcula o valor certo**. Ele não mede
se o NLU escolhe a consulta certa (isso é a bateria de 100 perguntas, por status +
título) nem substitui a verificação semântica de ponta a ponta — é a camada de
**correção numérica** que faltava entre os dois.

