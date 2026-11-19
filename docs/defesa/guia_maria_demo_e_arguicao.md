# Defesa · Parte da Maria Luiza (slides 12 a 17) e demonstração ao vivo

Material de apoio para a defesa. Tem quatro partes:

1. [O que mudou e por quê](#1-o-que-mudou-e-por-quê) (leia primeiro)
2. [Fala revisada, slide a slide](#2-fala-revisada-slide-a-slide)
3. [Roteiro da demonstração ao vivo (3:30)](#3-roteiro-da-demonstração-ao-vivo-330)
4. [Kit da arguição: o que a banca pode pedir na hora](#4-kit-da-arguição)

Arquivos da demonstração, nesta mesma pasta:

| Arquivo | O que é |
|---|---|
| `Empresa_A_Loja_Estacao_Moda.xlsx` | Loja de roupas fictícia. 14 linhas, setembro e outubro de 2026 |
| `Empresa_B_Papelaria_Traco_Fino.xlsx` | Papelaria fictícia. 13 linhas, uma delas sem data de propósito |
| `telas/` | Capturas da interface real com essas planilhas, para o operador saber o que vai aparecer |

Cada planilha tem duas abas. **Vendas** é a que o Intellix lê. Ela segue o modelo
oficial de importação. **Conferência** traz fórmulas do próprio Excel que recalculam
faturamento, número de vendas, ticket médio etc. a partir da aba Vendas. É o
"gabarito independente" que o parecer pede: a banca pode abrir o arquivo e conferir.

> **Como isso foi testado.** Subi o Intellix localmente (mesmo código do `main`,
> commit `bd34783`, modelo v1.2.0, banco com o seed da demo), importei as duas
> planilhas pela tela e fiz todas as perguntas deste roteiro, na API e na interface.
> Todos os números abaixo saíram dessa execução e batem com a aba Conferência.
> **Repitam o teste no sistema publicado na véspera** (seção 3.4): é ele que vai
> estar na tela.

---

## 1. O que mudou e por quê

**A parte final do parecer (seção 5, "Demonstração e arguição") é um roteiro
sugerido para a banca, não um roteiro obrigatório para vocês.** Ela diz o que a
banca provavelmente vai pedir para ver ("importar planilha sintética em duas
empresas, formular pergunta inédita e conferir total e ticket manualmente...").
Tudo isso não cabe em 3:30, então dividi em duas camadas:

- **Demonstração principal (3:30, dentro da apresentação):** importa as duas
  planilhas, confere faturamento e ticket à mão, mostra a recusa fora do domínio e
  mostra que uma empresa não vê a outra. Já responde a maior parte do pedido.
- **Kit da arguição (seção 4):** o resto (falta de parâmetro × retorno vazio,
  histórico, isolamento entre usuários, versão e hash, pergunta ditada pela banca),
  pronto para mostrar se pedirem.

**Correções importantes que apareceram nos testes:**

1. **A tela não mostra o nome da intenção nem a confiança em %.** O roteiro atual
   diz "reparem que a resposta mostra a intenção que o modelo reconheceu e a
   confiança dele". O que aparece de fato é um selo **"Alta confiabilidade"** (verde)
   ou **"Confiabilidade média"** (amarelo), e o painel **"Como cheguei nessa
   resposta"**, com o período analisado, o filtro, o agrupamento e a métrica. A fala
   da demonstração foi ajustada para isso.
2. **O "99,3%" do slide 14 só confere com o ponto de interrogação.** "quanto vendi de
   camiseta branca em abril**?**" dá 99,33% no modelo publicado (v1.2.0). Sem o "?",
   dá 98,3%. Se a frase do slide estiver sem "?", acrescentem. Se a banca digitar
   sem "?", a diferença é essa.
3. **O "99,99%" do slide 16 confere:** "quais os 5 produtos mais vendidos em março?"
   dá 99,99%, com número = 5 e período = março.
4. **"4.800 frases rotuladas pela equipe" é impreciso.** A equipe escreveu cerca de 200
   **moldes** de frase. O gerador sorteou valores e marcou as etiquetas sozinho. Se
   a banca perguntar "vocês anotaram 4.800 frases à mão?", a resposta honesta é não.
   A fala do slide 12 foi ajustada (detalhes na pergunta 8 da seção 4.3).
5. **Algumas formulações falham.** Estão listadas na seção 3.3 ("não usem na demo").
   A mais perigosa: **"quanto vendi ontem?"** e **"faturamento da semana"** não são
   recusadas. O sistema responde o **ano inteiro**, porque dia e semana não são
   períodos suportados. Não usem. Se a banca perguntar, a resposta está na seção 4.2.

---

## 2. Fala revisada, slide a slide

Critério: uma ideia por frase, nada de termo técnico sem tradução imediata, e um
exemplo concreto sempre que aparece um conceito. O tamanho de cada bloco é o mesmo
do roteiro original (cerca de 130 palavras por minuto).

### Slide 12 · O modelo (1:00)

> Obrigada, Erik. A primeira coisa que queremos deixar clara: o Intellix não é um
> ChatGPT. O ChatGPT escreve um texto novo a cada pergunta e, por isso, pode inventar
> uma resposta que parece certa. O nosso modelo não escreve nada. Ele só escolhe, entre
> 12 tipos de pergunta que conhece, qual é a sua. É uma triagem: lê a frase e coloca na
> gaveta certa.
>
> Por isso ele é pequeno. Tem cerca de 289 mil parâmetros e ocupa 1,1 MB, menos que
> uma foto de celular. Foi treinado com 4.800 frases de exemplo, geradas a partir de
> moldes que a equipe escreveu.
>
> De cada frase, ele tira duas coisas ao mesmo tempo: a **intenção**, que é o que a
> pessoa quer saber, e as **entidades**, que são os detalhes, como o mês ou o produto.

**Por que mudou:** "classifica a frase em categorias fechadas" e "bilhões de
parâmetros, terabytes" são abstratos para quem ouve. A imagem da triagem e a da foto
de celular ficam na cabeça. E "rotulados pela equipe" virou "geradas a partir de
moldes que a equipe escreveu", que é o que de fato aconteceu.

### Slide 13 · Intenções (1:00)

> Essas 12 intenções cobrem o que um pequeno comerciante mais pergunta, em quatro
> grupos. **"Quanto?"**: quanto faturei em março, qual o meu ticket médio. **"Quem e
> o quê?"**: quais os 5 produtos mais vendidos, quem são meus melhores clientes.
> **"Por onde e como?"**: vendi mais pelo site ou na loja, no pix ou no cartão. E
> **"comparar"**: quanto cresci em relação ao mês passado.
>
> E se a pergunta não for nenhuma dessas? Para cada resposta, o modelo calcula o
> quanto tem certeza. Se essa confiança ficar abaixo de 70%, o Intellix não arrisca:
> pede para reformular. E se a pergunta não tiver nada a ver com vendas, como "qual a
> previsão do tempo?", um filtro barra antes. Vocês vão ver isso na demonstração.

**Por que mudou:** explica o que é "confiança" antes de usar o número, e amarra com a
demo ("vocês vão ver"). A banca ouve a promessa e depois vê o sistema cumprir.

### Slide 14 · Entidades (1:00)

> As entidades são os detalhes que mudam a resposta. São nove tipos: período, data,
> produto, categoria, cliente, vendedor, canal, forma de pagamento e número.
>
> Para o modelo achar esses detalhes, cada palavra da frase recebe uma etiqueta. **B**
> quer dizer "aqui começa um detalhe". **I** quer dizer "o detalhe continua". **O** quer
> dizer "esta palavra não é detalhe".
>
> Na frase "quanto vendi de camiseta branca em abril?", "camiseta" recebe B de
> produto. "Branca" recebe I de produto, porque continua o mesmo produto. E "abril"
> recebe B de período. É assim que ele sabe que "camiseta branca" é **um** produto, e
> não duas coisas. Esse é o resultado real do modelo publicado para essa frase, com
> 99,3% de confiança.

**Por que mudou:** traduz B, I e O por extenso antes do exemplo e fecha com o *porquê*
("um produto, e não duas coisas"). Sem isso, a sigla BIO fica solta.

### Slide 15 · BiLSTM (1:00)

> Para ler a frase, usamos uma rede neural chamada LSTM bidirecional. A LSTM lê palavra
> por palavra e vai guardando uma memória do que já leu. Bidirecional quer dizer que
> ela lê a frase duas vezes: do começo para o fim e do fim para o começo. Assim, cada
> palavra é entendida pelo que vem antes **e** pelo que vem depois, do jeito que a gente
> às vezes só entende uma palavra quando chega ao fim da frase.
>
> E por que não um Transformer, como o BERT? Um BERT tem centenas de milhões de
> parâmetros e não caberia na hospedagem gratuita. As nossas perguntas são frases
> curtas, e a BiLSTM já bateu as metas: responde em 1,72 milissegundo por frase e roda
> no nosso próprio servidor, sem mandar dados para ninguém.

**Por que mudou:** a analogia com a leitura humana justifica o "bidirecional", e a
justificativa do Transformer termina num benefício para o usuário (dados não saem do
servidor), não só numa limitação.

### Slide 16 · O agente (1:30)

> Agora juntando tudo: o caminho de uma pergunta, do teclado até o gráfico. Vou usar
> "quais os 5 produtos mais vendidos em março?".
>
> **Um:** ele limpa o texto. Corrige abreviações e acentos, então "qto" vira "quanto".
>
> **Dois:** o modelo lê a frase. Intenção: produtos mais vendidos, com 99,99% de
> confiança. Número: 5. Período: março.
>
> **Três:** duas travas de segurança. A confiança precisa ser de pelo menos 70%, e a
> pergunta precisa ser sobre vendas. Se uma falhar, ele para aqui e pede para
> reformular.
>
> **Quatro:** ele traduz os detalhes. "Março" vira de 1º a 31 de março. O nome de um
> produto ou vendedor é conferido no cadastro da empresa. E a pergunta fica guardada
> para a próxima, como "e em abril?".
>
> **Cinco:** ele preenche uma consulta SQL pronta, escrita e testada por nós. O texto
> que o usuário digitou nunca vira SQL. Só os valores entram, como parâmetros.
>
> E o banco responde com o número, o gráfico e a opção de exportar. Resumindo numa
> frase: **o modelo decide o quê, as regras decidem como, e o banco responde.**

**Por que mudou:** o texto original era um parágrafo só. Numerar os passos (e, se der,
numerar também no slide) deixa a banca acompanhar e facilita perguntas do tipo "no
passo 4, como...".

### Slide 17 · Demonstração ao vivo (3:30)

A fala completa, sincronizada com o operador, está na seção 3.2.

---

## 3. Roteiro da demonstração ao vivo (3:30)

### 3.1 Antes de começar (checklist)

- [ ] **Uma conta de teste só para a demo**, sem nenhuma planilha importada. Se já
      houver, excluam em *Importar dados → Suas planilhas → Excluir*.
- [ ] **Uma segunda conta de teste** logada em outro navegador ou aba anônima, para o
      teste de isolamento da arguição (seção 4.1).
- [ ] As duas planilhas na **Área de Trabalho** do computador da apresentação, com o
      nome original (o nome do arquivo aparece na tela).
- [ ] Abrir o sistema **10 minutos antes** e fazer uma pergunta qualquer nos dados de
      exemplo: o Render gratuito "dorme" e a primeira resposta pode levar uns 30 s.
      Depois, clicar em **Nova conversa**.
- [ ] Deixar a tela em **Importar dados** antes de passar para o slide 17.
- [ ] Zoom do navegador em 110–125% para a banca enxergar os números.
- [ ] Vídeo de plano B gravado **com estas mesmas planilhas e perguntas**.
- [ ] As perguntas da demo num papel ao lado do operador, para digitar sem pensar.

**Divisão:** o operador só digita e clica. A Maria Luiza narra e aponta o que
importa. Combinem um sinal (um aceno) para "pode digitar a próxima".

### 3.2 Passo a passo

| Tempo | Operador faz | O que aparece na tela | Maria Luiza fala |
|---|---|---|---|
| **0:00–0:35** | Em *Importar dados*, clica **Escolher arquivo** → `Empresa_A_Loja_Estacao_Moda.xlsx`. Depois **Enviar para análise**. | Prévia com as 12 colunas reconhecidas. Depois: "Planilha enviada. 14 linhas foram aceitas" e "1 linha repetia um produto na mesma venda e foi somada ao item, sem perder valor." ([tela](telas/1_relatorio_empresa_A.png)) | "Esta é a planilha de uma loja fictícia, no formato do nosso modelo de importação: uma linha por item vendido. O Intellix confere o arquivo antes de enviar. Achou as 12 colunas. [enviou] Catorze linhas aceitas. E reparem neste aviso: uma venda tinha o mesmo produto em duas linhas, e ele somou num item só, sem duplicar e sem perder valor." |
| **0:35–1:15** | Clica **Fazer perguntas sobre esses dados**. Digita **`quanto vendi em outubro?`**. Depois abre **Como cheguei nessa resposta**. | **R$ 1.000,00**, gráfico mês a mês (set R$ 0,8 mil, out R$ 1 mil), "vs set/26 ↑ 25%". No painel: "Período analisado: 01/10/2026 a 31/10/2026 · Métrica: Faturamento". Selo "Alta confiabilidade". ([tela](telas/2_A_outubro_como_cheguei.png)) | "Mil reais. Na planilha, as cinco vendas de outubro somam exatamente mil. [abre o painel] Aqui ele mostra o que entendeu: de 1º a 31 de outubro, métrica faturamento. E o selo verde diz que a confiança foi alta." |
| **1:15–1:35** | Digita **`e em setembro?`** | **R$ 800,00** | "Agora uma pergunta incompleta. Ele lembrou que eu estava falando de faturamento e só trocou o mês: oitocentos reais." |
| **1:35–2:05** | Digita **`qual foi o ticket médio em outubro?`** | **R$ 200,00** | "Ticket médio: duzentos reais, que são mil reais divididos por cinco vendas. Um detalhe: outubro tem oito linhas na planilha, mas só cinco vendas. Se dividisse por linha, daria cento e vinte e cinco, que está errado. O ticket é por venda, e é assim que ele calcula." |
| **2:05–2:20** | Digita **`qual a previsão do tempo?`** | "Não entendi a pergunta. Tente reformular." com duas perguntas de exemplo clicáveis. ([tela](telas/4_fora_do_dominio.png)) | "E uma pergunta fora do assunto. Ele não inventa: pede para reformular e sugere o que dá para perguntar." |
| **2:20–3:05** | Clica **Importar dados** no menu → **Escolher arquivo** → `Empresa_B_Papelaria_Traco_Fino.xlsx` → **Enviar para análise** → **Fazer perguntas sobre esses dados**. Digita **`quanto vendi em outubro?`** | Relatório: "12 linhas foram aceitas · 13 linhas lidas · 1 linha ficou de fora: 1 × data inválida ou ausente" ([tela](telas/5_relatorio_empresa_B.png)). No chat, a faixa "Respondendo sobre Empresa_B_Papelaria_Traco_Fino.xlsx" e **R$ 600,00**. | "Agora uma segunda empresa, uma papelaria. Deixamos de propósito uma linha sem data: ele aceita as outras doze e diz exatamente qual problema deixou uma de fora. [no chat] A mesma pergunta de antes: quanto vendi em outubro? Seiscentos reais. Mesma pergunta, outra empresa, outro número: cada empresa só enxerga os próprios dados." |
| **3:05–3:30** | Volta para os slides (QR code). | — | "Quem quiser acompanhar, o QR code leva ao sistema publicado, e o código e a documentação estão no GitHub. A Amanda agora apresenta os resultados que medimos." |

**Se estiver atrasado, cortem nesta ordem:** (1) a previsão do tempo, já explicada no
slide 13; (2) o "e em setembro?". **Não cortem** a conferência do ticket nem a segunda
empresa: são os dois pedidos centrais do parecer.

**Se der tempo sobrando** (só se sobrar): clicar em **Início** com a Empresa B ativa. O
painel mostra os indicadores do mês sem digitar nada ([exemplo com a A](telas/8_inicio_empresa_A.png)).

**Se algo falhar ao vivo:**
- Resposta demorando mais de 10 s: "o servidor gratuito está acordando", esperem uma
  vez. Se não vier, vão para o vídeo sem pedir desculpas.
- Pergunta recusada por erro de digitação: o operador apaga e digita de novo, sem
  comentário.

### 3.3 Gabarito das perguntas (testadas)

Todas foram feitas na interface e na API com as duas planilhas importadas.

**Empresa A, Loja Estação Moda**

| Pergunta | Resposta do Intellix | Conferência na planilha |
|---|---|---|
| quanto vendi em outubro? | R$ 1.000,00 | 300 + 200 + 200 + 200 + 100 |
| e em setembro? *(logo depois da anterior)* | R$ 800,00 | 200 + 250 + 300 + 50 |
| qual foi o ticket médio em outubro? | R$ 200,00 | 1.000 ÷ 5 vendas (A-201 a A-205) |
| qual o ticket médio de setembro? | R$ 200,00 | 800 ÷ 4 vendas |
| quantas vendas fiz em outubro? | 5 | A-201 a A-205 |
| quantas peças vendi em outubro? | 12 | soma da coluna quantidade em outubro |
| quais os 3 produtos mais vendidos em outubro? | Camiseta básica R$ 350 (7 un.) · Tênis casual R$ 220 · Jaqueta R$ 200 | aba Conferência, "por produto" |
| quanto vendi de camiseta em outubro? | R$ 350,00 | 50 + 200 + 100 |
| quantas camisetas vendi em outubro? | 7 | 1 + 4 + 2 |
| quanto cresci em outubro em relação a setembro? | +25% (R$ 1.000 vs R$ 800) | 1.000 ÷ 800 − 1 |
| vendas por canal em outubro | loja R$ 600 (3) · site R$ 200 (1) · whatsapp R$ 200 (1) | aba Conferência, "por canal" |
| vendas por forma de pagamento em outubro | pix R$ 500 · crédito R$ 200 · dinheiro R$ 200 · débito R$ 100 | — |
| como foi o desempenho da Bruna em outubro? | R$ 600,00 em 3 vendas | A-201, A-203, A-205 |
| e o Diego? *(logo depois da anterior)* | R$ 400,00 em 2 vendas | A-202, A-204 |
| qual vendedor vendeu mais em outubro? | Bruna R$ 600 · Diego R$ 400 | — |
| qual categoria vendeu mais em outubro? | Vestuário R$ 700 · Calçados R$ 220 · Acessórios R$ 80 | — |
| quanto vendi no pix em outubro? | R$ 500,00 | A-201 + A-202 |
| qual mês vendeu mais em 2026? | outubro de 2026, R$ 1.000 | — |
| como foi o desempenho do vendedor? | "Quase lá — só preciso saber sobre qual vendedor(a)?" | falta parâmetro |
| quanto vendi em janeiro? | "Não há registros para o período ou filtro informado." | não há venda em janeiro |
| qual a previsão do tempo? | "Não entendi a pergunta. Tente reformular." | fora do domínio |

**Empresa B, Papelaria Traço Fino**

| Pergunta | Resposta do Intellix | Conferência |
|---|---|---|
| quanto vendi em outubro? | R$ 600,00 | 180 + 150 + 150 + 120 |
| quanto vendi em setembro? | R$ 450,00 | 150 + 150 + 150 |
| qual foi o ticket médio em outubro? | R$ 150,00 | 600 ÷ 4 vendas |
| quais os produtos mais vendidos em outubro? | Caderno universitário R$ 270 (9 un.) · Mochila escolar R$ 240 · Caneta gel R$ 60 · Estojo R$ 30 | — |
| quantos cadernos vendi em outubro? | 9 | 2 + 3 + 4 |
| como foi o desempenho da Marina em outubro? | R$ 270,00 em 2 vendas | B-12, B-14 |
| quanto cresci em outubro em relação a setembro? | +33,33% | 600 ÷ 450 − 1 |

**Não usem na demo (falham ou enganam):**

| Pergunta | O que acontece | Use no lugar |
|---|---|---|
| compare setembro e outubro | recusa (baixa confiança) | quanto cresci em outubro em relação a setembro? |
| qual foi o faturamento em outubro **de 2026**? | pede "qual vendedor" (intenção errada) | qual o faturamento de outubro? |
| quanto vendi de mochila em outubro? *(B)* | recusa | quanto vendi de caderno universitário em outubro? |
| quanto vendi ontem? / faturamento da semana | **responde o ano inteiro** (R$ 1.800 na A) | sempre citar mês ou ano |
| quanto a loja faturou em outubro? | responde o total (R$ 1.000) e não só o canal "loja" | vendas por canal em outubro |

### 3.4 Ensaio na véspera, no sistema publicado

1. Logar com a conta da demo, importar a A, fazer as 5 perguntas da tabela 3.2 e
   conferir os números com a seção 3.3. Importar a B e conferir R$ 600.
2. Se algum número não bater, avisem: pode ser que a versão publicada não seja a do
   `main` testada aqui.
3. **Excluir as duas planilhas da conta da demo** no fim, para começar limpa no dia.
4. Gravar o vídeo de plano B nesse ensaio.

---

## 4. Kit da arguição

### 4.1 O que o parecer sugere que a banca peça, e como mostrar

| Pedido do parecer (seção 5) | Como mostrar | O que deve aparecer |
|---|---|---|
| Importar planilha sintética em duas empresas | Já feito na demo | A: 14 aceitas, 1 somada · B: 12 aceitas, 1 fora |
| Pergunta inédita, conferir total e ticket à mão | Já feito na demo. Se pedirem para ver o cálculo, abrir a aba **Conferência** do Excel | Faturamento, nº de vendas e ticket calculados pelo Excel |
| Pergunta ambígua | `como foi o desempenho da Bruna em outubro?` e depois `e o Diego?` | Ele entende que "e o Diego?" é a mesma pergunta para outro vendedor: R$ 400 em 2 vendas |
| Retorno vazio × falta de parâmetro | `quanto vendi em janeiro?` e depois `como foi o desempenho do vendedor?` ([tela](telas/6_vazio_x_falta_parametro.png)) | Vazio: "Não há registros para o período" (entendeu, mas não há dado). Falta: "Quase lá — só preciso saber sobre qual vendedor(a)?" (faltou informação na pergunta) |
| Recuperação do histórico | Barra lateral → **Histórico** → clicar numa conversa anterior | A conversa reabre com as respostas. O histórico fica salvo na conta (migração 008) |
| Isolamento sem contas reais | Na **segunda conta de teste**: abrir *Importar dados* | "Você ainda não importou nenhuma planilha": a outra conta não vê a A nem a B |
| (complemento técnico) | Testamos também forçar o identificador da Empresa A estando logado na outra conta ([tela](telas/7_outro_usuario_bloqueado.png)) | O servidor responde "Não encontrei esses dados". Mesma resposta para "não existe" e "não é seu", de propósito, para não revelar quais empresas existem. No banco, o `scripts/demo_isolamento.py` confere 6/6 passos (RLS nega por padrão, A não vê B, o usuário do app não apaga vendas) |
| Versão do código e hash do modelo | Abrir `docs/evidencias/manifesto_reproducao_*.md` | Modelo `intellix_nlu_v1.2.0.pt`, SHA-256 `ea30338e9626f4b6…`; fingerprint do dataset `58d126cf…`. **Gerem um manifesto novo no commit publicado** antes da defesa (`python scripts/manifesto_reproducao.py`), porque o último foi gerado num commit anterior |
| Separar a medição conhecida do resultado da pergunta nova | Falar | "As 88 de 100 são regressão no repertório que guiou as correções. O que acabamos de ver é uma pergunta nova, numa base nova, com valor conferido à mão." |

**Se a banca ditar uma pergunta própria:** o operador digita exatamente o que foi
dito.
- Se responder, confiram o número na aba Conferência, na frente da banca.
- Se recusar, digam: *"Esse é o comportamento projetado: abaixo de 70% de confiança ele
  recusa em vez de arriscar um número errado. Em perguntas inéditas, medimos 27 de 30
  num conjunto representativo e 18 de 30 num conjunto feito para ser difícil. A
  formulação que ele conhece seria..."* e reformulem num formato da seção 3.3.

### 4.2 Respostas para as 6 perguntas do parecer (seção 5)

**1. O que 88 de 100 comprova?** *(Amanda)*
Comprova que, nessas 100 perguntas, o sistema devolve o tipo de resposta e o estado
esperados. Não comprova generalização, porque as mesmas perguntas guiaram as correções.
Por isso fizemos mais três medições: (a) **gabarito numérico**: as 14 consultas
conferidas valor a valor contra um cálculo independente em Python, **19/19**; (b)
**perguntas inéditas**, fora dos moldes e das 100: **27/30** no conjunto representativo
(intervalo de confiança de 95%: 74% a 97%) e **18/30** no adversarial (42% a 75%); (c)
a conferência à mão que acabamos de mostrar.

**2. Por que o modelo final foi escolhido se a acurácia no conjunto manual foi menor?**
*(Maria Luiza)*
No teste manual de 120 frases, a v1.0.0 fez 93,3% e a v1.2.0 fez 88,3%. Sete dessas
frases acabaram entrando no treino da v1.2.0. Tirando as sete, ela faz 88,5%, então a
sobreposição não inflou o resultado. Escolhemos a v1.2.0 porque o objetivo é o agente
inteiro, não o modelo isolado. Os moldes novos foram escritos a partir das frases que a
versão anterior recusava na interface, como "mês passado", "quantas peças" e "qual mês
vendeu mais". Com isso, da v1.1.0 para a v1.2.0, o NLU foi de 77 para 83 acertos nas 100
perguntas, e de 30 para 37 nas 40 perguntas de detalhe. As duas versões ficam acima da meta de 85%. Sobre o
F1: o 0,838 da v1.0.0 cai para 0,803 quando reavaliado com as anotações revisadas. A
v1.2.0 tem 0,831 na mesma régua.

**3. Que função a cabeça de entidades exerce?** *(Maria Luiza)*
Ela marca os trechos da frase, como "camiseta branca" ou "abril". Depois, as regras
convertem esses trechos em valores do cadastro e em datas. Fomos honestos na ablação:
na v1.2.0, com corpus externo e conferência de valor, tirar a cabeça BIO **não mudou**
nenhum acerto (+0), porque período e limite são resolvidos por regras e o vendedor por
uma heurística. Mantivemos a cabeça por finalidade de pesquisa e robustez, não por ganho
operacional demonstrado. O custo do filtro de domínio também foi medido: ele barrou 7 de
8 paráfrases válidas sem palavras típicas de vendas. É o preço de nunca responder fora
do assunto.

**4. Como tratar duas linhas da mesma venda para o mesmo produto?** *(Erik, com a demo)*
Elas viram um item só, com quantidade e valor somados. A chave é (empresa, venda,
produto). A tela avisa quantas linhas foram somadas. A venda A-203 da Empresa A tem
exatamente isso: duas linhas de "Camiseta básica" com 2 unidades cada viram 1 item com 4
unidades e R$ 200. O ticket conta a venda uma vez. Há um teste automatizado de
reconciliação (`test_reconciliacao_carga.py`): vendas, itens, faturamento, ticket,
nenhuma linha órfã e reimportação sem duplicar.

**5. O que muda com o limitador ativo e a instância fria?** *(Erik)*
Refizemos o teste em configuração normal. Com o limitador ligado (30 perguntas por
minuto por IP), um disparo de 35 perguntas teve 30 respostas normais e 5 bloqueadas
(429). No caminho da aplicação, a primeira pergunta levou 55 ms e as seguintes, 17 ms de
mediana. A hibernação do Render (cerca de 30 s) é da hospedagem gratuita e não se
reproduz localmente. Por isso não prometemos nível de serviço nem vazão.

**6. Como a banca reproduz a versão publicada?** *(Erik)*
O `REPRODUZIR.md` tem comando a comando, com o resultado esperado ao lado. O manifesto
traz o commit, o SHA-256 dos pesos, o fingerprint do dataset e o hash das migrações e
dos templates. *(Antes da defesa: garantir que a banca tenha acesso ao repositório. O
parecer diz que não conseguiu recuperá-lo.)*

### 4.3 Os "[completar]" do roteiro que são da Maria Luiza

Preenchidos com o que está no repositório. Confiram com a monografia antes de usar.

**Pergunta 7 (testaram algum Transformer?):** não encontrei no repositório nenhum
experimento com Transformer. **Confirmem com a equipe.** Se não houve, a resposta
honesta é: "Não testamos. Descartamos pelo tamanho, e comparar com um Transformer
pequeno é continuidade."

**Pergunta 8 (como as 4.800 frases foram criadas):** a equipe escreveu cerca de 200
moldes de frase (15 a 20 por intenção, cada integrante com 3 intenções), por exemplo
"quanto faturei em {periodo}". O gerador (`ia training/gerar_dataset.py`) sorteia
valores para os espaços e já marca as etiquetas BIO sozinho. Um validador confere as
etiquetas. As intenções foram balanceadas em 400 exemplos cada (12 × 400 = 4.800),
porque moldes com dois espaços geravam muito mais frases e desequilibravam o treino. A
divisão é 70% treino, 15% validação e 15% teste, estratificada por intenção (semente
42). Separado disso, o **teste manual** tem 120 frases (10 por intenção), escritas à mão
sem olhar os moldes, pré-etiquetadas pelo `anotar.py` e revisadas.

**Pergunta 10 (por que 70%):** fizemos uma varredura. Com o limiar em 0,50, 0,60 ou
0,70, o sistema aceita 78 de 84 perguntas válidas e 0 de 12 fora do domínio. Em 0,80, cai
para 76 de 84 válidas. Ou seja, 0,70 é o valor mais alto que não perde nenhuma pergunta
válida. É o lado conservador. *(Evidência: `docs/evidencias/confianca_filtro_2026-11-05_1044.md`.)*

**Pergunta 12 (intenções com F1 mais baixo):** as confusões se concentram onde o
vocabulário é parecido: `vendas_por_pagamento`; `comparacao_periodos` × `variacao_periodo`
× `total_vendas_periodo`; e `vendas_por_categoria`/`vendas_por_canal` × `top_produtos`
("quais categorias mais venderam"). *(Fonte: `docs/avaliacao-100-perguntas.md`. Conferir
o F1 por intenção na monografia.)*

**Pergunta 13 (vazamento entre treino e teste):** a divisão 70/15/15 é estratificada,
mas frases do mesmo molde podem cair no treino e no teste. Por isso o teste sintético
(99,6%) é otimista e não é o número que reportamos. Reportamos o teste manual, escrito
fora dos moldes. Nele, 7 das 120 frases coincidiram com o treino da v1.2.0, e o
resultado sem elas é 88,5%. Para generalização de verdade, o número é o das perguntas
inéditas (27/30 e 18/30).

---

*Testes executados em 19/11/2026 num ambiente local com o commit `bd34783` do `main`,
modelo v1.2.0 e o banco de demonstração (`SEED=42`).*
