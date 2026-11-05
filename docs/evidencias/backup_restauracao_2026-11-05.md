# Backup e restauração — evidência (TC2 F10)

Atende ao feedback TC2 **F10** ("recuperação não pode depender de backup
presumido do plano gratuito"): aqui há um **backup próprio verificável**, com
restauração **em ambiente separado**, tempo e resultado registrados.

- **Data:** 05/11/2026
- **Banco:** Supabase (PostgreSQL), pooler de transação (porta 6543)
- **Ferramentas (versionadas):** `scripts/backup_db.py`,
  `scripts/verificar_restauracao.py`

## O que é "dump de esquema, dados e configurações"
- **Esquema:** versionado em `database/migrations/` (001–005). Não presume
  backup da plataforma; recria-se o schema rodando as migrations.
- **Dados:** `backup_db.py` gera um `.sql` lógico (INSERTs) + um manifesto
  (contagem por tabela e `sum(valor_total)`).
- **Configurações:** `backend/.env.example` (DATABASE_URL, EMPRESA_ID,
  NLU_BACKEND, SUPABASE_URL…) e as variáveis do Render.

## Backup (manifesto)

| Tabela | Linhas |
|---|---:|
| empresa | 20 |
| dim_data | 3.653 |
| dim_produto | 405 |
| dim_cliente | 3.005 |
| dim_vendedor | 72 |
| importacao | 16 |
| staging_venda | 57.707 |
| fato_item_venda | 66.657 |
| log_consulta | 12 |
| **sum(valor_total)** | **15.476.841,57** |

Arquivo gerado: `intellix_backup_20261105_1440.sql` — ~55 MB, 131.569 linhas.

## Restauração verificada (ambiente separado)

A restauração foi feita num **schema isolado** (`verif_restore`) do mesmo banco
— tabelas próprias criadas com `like public.<t>`, dump aplicado com
`search_path` no schema, contagens conferidas e o schema **descartado** ao fim
(não toca a produção). Razão: o plano gratuito não oferece um segundo banco à
vontade; um schema próprio é um ambiente de verificação isolado de verdade.

| Tabela | Restaurado | Esperado | OK |
|---|---:|---:|:--:|
| empresa | 20 | 20 | ✅ |
| dim_data | 3.653 | 3.653 | ✅ |
| dim_produto | 405 | 405 | ✅ |
| dim_cliente | 3.005 | 3.005 | ✅ |
| dim_vendedor | 72 | 72 | ✅ |
| importacao | 16 | 16 | ✅ |
| staging_venda | 57.707 | 57.707 | ✅ |
| fato_item_venda | 66.657 | 66.657 | ✅ |
| log_consulta | 12 | 12 | ✅ |

- **Tempo de restauração (dados):** **91,6 s** para ~128 mil linhas.
- **Resultado:** todas as tabelas bateram → **restauração validada**.

## RPO / RTO (proporcionais ao protótipo)

- **RPO (perda máxima aceitável):** até **24 h** / **sob demanda**. A base é
  **sintética e reprodutível** (`database/seed.py`, semente fixa) e importável
  por planilha, então a perda de dados tem impacto baixo; recomenda-se um backup
  **antes de cada deploy ou demonstração**.
- **RTO (tempo de recuperação):** meta **< 15 min**. Medido aqui: schema
  (migrations) em segundos + dados em **~1,5 min** para ~128 mil linhas — folga
  confortável para o volume do protótipo.

## Como reproduzir

```bash
cd backend            # usa o .env com a DATABASE_URL
python ../scripts/backup_db.py
python ../scripts/verificar_restauracao.py ../scripts/backups/intellix_backup_<TS>.sql
```
