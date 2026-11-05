-- =============================================================================
-- O mínimo do Supabase que as migrations esperam, para um Postgres comum
-- (CI e máquina local). NÃO rodar no Supabase: lá isto já existe.
--
--   001 usa o schema "extensions" (pgcrypto/gen_random_uuid);
--   005 referencia auth.users (dono do dataset);
--   006 revoga acesso dos papéis anon/authenticated.
--
-- Ordem: este arquivo -> migrations/001..006 -> seed.py.
-- =============================================================================
create schema if not exists extensions;
create extension if not exists pgcrypto schema extensions;

create schema if not exists auth;
create table if not exists auth.users (id uuid primary key);

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
end $$;
