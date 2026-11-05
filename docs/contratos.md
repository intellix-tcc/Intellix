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
```

| Campo | Tipo | Observação |
|---|---|---|
| `intencao` | `str \| None` | Chave de `TEMPLATES` (ver [`app/sql/templates.py`](../backend/app/sql/templates.py)), ou `None` se nada bateu. |
| `confianca` | `float` | 0.0–1.0. Abaixo de `0.70` o backend não tenta consultar — pede reformulação (ver `app/fallbacks.py`). |
| `entidades` | `dict` | Só o que o template correspondente precisa (`periodo_inicio`, `periodo_fim`, `limite`, ...). |
| `texto_original` | `str` | Pergunta como o usuário digitou, sem normalização. |

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
```

Regra inegociável: **valores numéricos ficam como número** (`48231.50`),
nunca como texto formatado (`"R$ 48.231,50"`). Formatação de moeda é
responsabilidade do frontend — é o que faz o exportador de Excel/PDF virar
poucas linhas de código em vez de precisar re-parsear texto.

`tipo_visualizacao` decide como o frontend renderiza (já implementado em
[`frontend/src/App.jsx`](../frontend/src/App.jsx)):

- `numero` → usa `linhas[0][1]` como valor único.
- `barra` → gráfico de barras (`GraficoBarra.jsx`), uma linha por categoria.
- `tabela` → tabela com `colunas` como cabeçalho.

## 3. Endpoints

### `GET /health`

**Implementado.** Usado pelo Dev C para o healthcheck do deploy.

```json
{ "status": "ok" }
```

### Autenticação (vale para `/chat` e `/import`)

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

### `POST /chat`

**Contrato definido, implementação pendente** (depende de banco no ar —
ver `dev-b-backend.md`, Bloco 2, item B10).

Requisição — modelo `Pergunta`:
```json
{ "pergunta": "quanto faturei em março", "empresa_id": "opcional" }
```
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

O frontend espera `err.mensagem` e `err.exemplos` no corpo de erro (ver
[`frontend/src/api.js`](../frontend/src/api.js)) — por isso o fallback
sempre populua esses dois campos dentro de `detail`.

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
  "colunas_ignoradas": ["observacao"]
}
```
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

## Regra de ouro: a pergunta nunca vira SQL diretamente

O NLU só escolhe **qual** template usar (uma chave fixa de
[`TEMPLATES`](../backend/app/sql/templates.py)) e preenche os valores dos
`%(...)s`, que o `psycopg` parametriza. O usuário influencia os *valores*,
nunca a *estrutura* da consulta. É o argumento central do capítulo 7.7 do
TCC contra soluções que deixam o modelo gerar SQL livremente.
