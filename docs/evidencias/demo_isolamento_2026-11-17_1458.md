# Demonstração de isolamento entre empresas (dados fictícios)

Demonstração ao vivo pedida pela banca final (F05/F09): duas empresas
inventadas, o usuário de aplicação de privilégio mínimo `intellix_app`, e a
prova de que uma não alcança a outra. Gerado por `scripts/demo_isolamento.py`.
Nenhuma conta real é usada.

- **Data:** 17/11/2026 14:58 (UTC+0000)
- **Alvo:** localhost:5432/intellix
- **Empresas fictícias:** A `Padaria Pão Quente (fictícia)` · B `Livraria Saber Ler (fictícia)`

## Passos

| # | Demonstração | Resultado |
|---|---|:-:|
| 1 | Admin (`postgres`) enxerga as duas empresas — count(distinct empresa_id) = 2 (scripts de backup/seed usam este papel) | ✅ |
| 2 | Sem declarar empresa, o app não vê nada — count(*) = 0 (RLS nega por padrão) | ✅ |
| 3 | Declarada a empresa A, vê só a empresa A — 3 itens, ∑=R$ 94.00 (esperado 94.00), empresas distintas = 1 | ✅ |
| 4 | Com A declarada, pedir B de propósito devolve zero — count(*) where empresa_id = B  →  0 (RLS barra mesmo com filtro explícito) | ✅ |
| 5 | Privilégio mínimo: o app não apaga vendas — permission denied (sem grant de delete) | ✅ |
| 6 | Auditoria: grava sob A, barra escrita para B, fica atribuída a A — gravou em A (1); escrita de B barrada = True; registros de B = 0 | ✅ |

**6/6** passos conferem.

## Camadas do isolamento

- **Autorização na aplicação** (`app/acesso.py::resolver_empresa`): dataset de
  outro dono responde 404 `dataset_nao_encontrado`, idêntico ao de id inexistente
  (não revela quais ids existem). Provado em `backend/tests/test_isolamento.py`.
- **RLS no banco** (migration `006_rls_e_usuario_app.sql`): mesmo que uma consulta
  escape, o Postgres só devolve linhas da empresa declarada na transação
  (`set_config('app.empresa_id', …, true)`). Provado aqui e em `test_rls.py`.
- **Privilégio mínimo**: `intellix_app` lê e insere, mas não apaga nem altera vendas,
  e não acessa as views materializadas.
- **Auditoria** (`log_consulta`): toda consulta é registrada, e o registro também é
  isolado por empresa.

## Reproduzir

```bash
DATABASE_URL=postgresql://postgres:***@localhost:5432/intellix \
    python scripts/demo_isolamento.py --saida docs/evidencias
# para uma demonstração interativa, --manter deixa as empresas no banco
cd backend && pytest tests/test_isolamento.py tests/test_rls.py -q
```

