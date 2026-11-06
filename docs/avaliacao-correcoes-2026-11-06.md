# Reavaliação das 100 perguntas: antes e depois das correções de 06/11/2026

**Data:** 06/11/2026 · **Modelo:** `intellix_nlu_v1.2.0.pt` nas duas execuções

## 1. O que foi medido

As mesmas 100 perguntas (`docs/perguntas_validacao.md`), com o mesmo programa
(`scripts/avaliar_100_perguntas.py --modo api`) e o mesmo critério de acerto
(código de estado HTTP e título do template esperado), em duas versões do
backend, no mesmo dia e sobre o mesmo banco:

| | Antes | Depois |
|---|---|---|
| Código | `c6d47be` (main antes das correções da revisão) | `3e71918` (main + PR #30) |
| API | local, porta 8001 | local, porta 8002 |
| Banco | Postgres 16 local, base de demonstração (`database/seed.py`) | o mesmo |
| NLU | modelo treinado v1.2.0 (`NLU_BACKEND=modelo`) | o mesmo |

Mudou só o código: o que diferir entre as colunas vem das correções.

Evidências: `docs/evidencias/avaliacao_api_2026-11-06_antes_correcoes.{md,csv}`
e `docs/evidencias/avaliacao_api_2026-11-06_depois_correcoes.{md,csv}`.

## 2. Resultado

| Categoria | Perguntas | Antes | Depois |
|---|---:|---:|---:|
| total_vendas_periodo | 7 | 7 | 7 |
| top_produtos | 7 | 7 | 7 |
| ticket_medio | 7 | 7 | 7 |
| quantidade_vendas | 7 | 6 | 6 |
| top_clientes | 7 | 7 | 7 |
| desempenho_vendedor | 7 | 3 | 3 |
| **produtos_sem_saida** | 7 | **2** | **7** |
| comparacao_periodos | 7 | 6 | 6 |
| variacao_periodo | 7 | 6 | 6 |
| vendas_por_canal | 7 | 6 | 6 |
| vendas_por_categoria | 7 | 7 | 7 |
| vendas_por_pagamento | 7 | 4 | 4 |
| Fora de escopo | 6 | 6 | 6 |
| Parâmetro ausente | 5 | 4 | 4 |
| Sem resultado esperado | 5 | 5 | 5 |
| **Total** | **100** | **83** | **88** |

A execução "antes" reproduz os 83/100 da reavaliação de 05/11/2026 com o
modelo v1.2.0 (`avaliacao_api_2026-11-05_v1.2.0.md`).

**O que mudou:** exatamente as 5 perguntas de produtos sem saída que falhavam
(n.º 44, 45, 46, 48 e 49). Na base de demonstração todos os produtos venderam
nos períodos perguntados; antes a lista vazia virava 404 "sem resultado", agora
é a resposta (200, "nenhum produto ficou parado"). Nenhuma pergunta piorou.

## 3. Os 12 erros que restam

| Grupo | Perguntas | Causa |
|---|---|---|
| Vendedor inexistente na base de demonstração | 37 (João), 38 (Maria), 40 (Ana) | A base tem Amanda, Carlos, Fernanda, Gustavo, Patrícia e Rodrigo. A pergunta é entendida e a resposta "sem resultado" é a correta para esses dados; o erro é do repertório, não do sistema. |
| Confiança abaixo do limiar (0,70) | 25, 54, 67, 78, 84 | O modelo não reconhece a formulação; o sistema pede para reformular, sem resposta errada. Pede novos moldes de treino. |
| Intenção errada | 41, 62 | "Performance do time" lida como quantidade de vendas; "quanto caiu... comparado ao mês anterior" lida como faturamento do período. |
| Recorte em vez de distribuição | 83 | "Quantas vendas no pix" responde a quantidade de vendas no pix, de propósito, e não a distribuição por forma de pagamento que o roteiro esperava. |
| Não pediu complemento | 94 | "Quanto vendi?", sem período, responde o ano corrente em vez de pedir o período. |

Sem o grupo dos vendedores inexistentes, que depende só dos dados de teste,
restam 9 erros, todos ligados ao modelo ou a uma decisão de comportamento.

## 4. Observações

- **Vendedor com acento (correção do PR #28):** não mudou nenhuma resposta.
  Os nomes que existem no cadastro já eram casados por `app/filtros.py` e
  normalizados em `app/refino.py`; a correção em `adaptador_modelo.py` cobre só
  o caminho em que o nome não casa com o cadastro. Conferido com "Como foi o
  desempenho da Patrícia em março de 2024?": as duas versões encontram
  "Patrícia Alves".
- **Latência:** não comparável à produção (API e banco na mesma máquina):
  mediana de 10 a 11 ms nas duas execuções. O indicador de produção continua o
  da versão publicada.
- **PyTorch:** 2.15 (CPU) nesta máquina; a produção usa 2.4.1. Os pesos do
  modelo são os mesmos; a execução "antes" reproduzir os 83/100 de 05/11 indica
  que a diferença de versão não alterou as classificações.
- **Período relativo:** "esse ano", "último mês" e semelhantes partem da data
  da execução (06/11/2026), limitada à última venda da base.

## 5. Como reproduzir

```bash
# banco local como no CI: supabase_minimo.sql + migrations + seed.py
cd backend
DATABASE_URL=postgresql://... EMPRESA_ID=00000000-0000-0000-0000-000000000001 \
AUTH_OBRIGATORIA=false LIMITE_REQUISICOES=0 NLU_BACKEND=modelo \
uvicorn app.main:app --port 8000
# em outro terminal, na raiz do repositório
python scripts/avaliar_100_perguntas.py --modo api --url http://127.0.0.1:8000
```
