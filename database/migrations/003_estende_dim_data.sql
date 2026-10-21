-- =====================================================================
-- 003_estende_dim_data.sql  —  Intellix
-- Estende o calendário para frente: 2027 a 2032.
--
-- Por quê: a 002 populou só 2023–2026 (suficiente para a base de
-- demonstração sintética). Com dados reais de clientes entrando pela
-- importação de planilha / banco externo, vendas de 2027 em diante
-- precisam ter linha em dim_data -- senão o ETL rejeita a linha na
-- resolução do data_id (ver backend/app/importacao/etl.py).
--
-- Rode DEPOIS da 002. Idempotente (on conflict do nothing): rodar de novo
-- não duplica. Resultado esperado: dim_data passa de 1461 para 3653 linhas.
-- =====================================================================

insert into dim_data (data, dia, mes, trimestre, ano)
select d::date,
       extract(day     from d),
       extract(month   from d),
       extract(quarter from d),
       extract(year    from d)
from generate_series('2027-01-01'::date, '2032-12-31'::date, '1 day') d
on conflict (data) do nothing;

-- Verificação:  select count(*) from dim_data;  -> 3653
--               select min(data), max(data) from dim_data;  -> 2023-01-01, 2032-12-31
