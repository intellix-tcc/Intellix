# ADR 002 — Supabase como plataforma de banco de dados

- **Status:** aceito
- **Data:** (preencher)
- **Decisores:** equipe Intellix

## Contexto

O projeto precisa de um banco relacional na nuvem (requisito de cloud computing da
disciplina), a custo zero na fase de protótipo, com região no Brasil e sem prender a
solução a um fornecedor.

## Decisão

Usar o **Supabase** (PostgreSQL gerenciado), região *South America (São Paulo)*,
no free tier, com projetos separados `intellix-dev` e `intellix-prod`.

## Justificativa

- **Free tier real** e suficiente para o protótipo (até 500 MB).
- **PostgreSQL puro** — a solução fica **portável**: dá para migrar para outro provedor
  ou auto-hospedar sem reescrever a aplicação.
- Região SP reduz latência para os usuários brasileiros.
- Recursos extras (Auth, RLS, APIs automáticas) ficam disponíveis para uso futuro.

## Consequências

- Dependência de nuvem terceirizada na fase atual (registrada como fraqueza na SWOT).
  Mitigada pela portabilidade do PostgreSQL.
- Conexões da aplicação devem usar o **Transaction pooler (porta 6543)** — a porta
  direta 5432 não funciona no Render.
- Credenciais ficam em variáveis de ambiente, nunca no código versionado.
