# Intellix · Dossiê técnico completo

**Material de estudo para a defesa do TCC, com ênfase no modelo de IA.**

Este documento reúne, num lugar só, tudo o que foi construído no Intellix: o modelo
de linguagem (como foi feito, treinado, medido e usado), o caminho completo de uma
pergunta até a resposta, as consultas SQL parametrizadas, o banco de dados, a API,
a segurança, a infraestrutura (Render, Vercel, Supabase), os testes e os diagramas.

**De onde vêm as informações.** Tudo aqui foi conferido diretamente no repositório do
projeto (código, migrações do banco, arquivos dos modelos e evidências em
`docs/evidencias/`), na versão do `main` de 19/11/2026 (commit `bd34783`), com o modelo
publicado **v1.2.0**. Os números de cada versão do modelo foram lidos dos próprios
arquivos `.pt`. Quando um dado vem de outra fonte (o roteiro da defesa ou o parecer da
banca), isso está dito no texto.

**Como usar no NotebookLM.** Carregue este PDF como fonte. Perguntas que funcionam bem:
"explique a cabeça de intenção como se eu fosse leiga", "por que a confiança mínima é
70%?", "o que acontece com a frase 'quanto vendi ontem?'", "faça um quiz sobre o
esquema BIO", "quais perguntas difíceis a banca pode fazer sobre o modelo?". O Apêndice
A traz perguntas e respostas prontas, e o Apêndice B, os números que vale decorar.

---

# Parte I · Visão geral

## 1. O problema e a proposta

Pequenas empresas registram vendas (no sistema de caixa ou numa planilha), mas quase
nunca analisam esses dados. Os dois caminhos disponíveis não servem bem a esse
público:

- **BI tradicional** (Power BI, Tableau): exige conhecimento técnico para configurar e
  tem licenças fora do orçamento de um pequeno negócio.
- **Soluções com LLM** (Julius AI, Obvious, Rows AI, Microsoft Copilot): cobram por
  pergunta, enviam os dados da empresa para um provedor de IA externo e respondem de
  forma pouco previsível, porque o SQL é gerado livremente pelo modelo.

O **Intellix** é um agente de análise de vendas em que o gestor pergunta em português
("quanto vendi em outubro?") e recebe número, gráfico ou tabela. A diferença central é
como a pergunta é entendida: em vez de um LLM, um **modelo próprio e pequeno** (uma rede
BiLSTM com cerca de 289 mil parâmetros, 1,1 MB) classifica a pergunta em uma de **12
intenções** e marca os detalhes (período, produto, vendedor...). A consulta ao banco sai
de um **modelo de SQL fixo e testado**, preenchido com parâmetros. O texto do usuário
nunca vira SQL.

Consequências dessa escolha: custo zero por pergunta, os dados não saem para terceiros,
e a resposta é previsível e auditável (a mesma pergunta gera sempre a mesma consulta). O
preço é a flexibilidade: só são respondidas perguntas dentro das 12 intenções (mais 2
refinamentos).

## 2. O caminho de uma pergunta, em resumo

Exemplo: "quais os 5 produtos mais vendidos em março?"

1. **Interface (React):** a pessoa digita e a interface envia `POST /chat` para a API,
   com a pergunta, o contexto da pergunta anterior e o token de login.
2. **API (FastAPI):** confere o token, o limite de requisições e o tamanho do texto.
3. **Normalização e tokenização:** minúsculas, espaços, abreviações ("qto" → "quanto").
   A frase vira uma lista de tokens: `quais | os | 5 | produtos | mais | vendidos | em | março | ?`.
4. **Modelo (BiLSTM):** devolve a intenção `top_produtos` com 99,99% de confiança e as
   etiquetas BIO: `5` = B-NUMERO, `março` = B-PERIODO.
5. **Travas:** confiança ≥ 70% e a frase precisa ter um termo do domínio de vendas. Se
   uma falhar, ele pede para reformular (HTTP 422).
6. **Resolução determinística:** "março" vira `2026-03-01` a `2026-03-31` (o ano vem da
   data de referência do conjunto de dados), o limite vira `5`, os nomes de produto ou
   vendedor são conferidos no cadastro da empresa, e a conversa anterior pode completar
   o que faltar.
7. **Consulta:** escolhe o template `top_produtos` e o executa com parâmetros nomeados.
8. **Banco (PostgreSQL):** só enxerga as vendas da empresa declarada (RLS) e devolve as
   linhas.
9. **Auditoria:** a consulta fica registrada em `log_consulta`.
10. **Resposta:** um JSON (`ResultSet`) com título, colunas, linhas, tipo de gráfico e
    confiança, que a interface desenha.

Frase-resumo usada na apresentação: **o modelo decide o quê, as regras decidem como, e o
banco responde.**

## 3. Glossário

| Termo | O que significa no Intellix |
|---|---|
| **NLU** (Natural Language Understanding) | Compreensão de linguagem natural: transformar uma frase em algo estruturado (intenção + entidades). É o papel do modelo. |
| **Domínio fechado** | O sistema só entende um assunto (vendas) e um conjunto finito de tipos de pergunta (12 intenções). |
| **Intenção** | O que a pessoa quer saber. Ex.: `ticket_medio`. É uma classificação da frase inteira. |
| **Entidade** | Um detalhe dentro da frase. Ex.: "março" (PERIODO), "camiseta branca" (PRODUTO). |
| **Slot / parâmetro** | O valor que o template SQL precisa (ex.: `periodo_inicio`). Entidades viram slots. |
| **Esquema BIO** | Forma de marcar entidades palavra a palavra: B = começa uma entidade, I = continua, O = fora. |
| **Token** | Cada pedaço da frase depois da tokenização (palavra, número ou pontuação). |
| **Vocabulário** | Lista de tokens que o modelo conhece, cada um com um número (id). Token desconhecido vira `<UNK>`. |
| **Embedding** | Vetor de números (aqui, 100) que representa cada token. É aprendido no treino. |
| **LSTM** | Rede neural recorrente que lê a sequência palavra por palavra e mantém uma memória, controlada por portões. |
| **BiLSTM** | Duas LSTMs: uma lê da esquerda para a direita, outra da direita para a esquerda. Cada palavra é representada pelo contexto dos dois lados. |
| **Cabeça (head)** | Camada final especializada numa tarefa. O Intellix tem duas: intenção e etiquetas. |
| **Logits** | Saídas cruas da camada final, antes de virarem probabilidades. |
| **Softmax** | Função que transforma logits em probabilidades que somam 1. A maior delas é a **confiança**. |
| **Dropout** | Desliga aleatoriamente parte dos neurônios no treino (aqui, 30%) para evitar decorar os dados. |
| **Perda (loss)** | Medida do erro que o treino tenta diminuir. Aqui, entropia cruzada. |
| **Época** | Uma passada completa pelo conjunto de treino. |
| **Early stopping** | Parar o treino quando a validação para de melhorar (aqui, 6 épocas sem melhora). |
| **Overfitting** | Quando o modelo decora o treino e vai mal em frases novas. |
| **Vazamento (leakage)** | Quando frases do teste também estão no treino, deixando o teste otimista. |
| **Acurácia** | Proporção de acertos. |
| **Precisão** | Das vezes em que o modelo disse "X", quantas eram X. |
| **Revocação (recall)** | Dos casos que eram X, quantos o modelo achou. |
| **F1** | Média harmônica entre precisão e revocação. |
| **F1 macro / micro** | Macro: média simples do F1 de cada classe (todas pesam igual). Micro: soma todos os acertos e erros antes de calcular. |
| **seqeval** | Biblioteca que calcula o F1 das entidades por entidade completa (não por token). |
| **Limiar de confiança** | Valor mínimo (0,70) para aceitar a classificação. Abaixo disso, o sistema pede para reformular. |
| **Template SQL** | Consulta SQL pronta, com lugares marcados para os valores (`%(periodo_inicio)s`). |
| **Consulta parametrizada** | Os valores vão ao banco separados do texto da consulta. Impede SQL injection. |
| **Esquema estrela** | Modelo de banco analítico: uma tabela de fatos (vendas) no centro, cercada de dimensões (data, produto, cliente, vendedor). |
| **RLS** (Row Level Security) | Segurança em nível de linha no PostgreSQL: o banco só devolve as linhas da empresa declarada. |
| **JWT** | Token de login assinado, emitido pelo Supabase Auth e conferido pela API a cada pedido. |
| **ETL** | Extrair, transformar e carregar: o processo de importar a planilha para o banco. |

---

# Parte II · O modelo de IA (a parte principal)

## 4. Que tipo de modelo é

O modelo do Intellix é um **classificador**, e não um **gerador** de texto. Essa é a
diferença mais importante para explicar.

| | LLM de uso geral (ex.: ChatGPT) | Modelo do Intellix |
|---|---|---|
| O que faz | Gera texto novo, palavra por palavra | Escolhe uma entre 12 intenções e etiqueta as palavras |
| Tamanho | Bilhões de parâmetros | 288.987 parâmetros (1,17 MB) |
| Treino | Terabytes de texto da internet | 4.800 frases de vendas geradas a partir de moldes da equipe |
| Pode inventar resposta? | Sim (alucinação) | Não: no máximo erra a classe, e abaixo de 70% recusa |
| Onde roda | Servidor do provedor, custo por pergunta | Na memória do nosso próprio servidor, custo zero |
| Saída | Texto livre (ou SQL livre, no Text-to-SQL) | Um rótulo + etiquetas. O SQL vem de um template fixo |

É um modelo **multitarefa**: a mesma rede faz duas tarefas ao mesmo tempo, a
classificação da intenção (uma resposta para a frase inteira) e a etiquetagem das
entidades (uma resposta para cada palavra). Essa linha, de tratar intenção e entidades
juntas, segue o trabalho de Goo et al. (2018), citado nas referências do TCC. As duas
tarefas se ajudam: saber a intenção ajuda a achar as entidades, e vice-versa. Além
disso, um modelo só é menor e roda uma única inferência por frase.

## 5. As 12 intenções

As intenções foram definidas a partir das perguntas mais comuns de um pequeno
comerciante. Cada uma corresponde a um template SQL com o mesmo nome.

| Intenção | O que responde | Exemplo de pergunta |
|---|---|---|
| `total_vendas_periodo` | Faturamento no período | "quanto faturei em março?" |
| `top_produtos` | Produtos que mais faturaram (ranking) | "quais os 5 produtos mais vendidos?" |
| `ticket_medio` | Faturamento ÷ número de vendas | "qual o meu ticket médio?" |
| `quantidade_vendas` | Número de vendas (pedidos) | "quantas vendas fiz em abril?" |
| `top_clientes` | Clientes que mais compraram | "quem são meus melhores clientes?" |
| `desempenho_vendedor` | Faturamento e vendas por vendedor | "como foi o desempenho da Fernanda?" |
| `produtos_sem_saida` | Produtos sem nenhuma venda no período | "tem produto encalhado?" |
| `comparacao_periodos` | Faturamento de dois períodos lado a lado | "vendi mais em março ou abril?" |
| `variacao_periodo` | Variação percentual entre dois períodos | "quanto cresci em relação ao mês passado?" |
| `vendas_por_canal` | Faturamento por canal (loja, site...) | "vendi mais pelo site ou na loja?" |
| `vendas_por_categoria` | Faturamento por categoria | "quanto vendi em cada categoria?" |
| `vendas_por_pagamento` | Faturamento por forma de pagamento | "quanto vendi no pix?" |

Na apresentação, elas são agrupadas em quatro perguntas: **"Quanto?"** (faturamento,
ticket, quantidade), **"Quem? O quê?"** (produtos, clientes, vendedores, sem saída),
**"Por onde? Como?"** (canal, categoria, pagamento) e **"Comparar"** (comparação e
variação).

**Os 2 refinamentos (14 tipos de análise no total).** A tela "O que posso perguntar"
fala em 14 tipos de análise porque há dois refinamentos feitos por regra, sem classe
nova no modelo (`backend/app/refino.py`):

- **`unidades_vendidas`**: "quantas camisetas vendemos?" → o modelo diz
  `quantidade_vendas` (que conta pedidos), mas a frase pede peças. O refino troca para a
  soma de unidades.
- **`melhor_mes`**: "qual mês vendeu mais?" → o modelo diz `total_vendas_periodo`, e o
  refino devolve o mês campeão, com a série mensal em destaque.

## 6. As 9 entidades e o esquema BIO

### 6.1 Os tipos de entidade

São 9 tipos: **PERIODO, DATA, PRODUTO, CATEGORIA, CLIENTE, VENDEDOR, CANAL, PAGAMENTO e
NUMERO**.

### 6.2 Como o BIO funciona

Cada token recebe uma etiqueta:

- **B-TIPO** (*begin*): aqui começa uma entidade desse tipo;
- **I-TIPO** (*inside*): continuação da mesma entidade;
- **O** (*outside*): a palavra não faz parte de nenhuma entidade.

Com 9 tipos, são **19 etiquetas**: `O` + `B-` e `I-` para cada tipo (1 + 9 × 2 = 19).
A ordem fixa usada no treino é: O, B-PERIODO, I-PERIODO, B-DATA, I-DATA, B-PRODUTO,
I-PRODUTO, B-CATEGORIA, I-CATEGORIA, B-CLIENTE, I-CLIENTE, B-VENDEDOR, I-VENDEDOR,
B-CANAL, I-CANAL, B-PAGAMENTO, I-PAGAMENTO, B-NUMERO, I-NUMERO.

**Exemplo** (resultado real do modelo publicado, v1.2.0):

| Token | quanto | vendi | de | camiseta | branca | em | abril | ? |
|---|---|---|---|---|---|---|---|---|
| Etiqueta | O | O | O | **B-PRODUTO** | **I-PRODUTO** | O | **B-PERIODO** | O |

Resultado agrupado: `{PRODUTO: "camiseta branca", PERIODO: "abril"}`, intenção
`total_vendas_periodo`, confiança **99,33%** (com o "?"; sem o ponto de interrogação, a
confiança é 98,3%).

**Por que precisa do B e do I?** Para separar entidades vizinhas do mesmo tipo e saber
onde cada uma termina. "Camiseta branca" é **um** produto (B, I), e não dois produtos (B, B).

### 6.3 Como as etiquetas viram entidades

A função `_agrupar_entidades` percorre os tokens: um `B-X` abre uma entidade nova, um
`I-X` do mesmo tipo a continua, e qualquer outra etiqueta fecha a entidade aberta. Se o
mesmo tipo aparecer duas vezes (ex.: dois períodos numa comparação), o valor vira uma
lista: `{PERIODO: ["março", "abril"]}`.

### 6.4 Para que as entidades são usadas de fato (ponto importante)

No sistema publicado, as entidades do modelo **não** são a única fonte dos parâmetros:

- **Período e limite** são resolvidos por **regras determinísticas** sobre o texto
  (expressões regulares), e não pelas etiquetas. Motivo: converter "março" em
  `2026-03-01..2026-03-31` é determinístico, e a cabeça BIO é mais ruidosa (F1 de cerca
  de 0,83 a 0,87).
- **Vendedor:** a entidade VENDEDOR do modelo é a **primeira escolha**. Se o modelo não
  marcar, uma heurística procura um nome próprio no texto original.
- **Produto, categoria, cliente, canal e pagamento:** o trecho marcado pelo modelo é
  tentado **primeiro** contra o catálogo da empresa. Se não casar, a frase inteira é
  comparada com o catálogo.

Isso explica um resultado da ablação (seção 15.5): tirar a cabeça de entidades **não
mudou** o acerto final no conjunto externo, porque as regras e o catálogo compensam. A
cabeça foi mantida por finalidade de pesquisa e robustez, não por ganho operacional
demonstrado.

## 7. Pré-processamento: normalização e tokenização

O texto passa por duas funções antes de entrar no modelo (`modelo_nlu.py`):

**`normalizar(texto)`:**

1. passa para minúsculas e tira espaços das pontas;
2. troca espaços repetidos por um só;
3. aplica normalização Unicode **NFC** (garante que "ç" digitado de dois jeitos vire o
   mesmo caractere);
4. troca abreviações comuns palavra por palavra: `qnt`/`qto` → quanto, `qtd` →
   quantidade, `qtas` → quantas, `qts` → quantos, `vlr` → valor, `tkt` → ticket, `fat` →
   faturamento, `pq` → porque, `vc` → você, `q` → que, `pra` → para, `pro` → para o.

**Os acentos não são removidos**, de propósito: em português, acento muda o sentido.

**`tokenizar(texto)`:** aplica a expressão regular `\w+|[^\w\s]`, que separa palavras e
números de cada sinal de pontuação. "quanto faturei em março?" vira
`['quanto', 'faturei', 'em', 'março', '?']`. Sem separar o "?", "março?" seria um token
diferente de "março".

**Regra crítica do projeto:** a mesma tokenização tem que ser usada na geração do
dataset, no treino e no servidor. Se divergirem, o modelo vai bem nos testes e mal em
produção, um erro silencioso. Por isso o `treinar.py` importa `tokenizar` diretamente de
`backend/app/nlu/modelo_nlu.py`, e o gerador tem uma cópia idêntica.

## 8. O conjunto de dados

### 8.1 Moldes e valores

Em vez de escrever milhares de frases à mão, a equipe escreveu **moldes**: frases com
espaços marcados por tipo de entidade.

```
"quanto faturei em {periodo}"
"vendi mais pelo {canal} ou pelo {canal2}"
"quais os {numero} produtos mais vendidos"
```

Os valores possíveis de cada espaço ficam no dicionário `VALORES`
(`ia training/moldes.py`). Na versão atual são 43 valores de período (meses, "mês
passado", "esta semana", "ontem", "2025", "o último trimestre"...), 18 de data, 40 de
produto, 18 de categoria, 17 de cliente, 30 de vendedor, 17 de canal, 13 de pagamento e
19 de número (inclusive por extenso, como "vinte e cinco").

Regras dos moldes: usar só espaços que existem em `VALORES`; para repetir o mesmo tipo,
`{periodo}` e `{periodo2}`; frase com e sem período são dois moldes diferentes; escrever
como o gestor fala (gíria, abreviação, sem acento, sem "?").

### 8.2 O gerador (`gerar_dataset.py`)

1. Para cada molde, gera **60 variações**, sorteando valores. Na mesma frase, não repete
   o mesmo valor de um tipo (evita "vendi mais em março ou março").
2. **Etiqueta sozinho:** o texto fixo do molde recebe `O`, o primeiro token de cada valor
   sorteado recebe `B-TIPO` e os seguintes, `I-TIPO`. É por isso que não foi preciso
   anotar à mão.
3. **Remove repetidas** (moldes sem espaço geram sempre a mesma frase).
4. **Filtro de vazamento:** remove qualquer frase igual a uma das 100 perguntas de
   validação (`docs/perguntas_validacao.md`), para que a validação meça generalização.
5. **Balanceamento:** corta todas as intenções em **400 exemplos**. Moldes com dois
   espaços geram muito mais combinações. Sem o corte, uma intenção ficava com 751
   exemplos e outra com 332, e o modelo aprenderia a "chutar" a maior.
6. Semente fixa (42): rodar de novo gera exatamente o mesmo conjunto.

Resultado: **12 × 400 = 4.800 exemplos**, salvos em `dados/dataset.jsonl`, cada um com
texto, intenção, tokens, etiquetas e origem.

### 8.3 Evolução dos moldes

| Versão do modelo | Moldes | O que mudou |
|---|---:|---|
| v1.0.0 (08/09/2026) | 387 | Moldes v2, "turbinados com linguagem informal" ("tá vendendo", "encalhado"), com reforço nas intenções que tinham zerado no primeiro teste real: desempenho de vendedor, produtos sem saída, canal e pagamento |
| v1.1.0 (05/11/2026) | 423 | Dataset aumentado: comparações, canal, pagamento, categoria |
| v1.2.0 (05/11/2026) | 561 | Moldes v3, escritos a partir das frases que a v1.1.0 recusava na interface: período relativo com preposição ("no mês passado"), produto em perguntas de vendedor/cliente/canal, "quantas peças de {produto}" e "qual mês vendeu mais" |

Total de moldes da versão atual por intenção: total_vendas_periodo 88, desempenho_vendedor
67, quantidade_vendas 65, vendas_por_pagamento 46, top_clientes 44, vendas_por_canal 44,
ticket_medio 39, produtos_sem_saida 38, comparacao_periodos 35, vendas_por_categoria 33,
top_produtos 32, variacao_periodo 30.

### 8.4 Estatísticas do conjunto da v1.0.0

O `dataset.jsonl` nunca foi versionado, só o gerador. Como a semente é fixa, o conjunto
foi recriado (`reproduzir_dataset_v1.0.0.py`) e a prova de identidade é que o
vocabulário sai idêntico ao gravado no modelo (404 tokens).

- 4.800 exemplos, 12 intenções, 19 etiquetas usadas;
- frases de 2 a 14 tokens, média de **7,3 tokens**;
- etiquetas de entidade (B / I): PERIODO 4.654 / 4.568, CANAL 457 / 124, PAGAMENTO 440 /
  245, CATEGORIA 296 / 48, VENDEDOR 292 / 118, NUMERO 235 / 64, CLIENTE 188 / 120,
  PRODUTO 187 / 145, DATA 54 / 194;
- PERIODO domina: aparece **10,2 vezes** mais que a segunda entidade. Isso ajuda a
  explicar por que período é a entidade mais confiável e vendedor, uma das mais fracas.

### 8.5 O teste manual ("teste real")

Um conjunto gerado por moldes tem um risco: o modelo aprende os moldes e não o
português. A defesa foi um conjunto que **nenhum molde gerou**:

- **120 frases, 10 por intenção** (`ia training/teste_manual.jsonl`);
- escritas à mão **sem olhar os moldes**, de propósito "tortas": sem acento, com
  abreviação, sem "?", com "oi" na frente;
- pré-etiquetadas pelo `anotar.py` e revisadas à mão;
- **16,5%** das palavras distintas desse teste (39 de 236) não estavam no vocabulário da
  v1.0.0 (ex.: "bombando", "encalhada", "grana", "fregueses", "prateleira"). Nenhuma
  delas era valor de entidade.

O README do treino resume a filosofia: o número que vale é o do teste real, e a queda
em relação ao teste sintético **é** o resultado a discutir.

## 9. A arquitetura da rede

### 9.1 Camada por camada

```
tokens (ids) ──► Embedding (V × 100) ──► Dropout 0,3
             ──► BiLSTM (100 → 128 para cada lado) ──► saída de 256 por token
                     │                                    │
                     ▼                                    ▼
      média mascarada dos tokens (256)          por token: Linear 256 → 19
      ──► Dropout 0,3 ──► Linear 256 → 12       (cabeça de etiquetas BIO)
      (cabeça de intenção)
```

1. **Embedding** (`nn.Embedding(V, 100, padding_idx=0)`): cada token vira um vetor de
   100 números. O índice 0 é o preenchimento (`<PAD>`) e fica fixo em zero.
2. **Dropout de 30%** sobre os embeddings, só no treino.
3. **BiLSTM** (`nn.LSTM(100, 128, bidirectional=True)`): uma LSTM lê da esquerda para a
   direita e outra da direita para a esquerda, cada uma com estado oculto de 128. A saída
   de cada token é a concatenação das duas: **256 números**.
4. **Cabeça de intenção:** precisa de um vetor para a frase inteira. Faz a **média das
   saídas da BiLSTM, ignorando os tokens de preenchimento** (média mascarada), aplica
   dropout e uma camada linear de 256 → 12. Saem 12 logits, um por intenção.
5. **Cabeça de etiquetas:** uma camada linear 256 → 19 aplicada a **cada token**. Saem
   19 logits por palavra.

**Por que média mascarada e não o último estado da LSTM?** Num lote, as frases são
completadas com `<PAD>` até o tamanho da maior. O "último estado" da direção para a
frente cairia em cima do preenchimento e viraria lixo. A média só das palavras reais é
mais simples e mais robusta. Foi uma correção registrada no README do treino.

### 9.2 O que é uma LSTM (para explicar com segurança)

Uma rede recorrente lê a frase um token por vez e carrega um estado de uma palavra para
a próxima. A LSTM (*Long Short-Term Memory*) resolve o problema de "esquecer" o começo
da frase com uma **memória de célula** controlada por três **portões**:

- **portão de esquecimento:** decide o que apagar da memória;
- **portão de entrada:** decide o que da palavra atual entra na memória;
- **portão de saída:** decide o que da memória vira a saída daquele passo.

Por isso cada matriz de pesos da LSTM tem 4 × 128 = **512 linhas**: os três portões mais
a proposta de conteúdo novo, cada um com 128 unidades.

**Por que bidirecional?** Numa frase curta, o sentido de uma palavra depende das
vizinhas dos dois lados. A direção de trás para a frente permite que, ao representar
"camiseta", a rede já saiba que vem "branca" depois. Cada palavra é entendida pelo que
vem antes **e** pelo que vem depois.

### 9.3 Contagem de parâmetros (v1.2.0, conferida no arquivo)

| Camada | Formato | Parâmetros |
|---|---|---:|
| Embedding | 455 × 100 | 45.500 |
| LSTM para a frente | pesos 512 × 100 e 512 × 128, mais 2 vieses de 512 | 117.760 |
| LSTM para trás | idem | 117.760 |
| Cabeça de intenção | 12 × 256 + 12 | 3.084 |
| Cabeça de etiquetas | 19 × 256 + 19 | 4.883 |
| **Total** | | **288.987** |

Arquivo: 1.169.745 bytes (1,17 MB). Só o embedding cresce entre versões, porque depende
do tamanho do vocabulário. O resto da rede é igual em todas as versões.

### 9.4 Por que BiLSTM e não um Transformer (BERT)

- **Hospedagem gratuita:** o Render gratuito tem de 256 a 512 MB de RAM. Um BERT tem
  centenas de milhões de parâmetros e não caberia. O Intellix inteiro usa cerca de 222 MB
  em execução (dado do roteiro da defesa).
- **Frases curtas** (média de 7,3 tokens): a vantagem dos Transformers em textos longos
  pesa pouco.
- **As metas foram batidas** com a BiLSTM (93,3% de acurácia na v1.0.0, contra meta de
  85%), respondendo em 1,72 ms por frase em CPU.
- **Não houve teste com Transformer.** O notebook de treino deixa isso como "próximo
  passo": trocar o miolo (Embedding + LSTM) por um encoder pequeno e comparar acurácia,
  F1, tamanho e tempo. É trabalho futuro.

## 10. O treino

### 10.1 Vocabulário

Montado só com o conjunto de treino: entram as palavras que aparecem **pelo menos 2
vezes**. Palavra vista uma vez só vira `<UNK>` (id 1). `<PAD>` é o id 0. Tamanho: 404
(v1.0.0), 411 (retreino de 21/10), 412 (v1.1.0) e **455 (v1.2.0)**.

### 10.2 Divisão dos dados

- **v1.0.0 (notebook no Google Colab):** divisão **70/15/15** estratificada por intenção,
  semente 42: **3.360 de treino, 720 de validação e 720 de teste sintético**, mais as 120
  frases do teste real.
- **v1.1.0 e v1.2.0 (`treinar.py`, local, em CPU):** divisão **70/30** estratificada,
  semente 42: **3.360 de treino e 1.440 de validação**, sem teste sintético separado. O
  teste que conta continua sendo o manual.

"Estratificada" quer dizer que cada parte mantém a mesma proporção de cada intenção.

### 10.3 Função de perda e otimização

- **Perda da intenção:** entropia cruzada entre os 12 logits e a intenção correta.
- **Perda das etiquetas:** entropia cruzada token a token, com `ignore_index = -100`: as
  posições de preenchimento recebem -100 e não contam. (O guia original usava 0, o que
  estava errado, porque 0 é a etiqueta "O" e o modelo ignoraria quase todas as palavras.)
- **Perda total:** `α × perda_intenção + (1 − α) × perda_etiquetas`, com **α = 0,5**
  (pesos iguais).
- **Otimizador Adam**, taxa de aprendizado 0,001, lotes de 32 frases.
- **Corte de gradiente** (*gradient clipping*) em norma 5, que evita saltos instáveis,
  comuns em redes recorrentes.
- Até **40 épocas**, com **early stopping**: se a acurácia de intenção na validação não
  melhorar por **6 épocas**, o treino para e os pesos da melhor época são restaurados.
- Épocas efetivamente rodadas: 18 (v1.0.0), 20 (retreino), 27 (v1.1.0) e 25 (v1.2.0).

### 10.4 O arquivo do modelo (`.pt`)

O arquivo não guarda só os pesos. É um "pacote" com: `state_dict` (pesos), `vocab`,
`intent2id`, `tag2id`, `config` (tamanhos da rede), `treino` (hiperparâmetros, épocas,
tamanhos dos conjuntos), `metricas`, `versao` e `data`. Por isso o servidor consegue
recriar a rede exatamente como foi treinada.

## 11. A inferência (o modelo em produção)

1. O modelo é carregado **uma vez**, quando a API sobe, e fica em memória. Não é
   recarregado a cada pergunta.
2. `prever(pergunta)`: tokeniza, troca cada token pelo id (desconhecido vira `<UNK>`) e
   roda a rede sem cálculo de gradiente.
3. Aplica **softmax** nos 12 logits: a maior probabilidade é a **confiança**, e a classe
   dela é a intenção.
4. Para as etiquetas, pega a de maior valor em cada token (*argmax*) e agrupa em
   entidades.
5. Se a confiança for menor que **0,70**, marca `fallback = True` (pedir reformulação).

Desempenho: **1,72 ms por frase em CPU** (v1.0.0, gravado no arquivo do modelo).

## 12. As versões do modelo

| | v1.0.0 | v1.0.0 (retreino) | v1.1.0 | **v1.2.0 (publicada)** |
|---|---|---|---|---|
| Data do treino | 08/09/2026 | 21/10/2026 | 05/11/2026 | 05/11/2026 |
| Onde | Colab | Colab | Local (CPU) | Local (CPU) |
| Moldes | 387 | — | 423 | 561 |
| Vocabulário | 404 | 411 | 412 | 455 |
| Parâmetros | 283.887 | 284.587 | 284.687 | 288.987 |
| Tamanho do arquivo | 1,09 MB | 1,10 MB | 1,10 MB | 1,17 MB |
| Treino / validação | 3.360 / 720 | 3.360 / 720 | 3.360 / 1.440 | 3.360 / 1.440 |
| Épocas | 18 | 20 | 27 | 25 |
| Acurácia de validação | 1,000 | 1,000 | 0,998 | 0,999 |
| Teste real: acurácia de intenção | **93,3%** | 90,0% | 88,3% | **88,3%** |
| Teste real: F1 de entidades | 0,838 (gravado) / 0,803 (reavaliado) | 0,868 | 0,873 | **0,831** |

A arquitetura e os hiperparâmetros são **os mesmos** em todas as versões. Só mudaram os
moldes (e, portanto, os dados de treino). Os dois arquivos com rótulo "1.0.0" (o original
e o retreino de 21/10) dificultam comparações sem os hashes, um ponto levantado pelo
parecer (F07) e resolvido com o manifesto de reprodução.

O servidor carrega a v1.2.0 por padrão. A variável de ambiente `NLU_MODELO` permite
apontar para outro arquivo (por exemplo, voltar à v1.1.0) sem novo deploy de código.

## 13. As métricas do modelo isolado

### 13.1 Metas do TCC

- Acurácia de intenção **≥ 85%**;
- F1 de entidades **≥ 0,80**;
- tamanho do modelo **≤ 256 MB**;
- resposta ponta a ponta **< 3 s**.

### 13.2 Teste real (120 frases), as três versões

Reavaliação de 06/11/2026 (`docs/evidencias/avaliacao_teste_real_2026-11-06_1309.md`),
intenção com scikit-learn e entidades com seqeval:

| Modelo | Acurácia | F1 de intenção (macro) | F1 de entidades (micro) | Precisão / revocação de entidades |
|---|---:|---:|---:|---:|
| v1.0.0 | **93,3%** | 0,932 | 0,803 | 0,742 / 0,876 |
| v1.1.0 | 88,3% | 0,881 | 0,873 | 0,835 / 0,914 |
| v1.2.0 | 88,3% | 0,887 | 0,831 | 0,762 / 0,914 |

O F1 de entidades da v1.0.0 aparece como **0,838** no arquivo do modelo (medido no dia do
treino) e como **0,803** na reavaliação, porque as anotações de entidades do arquivo de
teste foram revisadas depois. Comparações justas exigem a mesma régua: na régua revisada,
a v1.2.0 tem 0,831.

**Sete** das 120 frases do teste acabaram entrando no treino da v1.2.0. Sem elas, a
acurácia da v1.2.0 é **88,5%**, então a sobreposição não inflou o resultado.

### 13.3 Por intenção (F1 no teste real)

| Intenção | v1.0.0 | v1.2.0 |
|---|---:|---:|
| comparacao_periodos | 0,952 | 0,842 |
| desempenho_vendedor | 0,947 | 0,952 |
| produtos_sem_saida | 0,952 | 0,952 |
| quantidade_vendas | 1,000 | 0,952 |
| ticket_medio | 0,900 | 0,947 |
| top_clientes | 1,000 | 0,947 |
| top_produtos | 0,900 | 0,947 |
| total_vendas_periodo | 0,842 | **0,609** |
| variacao_periodo | 0,952 | 0,800 |
| vendas_por_canal | 0,900 | 0,900 |
| vendas_por_categoria | 0,889 | 0,842 |
| vendas_por_pagamento | 0,952 | 0,947 |

Na v1.2.0, o ponto fraco é `total_vendas_periodo` (precisão 0,538): várias frases de
outras intenções foram classificadas como faturamento. Uma hipótese provável (não
medida isoladamente) é o efeito dos moldes v3, que puseram frases como "qual mês vendeu
mais" dentro de `total_vendas_periodo`, ampliando o que a rede associa a essa classe.

### 13.4 Por entidade (v1.2.0, seqeval)

| Entidade | Precisão | Revocação | F1 | Ocorrências no teste |
|---|---:|---:|---:|---:|
| CANAL | 0,867 | 0,929 | 0,897 | 14 |
| CATEGORIA | 0,833 | 1,000 | 0,909 | 5 |
| CLIENTE | 0,667 | 1,000 | 0,800 | 2 |
| DATA | 1,000 | 1,000 | 1,000 | 1 |
| NUMERO | 0,750 | 1,000 | 0,857 | 3 |
| PAGAMENTO | 1,000 | 0,833 | 0,909 | 12 |
| PERIODO | 0,766 | 0,967 | 0,855 | 61 |
| VENDEDOR | 0,429 | 0,429 | **0,429** | 7 |

VENDEDOR é a entidade mais fraca (nomes de pessoa variam muito e aparecem pouco no
treino). Por isso existe a heurística de nome próprio no adaptador (seção 14.5).

### 13.5 Erros típicos de intenção (v1.0.0, as 8 frases erradas)

| Frase | Correta | Prevista |
|---|---|---|
| oi, quanto que eu vendi mês passado? | total_vendas_periodo | comparacao_periodos |
| qual foi a grana que entrou ontem | total_vendas_periodo | variacao_periodo |
| quais produtos bombaram mês passado | top_produtos | produtos_sem_saida |
| quanto o pessoal gasta por compra em média | ticket_medio | vendas_por_canal |
| quanto a leticia faturou essa semana | desempenho_vendedor | total_vendas_periodo |
| de onde vem mais venda | vendas_por_canal | top_produtos |
| qual seção puxa mais venda | vendas_por_categoria | ticket_medio |
| me mostra o total por categoria | vendas_por_categoria | vendas_por_pagamento |

Padrão: gírias e palavras fora do vocabulário ("grana", "bombaram", "seção") e intenções
de vocabulário parecido.

### 13.6 Teste sintético × teste real

No teste sintético (720 frases geradas pelos mesmos moldes), a v1.0.0 fez 99,6% de
acurácia e 0,996 de F1. É otimista: frases do mesmo molde caem no treino e no teste, e o
modelo reconhece o molde. Por isso esse **não** é o número reportado como resultado. O
reportado é o do teste real.

## 14. Do modelo à consulta: o que é do modelo e o que é regra

Arquivo central: `backend/app/nlu/adaptador_modelo.py`. Ele implementa a "porta" do NLU
(`parse(texto) → Interpretacao`) usando o modelo treinado, e complementa a rede com
regras determinísticas.

### 14.1 A divisão de trabalho

- **O modelo decide a intenção.**
- **As regras resolvem os parâmetros** que os templates exigem (datas ISO, limite, nome
  do vendedor), porque isso é determinístico e testável.
- **Falha segura:** se não der para resolver um parâmetro obrigatório, o adaptador
  devolve entidades incompletas de propósito. O executor responde 422
  `parametro_faltando` e pede o que falta, em vez de rodar um SQL errado.

### 14.2 Filtro de domínio

Um classificador fechado em 12 classes **sempre** escolhe uma delas, às vezes com
confiança alta. "Qual a capital da França?" saiu como `variacao_periodo` com confiança
0,92 e "Me conta uma piada" como `produtos_sem_saida` com 0,85. Por isso, mesmo confiante,
a classificação só é aceita se a frase tiver pelo menos um **termo do domínio de vendas**
(expressão regular com raízes como `vend`, `fatur`, `produt`, `client`, `ticket`,
`canal`, `pagament`, `pix`, `estoque`, `loja`, `cresc`...). Sem termo de domínio, a
intenção vira nula e a resposta é 422 `baixa_confianca`.

Custo medido: o filtro barrou 7 de 8 paráfrases válidas que não usavam palavras típicas
(ex.: "o que saiu mais mês passado", "quanto entrou no caixa em março"). É o preço de
nunca responder fora do assunto.

### 14.3 Sinônimos de domínio (PR #54, mergeado em 19/11/2026)

Três intenções de "quebra por atributo" concentravam a confusão do modelo em frases
novas: forma de pagamento, categoria e canal ("linha de produtos" saía como
`top_produtos`, "meio de pagamento" como `quantidade_vendas`). Uma camada léxica de alta
precisão corrige isso: se a frase traz um termo **inequívoco** (ex.: "forma/meio/método
de pagamento", "como os clientes pagaram", "por categoria", "linha de produtos",
"departamento", "por canal", "canal de venda", "por onde eu vendi"), a intenção passa a
ser essa, qualquer que seja o rótulo do modelo. Se o modelo ficou abaixo do limiar mas há
um desses termos, a regra "resgata" a pergunta e a confiança reportada passa a ser 0,80
(a certeza da regra). Efeito: 100 perguntas de 88 para 90; inéditas adversariais de 13
para 18 de 30. Consequência a admitir na banca: nessas três intenções, a decisão final
não é só do modelo.

### 14.4 Resolução de períodos

A data de referência ("hoje") de cada conjunto de dados é **a data atual (horário de
Brasília), limitada à data da última venda** (`periodo_dataset.py`). Assim, uma planilha
com vendas até junho de 2025 responde "mês passado" com maio de 2025, em vez de "sem
resultado".

**Um período** (ordem de tentativa):

1. **Relativos:** "1º/2º/3º/4º trimestre", "último trimestre" (o último completo),
   "1º/2º semestre", "mês passado"/"último mês", "este mês"/"mês atual", "ano passado".
2. **Mês por extenso** (aceita "marco" sem cedilha): de 1º ao último dia do mês. O ano é o
   citado na frase, ou o da data de referência.
3. **Só um ano** ("em 2025"): o ano inteiro.
4. **Nada reconhecido:** o **ano inteiro da referência**. É por isso que "quanto vendi
   ontem?" e "faturamento da semana" respondem o ano todo: dia e semana não são períodos
   que as regras resolvem (embora o modelo etiquete "ontem" como PERIODO). O painel "Como
   cheguei nessa resposta" mostra o período usado. É uma limitação conhecida.

**Dois períodos** (`comparacao_periodos` e `variacao_periodo`), sete regras em ordem: dois
anos distintos; dois meses por extenso; dois trimestres; "mês passado/anterior"; "ano
passado/este ano"; trimestres genéricos; um único mês (compara com o mês anterior). Os
dois períodos são ordenados por data: o mais recente vira "atual" e o mais antigo,
"anterior". Se nada se aplicar, falha segura (422).

### 14.5 Limite e vendedor

- **Limite** (`top_produtos`, `top_clientes`): o primeiro número de 1 ou 2 dígitos da
  frase. Se não houver, **5**.
- **Vendedor** (`desempenho_vendedor`): (1) a entidade VENDEDOR do modelo, descartada se
  for só uma palavra como "vendedor"; (2) senão, uma heurística sobre o texto original,
  que procura um nome com inicial maiúscula depois de "vendedor(a)", "da", "do", "de", ou
  antes de "vendeu/faturou"; (3) sem nome, mas com sinal de ranking ("quem", "melhor",
  "mais", "ranking", "time", "vendedores"), lista todos (`ILIKE '%'`); (4) senão, pede o
  nome (422). A busca usa o nome sem acento e em minúsculas, igual à coluna `nome_norm` do
  banco, para "José" casar com "jose".

### 14.6 Filtros por catálogo (`filtros.py`)

O trecho que o modelo marcou ("botas de couro") vira um valor que **existe** no conjunto
de dados consultado ("Bota couro"), comparando palavras com o catálogo da empresa
(produtos, categorias, vendedores, clientes, canais, formas de pagamento). A primeira
palavra do nome (o "núcleo") tem de estar na frase. Vence quem tem mais palavras em
comum, e empate não filtra (melhor responder sem recorte do que com o recorte errado).
Cliente só casa pelo nome completo. O valor resolvido é sempre um texto copiado do banco
e vai ao SQL como parâmetro. O catálogo fica em cache por um curto período.

### 14.7 Contexto da conversa (`contexto.py`)

O `/chat` não guarda estado: a interface reenvia a intenção e os parâmetros da resposta
anterior. Três situações:

1. **Frase elíptica**, que não se classifica sozinha ("e em abril?", "e de calçados?",
   "e o Diego?"): herda a intenção e os parâmetros anteriores, trocando só o que a frase
   trouxe de novo. Se não trouxe nada reconhecível, não herda (pede para reformular).
2. **Continuação** ("e o ticket médio?"): vale a intenção nova, herdando período e
   filtros.
3. **Pergunta nova:** vale tudo dela. Só o período, se ela não citar, continua o da
   conversa.

### 14.8 Refino (`refino.py`)

- "qual foi o mês que mais vendeu?" → `melhor_mes`;
- "quantas botas vendemos?" → `unidades_vendidas` (peças, não pedidos);
- "quanto vendi no pix?" com o pix filtrado → faturamento total filtrado (uma pizza com
  uma fatia só, 100%, não responderia nada);
- vendedor achado no catálogo → usa o nome exato.

### 14.9 As respostas possíveis

| Situação | HTTP | Tipo | Mensagem na tela |
|---|---|---|---|
| Deu certo | 200 | — | número, gráfico ou tabela |
| Confiança < 0,70 ou fora do domínio | 422 | `baixa_confianca` | "Não entendi a pergunta. Tente reformular." + exemplos |
| Falta parâmetro obrigatório | 422 | `parametro_faltando` | "Quase lá — só preciso saber..." |
| Valor impossível (data malformada) | 422 | `parametro_invalido` | "Não consegui usar algum dado da pergunta..." |
| Consulta sem linhas | 404 | `sem_resultado` | "Não há registros para o período ou filtro informado." |
| Conjunto de dados de outra pessoa ou inexistente | 404 | `dataset_nao_encontrado` | "Não encontrei esses dados..." |
| Banco fora do ar | 503 | `banco_indisponivel` | "Serviço temporariamente indisponível..." |
| Excesso de pedidos | 429 | `limite_requisicoes` | — |

Exceção: em `produtos_sem_saida`, lista vazia **é** a resposta ("Todos os produtos
tiveram pelo menos uma venda no período").

**Na tela**, a confiança aparece como selo: **"Alta confiabilidade"** (verde) para 80% ou
mais, **"Confiabilidade média"** (amarelo) entre 70% e 80%. A interface não mostra o nome
da intenção nem a porcentagem. O que ela mostra é o painel **"Como cheguei nessa
resposta"**: período analisado, filtro, agrupamento e métrica.

### 14.10 O plano B: NLU por regras

`RuleBasedNLU` (`regras.py`) é um interpretador só com regras, sem rede. Serve como linha
de base do comparativo (25,6% de acerto contra 74,4% do modelo, nas 90 perguntas
classificáveis) e como "seguro de vida": `NLU_BACKEND=regras` no painel do Render põe o
sistema no ar se o modelo quebrar.

## 15. Avaliação do sistema inteiro e generalização

### 15.1 As 100 perguntas de validação

`docs/perguntas_validacao.md`: **12 intenções × 7 perguntas (84)**, mais **6 fora de
escopo** (devem dar 422), **5 com parâmetro faltando** (422) e **5 sem resultado** (404).
Critério de acerto: o código HTTP e o tipo/título da resposta esperados. O critério
confere status e tipo, **não o valor numérico** (crítica F02 do parecer, tratada com o
gabarito numérico).

| Data | Situação | Resultado |
|---|---|---:|
| 13/10/2026 | Só o NLU por regras, offline (90 classificáveis) | 23/90 (25,6%) |
| 13/10/2026 | Só o modelo v1.0.0, offline | 67/90 (74,4%) |
| 13/10/2026 | API completa com v1.0.0 | **58/100** |
| 05/11/2026 | API com v1.1.0 → v1.2.0 | 77 → 83/100 |
| 06/11/2026 | Correções de código (ex.: produtos sem saída, slots) | **88/100** |
| 18–19/11/2026 | Sinônimos de domínio (PR #54) | **90/100** |

**Ressalva honesta:** as correções foram guiadas por esse mesmo conjunto. As 88 (ou 90) de
100 medem a regressão no repertório previsto, e não a generalização para perguntas novas.

Tempo de resposta (versão publicada): média de **0,63 s**, 95% abaixo de **1,42 s**, todas
abaixo da meta de 3 s (dados do roteiro da defesa).

### 15.2 Perguntas inéditas (generalização)

Conjuntos escritos fora dos moldes e das 100 perguntas, com gabarito de intenção **e de
valor**, rodados pelo `scripts/avaliar_ineditas.py` (que congela commit e hash do modelo e
calcula intervalo de confiança de Wilson):

| Conjunto | Resultado | Intervalo de confiança (95%) |
|---|---:|---|
| Adversarial (difícil de propósito), antes do PR #54 | 13/30 | 27% a 61% |
| Adversarial, depois do PR #54 | **18/30** | 42% a 75% |
| Representativo (uso realista, escrito depois da mudança) | **27/30** | 74% a 97% |

Quando o sistema responde, o valor confere. Quando não entende, na maioria das vezes
**recusa** (422) em vez de responder errado. O conjunto adversarial é o mesmo que mostrou
o problema corrigido pelo PR #54, então sozinho não prova generalização. Por isso o
conjunto representativo novo.

### 15.3 Gabarito numérico

`scripts/gabarito_numerico.py`: as 14 consultas conferidas **valor a valor** contra um
cálculo independente em Python puro sobre o seed determinístico. Cobre valor, filtros,
agrupamento, ordenação, unidade, nulos, fronteira de período e venda com vários itens.
Resultado: **19/19** provas numéricas.

### 15.4 Varredura do limiar de confiança

| Limiar | Válidas aceitas (de 84) | Fora do domínio aceitas (de 12) |
|---:|---:|---:|
| 0,50 | 78 | 0 |
| 0,60 | 78 | 0 |
| **0,70** | **78** | **0** |
| 0,80 | 76 | 0 |

0,70 é o valor **mais alto que não perde nenhuma pergunta válida**: o lado conservador. A
margem mediana entre a primeira e a segunda intenção é 1,00 nas válidas e 0,54 nas fora do
domínio.

### 15.5 Ablação (quanto cada parte contribui)

- **v1.1.0, 84 perguntas:** intenção pelo modelo 84,5% contra 20,2% só com regras. Tirar a
  cabeça de entidades não mudou o indicador conjunto.
- **v1.2.0, corpus externo, com conferência de valor:** modelo completo 8/24 aceitos e 7/24
  com valor certo; modelo **sem** a cabeça BIO, exatamente o mesmo; só regras, 1/24. A
  cabeça BIO adicionou **+0** acertos de valor. Ela foi mantida por finalidade de
  pesquisa e robustez.

### 15.6 Carga e operação

- **Ensaio de capacidade** (limitador desligado): 200 solicitações, instância aquecida;
  com 20 usuários simultâneos, p95 de 2,3 s.
- **Reteste em configuração normal** (17/11/2026, limitador ligado): primeira pergunta 55 ms
  e as seguintes com mediana de 17 ms, no caminho da aplicação. Num disparo de 35
  perguntas, 30 responderam normalmente e 5 foram bloqueadas (429). A hibernação do Render
  (cerca de 30 s) é da hospedagem gratuita. Não se promete nível de serviço.

---

# Parte III · O sistema

## 16. Arquitetura em camadas

O backend é organizado em camadas, cada módulo com uma responsabilidade (ADR 004):

| Camada | Módulos | O que faz |
|---|---|---|
| Entrada (HTTP) | `main.py`, `models.py`, `auth.py`, `limite.py` | Recebe pedidos, valida dados (Pydantic), autentica pelo token e limita a taxa |
| Interpretação (NLU) | `nlu/base.py` (porta), `nlu/regras.py` e `nlu/adaptador_modelo.py` (adaptadores) | Texto → `Interpretacao` (intenção, confiança, entidades) |
| Regras de negócio | `filtros.py`, `contexto.py`, `refino.py`, `periodo_dataset.py`, `fallbacks.py` | Catálogo, continuação da conversa, data de referência, limiar |
| Consulta | `sql/templates.py`, `sql/executor.py`, `sql/evolucao.py` | Escolhe e executa o template com parâmetros |
| Dados | `db.py`, `acesso.py`, `importacao/`, `auditoria.py` | Pool de conexões, isolamento por empresa, importação, auditoria |

**Porta e adaptadores** (a ideia central da arquitetura hexagonal), aplicados no NLU: a
porta é o protocolo `NLUService`, com um único método `parse(texto) → Interpretacao`.
Os adaptadores são `RuleBasedNLU` e `ModeloTreinadoNLU`. Trocar regras → modelo → nova
versão do modelo não muda nada no resto do sistema. Isso permitiu desenvolver e testar o
backend enquanto o modelo ainda estava sendo treinado.

**Pilha:** interface em React + Vite (Vercel); API em FastAPI, Python 3.12 (Render);
acesso a dados com psycopg 3 e pool de conexões; PostgreSQL gerenciado pelo Supabase;
login pelo Supabase Auth.

![Arquitetura em camadas](/workspace/Intellix/docs/diagramas/arquitetura_camadas.png)

## 17. A API (FastAPI)

### 17.1 Endpoints

| Método e rota | O que faz |
|---|---|
| `GET /health` | Verifica se a API está no ar |
| `GET /capacidades` | Lista o que o agente responde (alimenta "O que posso perguntar") |
| `POST /chat` | Recebe a pergunta e devolve a resposta (`ResultSet`) |
| `GET /resumo` | Panorama do mês (tela Início) |
| `POST /import` | Recebe a planilha `.xlsx` e carrega no banco |
| `GET /planilhas` | Lista as planilhas importadas pela conta |
| `DELETE /planilhas/{empresa_id}` | Exclui uma planilha da conta |
| `GET /conversas` | Lista o histórico de conversas da conta |
| `PUT /conversas/{id}` | Cria ou atualiza uma conversa (upsert) |
| `DELETE /conversas/{id}` | Apaga uma conversa |

### 17.2 O pedido e a resposta do `/chat`

Pedido (`Pergunta`): `pergunta` (1 a 500 caracteres), `empresa_id` (opcional: ausente =
base de demonstração) e `contexto` (intenção e entidades da resposta anterior).

Resposta (`ResultSet`): `titulo`, `colunas`, `linhas`, `tipo_visualizacao` (número, tabela,
barra, linha ou pizza), `parametros`, `confianca`, `gerado_em`, `intencao`, `mensagem`
(quando a resposta é uma frase pronta) e, em perguntas de um mês, a evolução dos 12 meses
até ele. **Números vão crus** (ex.: 48231.50), nunca formatados: a formatação em reais é da
interface. O mesmo `ResultSet` alimenta a tela, o Excel e o PDF.

### 17.3 O fluxo interno do `/chat` (`main.py`)

1. O NLU lê a frase (triagem).
2. Se não há contexto e a confiança é baixa, recusa logo, **sem abrir conexão com o banco**.
3. Abre uma conexão do pool e resolve a empresa (base demo ou planilha do dono).
4. Calcula a data de referência do conjunto. Se a frase não tem ano, lê a frase de novo
   com essa referência.
5. Aplica filtros do catálogo, contexto da conversa e refino.
6. Confere a confiança de novo e executa o template.
7. Registra a consulta em `log_consulta` e devolve o resultado.
8. Se o banco falhar, responde 503 `banco_indisponivel`.

### 17.4 Proteções na entrada

- **Autenticação:** o token JWT do Supabase vem no cabeçalho `Authorization: Bearer`. A API
  confere a assinatura (chaves assimétricas via JWKS, ou segredo HS256 legado), a
  validade, o emissor, o público (`authenticated`) e o papel. O id do usuário sai do token,
  **nunca do pedido**. Token inválido nunca é tratado como anônimo.
- **Limite de requisições** (em memória, janela deslizante por IP e rota): `/chat` 30 por
  minuto, `/resumo` 60 por minuto, `/import` 10 por hora.
- **CORS** restrito às origens da interface (localhost em desenvolvimento e o domínio da
  Vercel), com origens extras configuráveis.
- **Validação** com Pydantic (tamanhos, tipos, saneamento do contexto reenviado).

## 18. Consultas SQL parametrizadas

### 18.1 O que são e por que importam

Uma consulta parametrizada separa **o texto da consulta** dos **valores**. O SQL é fixo,
com lugares nomeados (`%(periodo_inicio)s`), e os valores vão ao banco à parte, pelo
psycopg. O banco nunca interpreta um valor como comando. Isso elimina SQL injection: mesmo
que alguém digite `'; drop table vendas; --`, isso nunca vira SQL, porque **o texto do
usuário não entra no SQL de jeito nenhum**. O modelo só escolhe **qual** template usar, e
as entidades entram como parâmetros. No código há a regra explícita: nunca f-string nem
concatenação.

### 18.2 Os 14 templates (`backend/app/sql/templates.py`)

As 12 primeiras chaves batem com as 12 intenções. As duas últimas são os refinamentos.

| Template | O que calcula | Parâmetros obrigatórios | Visual |
|---|---|---|---|
| `total_vendas_periodo` | Soma de `valor_total` por mês | início, fim | número |
| `top_produtos` | Produtos por faturamento, com quantidade | início, fim, limite | barras |
| `ticket_medio` | Soma de `valor_total` ÷ vendas distintas | início, fim | número |
| `quantidade_vendas` | Vendas distintas (`count(distinct venda_id)`) por mês | início, fim | número |
| `top_clientes` | Clientes por faturamento | início, fim, limite | barras |
| `desempenho_vendedor` | Faturamento e vendas por vendedor (`ilike`) | início, fim, nome | tabela |
| `produtos_sem_saida` | Produtos sem venda no período | início, fim | tabela |
| `comparacao_periodos` | Faturamento do período A e do B | 4 datas | barras |
| `variacao_periodo` | Atual, anterior e variação % | 4 datas | número |
| `vendas_por_canal` | Faturamento e vendas por canal | início, fim | pizza |
| `vendas_por_categoria` | Faturamento por categoria | início, fim | pizza |
| `vendas_por_pagamento` | Faturamento e vendas por forma de pagamento | início, fim | pizza |
| `unidades_vendidas` | Soma das quantidades (peças) | início, fim | número |
| `melhor_mes` | Mês de maior (ou menor) faturamento | início, fim | número |

**Exemplo completo, o ticket médio:**

```sql
select sum(f.valor_total) / nullif(count(distinct f.venda_id), 0) as ticket_medio
from fato_item_venda f
join dim_data d on d.id = f.data_id
where f.empresa_id = %(empresa_id)s
  and d.data between %(periodo_inicio)s and %(periodo_fim)s
```

Detalhes que a banca pode perguntar: o ticket é por **venda**, não por item (o grão da
tabela é o item: `avg(valor_total)` daria a média por item, um erro corrigido após o
feedback do TC2); o `nullif` evita divisão por zero num período sem vendas (resultado nulo
→ 404 "sem resultado").

### 18.3 Filtros opcionais

Todo template recebe os mesmos seis recortes opcionais, inseridos logo depois de `where
f.empresa_id = %(empresa_id)s`: produto, categoria, vendedor, cliente, canal e forma de
pagamento. Cada um tem a forma `(%(produto)s::text is null or ...)`: **parâmetro nulo =
sem recorte**. O texto do filtro é fixo. O usuário só influencia os **valores**, e eles vêm
do catálogo do próprio banco. O `empresa_id` está em **toda** consulta.

### 18.4 Evolução de 12 meses

Para faturamento, quantidade de vendas e ticket médio de um mês, o `/chat` também devolve
a mesma métrica nos 12 meses que terminam no mês perguntado (`sql/evolucao.py`), para a
interface desenhar o gráfico com o mês em destaque e as comparações ("vs set/26 ↑ 25%").

## 19. O banco de dados

### 19.1 Esquema estrela (ADR 001)

A carga é analítica (somas, contagens, rankings), então o modelo escolhido foi o
**esquema estrela**, e não o normalizado até a 3FN: menos junções, consultas mais rápidas
e templates mais simples (Kimball e Ross).

- **Tabela de fatos `fato_item_venda`**, com grão de **um item de uma venda**:
  `empresa_id`, `venda_id` (agrupa os itens da mesma venda), `data_id`, `produto_id`,
  `cliente_id`, `vendedor_id`, `canal`, `forma_pagamento`, `quantidade`,
  `valor_unitario`, `desconto`, `valor_total`, `origem_importacao`. Chave única
  `(empresa_id, venda_id, produto_id)`.
- **Dimensões:** `dim_data` (dia, mês, trimestre, ano), `dim_produto` (nome e categoria),
  `dim_cliente`, `dim_vendedor`.
- **Dimensões degeneradas:** `canal` e `forma_pagamento` ficam na própria fato, por terem
  poucos valores.
- **Estrela e não floco de neve:** a categoria é um atributo de `dim_produto`, sem
  `dim_categoria` separada.
- **Grão de item** preserva "produtos mais vendidos" e "faturamento por categoria", que se
  perderiam com grão de venda.

### 19.2 Outras tabelas

- `empresa`: cada conjunto de dados (a base demo e cada planilha importada). `dono_id` liga
  ao usuário que importou.
- `importacao` e `staging_venda`: controle da importação. A staging guarda cada linha da
  planilha **como texto**, com o motivo da rejeição, para auditoria.
- `log_consulta`: auditoria de cada consulta executada (empresa, pergunta, intenção,
  entidades, confiança, template, parâmetros, tempo).
- `conversa`: histórico do chat por conta (mensagens em JSONB).
- **Views materializadas:** faturamento mensal, ranking de produtos e desempenho por
  vendedor, atualizadas após cada importação.
- **`norm_key(texto)`:** função que deixa o texto em minúsculas, sem acento e sem espaços
  nas pontas. As dimensões têm uma coluna `nome_norm` gerada por ela, com unicidade por
  empresa: "Camiseta" e "camiseta " viram o mesmo registro.
- **`dim_data`:** calendário de **2023 a 2032**, com 3.653 dias. Uma venda fora desse
  intervalo é rejeitada na importação.

### 19.3 As migrações (versionadas em `database/migrations/`)

| Migração | O que faz |
|---|---|
| 001_schema | Tabelas, índices, view de faturamento mensal, empresa de demonstração |
| 002_dim_data | Calendário 2023–2026 (1.461 dias) |
| 003_estende_dim_data | Calendário até 2032 (3.653 dias) |
| 004_views_ranking_desempenho | Views de ranking de produtos e desempenho por vendedor |
| 005_dono_do_dataset | `empresa.dono_id`: cada planilha pertence a quem importou |
| 006_rls_e_usuario_app | RLS por empresa e usuário `intellix_app` com privilégio mínimo |
| 006_protege_api_do_supabase | Fecha as tabelas para a API REST pública do Supabase |
| 007_minhas_planilhas | Funções para listar e excluir as planilhas da conta |
| 008_historico_conversas | Tabela `conversa` e funções do histórico por conta |

![Modelo entidade-relacionamento](/workspace/Intellix/docs/diagramas/der.png)

## 20. Segurança, camada por camada

1. **Senhas:** quem cadastra, faz login e guarda o hash (bcrypt) é o **Supabase Auth**. A
   API nunca vê senha.
2. **Token JWT** conferido em toda chamada (assinatura, validade, emissor, papel).
3. **Dono dos dados** (`acesso.py`): sem `empresa_id`, base de demonstração; com
   `empresa_id`, só o dono acessa. Planilha de outra pessoa e planilha inexistente recebem
   a **mesma** resposta (404), para não revelar quais existem.
4. **RLS no PostgreSQL:** o usuário de banco da aplicação, `intellix_app`, só vê e grava
   linhas da empresa **declarada na transação**. A declaração é feita por
   `declarar_empresa` (um `set_config` que vale só até o fim da transação, o que funciona
   no pooler do Supabase, onde a conexão física pode mudar entre transações). Sem
   declaração, o RLS nega tudo.
5. **Privilégio mínimo:** `intellix_app` não pode apagar vendas. Exceções pontuais
   (listar e excluir as planilhas do dono, histórico) passam por funções `security
   definer` que sempre filtram pelo dono.
6. **API pública do Supabase fechada:** a chave "anon" do login é pública (vai no
   JavaScript). RLS sem políticas nas tabelas impede que ela leia dados pela API REST do
   Supabase.
7. **SQL só por template** e com parâmetros.
8. **Auditoria** em `log_consulta`, gravada num savepoint: se falhar, não derruba a
   resposta.
9. **Limite de requisições** por IP e **CORS** restrito.
10. **Cabeçalhos de segurança na Vercel:** Content-Security-Policy, X-Frame-Options DENY,
    HSTS, nosniff, Permissions-Policy.

**Provas:** `scripts/demo_isolamento.py`, com duas empresas fictícias, confere **6/6**
passos (o administrador vê as duas; sem declarar empresa, o app não vê nada; declarada A,
vê só A; pedir B de propósito devolve zero; o app não apaga vendas; a auditoria fica
isolada). Há também 8 testes de isolamento e auditoria e 4 testes de RLS rodados com o
usuário restrito.

## 21. Importação de planilhas (ETL)

1. **Leitura** (`leitor_excel.py`): só `.xlsx` (até 10 MB e 50 mil linhas), lido em fluxo.
   Confere a assinatura do arquivo (ZIP), lê a primeira aba e mapeia os cabeçalhos para
   as colunas canônicas, aceitando sinônimos ("qtd" → quantidade, "preço" → valor
   unitário, "pedido"/"cupom" → venda_id...), sem acento e sem diferenciar maiúsculas.
   **Obrigatórias:** data da venda, produto, quantidade e pelo menos um valor (unitário ou
   total). A interface faz a mesma validação antes de enviar, e o servidor confere de novo.
2. **Validação linha a linha** (`etl.py`): data (ISO ou dd/mm/aaaa), produto, quantidade >
   0, valor não negativo, data dentro do calendário. Linha inválida é **rejeitada com o
   motivo**, sem derrubar o arquivo. Total ausente é calculado (quantidade × unitário −
   desconto).
3. **Cada importação cria uma empresa nova** (conjunto de dados isolado), com o dono.
4. **Dimensões** sem duplicar (por `nome_norm`).
5. **Grão:** o mesmo produto em duas linhas da mesma venda vira **um item**, com
   quantidade e valores somados. Antes, a segunda linha era descartada em silêncio e o
   faturamento ficava menor.
6. **Idempotência:** reenviar o mesmo arquivo não duplica (hash do arquivo e chave única).
7. **Atualiza as views** e devolve o relatório: linhas lidas, válidas, rejeitadas (com
   motivos) e agrupadas.

Prova: `scripts/reconciliacao_carga.py` confere planilha × banco (vendas, itens,
faturamento, ticket, grão, zero linhas órfãs, idempotência).

## 22. A interface (frontend)

React com Vite, publicada na Vercel. Telas:

- **Página pública, cadastro e login** (Supabase Auth): confirmação por e-mail,
  recuperação de senha, sessão de 12 horas.
- **Início:** panorama do mês, calculado no servidor (`GET /resumo`) com SQL fixo, sem o
  modelo. Cinco indicadores com variação contra o mês anterior (faturamento, ticket médio,
  vendas, itens vendidos, clientes), seletor de mês, Exportar PDF, "O mês em resumo",
  observações por regras fixas, vendas por dia e por dia da semana, ranking de produtos,
  categorias, canais, pagamentos e evolução de 12 meses. Clicar num item abre a análise no
  chat.
- **Perguntar (chat):** resposta em número, gráfico (barras, rosca ou tabela) ou tabela,
  selo de confiabilidade, "Como cheguei nessa resposta", sugestões de continuação, Copiar,
  Excel e PDF (gerados no navegador, para não pesar no servidor), histórico salvo na conta.
- **O que posso perguntar:** os 14 tipos de análise, com exemplos clicáveis.
- **Importar dados:** prévia e conferência antes de enviar, modelo de planilha para baixar,
  relatório e "Suas planilhas" (usar, excluir, voltar aos dados de exemplo).
- **Busca rápida Ctrl+K**, tema claro/escuro, perfil (nome, foto, senha), Sobre, Ajuda
  (13 perguntas frequentes), Fale conosco e Termos.

## 23. Infraestrutura e deploy

| Peça | Onde | Detalhes |
|---|---|---|
| Interface | **Vercel** | Deploy do React; cabeçalhos de segurança e cache em `vercel.json` |
| API + modelo | **Render** (gratuito) | Python 3.12.7; modelo em memória; deploy automático a cada push no GitHub; hiberna após cerca de 15 min sem uso, e a primeira resposta leva cerca de 30 s (reativação + carga do modelo); RAM de 256–512 MB, o que favorece modelos leves |
| Banco | **Supabase** (PostgreSQL gerenciado, gratuito) | Projetos separados: desenvolvimento em São Paulo e produção em Oregon (EUA). Conexão obrigatória pelo pooler de transações (porta 6543) |
| Login | **Supabase Auth** | Cadastro, login, tokens, hash das senhas |
| Código | **GitHub** | Kanban no GitHub Projects; CI no GitHub Actions |

**Por que Render (ADR 003):** o plano gratuito não expira (o do Railway expira por
crédito) e tem deploy automático. **Por que Supabase (ADR 002):** plano gratuito real,
PostgreSQL puro (portável) e Auth/RLS disponíveis. A região de produção (Oregon) não pode
ser trocada depois de criada. O que pesa na latência é a distância entre o Render e o
banco, porque o navegador nunca fala direto com o PostgreSQL.

**Pool de conexões** (`db.py`): abrir uma conexão nova custava cerca de 1,1 s por pergunta
no Render (TCP + TLS + autenticação até Oregon). O pool abre uma vez e reaproveita (até 4
conexões, testadas antes de entregar, timeout de 10 s). `prepare_threshold=None` é
obrigatório, porque o pooler de transações do Supabase não mantém *prepared statements*
entre transações.

**CI (GitHub Actions):** a cada pull request, roda o lint (ruff) e os testes (pytest) contra
um **PostgreSQL 16 efêmero**, com as migrações e o seed, usando o **mesmo modelo treinado**
de produção.

**Reprodução e cópia de segurança:** `REPRODUZIR.md` tem os comandos com os resultados
esperados. O manifesto (`scripts/manifesto_reproducao.py`) registra o commit, o SHA-256 dos
pesos (v1.2.0: `ea30338e9626f4b6...`), o fingerprint do conjunto de dados
(`58d126cf...`) e os hashes das migrações e dos templates. A cópia lógica do banco foi
restaurada com as 9 tabelas e contagens idênticas.

## 24. A base de demonstração (seed)

`database/seed.py`, semente fixa 42, determinístico e idempotente:

- **3.527 vendas e 8.941 itens**, de 03/01/2023 a 31/12/2026, faturamento de **R$
  2.717.797,23**;
- **40 produtos em 8 categorias** (Vestuário, Calçados, Acessórios, Eletrônicos, Casa,
  Beleza, Alimentos, Bebidas), **131 clientes** e **6 vendedores**;
- canais loja (45%), site (25%), WhatsApp (20%) e marketplace (10%); pagamentos pix (34%),
  crédito (30%), débito (16%), dinheiro (14%) e boleto (6%);
- **sazonalidade de propósito:** dezembro vende cerca de 4 vezes fevereiro;
- de 1 a 6 itens por venda (média de cerca de 2,5).

É **sintética**: uma das três ressalvas da conclusão.

## 25. Testes automatizados

Mais de 200 testes (202 na execução de referência de 06/11, com 198 aprovados, nenhuma
falha e 4 pulados no ambiente comum; os 4 de RLS rodam à parte com o usuário restrito e
também passam), em 29 arquivos: regras do NLU, adaptador e vendedor, filtros, contexto,
refino, templates SQL, executor, chat de ponta a ponta, autenticação, limite, auditoria,
isolamento, RLS, importação (11 testes), reconciliação de carga, gabarito numérico,
valores de referência, resumo, conversas, planilhas e pool de conexões.

## 26. Os diagramas do TCC

Todos têm a fonte versionada em `docs/diagramas/` e são gerados a partir do código atual.

1. **Casos de uso:** o gestor faz pergunta em linguagem natural, visualiza a resposta,
   consulta o histórico, vê o que o agente sabe responder, vê o panorama do mês, importa
   planilha, gerencia as planilhas e se cadastra/entra. Inclusões: interpretar a pergunta,
   consultar dados (consulta parametrizada), validar e carregar as linhas. Extensões:
   pergunta de acompanhamento, reformular pergunta não compreendida, exportar o resultado.
2. **Classes:** cada responsabilidade separada: o controlador recebe a requisição, o
   orquestrador coordena, o serviço de NLU interpreta (`NLUService.parse`, com
   `RuleBasedNLU` e `ModeloTreinadoNLU`/`ModeloIntellix`), o construtor de SQL monta a
   consulta (`TEMPLATES`, `executar_template`) e o repositório acessa o banco.
3. **Sequência:** do usuário digitando até a resposta (figura abaixo), com os dois desvios
   de 422 (confiança baixa/fora do domínio e parâmetro ausente) e o 404 sem resultado.
4. **Entidade-relacionamento:** o esquema estrela mais as tabelas de importação, auditoria
   e conversa (seção 19).
5. **Fluxograma:** início → pergunta → POST /chat → normaliza, tokeniza, modelo classifica
   e marca → confiança ≥ 0,70 e termo do domínio? (não: pede reformulação) → identifica o
   conjunto de dados, aplica filtros, contexto e refino → parâmetros presentes? (não:
   pergunta o que falta) → executa o template → banco disponível? (não: indisponibilidade)
   → há registros? (não: sem registros) → registra em log_consulta → exibe com indicador de
   confiança → fim.
6. **Arquitetura em camadas:** apresentação (Vercel), aplicação (Render), acesso a dados
   (psycopg 3) e persistência (Supabase), com o Supabase Auth ao lado (seção 16).

![Diagrama de sequência](/workspace/Intellix/docs/diagramas/sequencia.png)

![Fluxograma](/workspace/Intellix/docs/diagramas/fluxograma.png)

![Casos de uso](/workspace/Intellix/docs/diagramas/casos_de_uso.png)

![Classes](/workspace/Intellix/docs/diagramas/classes.png)

## 27. Metodologia e gestão

(Do roteiro da defesa.) Segundo Gil (2017), a pesquisa é **aplicada e tecnológica** quanto
à natureza, **exploratória e descritiva** quanto aos objetivos e **experimental** quanto aos
procedimentos: foram manipuladas variáveis (versões do modelo, regras, limiar) e medido o
efeito (acurácia, F1, acerto ponta a ponta, tempo). Gestão em Kanban no GitHub Projects, em
quatro frentes: modelo de NLU, API, dados e infraestrutura, e interface e documentação. O
desenvolvimento passou por sete etapas, dos requisitos à homologação e aos testes. As
decisões de arquitetura foram registradas como ADRs.

## 28. Limitações e trabalhos futuros

**Limitações (dizer antes que a banca diga):**

- a base de vendas é **sintética**;
- não houve teste com **usuários externos** (gestores reais);
- as 88/90 de 100 foram medidas no **mesmo repertório** que guiou as correções;
- domínio fechado: só 12 intenções (14 tipos de análise);
- períodos em dias ou semanas ("ontem", "semana passada") caem no ano inteiro;
- a cabeça de entidades não mostrou ganho operacional na ablação;
- VENDEDOR é a entidade mais fraca (F1 0,43);
- hospedagem gratuita: hibernação, RAM limitada, banco de produção nos EUA;
- a viabilidade econômica é uma hipótese, baseada em preços de referência dos concorrentes.

**Trabalhos futuros (na ordem da conclusão):** um conjunto novo de perguntas inéditas
escritas por pessoas de fora, para medir generalização; dados reais de uma empresa cliente;
avaliação com usuários reais. Também: comparar com um Transformer pequeno, uma v1.3 dos
moldes com as frases que ainda falham, pedir o período quando ele não for reconhecido, e
pedir confirmação quando a margem entre as duas intenções mais prováveis for pequena.

---

# Apêndice A · Perguntas e respostas para estudar

**1. O Intellix usa ChatGPT ou algum LLM?**
Não. Usa um classificador próprio, uma BiLSTM de 288.987 parâmetros treinada pela equipe,
que roda no nosso servidor. Ele não gera texto: escolhe uma de 12 intenções e etiqueta as
palavras. O SQL vem de templates fixos.

**2. Por que não usar um LLM com Text-to-SQL, que seria mais flexível?**
É mais flexível, mas tem três custos para esse público: paga-se por pergunta, os dados da
empresa vão para terceiros, e o SQL gerado pode sair errado ou inseguro sem ninguém
perceber. Em domínio fechado, 12 intenções cobrem as perguntas mais comuns, e o SQL vem de
um template validado. Trocamos flexibilidade por previsibilidade (está como fraqueza na
SWOT).

**3. O que é uma BiLSTM?**
Uma rede recorrente que lê a frase nos dois sentidos. Cada LSTM guarda uma memória
controlada por portões (esquecimento, entrada, saída). Juntando as duas direções, cada
palavra é representada pelo que vem antes e pelo que vem depois. No Intellix, cada direção
tem 128 unidades e a saída por palavra tem 256 números.

**4. Por que não BERT/Transformer?**
Não caberia na hospedagem gratuita (256–512 MB de RAM), as frases são curtas (7,3 tokens em
média) e a BiLSTM já bateu as metas. Não testamos Transformer. Comparar com um pequeno é
trabalho futuro.

**5. Como o modelo decide a intenção?**
Faz a média das saídas da BiLSTM das palavras reais (ignorando o preenchimento), passa por
uma camada linear 256 → 12 e aplica softmax. A maior probabilidade é a confiança. Se for
menor que 0,70, o sistema pede para reformular.

**6. O que é o esquema BIO? Dê um exemplo.**
Cada palavra recebe B (começa uma entidade), I (continua) ou O (fora). Em "quanto vendi de
camiseta branca em abril?": camiseta = B-PRODUTO, branca = I-PRODUTO, abril = B-PERIODO.
São 19 etiquetas: O mais B e I para 9 tipos.

**7. Como as 4.800 frases foram criadas? Vocês anotaram à mão?**
Não. A equipe escreveu moldes (387 na v1.0.0, 561 na v1.2.0) com espaços como `{periodo}`.
O gerador sorteia valores, gera 60 variações por molde e marca as etiquetas sozinho. Depois
remove repetidas, remove frases iguais às 100 perguntas de validação e balanceia em 400 por
intenção: 12 × 400 = 4.800.

**8. Como foi dividido o treino?**
Na v1.0.0, 70/15/15 estratificado por intenção (3.360 / 720 / 720), semente 42. Na v1.1.0 e
na v1.2.0, 70/30 (3.360 / 1.440). Além disso, o teste manual de 120 frases escritas à mão,
que é o que vale.

**9. Quais os hiperparâmetros?**
Embedding de 100, LSTM de 128 por direção, dropout de 0,3, Adam com taxa 0,001, lote de 32,
até 40 épocas com early stopping de paciência 6, corte de gradiente em 5, perda = 0,5 ×
intenção + 0,5 × etiquetas.

**10. Por que a perda das etiquetas usa ignore_index = -100?**
Para que as posições de preenchimento não contem no erro. Usar 0 estaria errado, porque 0 é
a etiqueta "O", e o modelo ignoraria a maioria das palavras.

**11. Por que 70% de confiança mínima?**
Varredura: com 0,50, 0,60 ou 0,70, o sistema aceita 78 de 84 perguntas válidas e 0 de 12
fora do domínio. Em 0,80, cai para 76. 0,70 é o mais alto que não perde válidas: o lado
conservador. Dos erros finais nas 100 perguntas, parte foi recusa por baixa confiança, o
comportamento desejado.

**12. Por que acurácia de 93,3% e F1 de 0,838? Por que a diferença?**
São tarefas diferentes. A acurácia é da intenção. O F1 é das entidades, por entidade
completa (seqeval). E, dentro da intenção, o F1 macro dá o mesmo peso a cada classe, então
cai quando algumas classes vão pior.

**13. Por que a versão publicada (v1.2.0) tem acurácia menor que a v1.0.0?**
No teste manual, 93,3% contra 88,3% (88,5% sem as 7 frases que entraram no treino). Mas o
objetivo é o agente inteiro: os moldes v3 cobriram formulações reais da interface ("mês
passado", "quantas peças", "qual mês vendeu mais"), e da v1.1.0 para a v1.2.0 o NLU foi de
77 para 83 acertos nas 100 perguntas e de 30 para 37 nas 40 de detalhe. As duas estão acima
da meta de 85%.

**14. Houve vazamento entre treino e teste?**
O teste sintético é otimista (99,6%), porque frases do mesmo molde caem nos dois lados. Por
isso não é o número reportado. O gerador remove frases iguais às 100 perguntas de
validação. No teste manual, 7 de 120 frases coincidiram com o treino da v1.2.0, e sem elas o
resultado é 88,5%. Para generalização, os números são os das inéditas.

**15. A cabeça de entidades serve para quê, se as datas são resolvidas por regra?**
Ela marca os trechos (produto, vendedor, canal...) que os filtros convertem em valores do
catálogo, e é a primeira escolha para o nome do vendedor. Mas a ablação na v1.2.0 mostrou
+0 de ganho no valor final, porque as regras e o catálogo compensam. Mantivemos por
finalidade de pesquisa e robustez.

**16. O que acontece com uma pergunta fora do assunto?**
Duas barreiras: confiança < 0,70, ou a frase não tem nenhum termo do domínio de vendas.
Qualquer uma devolve "Não entendi a pergunta. Tente reformular." com exemplos. O filtro
existe porque um classificador fechado sempre escolhe uma classe ("capital da França" saiu
com 0,92).

**17. O que é a melhoria de 19/11 (PR #54)? Não é ajustar ao teste?**
Uma camada de sinônimos do domínio para pagamento, categoria e canal ("meio de pagamento",
"linha de produtos", "por onde vendi"). São termos reais do domínio, não frases de teste. O
conjunto adversarial (13 → 18 de 30) é o mesmo que mostrou o problema, então medimos também
num conjunto novo (27 de 30), e as 100 perguntas não regrediram (88 → 90).

**18. O que 88 (ou 90) de 100 comprova?**
Que o sistema devolve o tipo e o estado de resposta esperados nesse repertório. Não prova
generalização, porque as mesmas perguntas guiaram as correções, nem o valor numérico.
Para isso: gabarito numérico (19/19), perguntas inéditas (27/30 e 18/30) e conferência à
mão na demonstração.

**19. Como vocês garantem que o valor está certo?**
O SQL é determinístico (a mesma pergunta gera sempre a mesma consulta), o gabarito numérico
confere as 14 consultas contra um cálculo independente (19/19) e há testes que conferem
valores contra uma base calculável à mão.

**20. E SQL injection?**
O texto do usuário nunca vira SQL. O modelo só escolhe qual template usar, e as entidades
entram como parâmetros pelo psycopg (`%(nome)s`). Os valores de filtro vêm do catálogo do
banco. Cada consulta fica registrada em `log_consulta` e há limite de requisições por IP.

**21. Como uma empresa não vê os dados de outra?**
Coluna `empresa_id` em todas as tabelas de negócio, RLS no PostgreSQL (só a empresa
declarada na transação) e um usuário de banco com privilégio mínimo. Na API, só o dono da
planilha a consulta, e outra pessoa recebe a mesma resposta de "não existe". Provado com
6/6 passos no script de isolamento e com testes de RLS.

**22. Por que esquema estrela?**
As consultas são analíticas (somas, rankings, comparações por período). O esquema estrela
precisa de menos junções e deixa os templates mais simples e rápidos. O grão de item
preserva "produtos mais vendidos" e "por categoria".

**23. Por que "quanto vendi ontem?" responde o ano inteiro?**
Os períodos que as regras resolvem são mês, trimestre, semestre e ano. Sem um deles, o
padrão é o ano da data de referência. O painel "Como cheguei" mostra o período usado. É uma
limitação: o certo seria pedir o período.

**24. Por que a primeira resposta às vezes demora?**
O Render gratuito hiberna após cerca de 15 minutos sem uso, e a primeira requisição leva
cerca de 30 s (reativar e carregar o modelo). Depois disso, a média é 0,63 s.

**25. Como alguém reproduz os resultados?**
`REPRODUZIR.md` (comando a comando, com o esperado ao lado) e o manifesto com commit, hash
dos pesos, fingerprint do conjunto de dados e hashes das migrações e dos templates.

**26. Qual a contribuição científica?**
Duas: o conjunto de 4.800 frases anotadas em português para o domínio de vendas (recurso
escasso), e a evidência de que, em domínio fechado, um modelo pequeno com SQL
determinístico atinge as metas de acerto e tempo sem LLM externo.

---

# Apêndice B · Números para decorar

| O quê | Número |
|---|---|
| Parâmetros do modelo publicado (v1.2.0) | **288.987** (cerca de 289 mil) |
| Tamanho do arquivo | 1,17 MB (v1.0.0: 1,09 MB) |
| Vocabulário (v1.2.0) | 455 tokens |
| Intenções / tipos de análise | 12 / 14 |
| Tipos de entidade / etiquetas BIO | 9 / 19 |
| Exemplos de treino gerados | 4.800 (400 por intenção) |
| Moldes | 387 (v1.0.0) · 423 (v1.1.0) · 561 (v1.2.0) |
| Divisão v1.0.0 | 3.360 / 720 / 720 (70/15/15) |
| Embedding / LSTM por direção / saída por token | 100 / 128 / 256 |
| Dropout · taxa de aprendizado · lote | 0,3 · 0,001 · 32 |
| Épocas máximas · paciência · corte de gradiente · α | 40 · 6 · 5 · 0,5 |
| Teste real | 120 frases (10 por intenção) |
| Acurácia v1.0.0 / v1.2.0 (teste real) | 93,3% / 88,3% (88,5% sem as 7 sobrepostas) |
| F1 entidades v1.0.0 / v1.2.0 | 0,838 gravado (0,803 reavaliado) / 0,831 |
| Metas | acurácia ≥ 85% · F1 ≥ 0,80 · modelo ≤ 256 MB · resposta < 3 s |
| Inferência | 1,72 ms por frase (CPU) |
| Memória em execução | cerca de 222 MB |
| Limiar de confiança | 0,70 |
| Selo verde / amarelo | ≥ 0,80 / entre 0,70 e 0,80 |
| 100 perguntas | 58 (13/10) → 83 → 88 (06/11) → 90 (19/11) |
| Regras sozinhas × modelo (90 classificáveis) | 25,6% × 74,4% |
| Inéditas | representativo 27/30 · adversarial 18/30 (antes 13/30) |
| Gabarito numérico | 19/19 |
| Isolamento | 6/6 passos |
| Tempo de resposta | média 0,63 s · p95 1,42 s |
| Testes automatizados | mais de 200 (202 na execução de referência) |
| Base demo | 3.527 vendas · 8.941 itens · 40 produtos · 8 categorias · R$ 2.717.797,23 |
| Calendário | 2023 a 2032 (3.653 dias) |
| Limites da API | /chat 30/min · /resumo 60/min · /import 10/h · pergunta até 500 caracteres |
| Planilha | `.xlsx` até 10 MB e 50 mil linhas |
