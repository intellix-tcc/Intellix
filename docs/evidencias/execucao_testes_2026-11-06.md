# Execução dos testes — versão final (06/11/2026)

Pacote de execução da versão que vai para a entrega final. **Substitui, como
número oficial, as contagens anteriores** (28 testes em 13/10/2026 e 101 em
05/11/2026, que ficam como histórico em
[`relatorio-execucao-testes.md`](../relatorio-execucao-testes.md) e
[`execucao_testes_2026-11-05.md`](execucao_testes_2026-11-05.md)).

## Resumo

| Verificação | Resultado |
|---|---|
| Testes do backend (`pytest`) | **202 testes: 198 aprovados, 0 falhas, 4 ignorados** |
| Os 4 ignorados (RLS), rodados como `intellix_app` | **7 de 7 aprovados** em `test_rls.py` |
| Lint do backend (`ruff check backend/`, ruff 0.16.5) | sem apontamentos |
| Lint do frontend (`npm run lint`) | sem apontamentos |
| Build do frontend (`npm run build`) | concluído |
| 100 perguntas de validação, ponta a ponta | **88/100** (o mesmo de `avaliacao-correcoes-2026-11-06.md`) |

## Pacote de execução

| Campo | Valor |
|---|---|
| Commit | `311c866` (main, após o PR #37) |
| Comando | `cd backend && pytest -q -rs --junitxml=../docs/evidencias/pytest_2026-11-06.xml` |
| Banco | PostgreSQL 16 local, montado como no CI: `database/local/supabase_minimo.sql` + `database/migrations/*.sql` (001 a 008) + `database/seed.py` |
| Usuário do banco | `postgres` (o mesmo do CI) |
| **NLU ativo** | **`NLU_BACKEND=modelo`**, `intellix_nlu_v1.2.0.pt` (confirmado por `test_backend_nlu.py`) |
| Ambiente | Linux · Python 3.13 · PyTorch 2.15 (CPU) · pytest 8.3.2 |
| Saída (JUnit) | [`pytest_2026-11-06.xml`](pytest_2026-11-06.xml) |

A produção (Render) e o CI usam Python 3.12 e PyTorch 2.4.1. Os pesos do
modelo são os mesmos; a avaliação das 100 perguntas reproduziu exatamente os
88/100 medidos antes, então a diferença de versão não mudou as respostas.

## Os 4 testes ignorados: isolamento por RLS

Os 4 testes de integração de `test_rls.py` só fazem sentido conectados como o
usuário da aplicação, `intellix_app` (migration 006): o `postgres` é dono das
tabelas e não passa pelo RLS. Por isso o CI, que conecta como `postgres`, os
ignora por projeto. Eles foram rodados à parte, no mesmo banco, como
`intellix_app`, que é o usuário que o Render usa em produção:

| Teste | O que prova | Resultado |
|---|---|---|
| `test_declarar_empresa_e_local_a_transacao` | a empresa é declarada só para a transação atual | aprovado |
| `test_base_demo_tambem_e_declarada` | a base demo também passa pela declaração | aprovado |
| `test_empresa_pedida_e_declarada_antes_de_ler_o_dono` | a declaração acontece antes de qualquer leitura | aprovado |
| `test_sem_declarar_empresa_o_app_nao_ve_vendas` | sem declarar a empresa, o app não vê nenhuma venda | aprovado |
| `test_declarando_a_demo_ve_so_a_demo` | declarando uma empresa, só as vendas dela aparecem | aprovado |
| `test_declaracao_nao_vaza_para_a_proxima_transacao` | a declaração não passa para a requisição seguinte | aprovado |
| `test_app_nao_apaga_vendas` | o usuário da aplicação não consegue apagar vendas | aprovado |

Saída (JUnit): [`pytest_rls_intellix_app_2026-11-06.xml`](pytest_rls_intellix_app_2026-11-06.xml).

## Cobertura por módulo (202 testes)

"Integração" = usa o banco (roda no CI, contra o Postgres efêmero).

| Módulo | Testes | Tipo | Capacidade coberta |
|---|---:|---|---|
| `test_health.py` | 1 | unit | disponibilidade `/health` |
| `test_backend_nlu.py` | 1 | unit | NLU ativo = modelo treinado (controle) |
| `test_nlu_regras.py` | 5 | unit | classificação por regras (baseline) |
| `test_adaptador_vendedor.py` | 5 | unit | nome de vendedor (com e sem acento) para a busca |
| `test_filtros.py` | 13 | unit | trecho da pergunta → valor exato do catálogo (produto, categoria, canal...) |
| `test_contexto.py` | 15 | unit | continuidade da conversa ("e em abril?", "e de calçados?") |
| `test_refino.py` | 11 | unit | refinamentos sem retreino (`unidades_vendidas`, `melhor_mes`) |
| `test_periodo_dataset.py` | 10 | unit | "hoje" por dataset e períodos relativos |
| `test_fallbacks.py` | 2 | unit | recusa por baixa confiança |
| `test_templates_sql.py` | 5 | unit | templates existem e **não interpolam valores** (SQL injection) |
| `test_executor_robustez.py` | 8 | unit | erros do executor viram 422/404/503, nunca 500 |
| `test_evolucao_mensal.py` | 4 | unit | evolução de 12 meses nas respostas de um mês |
| `test_limite.py` | 9 | unit | limite de requisições (429) e tamanho da pergunta |
| `test_auth.py` | 27 | unit | validação do token do Supabase (assinatura, validade, papel) |
| `test_auditoria.py` | 2 | unit | auditoria não derruba a resposta se falhar |
| `test_db_pool.py` | 4 | unit + integração | pool de conexões |
| `test_import.py` | 14 | unit | leitura e validação da planilha |
| `test_import_carga.py` | 2 | integração | carga no star schema (itens somados, motivos de rejeição) |
| `test_chat_integration.py` | 13 | integração | fluxo `/chat` → NLU → SQL → banco |
| `test_valores_referencia.py` | 5 | integração | **valores corretos** contra uma base calculável à mão (F01) |
| `test_sem_saida_recorte.py` | 3 | integração | produtos sem saída respeitando o recorte |
| `test_resumo.py` | 15 | unit | `/resumo` (panorama do mês, tela Início) |
| `test_isolamento.py` | 8 | unit + integração | dataset de outra pessoa → 404; auditoria em `log_consulta` (F09) |
| `test_rls.py` | 7 | unit + integração | isolamento no próprio banco (RLS, C14) |
| `test_planilhas.py` | 5 | integração | minhas planilhas (`/planilhas`, migration 007) |
| `test_conversas.py` | 8 | integração | histórico de conversas (`/conversas`, migration 008) |
| **Total** | **202** | | |

## Integração contínua

O workflow `.github/workflows/ci.yml` roda em todo PR e em todo push na
`main`, em três jobs:

1. **lint** — `ruff check backend/`;
2. **test** — sobe um **Postgres 16 efêmero** (existe só durante o job), aplica
   `supabase_minimo.sql`, todas as migrations e o `seed.py`, e roda o `pytest`
   com `NLU_BACKEND=modelo`. Sem nenhuma credencial de produção;
3. **frontend** — `npm ci`, `npm run lint` e `npm run build`.

Com isso, os testes de integração deixaram de ser "ignorados no CI": só os 4
de RLS ficam de fora, pelo motivo explicado acima.

**Execução do CI neste mesmo commit:** run
[`42266814533`](https://github.com/intellix-tcc/Intellix/actions/runs/42266814533)
(06/11/2026, 18:00 UTC), os três jobs com sucesso. Job `test` em Python
3.12.16 e PostgreSQL 16.15: **198 passed, 4 skipped** — o mesmo resultado da
execução local acima.

## Avaliação ponta a ponta (100 perguntas)

Reexecutada no mesmo commit, com a API local conectada como `intellix_app`:
**88/100**, idêntico à medição de
[`avaliacao-correcoes-2026-11-06.md`](../avaliacao-correcoes-2026-11-06.md).
Os 12 erros são os mesmos e têm a causa registrada no ledger.
Arquivos: [`avaliacao_api_2026-11-06_versao_final.md`](avaliacao_api_2026-11-06_versao_final.md)
e [`.csv`](avaliacao_api_2026-11-06_versao_final.csv).

## Como reproduzir

```bash
# banco como no CI (Postgres 16 vazio, base "intellix")
psql -d intellix -f database/local/supabase_minimo.sql
for f in database/migrations/*.sql; do psql -d intellix -v ON_ERROR_STOP=1 -f "$f"; done
python database/seed.py

# suíte completa (como o CI)
cd backend
DATABASE_URL=postgresql://postgres:...@localhost:5432/intellix \
EMPRESA_ID=00000000-0000-0000-0000-000000000001 NLU_BACKEND=modelo \
pytest -q -rs

# os 4 testes de RLS, como o usuário da aplicação
psql -d intellix -c "alter role intellix_app with password '<senha local>'"
DATABASE_URL=postgresql://intellix_app:<senha local>@localhost:5432/intellix \
EMPRESA_ID=00000000-0000-0000-0000-000000000001 NLU_BACKEND=modelo \
pytest -v tests/test_rls.py
```
