# Migrations aplicadas

| Migration | dev | prod | Observação |
|---|---|---|---|
| 001_schema.sql | 23/07/2026 | 23/07/2026 | RLS habilitado |
| 002_dim_data.sql | 23/07/2026 | 23/07/2026 | 1461 linhas |
| seed.py | 23/07/2026 | — | 8941 itens, R$ 2,72 mi |
| 003_estende_dim_data.sql | 27/10/2026 | 27/10/2026 | estende para 2027–2032 (3653 linhas) |
| 004_views_ranking_desempenho.sql | ago/2026 | ago/2026 | views já existiam (criadas por um 003_views.sql nunca versionado); a 004 recria o registro |
| 005_dono_do_dataset.sql | 27/10/2026 | 27/10/2026 | empresa.dono_id → auth.users (login, PR feat/autenticacao) |
