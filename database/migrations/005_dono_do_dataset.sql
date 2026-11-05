-- =====================================================================
-- 005_dono_do_dataset.sql  —  Intellix
-- Liga cada dataset (empresa) ao usuário que o importou.
--
-- Por quê: desde o PR #5 cada importação cria uma empresa própria, e o
-- /chat aceita o empresa_id enviado pelo navegador. Sem dono registrado,
-- qualquer um que soubesse o id consultaria os dados de outra pessoa.
-- Com o login (Supabase Auth), o /import grava aqui o id do usuário, e o
-- /chat só aceita o empresa_id de quem é dono (backend/app/acesso.py).
--
-- dono_id nulo = base de demonstração ou importação feita antes do login.
-- on delete set null: apagar um usuário não apaga as vendas (as tabelas de
-- vendas não têm cascata), o dataset só fica sem dono e inacessível com
-- AUTH_OBRIGATORIA=true.
--
-- Rode ANTES de publicar o backend com autenticação: o código novo lê e
-- grava esta coluna. Idempotente.
-- =====================================================================

alter table empresa
  add column if not exists dono_id uuid references auth.users(id) on delete set null;

create index if not exists idx_empresa_dono on empresa (dono_id);

-- Verificação:
--   select column_name, data_type from information_schema.columns
--    where table_name = 'empresa' and column_name = 'dono_id';   -> 1 linha, uuid
