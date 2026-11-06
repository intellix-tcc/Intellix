-- =============================================================================
-- 007 — "Minhas planilhas": listar e excluir os datasets importados pela conta
-- =============================================================================
-- Por quê: cada importação cria um dataset (uma linha em `empresa`) com o
-- `dono_id` de quem importou (migration 005). O app só lembrava qual dataset
-- usar por um registro no navegador, apagado ao sair: depois de sair e entrar
-- de novo, a planilha ficava no banco mas inacessível pela tela.
--
-- Por que funções, e não um SELECT direto do backend: com a migration 006
-- (usuário intellix_app + RLS), o app só enxerga a empresa declarada na
-- transação e não pode apagar vendas. "Todas as planilhas do usuário X" e
-- "apagar a planilha Y" precisam de exceções pontuais, e é isto que estas duas
-- funções são: rodam com os direitos do dono das tabelas (security definer),
-- fazem só isso e sempre filtram por dono_id. Funcionam igual com ou sem a 006
-- aplicada (conectado como postgres, o RLS nem se aplica).
--
-- Confiança: quem chama informa o dono. O backend passa o id do usuário tirado
-- do token JWT já validado (app/auth.py) — a mesma confiança que ele já tem ao
-- declarar app.empresa_id. Por isso o EXECUTE é revogado de PUBLIC (que inclui
-- os papéis anon/authenticated da API REST do Supabase) e dado só ao app.
--
-- Idempotente: pode rodar mais de uma vez.
-- =============================================================================

create or replace function public.listar_planilhas(p_dono uuid)
returns table (
  empresa_id        uuid,
  nome_arquivo      text,
  importada_em      timestamptz,
  linhas_validas    int,
  linhas_rejeitadas int,
  primeira_venda    date,
  ultima_venda      date
)
language sql
stable
security definer
set search_path = ''
as $$
  select e.id,
         coalesce(i.nome_arquivo, e.nome),
         coalesce(i.criada_em, e.criada_em),
         i.linhas_validas,
         i.linhas_rejeitadas,
         p.primeira,
         p.ultima
  from public.empresa e
  left join lateral (
    select imp.nome_arquivo, imp.criada_em, imp.linhas_validas, imp.linhas_rejeitadas
    from public.importacao imp
    where imp.empresa_id = e.id
    order by imp.criada_em desc
    limit 1
  ) i on true
  left join lateral (
    select min(d.data) as primeira, max(d.data) as ultima
    from public.fato_item_venda f
    join public.dim_data d on d.id = f.data_id
    where f.empresa_id = e.id
  ) p on true
  where p_dono is not null
    and e.dono_id = p_dono
  order by coalesce(i.criada_em, e.criada_em) desc;
$$;


-- Apaga o dataset inteiro (vendas, staging, dimensões, auditoria e a própria
-- empresa) se, e só se, ele for de p_dono. Devolve false quando não é (ou não
-- existe): o backend responde 404 nos dois casos, sem revelar quais ids
-- existem. A base de demonstração não tem dono e nunca é apagada por aqui.
create or replace function public.excluir_planilha(p_empresa uuid, p_dono uuid)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  if p_dono is null or not exists (
    select 1 from public.empresa where id = p_empresa and dono_id = p_dono
  ) then
    return false;
  end if;

  -- ordem das chaves estrangeiras (nenhuma tem on delete cascade)
  delete from public.fato_item_venda where empresa_id = p_empresa;
  delete from public.staging_venda   where empresa_id = p_empresa;
  delete from public.log_consulta    where empresa_id = p_empresa;
  delete from public.importacao      where empresa_id = p_empresa;
  delete from public.dim_produto     where empresa_id = p_empresa;
  delete from public.dim_cliente     where empresa_id = p_empresa;
  delete from public.dim_vendedor    where empresa_id = p_empresa;
  delete from public.empresa         where id = p_empresa;

  -- as views materializadas somam todas as empresas: sem o refresh, ficariam
  -- números de um dataset que não existe mais
  refresh materialized view public.mv_faturamento_mensal;
  refresh materialized view public.mv_ranking_produtos;
  refresh materialized view public.mv_desempenho_vendedor;
  return true;
end;
$$;


-- Só o backend executa. Sem isto, qualquer um com a chave pública do Supabase
-- poderia chamar as funções pela API REST (/rpc) informando um dono qualquer.
revoke all on function public.listar_planilhas(uuid) from public;
revoke all on function public.excluir_planilha(uuid, uuid) from public;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    revoke all on function public.listar_planilhas(uuid) from anon;
    revoke all on function public.excluir_planilha(uuid, uuid) from anon;
  end if;
  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    revoke all on function public.listar_planilhas(uuid) from authenticated;
    revoke all on function public.excluir_planilha(uuid, uuid) from authenticated;
  end if;
  if exists (select 1 from pg_roles where rolname = 'intellix_app') then
    grant execute on function public.listar_planilhas(uuid) to intellix_app;
    grant execute on function public.excluir_planilha(uuid, uuid) to intellix_app;
  end if;
end $$;

-- Conferência (rodar depois):
--   select has_function_privilege('anon', 'public.listar_planilhas(uuid)', 'execute');      -> false
--   select has_function_privilege('intellix_app', 'public.listar_planilhas(uuid)', 'execute'); -> true
