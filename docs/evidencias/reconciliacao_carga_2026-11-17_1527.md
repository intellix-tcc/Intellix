# Reconciliação de carga com planilha de teste (F06)

Planilha de teste com conteúdo conhecido, carregada pela ETL real
(`app.importacao.etl.importar`) e reconciliada contra o banco. Gerado por
`scripts/reconciliacao_carga.py`.

- **Data:** 17/11/2026 15:27 (UTC+0000)
- **Planilha:** 6 linhas · 3 vendas · inclui produto repetido na mesma venda (grão) e multi-item

## Reconciliação (planilha esperado × banco carregado)

| Invariante | Esperado (planilha) | Carregado (banco) | OK |
|---|---|---|:-:|
| Vendas distintas | 3 | 3 | ✅ |
| Itens (linhas de fato, após o grão) | 5 | 5 | ✅ |
| Faturamento total | 290.00 | 290.00 | ✅ |
| Ticket médio | 96.67 | 96.67 | ✅ |
| Linhas agrupadas (repetidas somadas) | 1 | 1 | ✅ |
| Caneca em V1 — quantidade somada | 3 | 3 | ✅ |
| Caneca em V1 — valor somado | 75.00 | 75.00 | ✅ |
| Integridade referencial (linhas de fato órfãs) | 0 | 0 | ✅ |

## Invariantes de grão

- **Produto repetido na mesma venda é SOMADO, não descartado:** as duas linhas
  de "Caneca"/"caneca " em V1 viram **1 item** com quantidade **3** e total **R$ 75.00** (a dedupe por `nome_norm` casa as duas grafias; o valor não se perde).
- **Mesmo produto em vendas diferentes continua separado:** "Camiseta" em V1 e V3
  são dois itens, em duas vendas — a chave do grão é (empresa, venda, produto).

## Idempotência / reenvio

Reenviar o mesmo arquivo criou um dataset isolado (`5ef2e950…` ≠ `3ad4ca56…`) com **os mesmos**
totais (faturamento R$ 290.00, 5 itens), sem duplicar
itens dentro do dataset (chave única da fato `on conflict do nothing`): **✅**.

## Resultado: ✅ reconciliação completa

A reconciliação de **valor** (não só contagem de tabelas) também é a prova que a
banca pede após uma restauração: as mesmas consultas (vendas, itens, faturamento,
ticket, órfãs) aplicadas ao banco restaurado devem bater com a origem — ver
`docs/evidencias/backup_restauracao_2026-11-05.md` para o ciclo de dump/restore.

