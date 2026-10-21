# Plano — Duas fontes de dados (Excel + banco do cliente)

Status: **proposta de implementação** · Decisão de arquitetura tomada em 2026-10-05.

Este documento mapeia, arquivo por arquivo, o que muda no backend para o
Intellix deixar de depender só da base de demonstração e passar a aceitar os
dados do próprio cliente por **duas portas**:

1. **Upload de Excel** — para a loja pequena que não tem banco estruturado.
2. **Conexão a um banco** — para a empresa média que já tem seus dados num
   Postgres/Supabase.

## 1. Princípio: uma schema analítica, várias fontes de ingestão

Os 12 templates de consulta ([`backend/app/sql/templates.py`](../backend/app/sql/templates.py))
são escritos contra o **star schema** do Intellix (`fato_item_venda`,
`dim_produto`, `dim_cliente`, `dim_vendedor`, `dim_data`). Esse acoplamento é
proposital: é o que sustenta o argumento central do TCC (seção 7.7 — "a
pergunta nunca vira SQL livre; só escolhe um template parametrizado").

Portanto **as duas novas portas não consultam dados em formatos diferentes**.
Elas são apenas **adaptadores de ingestão** que carregam os dados do cliente
para o mesmo star schema:

```
                 ┌─────────────────────┐
  Excel (.xlsx) ─┤                     │
                 │  adaptador de       │     ┌──────────────────┐
  Banco externo ─┤  ingestão (ETL)     ├────▶│  star schema      │
  (Postgres)     │  → staging → dim/fato│     │ (dim_* / fato_*)  │
                 └─────────────────────┘     └────────┬─────────┘
                                                       │
                                            templates SQL (inalterados)
                                                       │
                                                  POST /chat
```

Consequência prática: **nenhum template muda**, o `/chat` continua idêntico, e
o modelo de segurança do TCC fica intacto. Todo o trabalho novo é de
**entrada de dados**, não de consulta.

## 2. O que já existe e será reaproveitado (não criar do zero)

| Peça | Onde | Observação |
|---|---|---|
| Tabelas `importacao` e `staging_venda` | [`001_schema.sql`](../database/migrations/001_schema.sql) | Criadas para isto ("dormente até semana 14"). Têm `hash_arquivo` (dedupe) e contadores de linhas válidas/rejeitadas. |
| Frontend de upload | [`Importar.jsx`](../frontend/src/paginas/Importar.jsx) + [`importacao.js`](../frontend/src/servicos/importacao.js) | Valida colunas (com sinônimos), mostra prévia e faz `POST /import`. Documentado: "quando a rota subir, nada aqui muda". |
| Padrão de ETL | [`seed.py`](../database/seed.py) | Dedupe de dimensões via `on conflict`, montagem da fato, `refresh materialized view`. O import segue este mesmo padrão. |
| `norm_key()` + colunas `nome_norm` geradas | [`001_schema.sql`](../database/migrations/001_schema.sql) | Deduplicação de "Coca Cola"/"COCA-COLA" já resolvida no banco via `unique (empresa_id, nome_norm)`. |

## 3. Mudanças no backend — Excel (`POST /import`)

Esta é a porta de maior prioridade e a mais autocontida.

### 3.1 Dependência nova
- `requirements.txt`: adicionar **`openpyxl`** (leitor de `.xlsx` no servidor —
  mais leve que `pandas`). `.xls` antigo **não** é suportado pelo openpyxl; o
  servidor rejeita `.xls` com mensagem pedindo "salve como .xlsx".

### 3.2 Arquivos novos
- **`backend/app/importacao/leitor_excel.py`** — abre o `.xlsx` (openpyxl em
  modo read-only), confere assinatura/tamanho (espelha o limite de 10 MB do
  frontend), mapeia o cabeçalho para as colunas de `staging_venda` usando os
  **mesmos sinônimos** do frontend (`importacao.js`). Devolve linhas cruas +
  relatório de colunas encontradas/faltando.
- **`backend/app/importacao/etl.py`** — recebe as linhas cruas e:
  1. grava uma linha em `importacao` (status `pendente`, `hash_arquivo`);
  2. joga tudo como texto em `staging_venda`;
  3. promove linha a linha: converte tipos, faz upsert em
     `dim_produto/dim_cliente/dim_vendedor` (`on conflict do nothing`),
     resolve `data_id` em `dim_data`, insere em `fato_item_venda`
     (`on conflict (empresa_id, venda_id, produto_id) do nothing`);
  4. linha inválida vira rejeitada (coluna `erros`), sem derrubar o lote;
  5. atualiza `importacao` (`processada`, contadores) e dá
     `refresh materialized view mv_faturamento_mensal`.

### 3.3 Arquivos alterados
- **`backend/app/main.py`** — adicionar `POST /import` (multipart, campo
  `arquivo` — nome que o `importacao.js` já envia). Trata dedupe (arquivo já
  importado → resposta clara), `psycopg.OperationalError` → 503
  `banco_indisponivel` (mesmo padrão do `executor.py`). Resposta JSON com
  `linhas_lidas`, `linhas_validas`, `linhas_rejeitadas` — campos que o
  `Importar.jsx` já lê.

### 3.4 Regras de conversão (o "template" que o cliente preenche)
- **Obrigatórias**: `data_venda`, `produto`, `quantidade`, e pelo menos uma de
  `valor_unitario`/`valor_total`.
- **`valor_total`**: se ausente, calculado como `quantidade * valor_unitario -
  desconto`.
- **`venda_id`**: recomendado na planilha (agrupa itens da mesma venda, faz
  `ticket_medio`/`quantidade_vendas` baterem). Se ausente, cada linha vira uma
  venda própria (id sintético pela linha de origem) — documentado no template.
- **Datas**: aceitam célula de data do Excel ou texto `dd/mm/aaaa` e
  `aaaa-mm-dd`.

## 4. Mudanças no backend — banco do cliente (sincronização)

Mesmo destino do Excel, fonte diferente. Entrega posterior ao Excel (reaproveita
o `etl.py`).

### 4.1 Arquivos novos
- **`backend/app/importacao/conector_banco.py`** — conecta ao Postgres do
  cliente (connection string informada por ele), roda uma **query de extração**
  e entrega as linhas no mesmo formato que o `leitor_excel.py` produz, para o
  `etl.py` seguir idêntico.
- **Mapa de colunas** — como o schema do cliente não é o nosso, é preciso um
  passo de **de→para** (coluna do cliente → coluna canônica do Intellix). No
  MVP pode ser um JSON de configuração por empresa; evoluível para uma tela de
  mapeamento no frontend.

### 4.2 Decisão de segurança
- A connection string do cliente é **segredo**: nunca em URL/log, só em
  variável de ambiente/secret do backend. A extração usa **uma query de leitura
  fixa** montada a partir do mapa de colunas — nunca SQL livre vindo do cliente.

## 5. Pontos transversais (valem para as duas portas)

### 5.1 `dim_data` só vai até 2026-12-31
[`002_dim_data.sql`](../database/migrations/002_dim_data.sql) popula 2023–2026.
Dados reais fora disso **são rejeitados** na resolução do `data_id`. Antes de
clientes reais: estender o calendário (ex.: 2023–2030) ou gerar a data sob
demanda no ETL. **Ação necessária.**

### 5.2 Isolamento por empresa (multi-tenant)
O schema **já tem `empresa_id`** em todas as tabelas — o isolamento está pronto
no banco. O que falta é a origem do `empresa_id`: hoje é uma env var fixa
([`db.py:get_empresa_id`](../backend/app/db.py)), coerente com o "MVP de tenant
único" do TCC. Quando houver login, passa a vir do usuário autenticado. Para o
escopo atual do TCC, **mantém-se tenant único** — cada porta nova grava sob o
mesmo `EMPRESA_ID`. Multi-tenant real fica registrado como evolução.

## 6. Novos contratos de API (atualizar `docs/contratos.md`)

| Método | Caminho | Entrada | Saída |
|---|---|---|---|
| `POST` | `/import` | multipart; campo `arquivo` (.xlsx) | `{importacao_id, status, linhas_lidas, linhas_validas, linhas_rejeitadas}` |
| `POST` | `/import/banco` *(fase 2)* | `{mapa_colunas}` (connection string via secret) | igual ao `/import` |

## 7. Feedback da professora — itens que tocam código

Separados do que é documentação (despriorizado). Ver [`Retorno - Maria`].

- **FB9 (menor) — endpoints/OpenAPI**: o FastAPI já gera `/openapi.json`.
  Adicionar `scripts/export_openapi.py` para exportar o spec como artefato do
  TCC (método, caminho, entradas, saídas). Fica ainda mais completo agora que
  `/import` entra na superfície da API.
- **FB2 (crítico) — modelo treinado na API**: o código de integração **existe**
  ([`adaptador_modelo.py`](../backend/app/nlu/adaptador_modelo.py)). O motivo de
  "só 3 das 12 intenções" é que produção roda com `NLU_BACKEND=regras` (o
  baseline cobre 3). **Ação**: definir `NLU_BACKEND=modelo` no Render e rodar o
  conjunto de 100 perguntas para consolidar taxa/latência. É config + validação,
  não código novo — mas exige o ambiente no ar.
- **FB7 (importante) — relatório de testes**: rodar `pytest` capturando data,
  ambiente e aprovados/falhos/ignorados. A suíte de banco precisa de
  `DATABASE_URL` real para comprovar "integração com banco executada".

## 8. Ordem de entrega sugerida

1. **Template `.xlsx`** oficial (baixo risco, destrava o cliente).
2. **`POST /import`** (Excel) — leitor + ETL + endpoint + testes.
3. **OpenAPI export** (FB9) — ganho fácil.
4. **Estender `dim_data`** antes de dados reais.
5. **Conexão a banco externo** (reaproveita o ETL).
6. **FB2/FB7** — validação no ambiente (depende de deploy/banco).

## 9. Como rodar/validar (ambiente)

Nada disto roda nesta máquina de desenvolvimento do frontend (sem
`DATABASE_URL`, sem libs do backend instaladas). Para validar:

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -r requirements.txt
# preencher backend/.env (DATABASE_URL do Supabase, EMPRESA_ID)
uvicorn app.main:app --reload
pytest -v                       # relatório para o FB7
```
