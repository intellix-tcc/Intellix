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

### `POST /chat`

**Contrato definido, implementação pendente** (depende de banco no ar —
ver `dev-b-backend.md`, Bloco 2, item B10).

Requisição — modelo `Pergunta`:
```json
{ "pergunta": "quanto faturei em março" }
```

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

## Regra de ouro: a pergunta nunca vira SQL diretamente

O NLU só escolhe **qual** template usar (uma chave fixa de
[`TEMPLATES`](../backend/app/sql/templates.py)) e preenche os valores dos
`%(...)s`, que o `psycopg` parametriza. O usuário influencia os *valores*,
nunca a *estrutura* da consulta. É o argumento central do capítulo 7.7 do
TCC contra soluções que deixam o modelo gerar SQL livremente.
