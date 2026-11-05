-- =============================================================================
-- 006 · Fecha as tabelas para a API pública do Supabase (PostgREST)
-- -----------------------------------------------------------------------------
-- O site usa a chave "anon" do Supabase para o login. Essa chave é pública por
-- natureza: vai no JavaScript que qualquer visitante baixa. Sem RLS, a mesma
-- chave permitiria ler (e alterar) estas tabelas direto pela API REST do
-- Supabase (https://<projeto>.supabase.co/rest/v1/...), sem passar pelo
-- backend do Intellix -- incluindo as vendas importadas por outros usuários.
--
-- O Intellix não acessa estas tabelas pela API do Supabase: quem lê e grava é
-- só o backend (FastAPI), conectado direto ao Postgres como dono das tabelas,
-- e dono não é afetado por RLS. Então basta:
--   1. ativar RLS em todas as tabelas, SEM nenhuma política: para os papéis
--      anon/authenticated o resultado é "nenhuma linha";
--   2. revogar desses papéis o acesso às views materializadas (RLS não vale
--      para views materializadas) e às sequências;
--   3. impedir que tabelas criadas no futuro nasçam abertas.
--
-- Idempotente: pode rodar mais de uma vez.
-- Como aplicar: SQL Editor do Supabase -> colar -> Run.
-- Como conferir: ver "Como testar" no fim do arquivo.
-- =============================================================================

alter table if exists empresa          enable row level security;
alter table if exists importacao       enable row level security;
alter table if exists staging_venda    enable row level security;
alter table if exists dim_data         enable row level security;
alter table if exists dim_produto      enable row level security;
alter table if exists dim_cliente      enable row level security;
alter table if exists dim_vendedor     enable row level security;
alter table if exists fato_item_venda  enable row level security;
alter table if exists log_consulta     enable row level security;

-- Os papéis da API pública não precisam de nada no schema public.
do $$
declare
  papel text;
begin
  foreach papel in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = papel) then
      execute format('revoke all on all tables in schema public from %I', papel);
      execute format('revoke all on all sequences in schema public from %I', papel);
      execute format('revoke all on all functions in schema public from %I', papel);
      -- tabelas, sequências e funções criadas depois desta migration
      execute format('alter default privileges in schema public revoke all on tables from %I', papel);
      execute format('alter default privileges in schema public revoke all on sequences from %I', papel);
      execute format('alter default privileges in schema public revoke all on functions from %I', papel);
    end if;
  end loop;
end $$;

-- -----------------------------------------------------------------------------
-- Como testar (no terminal, com a URL e a chave anon do projeto):
--
--   curl -s "https://<projeto>.supabase.co/rest/v1/fato_item_venda?select=*&limit=1" \
--     -H "apikey: <chave anon>" -H "Authorization: Bearer <chave anon>"
--
-- Antes desta migration: devolve linhas de venda. Depois: devolve [] ou um
-- erro de permissão (42501). O app continua funcionando normalmente, porque o
-- backend não usa a API do Supabase para os dados.
-- -----------------------------------------------------------------------------
