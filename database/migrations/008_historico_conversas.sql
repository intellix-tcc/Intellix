-- =============================================================================
-- 008 — Histórico de conversas por conta
-- =============================================================================
-- Por quê: as conversas do chat viviam só no localStorage do navegador
-- (frontend/src/utils/historico.js). Trocar de navegador ou de aparelho, ou
-- limpar os dados do site, apagava tudo. Com o login (Supabase Auth) já
-- pronto, dá para guardar as conversas na conta e reencontrá-las em qualquer
-- lugar.
--
-- Como: uma tabela `conversa` com o `dono_id` (o id do usuário, tirado do
-- token JWT já validado — app/auth.py) e as mensagens como JSONB, no mesmo
-- formato que o frontend já usa. O acesso passa por funções
-- (listar_conversas, salvar_conversa, excluir_conversa) que SEMPRE filtram
-- pelo dono — o mesmo desenho da migration 007 ("minhas planilhas"): com o
-- RLS e o usuário intellix_app (migration 006), o backend não lê nem grava a
-- conversa de outra pessoa, e a API REST pública do Supabase não enxerga a
-- tabela.
--
-- Confiança: quem chama informa o dono, e o backend só passa o id do usuário
-- autenticado. Por isso o EXECUTE é revogado de PUBLIC (anon/authenticated) e
-- dado só ao intellix_app.
--
-- Idempotente: pode rodar mais de uma vez.
-- =============================================================================

create table if not exists public.conversa (
  id            uuid primary key default gen_random_uuid(),
  dono_id       uuid not null references auth.users(id) on delete cascade,
  titulo        text not null,
  mensagens     jsonb not null default '[]'::jsonb,
  criada_em     timestamptz not null default now(),
  atualizada_em timestamptz not null default now()
);

-- Lista de conversas de um usuário: filtra por dono e ordena pela mais
-- recente, então o índice cobre a consulta inteira.
create index if not exists idx_conversa_dono
  on public.conversa (dono_id, atualizada_em desc);

-- RLS ligado e sem política para anon/authenticated: a REST do Supabase não
-- lê nem grava a tabela. O backend acessa só pelas funções abaixo, que rodam
-- com os direitos do dono das tabelas (security definer) e não passam por RLS.
alter table public.conversa enable row level security;


-- ---------------------------------------------------------------------------
-- Funções (security definer, sempre filtrando por dono)
-- ---------------------------------------------------------------------------

-- Conversas do dono, da mais recente para a mais antiga.
create or replace function public.listar_conversas(p_dono uuid)
returns table (
  id            uuid,
  titulo        text,
  mensagens     jsonb,
  criada_em     timestamptz,
  atualizada_em timestamptz
)
language sql
stable
security definer
set search_path = ''
as $$
  select c.id, c.titulo, c.mensagens, c.criada_em, c.atualizada_em
  from public.conversa c
  where p_dono is not null
    and c.dono_id = p_dono
  order by c.atualizada_em desc;
$$;

-- Insere ou atualiza uma conversa do dono (o id vem do frontend). Devolve o
-- id quando grava; null quando o id já existe e é de OUTRA pessoa — o backend
-- nunca sobrescreve a conversa de alguém. O título é limitado a 200 caracteres.
create or replace function public.salvar_conversa(
  p_id        uuid,
  p_dono      uuid,
  p_titulo    text,
  p_mensagens jsonb,
  p_criada_em timestamptz
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_dono uuid;
begin
  if p_dono is null or p_id is null then
    return null;
  end if;

  select dono_id into v_dono from public.conversa where id = p_id;

  if v_dono is null then
    insert into public.conversa (id, dono_id, titulo, mensagens, criada_em, atualizada_em)
    values (
      p_id,
      p_dono,
      left(coalesce(nullif(btrim(p_titulo), ''), 'Nova conversa'), 200),
      coalesce(p_mensagens, '[]'::jsonb),
      coalesce(p_criada_em, now()),
      now()
    );
    return p_id;
  elsif v_dono = p_dono then
    update public.conversa
       set titulo        = left(coalesce(nullif(btrim(p_titulo), ''), titulo), 200),
           mensagens     = coalesce(p_mensagens, mensagens),
           atualizada_em = now()
     where id = p_id;
    return p_id;
  else
    return null;  -- id de outra pessoa: não mexe
  end if;
end;
$$;

-- Apaga a conversa se, e só se, for do dono. True quando apagou; false quando
-- o id não existe ou é de outra pessoa.
create or replace function public.excluir_conversa(p_id uuid, p_dono uuid)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  if p_dono is null or p_id is null then
    return false;
  end if;
  delete from public.conversa where id = p_id and dono_id = p_dono;
  return found;
end;
$$;


-- ---------------------------------------------------------------------------
-- Só o backend (intellix_app) executa. Sem isto, qualquer um com a chave
-- pública do Supabase poderia chamar as funções pela REST (/rpc) informando
-- um dono qualquer.
-- ---------------------------------------------------------------------------
revoke all on function public.listar_conversas(uuid) from public;
revoke all on function public.salvar_conversa(uuid, uuid, text, jsonb, timestamptz) from public;
revoke all on function public.excluir_conversa(uuid, uuid) from public;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    revoke all on function public.listar_conversas(uuid) from anon;
    revoke all on function public.salvar_conversa(uuid, uuid, text, jsonb, timestamptz) from anon;
    revoke all on function public.excluir_conversa(uuid, uuid) from anon;
  end if;
  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    revoke all on function public.listar_conversas(uuid) from authenticated;
    revoke all on function public.salvar_conversa(uuid, uuid, text, jsonb, timestamptz) from authenticated;
    revoke all on function public.excluir_conversa(uuid, uuid) from authenticated;
  end if;
  if exists (select 1 from pg_roles where rolname = 'intellix_app') then
    grant execute on function public.listar_conversas(uuid) to intellix_app;
    grant execute on function public.salvar_conversa(uuid, uuid, text, jsonb, timestamptz) to intellix_app;
    grant execute on function public.excluir_conversa(uuid, uuid) to intellix_app;
  end if;
end $$;

-- Conferência (rodar depois):
--   select has_function_privilege('anon', 'public.listar_conversas(uuid)', 'execute');         -> false
--   select has_function_privilege('intellix_app', 'public.listar_conversas(uuid)', 'execute'); -> true
