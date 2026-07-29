-- =====================================================================
-- 001_schema.sql  —  Intellix
-- Esquema estrela (star schema) multi-tenant para análise de vendas.
-- Rode este arquivo INTEIRO no SQL Editor do Supabase (Run).
--
-- Ordem lógica: extensões -> função de normalização -> tabelas ->
--               índices -> view materializada -> empresa demo.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Extensões
-- ---------------------------------------------------------------------
-- unaccent: remove acentos ("João" -> "joao") para deduplicar cadastros.
-- Fica no schema "extensions" (padrão do Supabase).
create extension if not exists unaccent with schema extensions;

-- ---------------------------------------------------------------------
-- Função de normalização (norm_key)
-- ---------------------------------------------------------------------
-- Gera a chave canônica usada para dizer que "Coca Cola", "COCA-COLA"
-- e "coca cola " são o MESMO cadastro. É marcada IMMUTABLE de propósito
-- para poder ser usada em coluna gerada (generated column) e índice.
create or replace function norm_key(txt text)
returns text
language sql
immutable
as $$
  select lower(btrim(extensions.unaccent(coalesce(txt, ''))));
$$;

-- ---------------------------------------------------------------------
-- empresa  (o "tenant" — cada pequena empresa é uma linha)
-- ---------------------------------------------------------------------
create table if not exists empresa (
  id         uuid primary key default gen_random_uuid(),
  nome       text not null,
  criada_em  timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- importacao  (dormente até a semana 14 — controle das planilhas)
-- ---------------------------------------------------------------------
create table if not exists importacao (
  id                 uuid primary key default gen_random_uuid(),
  empresa_id         uuid not null references empresa(id),
  nome_arquivo       text not null,
  hash_arquivo       text not null,               -- defesa contra reimportação duplicada
  status             text not null default 'pendente',  -- pendente | processada | erro
  linhas_lidas       integer not null default 0,
  linhas_validas     integer not null default 0,
  linhas_rejeitadas  integer not null default 0,
  criada_em          timestamptz not null default now(),
  unique (empresa_id, hash_arquivo)
);

-- ---------------------------------------------------------------------
-- staging_venda  (dormente — semana 14 joga TUDO como texto aqui)
-- ---------------------------------------------------------------------
create table if not exists staging_venda (
  id              bigint generated always as identity primary key,
  importacao_id   uuid not null references importacao(id),
  empresa_id      uuid not null references empresa(id),
  linha_origem    integer,                        -- nº da linha na planilha
  -- tudo texto: nenhuma conversão nesta fase
  data_venda      text,
  produto         text,
  categoria       text,
  cliente         text,
  vendedor        text,
  canal           text,
  forma_pagamento text,
  quantidade      text,
  valor_unitario  text,
  desconto        text,
  valor_total     text,
  erros           text                            -- motivo da rejeição, se houver
);

-- ---------------------------------------------------------------------
-- DIMENSÕES
-- ---------------------------------------------------------------------

-- dim_data: calendário compartilhado (dimensão conformada, sem empresa_id).
-- Populada pelo 002_dim_data.sql. Hierarquia dia -> mês -> trimestre -> ano.
create table if not exists dim_data (
  id         bigint generated always as identity primary key,
  data       date not null unique,
  dia        smallint not null,
  mes        smallint not null,
  trimestre  smallint not null,
  ano        smallint not null
);

-- dim_produto: nome_norm é GERADA a partir de nome -> permite o
-- "on conflict (empresa_id, nome_norm) do nothing" do importador.
create table if not exists dim_produto (
  id         bigint generated always as identity primary key,
  empresa_id uuid not null references empresa(id),
  nome       text not null,
  nome_norm  text generated always as (norm_key(nome)) stored,
  categoria  text,
  unique (empresa_id, nome_norm)
);

create table if not exists dim_cliente (
  id         bigint generated always as identity primary key,
  empresa_id uuid not null references empresa(id),
  nome       text not null,
  nome_norm  text generated always as (norm_key(nome)) stored,
  segmento   text,
  unique (empresa_id, nome_norm)
);

create table if not exists dim_vendedor (
  id         bigint generated always as identity primary key,
  empresa_id uuid not null references empresa(id),
  nome       text not null,
  nome_norm  text generated always as (norm_key(nome)) stored,
  unique (empresa_id, nome_norm)
);

-- ---------------------------------------------------------------------
-- TABELA DE FATO
-- Grão = UM ITEM de uma venda. Só números (medidas). canal e
-- forma_pagamento são dimensões degeneradas (atributos na própria fato).
-- ---------------------------------------------------------------------
create table if not exists fato_item_venda (
  id                 bigint generated always as identity primary key,
  empresa_id         uuid not null references empresa(id),
  venda_id           text not null,               -- agrupa itens da mesma venda
  data_id            bigint not null references dim_data(id),
  produto_id         bigint not null references dim_produto(id),
  cliente_id         bigint references dim_cliente(id),
  vendedor_id        bigint references dim_vendedor(id),
  canal              text,                         -- loja | site | whatsapp | marketplace
  forma_pagamento    text,                         -- pix | cartao_credito | ...
  quantidade         integer not null,
  valor_unitario     numeric(12,2) not null,
  desconto           numeric(12,2) not null default 0,
  valor_total        numeric(12,2) not null,
  origem_importacao  uuid references importacao(id),
  -- idempotência: rodar a carga 2x não duplica (uma linha por produto por venda)
  unique (empresa_id, venda_id, produto_id)
);

-- ---------------------------------------------------------------------
-- log_consulta  (auditoria — seção 7.7 do TCC)
-- ---------------------------------------------------------------------
create table if not exists log_consulta (
  id           bigint generated always as identity primary key,
  empresa_id   uuid not null references empresa(id),
  criado_em    timestamptz not null default now(),
  pergunta     text not null,
  intencao     text,
  entidades    jsonb,
  confianca    numeric(5,4),
  template_sql text,
  parametros   jsonb,
  tempo_ms     integer
);

-- ---------------------------------------------------------------------
-- ÍNDICES  (colunas usadas em filtros/agregações)
-- ---------------------------------------------------------------------
create index if not exists idx_fato_empresa     on fato_item_venda (empresa_id);
create index if not exists idx_fato_data         on fato_item_venda (data_id);
create index if not exists idx_fato_produto      on fato_item_venda (produto_id);
create index if not exists idx_fato_cliente      on fato_item_venda (cliente_id);
create index if not exists idx_fato_vendedor     on fato_item_venda (vendedor_id);
create index if not exists idx_fato_canal        on fato_item_venda (empresa_id, canal);
create index if not exists idx_fato_pagamento    on fato_item_venda (empresa_id, forma_pagamento);
create index if not exists idx_dim_data_ano_mes  on dim_data (ano, mes);
create index if not exists idx_dim_produto_cat   on dim_produto (empresa_id, categoria);

-- ---------------------------------------------------------------------
-- VIEW MATERIALIZADA — totais mensais (ajuda a meta de resposta < 3s)
-- O índice UNIQUE permite "refresh materialized view concurrently".
-- ---------------------------------------------------------------------
create materialized view if not exists mv_faturamento_mensal as
select
  f.empresa_id,
  d.ano,
  d.mes,
  sum(f.valor_total)          as faturamento,
  count(distinct f.venda_id)  as qtd_vendas,
  sum(f.quantidade)           as qtd_itens
from fato_item_venda f
join dim_data d on d.id = f.data_id
group by f.empresa_id, d.ano, d.mes;

create unique index if not exists uq_mv_fat_mensal
  on mv_faturamento_mensal (empresa_id, ano, mes);

-- ---------------------------------------------------------------------
-- Empresa demo (id fixo, usado pelo backend e pelo seed)
-- ---------------------------------------------------------------------
insert into empresa (id, nome)
values ('00000000-0000-0000-0000-000000000001', 'Empresa Demonstração')
on conflict (id) do nothing;

-- =====================================================================
-- Verificação rápida (rode depois, opcional):
--   select table_name from information_schema.tables where table_schema='public';
-- =====================================================================
