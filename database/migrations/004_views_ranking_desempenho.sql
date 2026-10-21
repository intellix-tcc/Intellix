-- =====================================================================
-- 004_views_ranking_desempenho.sql  —  Intellix
-- Visões materializadas complementares (seção 7.4 do TCC).
-- A 001_schema.sql já cria mv_faturamento_mensal; aqui entram as outras
-- duas citadas na documentação: ranking de produtos e desempenho por
-- vendedor.
--
-- HISTÓRICO: estas views foram criadas em dev e prod em ago/2026 por um
-- arquivo "003_views.sql" que nunca chegou a ser versionado. Este arquivo
-- recria o registro (13/10/2026) com a mesma definição. Numerado 004
-- porque a 003 é a 003_estende_dim_data.sql (PR #4).
--
-- Idempotente: em bancos onde as views já existem, não altera nada.
-- Rode DEPOIS da 001 e da 002. Para atualizar os dados das views:
--   refresh materialized view concurrently mv_ranking_produtos;
--   refresh materialized view concurrently mv_desempenho_vendedor;
-- =====================================================================

-- ---------------------------------------------------------------------
-- Ranking de produtos (unidades e faturamento por produto)
-- ---------------------------------------------------------------------
create materialized view if not exists mv_ranking_produtos as
select
  f.empresa_id,
  p.id                        as produto_id,
  p.nome,
  p.categoria,
  sum(f.quantidade)           as unidades,
  sum(f.valor_total)          as faturamento,
  count(distinct f.venda_id)  as vendas_distintas
from fato_item_venda f
join dim_produto p on p.id = f.produto_id
group by f.empresa_id, p.id, p.nome, p.categoria;

-- índice unique -> permite "refresh materialized view concurrently"
create unique index if not exists uq_mv_ranking_produtos
  on mv_ranking_produtos (empresa_id, produto_id);

-- índice de apoio para ordenação por faturamento
create index if not exists idx_mv_ranking_produtos_fat
  on mv_ranking_produtos (empresa_id, faturamento desc);


-- ---------------------------------------------------------------------
-- Desempenho por vendedor (faturamento, itens e vendas por vendedor)
-- ---------------------------------------------------------------------
create materialized view if not exists mv_desempenho_vendedor as
select
  f.empresa_id,
  v.id                        as vendedor_id,
  v.nome,
  sum(f.valor_total)          as faturamento,
  sum(f.quantidade)           as itens_vendidos,
  count(distinct f.venda_id)  as vendas_distintas
from fato_item_venda f
join dim_vendedor v on v.id = f.vendedor_id
group by f.empresa_id, v.id, v.nome;

create unique index if not exists uq_mv_desempenho_vendedor
  on mv_desempenho_vendedor (empresa_id, vendedor_id);

create index if not exists idx_mv_desempenho_vendedor_fat
  on mv_desempenho_vendedor (empresa_id, faturamento desc);

-- ---------------------------------------------------------------------
-- Popular as views (num banco novo; onde já existem, só atualiza)
-- ---------------------------------------------------------------------
refresh materialized view mv_ranking_produtos;
refresh materialized view mv_desempenho_vendedor;

-- Verificação (deve listar as três views):
--   select matviewname from pg_matviews order by 1;
-- Conferir que a definição no banco bate com este arquivo:
--   select pg_get_viewdef('mv_ranking_produtos'::regclass);
