# Migrations aplicadas

| Migration | dev | prod | Observação |
|---|---|---|---|
| 001_schema.sql | 23/07/2026 | 23/07/2026 | RLS habilitado |
| 002_dim_data.sql | 23/07/2026 | 23/07/2026 | 1461 linhas |
| seed.py | 23/07/2026 | — | 8941 itens, R$ 2,72 mi |
| 003_estende_dim_data.sql | 27/10/2026 | 27/10/2026 | estende para 2027–2032 (3653 linhas) |
| 004_views_ranking_desempenho.sql | ago/2026 | ago/2026 | views já existiam (criadas por um 003_views.sql nunca versionado); a 004 recria o registro |
| 005_dono_do_dataset.sql | 27/10/2026 | 27/10/2026 | empresa.dono_id → auth.users (login, PR feat/autenticacao) |
| 006_rls_e_usuario_app.sql | 05/11/2026 | — | usuário intellix_app (privilégio mínimo) + RLS por empresa + REST fechada. No dev, também `app_calendario` em dim_data (RLS já estava ligado). Views do prod fechadas para a REST em 04/11 (revoke manual) |
| 007_minhas_planilhas.sql | — | — | funções listar_planilhas e excluir_planilha (security definer, filtram por dono_id); EXECUTE só para intellix_app. **Aplicar antes de publicar o backend com GET/DELETE /planilhas** |
