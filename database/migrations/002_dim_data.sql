-- =====================================================================
-- 002_dim_data.sql  —  Intellix
-- Popula o calendário (4 anos). SEM isto, nada funciona.
-- Rode DEPOIS do 001_schema.sql.
-- Resultado esperado: 1461 linhas.
-- =====================================================================

insert into dim_data (data, dia, mes, trimestre, ano)
select d::date,
       extract(day     from d),
       extract(month   from d),
       extract(quarter from d),
       extract(year    from d)
from generate_series('2023-01-01'::date, '2026-12-31'::date, '1 day') d
on conflict (data) do nothing;

-- Verificação:  select count(*) from dim_data;  -> 1461
