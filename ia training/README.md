# Intellix — Modelo de NLU

Código do modelo de IA do Intellix: recebe *"quanto faturei em março"* e devolve `intenção` + `entidades`.

---

## Começando (15 minutos)

```bash
# 1. Baixe/clone esta pasta e entre nela
cd intellix

# 2. Gere o dataset (não precisa instalar nada, só Python)
python gerar_dataset.py

# 3. Confira se está tudo certo
python validar_dataset.py dados/dataset.jsonl
```

Se apareceu `✅ Dataset válido`, vocês já têm 4.800 exemplos etiquetados. **Abram `dados/dataset.jsonl` e olhem.** É o combustível do modelo.

Depois:

4. Escrevam as frases de teste em `dados/frases_cruas.txt` (veja abaixo)
5. `python anotar.py`
6. `python validar_dataset.py dados/teste_manual.jsonl`
7. Subam `dados/dataset.jsonl` e `dados/teste_manual.jsonl` no **`Intellix_NLU_Colab.ipynb`** e rodem as células

---

## Os arquivos

| Arquivo | O que faz | Vocês editam? |
|---|---|---|
| **`moldes.py`** | Os moldes de frase e os valores. **É aqui que mora o projeto.** | ✏️ **SIM, sempre** |
| `gerar_dataset.py` | Transforma moldes em 4.800 exemplos etiquetados | raramente |
| `validar_dataset.py` | Detector de bug. Rode sempre antes de treinar | não |
| `anotar.py` | Pré-etiqueta as frases que vocês escreveram à mão | não |
| **`Intellix_NLU_Colab.ipynb`** | Treina, avalia e salva o modelo (roda no Colab) | ✏️ sim, os hiperparâmetros |
| `dados/frases_cruas.txt` | As frases de teste escritas por vocês | ✏️ **SIM** |

---

## Como o dataset é montado

Vocês escrevem um **molde**:

```python
"quanto faturei em {periodo}"
```

O gerador sorteia valores e etiqueta sozinho:

```
tokens:  quanto  faturei  em   mês        passado
tags:      O        O      O   B-PERIODO  I-PERIODO
```

Um molde vira ~45 frases diferentes. 200 moldes viram 4.800 exemplos. **O trabalho de vocês é escrever moldes, não frases.**

### Como escrever um bom molde

- ✅ Como o gestor fala de verdade: `"qnt vendi mês passado"`, `"faturamento marco"`, `"o pix tá vendendo?"`
- ✅ Frase com e sem o período são **dois moldes**: `"quanto faturei"` e `"quanto faturei em {periodo}"`
- ✅ Repetir tipo na mesma frase: use `{periodo}` e `{periodo2}`
- ❌ Não invente slot novo. Só os que estão em `VALORES`.

**Meta:** 15–20 moldes por intenção. Dividam: cada integrante pega 3 intenções.

---

## O conjunto de teste real (a parte que não dá pra pular)

Este é o coração científico do TCC.

Um dataset feito de molde tem um risco: o modelo aprende **os moldes**, não o português. Aí, na banca, alguém digita algo com uma vírgula diferente e ele erra feio. Isso está no documento de vocês (seção 4.5: *overfitting* e *distribution shift*).

A única defesa é um conjunto de teste que **nenhum molde gerou**.

### Como fazer

Criem `dados/frases_cruas.txt`, formato `intencao | frase`:

```
total_vendas_periodo | oi, quanto que eu vendi mês passado?
top_produtos         | qual foi o produto que mais saiu em abril
ticket_medio         | quanto em média cada cliente deixa na loja
desempenho_vendedor  | a fernanda tá vendendo bem esse mês?
produtos_sem_saida   | tem alguma coisa encalhada no estoque
```

**Meta: 120 frases (10 por intenção).** Regras:

1. **Não olhem o `moldes.py` enquanto escrevem.** Sério. Se olharem, vão copiar sem querer.
2. Cada integrante escreve 30. Peçam também pra alguém de fora — a mãe, o tio que tem loja, um amigo.
3. Escrevam **torto**: sem acento, com abreviação, sem "?", com "oi" na frente. É o que o usuário digita.
4. Rodem `python anotar.py`, ele pré-etiqueta. **Revisem** o que ele marcou com `"revisar": true`.

Depois, no notebook, vocês vão ver **dois números**:

```
Intenção: 0.97 (molde) vs 0.89 (real) → queda de 8.0 pontos
```

Essa queda **é** o resultado. Um TCC que reporta só o 0.97 está se enganando. Um que reporta os dois e discute a diferença está fazendo ciência.

---

## Correções em relação ao guia anterior

Duas coisas que só apareceram quando o código foi escrito de verdade:

**1. O padding das tags é `-100`, não `0`.** No guia eu escrevi `CrossEntropyLoss(ignore_index=0)`. Isso está **errado** aqui, porque `0` é a tag `"O"` — usar `ignore_index=0` faria o modelo ignorar todas as palavras que não são entidade, que são a maioria. O certo é preencher com `-100` e usar `ignore_index=-100`. Está corrigido no notebook.

**2. A representação da frase usa média mascarada, não o último estado da LSTM.** Com padding, o "último estado" da direção pra frente cai em cima do enchimento e vira lixo. A média das palavras reais (ignorando o padding) é mais simples e mais robusta.

---

## Achados de quem escreveu isto

Rodando o gerador pela primeira vez, o validador pegou três problemas reais:

1. **`B-PRODUTO` tinha zero exemplos.** As 12 intenções do documento não têm nenhuma que use produto como filtro, mas `produto` está na lista de 9 entidades (seção 6.4.2). **Isso é uma inconsistência no documento de vocês.** Resolvi adicionando moldes como `"quanto vendi de {produto} em {periodo}"` dentro de `total_vendas_periodo`. Vale discutir se não merece uma intenção própria.
2. **`I-NUMERO` tinha zero exemplos**, porque números são sempre um token. Adicionei valores como `"vinte e cinco"` pra tag existir.
3. **O dataset nascia desbalanceado (2,26x).** Moldes com dois buracos (`{periodo}` e `{periodo2}`) geram muito mais combinações que moldes sem buraco. `comparacao_periodos` ficava com 751 exemplos e `produtos_sem_saida` com 332 — o modelo aprenderia a chutar a intenção maior. O gerador agora corta todas em 400.

---

## Quando o resultado vier ruim

**Quase nunca é o modelo. É o dataset.**

| Sintoma | Causa provável | Conserto |
|---|---|---|
| Acurácia < 85% no teste real, mas alta no sintético | Falta variedade nos moldes | Mais moldes, mais informais |
| Duas intenções se confundem na matriz | Os moldes delas são parecidos demais | Moldes que marquem a diferença |
| F1 de uma entidade baixo | Poucos exemplos dela | Mais valores em `VALORES` |
| Muita palavra virando `<UNK>` no teste | Vocabulário pobre | Mais valores e moldes |
| Validação cai enquanto treino sobe | Overfitting | Já tem early stopping; aumente o dropout |

⚠️ **Confusões esperadas** (não se assustem):
- `total_vendas_periodo` × `quantidade_vendas` — "**quanto** vendi" vs "**quantas** vendas". Uma letra de diferença.
- `total_vendas_periodo` × `variacao_periodo` × `comparacao_periodos` — as três falam de período e faturamento.
- `ticket_medio` × `total_vendas_periodo` — "média das vendas" é ambíguo até pra gente.

Essa última é boa notícia, aliás: ambiguidade real justifica o *fallback por ambiguidade* da seção 7.6. Se o modelo fica em dúvida entre duas intenções, o sistema **pergunta** em vez de chutar. Isso é feature, não bug — e rende parágrafo bom no TCC.

---

## Integrando no FastAPI depois

```python
import torch

pacote = torch.load("intellix_nlu_v1.0.0.pt", map_location="cpu")
vocab = pacote["vocab"]
modelo = ModeloNLU(**pacote["config_do_modelo"])
modelo.load_state_dict(pacote["state_dict"])
modelo.eval()
```

🚨 **A função `tokenizar` do backend tem que ser IDÊNTICA à do `gerar_dataset.py`.** Se forem diferentes, o modelo vai bem no teste e mal em produção, e vocês vão passar dias procurando o bug. Coloquem ela num arquivo único, importado pelos dois.

---

## Ordem sugerida

| Semana | Tarefa |
|---|---|
| 1 | Rodar `gerar_dataset.py`. Abrir o `dataset.jsonl` e entender o formato. Repo no GitHub. |
| 2 | Cada um escreve moldes pra 3 intenções em `moldes.py` |
| 3 | Escrever as 120 frases de teste. Revisão cruzada (seção 6.4.4 / kappa de Cohen) |
| 4 | Rodar o notebook até o fim. Ver a primeira acurácia. |
| 5 | Melhorar moldes olhando a matriz de confusão. Testar α = 0.3 / 0.5 / 0.7 |
| 6 | Salvar o `.pt` e integrar num FastAPI mínimo |
