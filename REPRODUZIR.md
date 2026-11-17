# Reproduzir as evidências do Intellix

Pacote de reprodução (parecer da banca final, F07): como recriar, do zero e bit a
bit, os resultados citados no TCC. Todos os comandos abaixo foram executados e
conferidos; os números esperados estão ao lado.

## Pré-requisitos

- **PostgreSQL 16** no ar (local), com um usuário de senha conhecida;
- **Python 3.12+**;
- dependências do backend: `pip install -r backend/requirements.txt`
  (inclui `torch`, `fastapi`, `psycopg`; só o `psycopg` basta para o gabarito
  numérico, o isolamento, o manifesto e a reconciliação — ver a nota no fim).

## 1. Banco (um comando)

```bash
PGPASSWORD=<senha-do-postgres> ./scripts/configurar_reproducao.sh
```

Cria o banco `intellix`, aplica `database/local/supabase_minimo.sql` e as
migrações `001`–`008`, e popula a base de demonstração determinística
(`database/seed.py`, `SEED=42`). Ao final imprime o `DATABASE_URL`. **Esperado:**
`3.527 vendas / 8.941 itens`, faturamento `R$ 2.717.797,23`.

```bash
export DATABASE_URL='postgresql://postgres:<senha>@localhost:5432/intellix'
```

## 2. Rodar as evidências

| Ensaio | Comando | Esperado |
|---|---|---|
| **Gabarito numérico** das 14 consultas (F02) | `python scripts/gabarito_numerico.py --saida docs/evidencias` | **19/19** provas numéricas |
| **Isolamento** com empresas fictícias (F05/F09) | `python scripts/demo_isolamento.py --saida docs/evidencias` | **6/6** passos |
| **Reconciliação** de carga (F06) | `python scripts/reconciliacao_carga.py --saida docs/evidencias` | reconciliação completa (vendas 3, itens 5, faturamento 290, ticket 96,67) |
| **Manifesto** de reprodução (F07) | `python scripts/manifesto_reproducao.py --saida docs/evidencias` | hashes dos pesos + fingerprint `58d126cf…` do dataset |
| **Generalização** — perguntas inéditas (F01) | `NLU_BACKEND=modelo EMPRESA_ID=00000000-0000-0000-0000-000000000001 python scripts/avaliar_ineditas.py --modo app --saida docs/evidencias` | **13/30** (IC95% 27–61%) |
| **Ablação** v1.2.0, corpus externo (F03) | `EMPRESA_ID=00000000-0000-0000-0000-000000000001 python "ia training/ablacao_nlu_externa.py" --saida docs/evidencias` | cabeça BIO **+0** de valor |
| **100 perguntas** (regressão) | iniciar a API (abaixo) e `python scripts/avaliar_100_perguntas.py --modo api --url http://127.0.0.1:8000` | **88/100** com v1.2.0 |

Para os ensaios que precisam da API no ar (100 perguntas; carga em config normal):

```bash
cd backend && NLU_BACKEND=modelo AUTH_OBRIGATORIA=false \
  EMPRESA_ID=00000000-0000-0000-0000-000000000001 DATABASE_URL="$DATABASE_URL" \
  uvicorn app.main:app --port 8000
# noutro terminal:
python scripts/teste_carga_normal.py --url http://127.0.0.1:8000 --saida docs/evidencias
```

**Carga em config normal (F05) esperado:** partida fria ~dezenas de ms × quente
menor; burst > 30/min no `/chat` → parte em `200`, parte em `429` (limitador).

## 3. Testes automatizados

```bash
cd backend && pytest -q -rs    # com DATABASE_URL apontando para o banco acima
```

Inclui, entre os 202 testes, os novos `test_gabarito_numerico.py` (F02) e
`test_reconciliacao_carga.py` (F06). Os 4 testes de RLS rodam à parte como
`intellix_app` (ver `docs/evidencias/execucao_testes_2026-11-06.md`).

## 4. Conferir a integridade

Rodar `python scripts/manifesto_reproducao.py` no mesmo commit deve reproduzir os
hashes dos pesos, das migrações e o fingerprint do dataset. Qualquer divergência
indica que o ensaio foi feito sobre outro estado. O painel de rastreamento das
correções está em [`docs/mapeamento_parecer_banca_final.md`](docs/mapeamento_parecer_banca_final.md).

## Nota sobre o `torch`

`backend/requirements.txt` fixa `torch==2.4.1` pelo índice de wheels CPU do
PyTorch, o que requer **Python 3.12** (não há wheel 2.4.1 para 3.13). Os ensaios
que usam o modelo (generalização, ablação, 100 perguntas, API) precisam do
`torch`; os demais (gabarito numérico, isolamento, manifesto, reconciliação)
dependem só de `psycopg` e rodam sem ele.
