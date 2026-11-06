# Contratos

Fonte da verdade dos formatos trocados entre as partes do sistema. Depois de
mesclado, ninguém muda o que está aqui sem avisar o grupo.

```
 Dev D                    Dev B                       Dev C
[React] --pergunta--> [FastAPI] --SQL--> [Postgres com dados]
                          ^
                    [Dev A: modelo]
```

## 1. `Interpretacao` — fronteira NLU → Backend

O que o serviço de NLU (regras hoje, modelo treinado depois) devolve para o
backend. Implementado em [`backend/app/models.py`](../backend/app/models.py).

```python
class Interpretacao(BaseModel):
    intencao: str | None
    confianca: float
    entidades: dict[str, Any] = {}
    texto_original: str
    entidades_modelo: dict[str, Any] = {}
```

| Campo | Tipo | Observação |
|---|---|---|
| `intencao` | `str \| None` | Chave de `TEMPLATES` (ver [`app/sql/templates.py`](../backend/app/sql/templates.py)), ou `None` se nada bateu. |
| `confianca` | `float` | 0.0–1.0. Abaixo de `0.70` o backend não tenta consultar — pede reformulação (ver `app/fallbacks.py`). |
| `entidades` | `dict` | Só o que o template correspondente precisa (`periodo_inicio`, `periodo_fim`, `limite`, ...). |
| `texto_original` | `str` | Pergunta como o usuário digitou, sem normalização. |
| `entidades_modelo` | `dict` | Trechos que o modelo marcou na frase (tags BIO), crus: `{"PRODUTO": "botas de couro"}`. Não vão para o SQL; servem de pista para `app/filtros.py` achar o valor exato no catálogo. |

## 2. `ResultSet` — fronteira Backend → Frontend

O que o backend devolve. **Passa por aqui tudo**: tela, exportação Excel e
PDF. Implementado em [`backend/app/models.py`](../backend/app/models.py).

```python
class ResultSet(BaseModel):
    titulo: str
    colunas: list[str]
    linhas: list[list[Any]]
    tipo_visualizacao: str   # numero | tabela | barra | linha | pizza
    parametros: dict[str, Any] = {}
    confianca: float = 1.0
    gerado_em: str
    intencao: str | None = None        # chave do template que respondeu
    evolucao: dict[str, Any] | None = None  # 12 meses até o mês perguntado
    mensagem: str | None = None        # frase pronta quando a lista vazia é a resposta
```

Regra inegociável: **valores numéricos ficam como número** (`48231.50`),
nunca como texto formatado (`"R$ 48.231,50"`). Formatação de moeda é
responsabilidade do frontend — é o que faz o exportador de Excel/PDF virar
poucas linhas de código em vez de precisar re-parsear texto.

`tipo_visualizacao` decide como o frontend renderiza (ver
[`frontend/src/paginas/Chat.jsx`](../frontend/src/paginas/Chat.jsx) e
[`frontend/src/componentes/GraficoResultado.jsx`](../frontend/src/componentes/GraficoResultado.jsx)):

- `numero` → usa `linhas[0][1]` como valor único.
- `barra` → gráfico de barras, uma linha por categoria.
- `linha` → evolução no tempo (ex.: faturamento de um ano, mês a mês).
- `pizza` → divisão do total (desenhada como rosca).
- `tabela` → tabela com `colunas` como cabeçalho.

O usuário pode trocar a visualização na tela; o tipo devolvido é só o padrão.

## 3. Endpoints

### `GET /health`

**Implementado.** Usado pelo Dev C para o healthcheck do deploy.

```json
{ "status": "ok" }
```

### Autenticação (vale para todas as rotas, menos `/health` e `/capacidades`)

O login é feito pelo **Supabase Auth**, direto do frontend: cadastro, entrada,
recuperação e troca de senha não passam pelo backend, e o backend nunca vê
senha. O frontend envia o token de acesso que o Supabase devolve em toda
requisição:

```
Authorization: Bearer <access_token do Supabase>
```

O backend confere a assinatura, a validade e o projeto do token
([`app/auth.py`](../backend/app/auth.py)) e usa o `id` do usuário para decidir
de quais datasets ele é dono ([`app/acesso.py`](../backend/app/acesso.py)).
`GET /health` continua aberto.

| Situação | Resposta |
|---|---|
| Sem cabeçalho e `AUTH_OBRIGATORIA=false` | segue como anônimo (só base demo e datasets sem dono) |
| Sem cabeçalho e `AUTH_OBRIGATORIA=true` | `401`, `tipo: "nao_autenticado"` |
| Token inválido (sempre, mesmo com login opcional) | `401`, `tipo: "nao_autenticado"` |
| Token expirado | `401`, `tipo: "sessao_expirada"` (frontend renova ou manda ao login) |
| `empresa_id` de outro usuário, inexistente ou malformado | `404`, `tipo: "dataset_nao_encontrado"` (mesma resposta, para não revelar ids) |

**Em produção (Render), `AUTH_OBRIGATORIA=true`:** nenhuma rota de dados
responde sem login. O valor `false` (padrão do código e do
`backend/.env.example`) existe para desenvolvimento local e para as
avaliações automatizadas (`scripts/avaliar_100_perguntas.py`).
`/planilhas` e `/conversas` exigem login mesmo com `false`: sem usuário não há
"minhas planilhas" nem "minhas conversas".

### Limite de requisições

Por IP de origem, em memória ([`app/limite.py`](../backend/app/limite.py)):
`/chat` 30 por minuto, `/resumo` 60 por minuto, `/import` 10 por hora
(ajustáveis por variável de ambiente). Acima do limite: `429` com
`tipo: "limite_requisicoes"` e o cabeçalho `Retry-After`.

### `GET /capacidades`

Aberto (sem login). Lista o que o agente responde, com exemplos, e o que está
fora do escopo. Alimenta a tela "O que posso perguntar".

```json
{
  "total_intencoes": 14,
  "intencoes": [{ "chave": "top_produtos", "titulo": "Produtos mais vendidos", "exemplos": ["Quais os 5 produtos mais vendidos?"] }],
  "limitacoes": ["Não faço previsões nem recomendações — só o que já aconteceu nos dados."],
  "dica": "Inclua sempre um período (ex.: 'em março de 2024' ou 'em 2024')."
}
```

**12 intenções × 14 tipos de pergunta.** O modelo NLU classifica **12
intenções** (as de `ia training/moldes.py`). Duas consultas a mais,
`unidades_vendidas` e `melhor_mes`, são **refinamentos** aplicados depois do
modelo ([`app/refino.py`](../backend/app/refino.py)), sem retreino: "quantas
botas vendemos" refina `total_vendas_periodo`; "qual foi o melhor mês" refina
uma pergunta de período. Por isso `templates.py` tem 14 consultas e a tela
mostra 14 tipos de pergunta, enquanto o modelo e as 100 perguntas de
validação trabalham com 12 intenções.

### `POST /chat`

**Implementado** ([`app/main.py`](../backend/app/main.py)). Pipeline: NLU
(intenção + trechos) → filtros pelo catálogo do dataset → contexto da conversa
→ refino → template SQL parametrizado → `ResultSet`. Cada consulta executada
é registrada em `log_consulta` (auditoria).

Requisição — modelo `Pergunta`:
```json
{
  "pergunta": "e em abril?",
  "empresa_id": "opcional",
  "contexto": { "intencao": "total_vendas_periodo", "entidades": { "periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31" } }
}
```
`pergunta` tem de 1 a 500 caracteres. `contexto` é opcional: é o resumo da
resposta anterior (`intencao` + `parametros`), que permite perguntas como
"e em abril?" ou "e de calçados?" (ver [`app/contexto.py`](../backend/app/contexto.py)).
`empresa_id` é **opcional**: quando presente (o id devolvido por um `/import`),
a consulta cai sobre os dados daquela planilha, **desde que o usuário logado
seja o dono** (ver Autenticação acima); ausente, usa a base de demonstração
(`EMPRESA_ID` fixo). O frontend guarda o id da última importação
em `localStorage` (ver `frontend/src/utils/dataset.js`) e o reenvia aqui.

Resposta em caso de sucesso — `200 OK` com um `ResultSet`:
```json
{
  "titulo": "Faturamento no período",
  "colunas": ["periodo", "faturamento"],
  "linhas": [["2024-03", 48231.5]],
  "tipo_visualizacao": "numero",
  "parametros": {"periodo_inicio": "2024-03-01", "periodo_fim": "2024-03-31"},
  "confianca": 0.93,
  "gerado_em": "2026-07-27T12:00:00Z"
}
```

Resposta em caso de baixa confiança — `422 Unprocessable Entity`, já
implementado em [`app/fallbacks.py`](../backend/app/fallbacks.py):
```json
{
  "detail": {
    "tipo": "baixa_confianca",
    "mensagem": "Não entendi a pergunta. Tente reformular.",
    "exemplos": ["Quanto faturei em março?", "Quais os 5 produtos mais vendidos?"]
  }
}
```

Os demais erros do `/chat` seguem o mesmo formato (`detail.tipo` +
`detail.mensagem`):

| Situação | Código | `tipo` |
|---|---|---|
| Falta um dado obrigatório (período, vendedor, quantos no ranking) | `422` | `parametro_faltando` (com `faltando` e uma pergunta de esclarecimento em `mensagem`) |
| Valor impossível vindo da pergunta ou do contexto | `422` | `parametro_invalido` |
| Nenhum registro no período/filtro | `404` | `sem_resultado` |
| Dataset de outra pessoa, inexistente ou malformado | `404` | `dataset_nao_encontrado` |
| Banco fora do ar | `503` | `banco_indisponivel` |
| Limite de requisições | `429` | `limite_requisicoes` |

Exceção: "produtos sem saída" com todos os produtos vendidos responde `200`
com `linhas: []` e a frase em `mensagem` (a lista vazia é a resposta).

O frontend espera `err.mensagem` e `err.exemplos` no corpo de erro (ver
[`frontend/src/servicos/api.js`](../frontend/src/servicos/api.js)) — por isso
os fallbacks sempre preenchem esses campos dentro de `detail`.

### `POST /import`

**Implementado** (ver [`app/main.py`](../backend/app/main.py) e
[`app/importacao/`](../backend/app/importacao/)). Recebe a planilha de vendas,
valida, carrega no star schema e devolve o relatório da carga. Plano completo
em [`plano-ingestao-dados.md`](plano-ingestao-dados.md).

Requisição — `multipart/form-data`, campo `arquivo` (`.xlsx`):
```
POST /import
Content-Type: multipart/form-data
arquivo=<planilha.xlsx>
```

Resposta — `200 OK`:
```json
{
  "importacao_id": "7b1e...",
  "empresa_id": "a3c9...",
  "status": "processada",
  "linhas_lidas": 1240,
  "linhas_validas": 1231,
  "linhas_rejeitadas": 9,
  "colunas_encontradas": ["data_venda", "produto", "quantidade", "valor_total"],
  "colunas_ignoradas": ["observacao"],
  "motivos_rejeicao": { "data inválida ou ausente": 9 },
  "linhas_agrupadas": 0
}
```
`motivos_rejeicao` explica, por motivo, quantas linhas ficaram de fora;
`linhas_agrupadas` conta as linhas que repetiam o mesmo produto na mesma venda
e foram somadas. Limite de 10 MB por arquivo.
Cada importação cria um **dataset próprio** (uma empresa nova), registrado em
nome do usuário logado (`empresa.dono_id`, migration 005), e devolve o
`empresa_id`; o frontend o reenvia no `/chat` para as perguntas caírem sobre
os dados importados, não sobre a base demo.

Planilha inválida (colunas obrigatórias faltando, arquivo ilegível) — `422`:
```json
{ "detail": { "tipo": "planilha_invalida", "mensagem": "Faltam colunas obrigatórias..." } }
```
Banco fora do ar — `503` com `tipo: "banco_indisponivel"` (mesmo padrão do `/chat`).

Colunas obrigatórias: `data_venda`, `produto`, `quantidade` e pelo menos uma de
`valor_unitario`/`valor_total`. Sinônimos aceitos (ex.: `qtd`, `preço`, `total`)
em [`leitor_excel.py`](../backend/app/importacao/leitor_excel.py) — a mesma
lista do frontend ([`importacao.js`](../frontend/src/servicos/importacao.js)).

### `GET /planilhas` e `DELETE /planilhas/{empresa_id}` — minhas planilhas

Exigem login (401 sem token, mesmo com `AUTH_OBRIGATORIA=false`). O dono é
sempre o usuário do token; nunca vem do pedido. Dependem da migration
`007_minhas_planilhas.sql`.

`GET /planilhas` devolve as planilhas importadas pela conta, da mais recente
para a mais antiga:

```json
{
  "planilhas": [
    {
      "empresa_id": "145d7414-63e3-4278-a582-7fb0fa4d1017",
      "nome_arquivo": "vendas_loja_2024.xlsx",
      "importada_em": "2026-11-06T03:41:29.739696+00:00",
      "linhas_validas": 2,
      "linhas_rejeitadas": 0,
      "primeira_venda": "2024-03-10",
      "ultima_venda": "2024-05-02"
    }
  ]
}
```

`DELETE /planilhas/{empresa_id}` apaga o dataset inteiro (vendas, staging,
dimensões e auditoria) e responde `{"excluida": true, "empresa_id": "..."}`.
Planilha de outra pessoa, a base de demonstração, id inexistente ou
malformado: o mesmo 404 `dataset_nao_encontrado`, sem revelar quais ids
existem.

### `GET /conversas`, `PUT /conversas/{id}` e `DELETE /conversas/{id}` — histórico de conversas

Exigem login, como `/planilhas`. Guardam as conversas do chat na conta, para
a pessoa reencontrá-las em outro aparelho (antes ficavam só no
`localStorage`). Dependem da migration `008_historico_conversas.sql`; o dono
vem sempre do token.

`GET /conversas` devolve as conversas da conta, da mais recente para a mais
antiga:

```json
{
  "conversas": [
    {
      "id": "5f0c1c8e-2a4b-4c0e-9d0a-0b8f2d7c6e11",
      "titulo": "Faturamento de março",
      "mensagens": [{ "tipo": "usuario", "texto": "Quanto faturei em março de 2024?" }],
      "criadoEm": "2026-11-06T13:10:00+00:00",
      "atualizadoEm": "2026-11-06T13:12:00+00:00"
    }
  ]
}
```

`PUT /conversas/{id}` cria ou atualiza (o `id` é o UUID gerado pelo
frontend). Corpo: `titulo` (1 a 200 caracteres), `mensagens` (até 200, no
formato do frontend, gravadas como JSONB) e `criadoEm` (opcional). Resposta:
`{"id": "..."}`. `DELETE /conversas/{id}` responde
`{"excluida": true, "id": "..."}`.

Conversa de outra pessoa, inexistente ou id malformado: o mesmo `404`
`conversa_nao_encontrada`, sem sobrescrever nem revelar nada.

### `GET /resumo` — panorama do mês (implementado)

Alimenta a tela Início. Implementação em
[`backend/app/resumo.py`](../backend/app/resumo.py); mesmas regras de
acesso do `/chat` (`empresa_id` opcional, só o dono consulta um dataset
importado).

```
GET /resumo?empresa_id=<uuid>&ano=2024&mes=3
```

`ano` e `mes` são opcionais: sem eles, vale o mês mais recente com dados que
já começou (fuso de São Paulo). `mes` fora de 1–12 → `422`; dataset sem
nenhuma venda → `404 sem_resultado`.

Resposta (resumida):
```json
{
  "periodo": { "ano": 2024, "mes": 3, "rotulo": "março de 2024", "inicio": "2024-03-01", "fim": "2024-03-31" },
  "periodo_anterior": { "ano": 2024, "mes": 2, "rotulo": "fevereiro de 2024" },
  "meses_disponiveis": [{ "ano": 2024, "mes": 3, "rotulo": "março de 2024" }],
  "kpis": [{ "chave": "faturamento", "rotulo": "Faturamento", "valor": 39275.59, "formato": "moeda", "variacao_pct": 10.5 }],
  "serie_diaria": [{ "dia": 1, "valor": 1520.4 }],
  "serie_mensal": [{ "ano": 2023, "mes": 4, "rotulo": "abr/23", "valor": 52310.0 }],
  "categorias": [{ "nome": "Vestuário", "valor": 9800.0, "pct": 24.9 }],
  "canais": [{ "nome": "Loja", "valor": 17000.0, "pct": 43.3 }],
  "top_produtos": [{ "nome": "Smartwatch", "valor": 4398.9, "pct": 11.2, "variacao_pct": 22.2 }],
  "observacoes": [{ "tipo": "alta", "texto": "Faturamento 10,5% acima de fevereiro.", "pergunta": "Quanto faturei em março de 2024?" }],
  "resumo_texto": ["Em março de 2024, a loja faturou R$ 39.275,59 em ..."],
  "total_registros": 218,
  "atualizado_em": "2026-11-05T14:32:00+00:00"
}
```

Regras:
- `valor` sempre número cru; `variacao_pct` é `null` sem mês anterior para
  comparar (o frontend não desenha seta nesse caso).
- `observacoes` saem de regras fixas com limiar (variação ≥ 3% no
  faturamento, ≥ 15% num produto que tinha ao menos 2% do faturamento
  anterior, produtos sem saída, melhor dia da semana, canal com ≥ 40%).
  Nenhuma regra disparou → lista vazia; nada é estimado.
- `pergunta` é uma pergunta pronta para o `/chat` (ou `null`): o frontend a
  usa para levar da observação à análise detalhada.
- `resumo_texto` é montado só com os números calculados, por modelo de
  frase -- não há geração de linguagem livre.

O `ResultSet` do `/chat` também passou a trazer `intencao` (opcional), a
chave do template que respondeu — o frontend usa para sugerir a próxima
pergunta.

E `mensagem` (opcional), presente quando a resposta certa é uma lista
vazia: em "produtos sem saída", se todos os produtos venderam no período, o
`/chat` devolve 200 com `linhas: []` e a frase pronta em `mensagem`, em vez
do 404 `sem_resultado`.

O `contexto` reenviado pelo frontend é filtrado antes de chegar ao SQL
(`sanear_entidades` em `app/models.py`): datas que não são ISO válidas,
`limite` fora de 1..100, listas, objetos e textos acima de 200 caracteres
são descartados. Um valor impossível que ainda chegue ao banco vira 422
`parametro_invalido`, nunca 500.

## Regra de ouro: a pergunta nunca vira SQL diretamente

O NLU só escolhe **qual** template usar (uma chave fixa de
[`TEMPLATES`](../backend/app/sql/templates.py)) e preenche os valores dos
`%(...)s`, que o `psycopg` parametriza. O usuário influencia os *valores*,
nunca a *estrutura* da consulta. É o argumento central do capítulo 7.7 do
TCC contra soluções que deixam o modelo gerar SQL livremente.
