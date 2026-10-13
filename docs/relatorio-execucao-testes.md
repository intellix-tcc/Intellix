# Relatório de execução dos testes automatizados

**Projeto:** Intellix — Agente inteligente de análise de vendas
**Atende:** Feedback 7 da orientação (*"Evidenciar execução dos testes automatizados"*)
**Data da execução de referência:** 13/10/2026, 19:01 (UTC−3)
**Versão testada:** branch `feat/ingestao-excel-e-banco` (PR #4), commit `694a5d5`
**Responsável:** Erik Alves Gonçalves (dados e infraestrutura)

---

## 1. Objetivo

Registrar, com data, ambiente e contagens, a execução da suíte automatizada do backend,
e comprovar que os testes de integração com o banco de dados foram de fato executados
(e não apenas ignorados).

## 2. Composição da suíte

São 28 testes em 6 módulos, escritos com `pytest`:

| Módulo | Testes | O que verifica | Usa banco? |
|---|---:|---|---|
| `test_chat_integration.py` | 5 | Fluxo completo `POST /chat`: NLU → template SQL → PostgreSQL → resposta | Sim (4 de 5) |
| `test_import.py` | 11 | Leitura e validação de planilhas `.xlsx` (colunas, sinônimos, formatos pt-BR) | Não |
| `test_nlu_regras.py` | 5 | Classificação de intenção e extração de entidades pelo NLU por regras | Não |
| `test_templates_sql.py` | 4 | Existência dos 12 templates e ausência de interpolação de valores no SQL (segurança) | Não |
| `test_fallbacks.py` | 2 | Rejeição de perguntas com confiança abaixo do limiar (HTTP 422) | Não |
| `test_health.py` | 1 | Disponibilidade da API (`GET /health`) | Não |

Os testes de integração são marcados para serem **ignorados automaticamente quando a
variável `DATABASE_URL` não está definida** (`pytest.mark.skipif`). Isso é proposital:
o servidor de integração contínua não possui credenciais do banco, por segurança. A
execução com banco ocorre no ambiente de desenvolvimento, registrada na seção 4.

## 3. Ambientes e resultados

A mesma versão do código (commit `694a5d5`) foi executada em três ambientes:

| Ambiente | Sistema / Python | Banco disponível | Aprovados | Falhos | Ignorados | Total |
|---|---|---|---:|---:|---:|---:|
| Desenvolvimento local | Windows (win32) · Python 3.12.0 · pytest 8.3.2 | Sim — Supabase (PostgreSQL, região São Paulo), pooler porta 6543 | **28** | **0** | **0** | 28 |
| Integração contínua | GitHub Actions `ubuntu-latest` · Python 3.12 | Não (por projeto) | 23 | 0 | 5 | 28 |
| Ambiente de verificação | Linux · Python 3.11.15 · pytest 8.3.2 | Não | 23 | 0 | 5 | 28 |

Nos dois ambientes sem banco, os 5 ignorados são exatamente os testes de
`test_chat_integration.py`. Nenhum teste falhou em nenhum ambiente.

A execução de integração contínua corresponde à execução `37393475413` do workflow
`CI` (jobs `lint` e `test`, ambos com sucesso, em 06/10/2026), disparada pelo PR #4.

## 4. Comprovação da integração com o banco

Na execução local de 13/10/2026 os 5 testes de integração foram **executados e
aprovados** (0 ignorados). Os tempos individuais, extraídos do relatório JUnit
(`evidencias/pytest_2026-10-13.xml`), mostram a ida e volta real ao banco:

| Teste | Cenário | Tempo |
|---|---|---:|
| `test_chat_total_vendas_periodo` | "quanto faturei em março de 2024" → valor numérico do período | 294 ms |
| `test_chat_top_produtos_sem_periodo_explicito` | "Quais os 5 produtos mais vendidos?" → até 5 linhas, gráfico de barras | 166 ms |
| `test_chat_sem_resultado` | Período sem dados (jan/2020) → HTTP 404 `sem_resultado` | 158 ms |
| `test_valores_decimais_viram_float_serializavel` | Ticket médio → valores `numeric` convertidos para número no JSON | 147 ms |
| `test_chat_baixa_confianca_nao_toca_banco` | Pergunta fora do escopo → HTTP 422, **sem** consultar o banco | 3 ms |

O contraste é a própria evidência: os quatro testes que consultam o PostgreSQL levaram
entre 147 e 294 ms, enquanto o que por desenho não toca o banco levou 3 ms.

### 4.1 Teste manual complementar: importação de planilha

O endpoint `POST /import` foi exercitado manualmente contra o mesmo banco em
07/10/2026, com uma planilha de 10 linhas (9 válidas e 1 sem data, de propósito):

| Cenário | Resultado obtido |
|---|---|
| Primeira importação | `status: processada` — 10 lidas, 9 válidas, 1 rejeitada (motivo gravado em `staging_venda.erros`) |
| Reenvio do mesmo arquivo | `status: duplicada` — nenhuma linha reprocessada (deduplicação por hash SHA-256) |

## 5. Limitações registradas

1. **Integração fora do CI.** Os testes com banco rodam apenas no ambiente de
   desenvolvimento. Levá-los ao CI exigiria um banco de teste efêmero ou credenciais
   guardadas como *secret*; optou-se por não expor o banco ao CI nesta fase.
2. **Carga do ETL sem teste automatizado com banco.** Os 11 testes de `test_import.py`
   cobrem leitura e validação; a carga no esquema estrela foi verificada manualmente
   (seção 4.1). Um teste de integração automatizado para ela é trabalho futuro.
3. **Volume.** A importação foi validada com 10 linhas. Cargas de milhares de linhas
   pelo pooler do Supabase ainda não foram testadas.

## 6. Como reproduzir

```bash
cd backend
pip install -r requirements.txt
# com backend/.env contendo DATABASE_URL e EMPRESA_ID (banco de desenvolvimento ativo):
pytest -v -rA --junitxml=relatorio_pytest.xml
```

Sem o `.env`, a mesma linha reproduz o resultado do CI (23 aprovados, 5 ignorados).

---

## Apêndice — texto sugerido para o TCC (seção de validação)

> Para evidenciar a execução dos testes automatizados, a suíte do backend, composta
> por 28 testes escritos com a biblioteca pytest, foi executada em 13 de outubro de 2026
> sobre a mesma versão do código (commit 694a5d5) em três ambientes, conforme a Tabela X.
> No ambiente de desenvolvimento, com acesso ao banco PostgreSQL hospedado no Supabase,
> todos os 28 testes foram aprovados, incluindo os cinco testes de integração, que
> percorrem o fluxo completo da pergunta em linguagem natural até a consulta ao banco.
> Nos ambientes sem credenciais de banco (integração contínua e verificação), esses cinco
> testes são ignorados por projeto, e os 23 demais foram aprovados. Nenhum teste falhou.
> A execução efetiva da integração é confirmada pelos tempos registrados: os testes que
> consultam o banco levaram entre 147 e 294 ms, contra 3 ms do teste que, por desenho,
> não o acessa.
>
> **Tabela X – Resultado da execução dos testes automatizados por ambiente**
>
> | Ambiente | Banco | Aprovados | Falhos | Ignorados |
> |---|---|---:|---:|---:|
> | Desenvolvimento (Windows, Python 3.12) | Sim | 28 | 0 | 0 |
> | Integração contínua (GitHub Actions, Python 3.12) | Não | 23 | 0 | 5 |
> | Verificação (Linux, Python 3.11) | Não | 23 | 0 | 5 |
>
> Fonte: Elaborado pelos autores (2026).
