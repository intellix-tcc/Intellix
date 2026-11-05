-- =====================================================================
-- 006_rls_e_usuario_app.sql  —  Intellix  —  C14, etapa A
--
-- Revisada e testada em 04/11/2026 (Postgres 16 local e Supabase dev).
-- Ordem: rodar no DEV -> testar o backend como intellix_app -> PROD ->
-- trocar o DATABASE_URL do Render para o intellix_app.
--
-- O QUE FAZ
--   1. Cria o usuário de banco da aplicação, `intellix_app`, com privilégio
--      mínimo. Hoje o backend conecta como `postgres`, que é dono de tudo e
--      ignora qualquer regra de RLS. É também o que o TCC (seção de
--      segurança) já afirma existir.
--   2. Liga RLS nas tabelas com empresa_id: o próprio Postgres só devolve
--      linhas da empresa declarada na transação
--      (set_config('app.empresa_id', ..., true)). Se uma consulta sair
--      errada, o banco não entrega dados de outra empresa.
--   3. Fecha o acesso pela API REST automática do Supabase (PostgREST) às
--      tabelas e views. A chave publishable foi para o navegador junto com o
--      login; ela não pode servir para ler vendas direto pela REST.
--
-- O QUE MUDA NO BACKEND (a fazer junto, mesmo PR):
--   - db.py: helper que roda `select set_config('app.empresa_id', %s, true)`
--     no início de cada transação. `true` = vale só nesta transação, o que
--     é compatível com o Transaction pooler (6543).
--   - acesso.py: declarar o empresa_id pedido ANTES de ler empresa.dono_id
--     (com RLS, a linha só aparece para a empresa declarada).
--   - etl.py: gerar o id da empresa nova no Python e declará-lo ANTES do
--     insert (um "returning id" de empresa não declarada é recusado); trocar
--     `refresh materialized view` pela função refresh_views() (só o dono da
--     view pode dar refresh).
--   - Render: DATABASE_URL passa a usar o usuário intellix_app.<ref>.
--   - Consequência: o "autocommit nas leituras" (-300 ms) fica descartado:
--     sem transação, o set_config se perderia entre um comando e outro.
--     Alternativa futura: modo pipeline do psycopg (manda BEGIN, set_config,
--     consulta e COMMIT numa ida e volta só).
--
-- Scripts administrativos (backup, seed, restore) continuam usando o
-- `postgres`, que é dono das tabelas e não passa pelo RLS.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 0. DIAGNÓSTICO (rodar antes, só leitura) -- ver o estado atual
-- ---------------------------------------------------------------------
-- RLS ligado em cada tabela?
--   select relname, relrowsecurity, relforcerowsecurity
--     from pg_class
--    where relnamespace = 'public'::regnamespace and relkind in ('r','m')
--    order by relname;
-- Quem tem acesso a quê (anon/authenticated são os papéis da REST):
--   select grantee, table_name, string_agg(privilege_type, ',') as privilegios
--     from information_schema.role_table_grants
--    where table_schema = 'public' and grantee in ('anon','authenticated')
--    group by 1, 2 order by 2, 1;
-- Políticas existentes:
--   select tablename, policyname, roles, cmd from pg_policies
--    where schemaname = 'public';


-- ---------------------------------------------------------------------
-- 1. Usuário da aplicação
-- ---------------------------------------------------------------------
-- A SENHA NÃO FICA NESTE ARQUIVO (ele vai para o Git). Depois de rodar,
-- defina no SQL Editor, numa consulta separada que não é salva:
--   alter role intellix_app with password '<gerar uma forte>';
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'intellix_app') then
    create role intellix_app login noinherit;
  end if;
end $$;

grant usage on schema public to intellix_app;
-- norm_key() (colunas nome_norm das dimensões) usa extensions.unaccent, e o
-- usuário da aplicação não tem acesso ao schema extensions. Em vez de dar esse
-- acesso (no Supabase, nem sempre o postgres pode repassá-lo), a função passa
-- a rodar com os direitos do dono: ela só normaliza texto, nada mais.
create or replace function norm_key(txt text)
returns text
language sql
immutable
security definer
set search_path = ''
as $$
  select lower(btrim(extensions.unaccent(coalesce(txt, ''))));
$$;

-- leitura das consultas do chat
grant select on dim_data, dim_produto, dim_cliente, dim_vendedor,
                fato_item_venda, empresa
  to intellix_app;

-- importação de planilhas (etl.py)
grant insert on empresa, importacao, staging_venda,
                dim_produto, dim_cliente, dim_vendedor, fato_item_venda
  to intellix_app;
grant select, update on importacao to intellix_app;
grant select on staging_venda to intellix_app;

-- registro de consultas
grant insert on log_consulta to intellix_app;

-- colunas "generated always as identity" precisam das sequências
grant usage on all sequences in schema public to intellix_app;

-- Sem update/delete nas vendas e sem acesso às views materializadas (o chat
-- não as usa; e views materializadas não aceitam RLS).


-- ---------------------------------------------------------------------
-- 2. Refresh das views pela aplicação
-- ---------------------------------------------------------------------
-- Só o dono da view pode dar refresh. Esta função roda com os direitos do
-- dono (security definer), faz só isso e mais nada.
create or replace function refresh_views()
returns void
language sql
security definer
set search_path = public
as $$
  refresh materialized view mv_faturamento_mensal;
  refresh materialized view mv_ranking_produtos;
  refresh materialized view mv_desempenho_vendedor;
$$;

revoke all on function refresh_views() from public;
grant execute on function refresh_views() to intellix_app;


-- ---------------------------------------------------------------------
-- 3. RLS por empresa
-- ---------------------------------------------------------------------
-- A empresa da transação vem de set_config('app.empresa_id', ..., true).
-- Sem declaração, current_setting(..., true) devolve nulo e nenhuma linha
-- aparece: o padrão é negar.

alter table empresa          enable row level security;
alter table importacao       enable row level security;
alter table staging_venda    enable row level security;
alter table dim_produto      enable row level security;
alter table dim_cliente      enable row level security;
alter table dim_vendedor     enable row level security;
alter table fato_item_venda  enable row level security;
alter table log_consulta     enable row level security;
-- dim_data é o calendário compartilhado (sem empresa_id). Se o RLS já estiver
-- ligado nele (no Supabase ele pode ter sido ligado pelo painel), o app
-- precisa de uma política de leitura; sem ela, nenhuma data aparece e toda
-- consulta por período volta vazia. Ligamos de propósito, para a REST
-- continuar sem acesso, e liberamos a leitura só para o app.
alter table dim_data enable row level security;
drop policy if exists app_calendario on dim_data;
create policy app_calendario on dim_data
  for select to intellix_app
  using (true);

-- empresa: vê só a declarada; pode criar novas (cada importação cria uma)
drop policy if exists app_empresa_ver on empresa;
create policy app_empresa_ver on empresa
  for select to intellix_app
  using (id = nullif(current_setting('app.empresa_id', true), '')::uuid);

drop policy if exists app_empresa_criar on empresa;
create policy app_empresa_criar on empresa
  for insert to intellix_app
  with check (true);

-- tabelas com empresa_id: ler e gravar só na empresa declarada
do $$
declare
  t text;
begin
  foreach t in array array['importacao', 'staging_venda', 'dim_produto',
                           'dim_cliente', 'dim_vendedor', 'fato_item_venda',
                           'log_consulta']
  loop
    execute format('drop policy if exists app_tenant on %I', t);
    execute format(
      'create policy app_tenant on %I to intellix_app '
      'using (empresa_id = nullif(current_setting(''app.empresa_id'', true), '''')::uuid) '
      'with check (empresa_id = nullif(current_setting(''app.empresa_id'', true), '''')::uuid)',
      t);
  end loop;
end $$;


-- ---------------------------------------------------------------------
-- 4. Fechar a API REST automática (PostgREST) para anon e authenticated
-- ---------------------------------------------------------------------
-- O Intellix não usa a REST do Supabase: o frontend fala com o nosso
-- backend. Mas a chave publishable está no navegador, e o Supabase dá
-- acesso às tabelas do schema public para esses papéis por padrão. Com RLS
-- ligado e sem política para eles, as tabelas já ficam vazias pela REST; as
-- views materializadas, porém, não têm RLS e ficariam expostas.
revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from anon, authenticated;
-- e para tabelas criadas no futuro:
alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;


-- ---------------------------------------------------------------------
-- 5. VERIFICAÇÃO (rodar depois)
-- ---------------------------------------------------------------------
-- a) Sem declarar empresa, o app não vê nada:
--      set role intellix_app;
--      select count(*) from fato_item_venda;            -- 0
-- b) Declarando a demo, vê só a demo:
--      select set_config('app.empresa_id', '00000000-0000-0000-0000-000000000001', false);
--      select count(*) from fato_item_venda;            -- 8941 no dev
--      select count(distinct empresa_id) from fato_item_venda;   -- 1
-- c) Não consegue apagar nem alterar vendas:
--      delete from fato_item_venda;                     -- ERRO: permission denied
--      reset role;
-- d) A REST não lê mais nada (no navegador, com a chave publishable):
--      https://<ref>.supabase.co/rest/v1/fato_item_venda?select=*&apikey=<publishable>
--      -> erro de permissão (42501), e nunca linhas de vendas.
