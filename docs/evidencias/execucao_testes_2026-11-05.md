# Execução dos testes — pacote e rastreabilidade (TC2 F11)

Atende ao feedback TC2 **F11** (identificar versão e cobertura real; confirmar
que as verificações usaram o modelo treinado; mapear requisitos aos testes).
Atualiza a contagem: **101 testes** (o texto antigo citava 5; o Quadro 13, 7).

## Pacote de execução

| Campo | Valor |
|---|---|
| Commit | `4f30a7f` (+ `test_backend_nlu.py` desta entrega) |
| Comando | `cd backend && pytest -q --junitxml=../docs/evidencias/pytest_2026-11-05.xml` |
| Ambiente | Windows 10 · Python 3.11.5 · pytest 8.3.2 |
| **NLU ativo** | **`NLU_BACKEND=modelo`** → `ModeloTreinadoNLU` (confirmado pelo `test_backend_nlu.py`) |
| Banco | Supabase (PostgreSQL), pooler 6543 |
| Resultado | **101 aprovados, 0 falhas** |
| Saída (JUnit) | `docs/evidencias/pytest_2026-11-05.xml` |

> Sem `DATABASE_URL` (como no CI), os testes de integração são **ignorados por
> projeto** e os demais passam — ver a nota de CI no fim.

## Cobertura por módulo (101 testes)

| Módulo | Testes | Tipo | Capacidade coberta | RF/RNF (confirmar nº no doc) |
|---|---:|---|---|---|
| `test_health.py` | 1 | unit | disponibilidade `/health` | RNF operação |
| `test_nlu_regras.py` | 5 | unit | classificação por regras (baseline) | RF interpretação |
| `test_backend_nlu.py` | 1 | unit | NLU ativo = modelo (controle) | — |
| `test_contexto.py` | 4 | unit | histórico conversacional | RF chat |
| `test_periodo_dataset.py` | 6 | unit | período por dataset (ano do dado) | RF chat / importação |
| `test_fallbacks.py` | 2 | unit | recusa por baixa confiança | RF robustez |
| `test_templates_sql.py` | 4 | unit | 12 templates e **ausência de interpolação** | RNF segurança (SQL) |
| `test_import.py` | 11 | unit | leitura/validação de planilha | RF importação |
| `test_auth.py` | 27 | unit | autenticação (token Supabase) | RNF05 segurança |
| `test_db_pool.py` | 4 | unit/integr. | pool de conexões | RNF desempenho |
| `test_chat_integration.py` | 8 | integração | fluxo `/chat` → SQL → banco | RF chat |
| `test_resumo.py` | 15 | integração | `/resumo` (panorama do mês) | RF panorama |
| `test_valores_referencia.py` | 5 | integração | **correção dos valores** (F01) | RF análises |
| `test_isolamento.py` | 8 | unit+integr. | autorização por empresa + **auditoria** | RNF05 segurança |

Distinção preservada: **unitário** (sem banco), **integração** (com banco) e,
à parte, o **benchmark** de latência (as 100 perguntas em
`scripts/avaliar_100_perguntas.py`, não no pytest).

## Sobre o SQL parametrizado (F05/F11)
`test_templates_sql.py` verifica que os 12 templates não concatenam valores
(sem `%s` por f-string/`.format`). Para o caminho **executado**, a prova
complementar é o `test_valores_referencia.py`, que confere os números devolvidos
pelo `/chat` real contra uma base calculável à mão.

## CI
O workflow roda `ruff check backend/` + `pytest` **sem** credencial de banco
(decisão legítima por segurança): 5 testes de integração ficam *skipped* e os
demais passam. Alternativa futura documentada: subir um **Postgres efêmero** no
job de CI (service container) para exercitar a integração automaticamente, sem
expor segredos de produção.
