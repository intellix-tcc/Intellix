# Migrations aplicadas

| Migration | dev | prod | Observação |
|---|---|---|---|
| 001_schema.sql | 23/07/2026 | 23/07/2026 | RLS habilitado |
| 002_dim_data.sql | 23/07/2026 | 23/07/2026 | 1461 linhas |
| seed.py | 23/07/2026 | — | 8941 itens, R$ 2,72 mi |
| 003_estende_dim_data.sql | 27/10/2026 | 27/10/2026 | estende para 2027–2032 (3653 linhas) |
| 004_views_ranking_desempenho.sql | ago/2026 | ago/2026 | views já existiam (criadas por um 003_views.sql nunca versionado); a 004 recria o registro |
| 005_dono_do_dataset.sql | 27/10/2026 | 27/10/2026 | empresa.dono_id → auth.users (login, PR feat/autenticacao) |
| 006_protege_api_do_supabase.sql | coberta pela 006_rls | coberta pela 006_rls | fecha as tabelas e views para a API REST pública do Supabase (RLS sem política + revoke de anon/authenticated). Veio do PR de segurança de 05/11, em paralelo à 006_rls; a 006_rls faz o mesmo e mais, e já está aplicada nos dois bancos. Rodar esta também é seguro (as duas são idempotentes). Conferir com a consulta abaixo |
| 006_rls_e_usuario_app.sql | 05/11/2026 | 05/11/2026 | usuário intellix_app (privilégio mínimo) + RLS por empresa (`app_tenant`, `app_empresa_ver`, `app_empresa_criar`, `app_calendario`) + REST fechada para anon/authenticated. Verificação: dev `1\|9\|1`, prod `1\|10\|1`. Render passou a conectar como `intellix_app` (PR #26) e a senha do `postgres` do prod foi trocada |
| 007_minhas_planilhas.sql | 06/11/2026 | 06/11/2026 | funções listar_planilhas e excluir_planilha (security definer, filtram por dono_id); EXECUTE só para intellix_app. O grant só é feito se o intellix_app já existir; no prod ele existe desde 05/11 (006_rls), então a 007 aplicada em 06/11 deve ter concedido o EXECUTE. Conferir com a consulta abaixo. Necessária para GET/DELETE /planilhas |
| 008_historico_conversas.sql | a aplicar | a aplicar | tabela `conversa` (JSONB de mensagens por `dono_id` → auth.users, on delete cascade) + RLS ligado sem política para a REST + funções listar_conversas/salvar_conversa/excluir_conversa (security definer, filtram por dono); EXECUTE só para intellix_app. Mesmo desenho da 007. Necessária para GET/PUT/DELETE /conversas (histórico de conversas na conta). Idempotente. Validada em Postgres 16 local (isolamento entre dois usuários). Aplicar no dev → testar o backend → prod |

## Duas migrations com o número 006

`006_protege_api_do_supabase.sql` e `006_rls_e_usuario_app.sql` foram criadas
em PRs paralelos no mesmo dia. Os nomes ficam como estão (renomear uma
migration já aplicada confunde o histórico); a ordem alfabética, que é a do CI,
roda a `protege` antes da `rls`, e as duas são idempotentes.

Para saber o que está aplicado num banco, rode no SQL Editor do Supabase:

```sql
select
  (select bool_and(relrowsecurity) from pg_class
    where relnamespace = 'public'::regnamespace
      and relname in ('empresa','importacao','staging_venda','dim_data','dim_produto',
                      'dim_cliente','dim_vendedor','fato_item_venda','log_consulta')) as rls_em_todas_as_tabelas,
  has_table_privilege('anon', 'public.fato_item_venda', 'select')      as rest_publica_le_vendas,
  has_table_privilege('anon', 'public.mv_faturamento_mensal', 'select') as rest_publica_le_views,
  exists (select 1 from pg_roles    where rolname    = 'intellix_app')  as existe_intellix_app,
  exists (select 1 from pg_policies where policyname = 'app_tenant')    as existe_rls_por_empresa,
  has_function_privilege('intellix_app', 'public.listar_planilhas(uuid)', 'execute') as app_lista_planilhas;
```

Leitura:
- `rls_em_todas_as_tabelas = true` e as duas colunas `rest_publica_* = false`:
  o efeito da `006_protege` está aplicado.
- `existe_intellix_app = true` e `existe_rls_por_empresa = true`: a
  `006_rls_e_usuario_app` está aplicada.
- `app_lista_planilhas = true`: a `007` concedeu o EXECUTE ao intellix_app.

## Regiões dos projetos Supabase

- `intellix-dev`: sa-east-1 (São Paulo)
- `intellix-prod`: us-west-2 (Oregon, EUA); pooler `aws-1-us-west-2.pooler.supabase.com:6543`
