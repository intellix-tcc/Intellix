# ADR 002 — Supabase como plataforma de banco de dados

- **Status:** aceito
- **Data:** (preencher)
- **Decisores:** equipe Intellix

## Contexto

O projeto precisa de um banco relacional na nuvem (requisito de cloud computing da
disciplina), a custo zero na fase de protótipo, com região no Brasil e sem prender a
solução a um fornecedor.

## Decisão

Usar o **Supabase** (PostgreSQL gerenciado), no free tier, com projetos separados
`intellix-dev` e `intellix-prod`.

**Regiões (situação real):** o `intellix-dev` foi criado em *South America (São Paulo)*
(sa-east-1), como planejado; o `intellix-prod` acabou criado em *West US (Oregon)*
(us-west-2). A região de um projeto Supabase não pode ser trocada depois de criado; mudar
exigiria criar outro projeto e migrar os dados. Para o protótipo a diferença foi aceita: o
que pesa na latência é a distância entre o **backend (Render)** e o banco, não entre o
usuário e o banco, porque o navegador nunca fala direto com o PostgreSQL.

## Justificativa

- **Free tier real** e suficiente para o protótipo (até 500 MB).
- **PostgreSQL puro** — a solução fica **portável**: dá para migrar para outro provedor
  ou auto-hospedar sem reescrever a aplicação.
- Região SP no dev reduz a latência dos testes feitos do Brasil. Em produção, o ideal é
  manter o serviço do Render na mesma região do banco (ver
  `docs/avaliacao-100-perguntas.md`, seções 3.3 e 3.4).
- Recursos extras (Auth, RLS, APIs automáticas) ficam disponíveis para uso futuro.

## Consequências

- Dependência de nuvem terceirizada na fase atual (registrada como fraqueza na SWOT).
  Mitigada pela portabilidade do PostgreSQL.
- Conexões da aplicação devem usar o **Transaction pooler (porta 6543)** — a porta
  direta 5432 não funciona no Render.
- Credenciais ficam em variáveis de ambiente, nunca no código versionado.
- Desde a migration 006 (C14), a aplicação conecta com o usuário `intellix_app`, de
  privilégio mínimo e sujeito a RLS por empresa; o `postgres` fica só para tarefas
  administrativas (migrations, seed, backup).
