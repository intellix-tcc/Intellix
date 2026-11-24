# Intellix · Ferramentas, tecnologias e métodos

**Por que usamos cada coisa, e como usamos.** Material para responder às perguntas do tipo
"por que vocês escolheram essa ferramenta?".

**Como responder a um "por quê?" em 20 segundos.** Use sempre a mesma ordem:
**(1) o problema** que precisávamos resolver → **(2) a escolha** → **(3) o benefício** →
**(4) a alternativa** e por que não → **(5) a limitação**, se houver.
Exemplo: "Precisávamos hospedar o modelo de graça (problema). Escolhemos o Render (escolha),
porque o plano gratuito não expira e publica sozinho a cada envio ao GitHub (benefício). O
Railway expira por crédito (alternativa). O preço é a hibernação de 30 segundos (limitação)."

**De onde vêm as justificativas.** Quatro decisões foram registradas formalmente pela equipe,
como ADRs (*Architecture Decision Records*, em `docs/decisoes/`): esquema estrela, Supabase,
Render e arquitetura em camadas. Para as demais ferramentas, as justificativas abaixo são
técnicas e coerentes com o código do projeto (versões conferidas em `backend/requirements.txt`
e `frontend/package.json`).

---

## 1. A pilha em uma tabela

| Camada | Ferramenta | Por que, em uma linha |
|---|---|---|
| Linguagem | **Python 3.12** | Mesma linguagem para o modelo, a API e os scripts |
| Modelo de IA | **PyTorch** | Montar uma rede sob medida (BiLSTM com duas cabeças), leve em CPU |
| Treino | **Google Colab** | GPU gratuita e notebook compartilhável para a primeira versão |
| Métricas | **scikit-learn** e **seqeval** | Métricas padrão; o seqeval mede entidades do jeito certo |
| API | **FastAPI** + **Uvicorn** | Python, validação automática e documentação automática |
| Validação | **Pydantic** | Recusar dados malformados antes de chegarem ao código |
| Acesso ao banco | **psycopg 3** + pool | Consultas parametrizadas e conexões reaproveitadas |
| Planilhas (servidor) | **openpyxl** | Ler `.xlsx` em fluxo, sem estourar a memória |
| Login (servidor) | **PyJWT** | Conferir a assinatura do token do Supabase |
| Banco | **PostgreSQL** | Relacional, ótimo para análise, com segurança por linha (RLS) |
| Banco gerenciado + login | **Supabase** | PostgreSQL e autenticação gratuitos, sem prender a solução |
| Modelo de dados | **Esquema estrela** | Consultas analíticas simples e rápidas |
| Interface | **React** + **Vite** | Componentes reutilizáveis e build rápido |
| Gráficos | **Recharts** | Gráficos declarativos feitos para React |
| Excel e PDF | **SheetJS** e **jsPDF** | Ler e gerar arquivos no navegador, sem pesar no servidor |
| Hospedagem da API | **Render** | Plano gratuito que não expira e deploy automático |
| Hospedagem da interface | **Vercel** | Gratuito para sites estáticos, com cabeçalhos de segurança |
| Código e processo | **GitHub**, **Actions**, **Projects** | Versionamento, testes automáticos e Kanban |
| Testes e qualidade | **pytest**, **Ruff**, **ESLint** | Testes automáticos e padrão de código |
| Diagramas | **Graphviz**, **matplotlib**, **draw.io** | Diagramas gerados a partir de arquivos versionados |

---

## 2. O modelo de IA

### Python
**O que é.** A linguagem de programação principal do projeto.

**Por que.** É a linguagem padrão de aprendizado de máquina (PyTorch, scikit-learn) e também
tem um bom framework web (FastAPI). Usar a mesma linguagem no treino e no servidor permite que
o servidor carregue o modelo direto, no mesmo processo, e que **a mesma função de tokenização**
seja usada no treino e em produção (se divergisse, o modelo funcionaria nos testes e falharia
em produção).

**Como usamos.** Treino, API, importação de planilhas, scripts de avaliação e de reprodução.
Versão 3.12 no Render e no CI.

### PyTorch
**O que é.** Biblioteca de redes neurais.

**Por que.** Precisávamos de uma rede **sob medida**: uma BiLSTM com **duas saídas** ao mesmo
tempo (intenção da frase e etiqueta de cada palavra), com uma média que ignora o
preenchimento. O PyTorch deixa montar essa arquitetura em poucas linhas, roda bem em CPU (o
servidor gratuito não tem GPU) e salva tudo num arquivo só.

**Como usamos.** A classe `ModeloNLU` define a rede; o treino usa o otimizador Adam; o
arquivo `.pt` guarda os pesos junto com o vocabulário, os rótulos e a configuração, para o
servidor recriar a rede exatamente igual. No servidor, o modelo é carregado uma vez, na
inicialização.

**Alternativas.** TensorFlow/Keras faria o mesmo. O PyTorch foi escolhido pela flexibilidade
para a arquitetura com duas cabeças e por ser o mais usado em pesquisa.

### Google Colab
**O que é.** Ambiente de notebooks Python no navegador, com GPU gratuita.

**Por que.** Para a primeira versão (v1.0.0) o treino com GPU foi mais rápido, e o notebook
deixa código, gráficos de treino e matriz de confusão num documento só, fácil de
compartilhar com a equipe e a orientadora.

**Como usamos.** O notebook `Intellix_NLU_Colab.ipynb` treinou a v1.0.0. As versões seguintes
(v1.1.0 e v1.2.0) foram treinadas localmente, em CPU, com o `treinar.py`, que reproduz o
notebook com os mesmos hiperparâmetros. O modelo é pequeno o bastante para treinar em CPU.

### BiLSTM (rede LSTM bidirecional)
**O que é.** Rede neural que lê a frase palavra por palavra, guardando uma memória, nos dois
sentidos (do começo para o fim e do fim para o começo).

**Por que.** As perguntas são **frases curtas** (7,3 palavras em média) e o sentido de cada
palavra depende das vizinhas dos dois lados. A BiLSTM captura isso com **288.987 parâmetros
(1,17 MB)**, cabe no servidor gratuito e responde em 1,72 ms.

**Alternativas.** Um **Transformer (BERT)** tem centenas de milhões de parâmetros e não caberia
nos 512 MB do Render gratuito. Um **LLM** traria custo por pergunta, dados enviados a
terceiros e respostas imprevisíveis. **Só regras** (sem rede) acertaram 25,6% contra 74,4% do
modelo. Não testamos Transformer, e isso é continuidade.

### Embeddings
**O que é.** Cada palavra vira um vetor de 100 números, aprendido no treino.

**Por que.** A rede não entende texto, só números. Com embeddings, palavras usadas de forma
parecida ficam com vetores parecidos.

**Como usamos.** Vocabulário montado só com o treino (palavras que aparecem pelo menos 2
vezes; o resto vira "desconhecida"). 455 palavras na v1.2.0.

### Esquema BIO
**O que é.** Uma etiqueta por palavra: **B** (começa um detalhe), **I** (continua), **O** (fora).

**Por que.** É o padrão para marcar entidades em sequência, e separa onde cada entidade começa
e termina: "camiseta branca" é **um** produto (B, I), não dois.

**Como usamos.** 9 tipos de entidade → 19 etiquetas. No sistema, as etiquetas indicam o nome do
vendedor e os trechos de produto, canal e pagamento, que são conferidos no cadastro da empresa.
As datas são resolvidas por regras.

### Geração de dados por moldes
**O que é.** Em vez de escrever milhares de frases, escrevemos **moldes** com espaços ("quanto
faturei em {período}") e um gerador preenche os valores.

**Por que.** Não existia um conjunto de perguntas de vendas em português, anotado com
intenção e entidades. Com moldes, o gerador **já marca as etiquetas sozinho**, sem anotação
manual, e é reprodutível (semente fixa).

**Como usamos.** 561 moldes (v1.2.0), 60 variações por molde, remoção de repetidas, remoção
das frases iguais às 100 perguntas de validação, e **balanceamento em 400 frases por
intenção** (4.800 no total).

**Limitação e como tratamos.** O modelo pode decorar os moldes. Por isso o resultado que vale é
o de um **teste manual de 120 frases escritas à mão**, sem olhar os moldes.

### Divisão estratificada, Adam, dropout e early stopping
- **Divisão estratificada:** cada parte (treino, validação, teste) mantém a mesma proporção de
  cada intenção, para nenhuma intenção ficar sub-representada.
- **Adam (taxa 0,001, lote 32):** otimizador padrão, que ajusta o passo sozinho e converge
  rápido.
- **Dropout de 30%:** desliga parte dos neurônios no treino para o modelo não decorar.
- **Early stopping (paciência 6):** para o treino quando a validação deixa de melhorar e volta
  aos melhores pesos. Evita treinar demais.
- **Corte de gradiente (5):** evita saltos instáveis, comuns em redes recorrentes.
- **Perda combinada (α = 0,5):** intenção e etiquetas pesam igual no treino.

### Limiar de confiança (70%)
**O que é.** A confiança mínima para aceitar a classificação. Abaixo disso, o sistema pede
para reformular.

**Por que.** É melhor pedir para reformular do que dar um número errado.

**Como escolhemos.** Varredura: com 50%, 60% ou 70%, o sistema aceitou 78 de 84 perguntas
válidas e 0 de 12 fora do assunto. Em 80%, caiu para 76. **70% foi o mais alto sem perder
pergunta válida.**

### scikit-learn e seqeval
**O que são.** Bibliotecas de métricas.

**Por que.** O **scikit-learn** é o padrão para acurácia, precisão, revocação, F1 e matriz de
confusão da intenção, e fez a divisão estratificada no notebook. O **seqeval** mede o F1 das
entidades **por entidade completa**: "camiseta branca" só conta como acerto se as duas
palavras estiverem certas. Medir por palavra inflaria o resultado.

### Regras determinísticas e catálogo (abordagem híbrida)
**O que é.** Código sem aprendizado que completa o modelo: converte "março" em datas, pega o
limite ("top 5"), reconhece o nome do vendedor, confere nomes no cadastro e aplica sinônimos do
domínio.

**Por que.** O que é **determinístico** (calendário, número, nome que existe no banco) fica mais
confiável e testável com regra do que com rede. Frase-resumo: **o modelo decide o quê, as
regras decidem como.**

---

## 3. O servidor (backend)

### FastAPI
**O que é.** Framework Python para criar APIs web.

**Por que.** (1) É **Python**, então o modelo roda no mesmo processo da API; (2) **valida os
dados automaticamente** (com Pydantic) a partir das definições de tipo; (3) **gera a
documentação da API sozinho** (o arquivo `docs/openapi.json` sai daí); (4) é rápido e simples.

**Como usamos.** 10 rotas: `/health`, `/capacidades`, `/chat`, `/resumo`, `/import`,
`/planilhas` (listar e excluir) e `/conversas` (listar, salvar e apagar).

**Alternativas.** Flask (não valida dados sozinho), Django (pesado demais para uma API), Node.js
(separaria a linguagem da API da linguagem do modelo).

### Uvicorn
**O que é.** O servidor que executa a aplicação FastAPI e atende as conexões HTTP.

**Como usamos.** É o comando que sobe a API no Render e localmente.

### Pydantic
**O que é.** Biblioteca de validação de dados por tipos.

**Por que.** Barra dados malformados na entrada: pergunta vazia ou com mais de 500 caracteres,
contexto inválido reenviado pelo navegador. Também garante o formato da resposta (`ResultSet`),
que alimenta a tela, o Excel e o PDF.

### psycopg 3 e pool de conexões
**O que é.** O driver que liga o Python ao PostgreSQL.

**Por que.** (1) Faz **consultas parametrizadas**: os valores vão separados do texto do SQL, o
que impede SQL injection; (2) tem **pool de conexões**: abrir uma conexão nova custava cerca
de 1,1 s por pergunta no Render (o banco de produção fica nos EUA); o pool abre uma vez e
reaproveita.

**Detalhe técnico que pode cair.** O pooler do Supabase (porta 6543) não guarda *prepared
statements* entre transações, então o pool foi configurado com `prepare_threshold=None`.

### Templates SQL parametrizados
**O que é.** 14 consultas SQL **fixas**, escritas e testadas pela equipe, com lugares marcados
para os valores (`%(periodo_inicio)s`).

**Por que.** O texto do usuário **nunca vira SQL**. O modelo só escolhe qual consulta usar.
Isso dá **segurança** (sem SQL injection), **previsibilidade** (mesma pergunta, mesma
consulta) e **auditoria** (cada consulta fica registrada em `log_consulta`).

**Alternativa.** Text-to-SQL com LLM: mais flexível, mas o SQL gerado pode sair errado ou
inseguro sem ninguém perceber.

### openpyxl
**O que é.** Biblioteca para ler arquivos Excel no Python.

**Por que.** Ler a planilha no servidor **em fluxo** (linha a linha), com limite de 10 MB e 50
mil linhas, sem carregar tudo na memória dos 512 MB do servidor gratuito.

**Como usamos.** Só `.xlsx` (o `.xls` antigo é recusado com orientação para salvar como
`.xlsx`). As colunas são reconhecidas pelo nome, com sinônimos ("qtd", "preço").

### PyJWT
**O que é.** Biblioteca para conferir tokens JWT.

**Por que.** O login é do Supabase, mas a API precisa saber **quem** está pedindo. A cada
pedido, ela confere a assinatura, a validade e o papel do token, e tira dele o id do usuário
(nunca do pedido).

### Arquitetura em camadas, com porta e adaptadores (ADR 004)
**O que é.** Cada módulo com uma responsabilidade (entrada, interpretação, regras, consulta,
dados). O NLU tem uma "porta" (`parse(texto)`), com dois "adaptadores": regras e modelo.

**Por que.** O modelo ainda estava sendo treinado enquanto o resto do backend era construído.
Com a porta, trocamos **regras → modelo → nova versão** sem mexer no resto. Também deixou um
**plano B**: se o modelo falhar, `NLU_BACKEND=regras` no Render põe o sistema no ar.

### Limite de requisições (em memória)

**Por que.** Proteger o plano gratuito contra abuso e contra erros do próprio frontend.

**Como.** 30 perguntas por minuto por IP no `/chat`, 60 no `/resumo`, 10 importações por hora.
Em memória, sem Redis: o servidor roda num processo só, e um Redis seria infraestrutura a mais
para um protótipo.

---

## 4. Os dados

### PostgreSQL
**O que é.** Banco de dados relacional de código aberto.

**Por que.** Os dados de vendas são estruturados e as perguntas são agregações (somas,
contagens, rankings), o forte de um banco relacional. Ele também traz recursos que usamos:
**segurança por linha (RLS)**, **views materializadas**, colunas geradas, a extensão
`unaccent` (comparar nomes sem acento) e transações.

**Alternativas.** MySQL não tem RLS nativo. Um banco NoSQL (como MongoDB) é ruim para
agregações e junções analíticas.

### Supabase (ADR 002)
**O que é.** PostgreSQL gerenciado na nuvem, com autenticação pronta.

**Por que.** Plano **gratuito** real (até 500 MB), é **PostgreSQL puro** (dá para migrar para
outro provedor sem reescrever nada) e já traz **login** (cadastro, confirmação por e-mail,
recuperação de senha, hash das senhas).

**Como usamos.** Dois projetos: desenvolvimento (São Paulo) e produção (Oregon, EUA; a região
não pode ser trocada depois de criada). A API conecta pelo pooler (porta 6543). A senha nunca
passa pelo nosso servidor.

### Esquema estrela (ADR 001)
**O que é.** Uma tabela de fatos no centro (`fato_item_venda`, um item por linha) cercada de
dimensões (data, produto, cliente, vendedor).

**Por que.** É o modelo clássico para análise (Kimball e Ross): **menos junções**, consultas
mais rápidas e templates mais simples. O grão de item preserva "produtos mais vendidos" e "por
categoria".

**Alternativa.** O modelo normalizado (3ª forma normal) é melhor para cadastro e transações, mas
exige muitas junções nas consultas analíticas.

### Views materializadas
**O que é.** Resultados de consultas já calculados e guardados (faturamento mensal, ranking de
produtos, desempenho por vendedor).

**Por que.** Respostas mais rápidas, ajudando na meta de menos de 3 segundos. São atualizadas
depois de cada importação.

### RLS e usuário com privilégio mínimo
**O que é.** Regras do próprio banco que só devolvem as linhas da empresa declarada na
transação. O usuário da aplicação (`intellix_app`) não tem permissão de apagar vendas.

**Por que.** **Defesa em profundidade:** mesmo que houvesse um erro no código da API, o banco não
entregaria dados de outra empresa. Provado com duas empresas fictícias (6 de 6 verificações).

### Migrações versionadas e seed determinístico
- **Migrações** (`001` a `008`): cada mudança no banco é um arquivo no GitHub, aplicado em ordem.
  Qualquer pessoa recria o banco do zero, e o CI faz isso a cada mudança.
- **Seed** (semente 42): a base de demonstração (3.527 vendas, 8.941 itens, R$ 2.717.797,23) é
  sempre idêntica. Isso permite comparar versões e conferir valores à mão.

---

## 5. A interface (frontend)

### React
**O que é.** Biblioteca JavaScript para montar interfaces com componentes.

**Por que.** O chat, o painel e a importação mudam o tempo todo conforme o estado (mensagens,
carregando, erro). O React organiza isso em **componentes reutilizáveis** (gráfico, resposta,
cartão de indicador). É o mais usado do mercado, com muito material e bibliotecas.

**Alternativas.** Angular (mais pesado e verboso), Vue (também serviria; o React tem mais
bibliotecas de gráfico prontas).

### Vite
**O que é.** Ferramenta que roda o site em desenvolvimento e gera a versão final.

**Por que.** Recarrega na hora durante o desenvolvimento e gera arquivos pequenos e otimizados
para a Vercel. É o padrão atual para projetos React (o antigo Create React App foi abandonado).

### Recharts
**O que é.** Biblioteca de gráficos para React.

**Por que.** Gráficos **declarativos** (descreve-se o gráfico como um componente) e já
integrados ao React: barras, rosca, linha, evolução mensal com média e destaque do mês.

### SheetJS (xlsx) e jsPDF
**O que são.** Bibliotecas para ler e gerar Excel (SheetJS) e PDF (jsPDF) no navegador.

**Por que.** Tudo acontece **no navegador**, e não no servidor, porque o servidor gratuito tem
256–512 MB e o modelo já ocupa boa parte. O SheetJS também deixa a interface **conferir a
planilha antes de enviar** (colunas, arquivo corrompido), para a pessoa não descobrir o erro
depois.

---

## 6. Infraestrutura e processo

### Render (ADR 003)
**O que é.** Plataforma de hospedagem de aplicações.

**Por que.** O plano **gratuito não expira** (o do Railway expira por consumo de crédito) e faz
**deploy automático** a cada envio ao GitHub.

**Limitações.** Hiberna depois de cerca de 15 minutos sem uso, e a primeira resposta leva cerca de
30 s (por isso o `scripts/aquecer.sh`, rodado antes da banca); RAM de 256–512 MB, o que
favoreceu o modelo leve.

### Vercel
**O que é.** Hospedagem de sites estáticos.

**Por que.** Gratuita, deploy automático pelo GitHub, rede de distribuição global e cabeçalhos
de segurança configuráveis (Content-Security-Policy, X-Frame-Options, HSTS) no `vercel.json`.

### GitHub, GitHub Actions e GitHub Projects
- **GitHub:** versionamento do código, das migrações, dos diagramas e das evidências; pull
  requests revisados.
- **GitHub Actions (CI):** a cada pull request, roda o **Ruff** (padrão de código) e o **pytest**
  contra um **PostgreSQL 16 temporário**, com as migrações, a base de demonstração e o **mesmo
  modelo treinado** de produção. Erro aparece antes de publicar.
- **GitHub Projects (Kanban):** gestão das tarefas em quatro frentes: modelo, API, dados e
  infraestrutura, interface e documentação.

### pytest, Ruff e ESLint
- **pytest:** 202 testes automatizados do backend.
- **Ruff:** confere o padrão do código Python (rápido, substitui várias ferramentas).
- **ESLint:** confere o padrão do código da interface.

### ADRs (registros de decisão)
**O que é.** Um documento curto por decisão importante: contexto, decisão, justificativa e
consequências.

**Por que.** Para que as escolhas (e os motivos) não se percam, e qualquer pessoa entenda o
"porquê" depois. Há quatro: esquema estrela, Supabase, Render e arquitetura em camadas.

### Graphviz, matplotlib e draw.io

**Por que.** Os diagramas do TCC (casos de uso, classes, sequência, entidade-relacionamento,
fluxograma, arquitetura) são **gerados a partir de arquivos de texto versionados**. Quando o
sistema muda, o diagrama é regerado e continua batendo com o código.

### Reprodução e manifesto

**Por que.** O parecer pediu um pacote de reprodução. O `REPRODUZIR.md` tem os comandos com o
resultado esperado, e o manifesto registra o commit, o hash dos pesos do modelo, o
fingerprint dos dados e os hashes das migrações.

---

## 7. Métodos de pesquisa e de avaliação

| Método | O que é | Por que usamos |
|---|---|---|
| **Pesquisa aplicada e experimental** (Gil, 2017) | Resolver um problema real, manipulando variáveis e medindo o efeito | Variamos versões do modelo, regras e limiar, e medimos acurácia, F1, acerto e tempo |
| **Teste manual** | 120 frases escritas à mão, sem olhar os moldes | Medir o modelo em frases que ele não viu, não só nos moldes |
| **100 perguntas de validação** | Bateria fixa, rodada contra a API inteira | Medir o sistema de ponta a ponta e servir de teste de regressão |
| **Perguntas inéditas** com intervalo de Wilson | Conjuntos novos, com gabarito de valor | Medir generalização com honestidade sobre o tamanho da amostra |
| **Gabarito numérico** | Cálculo independente em Python dos 14 tipos de consulta | Provar que o valor está certo, não só o tipo de resposta |
| **Ablação** | Tirar uma parte e medir de novo | Saber o quanto cada parte (como a cabeça de entidades) contribui |
| **Varredura do limiar** | Testar vários valores de confiança mínima | Justificar os 70% com dados |

---

## 8. Perguntas e respostas sobre as ferramentas

**Por que Python?**
É a linguagem do aprendizado de máquina e também tem um bom framework web. Assim, o modelo e a
API ficam na mesma linguagem e a mesma tokenização é usada no treino e em produção.

**Por que PyTorch e não TensorFlow?**
Precisávamos de uma rede sob medida, com duas saídas ao mesmo tempo. O PyTorch monta isso de
forma simples e roda bem em CPU. O TensorFlow também serviria.

**Por que treinar no Colab?**
GPU gratuita e notebook fácil de compartilhar na primeira versão. As versões seguintes
treinamos no próprio computador, porque o modelo é pequeno.

**Por que FastAPI?**
É Python (o modelo roda junto), valida os dados sozinho e gera a documentação da API
automaticamente. O Flask não valida, e o Django é pesado demais para uma API.

**Por que PostgreSQL?**
Os dados são estruturados e as perguntas são somas e rankings, o forte de um banco relacional.
E ele tem segurança por linha, que usamos para isolar as empresas.

**Por que Supabase?**
PostgreSQL e login gratuitos, e PostgreSQL puro: dá para mudar de provedor sem reescrever nada.

**Por que esquema estrela?**
As consultas são analíticas. Com o esquema estrela há menos junções e as consultas ficam mais
simples e rápidas.

**Por que consultas fixas (templates) e não deixar a IA gerar o SQL?**
Segurança, previsibilidade e auditoria. O texto do usuário nunca vira SQL: o modelo só escolhe a
consulta pronta.

**Por que Render e não AWS?**
Precisávamos de custo zero. O Render é gratuito sem expirar e publica sozinho a cada envio ao
GitHub. Na AWS, o gratuito é limitado no tempo e a configuração é bem mais trabalhosa.

**Por que React?**
A interface muda muito conforme o estado (chat, carregando, erro). O React organiza isso em
componentes reutilizáveis, e é o mais usado do mercado.

**Por que gerar Excel e PDF no navegador?**
O servidor gratuito tem pouca memória e o modelo já ocupa boa parte. No navegador, não pesa.

**Por que um pool de conexões?**
Abrir uma conexão nova custava cerca de 1,1 s por pergunta. O pool abre uma vez e reaproveita.

**Por que limitar as requisições?**
Para proteger o plano gratuito de abuso e de erros do próprio sistema: 30 perguntas por minuto
por pessoa.

**Por que RLS, se a API já confere o dono?**
Defesa em profundidade: mesmo que houvesse um erro na API, o banco não entregaria dados de outra
empresa.

**Por que arquitetura em camadas?**
Para trocar o interpretador (regras → modelo → nova versão) sem mexer no resto do sistema. E
deixa um plano B: se o modelo falhar, as regras assumem.

**Por que GitHub Actions?**
A cada mudança, os testes rodam sozinhos num banco temporário, com o mesmo modelo de produção.
Erro aparece antes de publicar.

**Por que gerar dados com moldes e não usar dados reais?**
Não existia um conjunto de perguntas de vendas em português anotado. Os moldes geram e anotam
sozinhos. Para não enganar, medimos num teste escrito à mão.

**Por que BiLSTM e não BERT ou um LLM?**
O BERT não cabe no servidor gratuito, e o LLM cobra por pergunta e manda os dados para fora.
Com frases curtas, a BiLSTM bateu as metas com 289 mil parâmetros.

---

## 9. Resumo rápido dos testes

| Teste | Tamanho | Resultado |
|---|---|---|
| Frases de treino geradas | 4.800 (400 por intenção) | Divisão v1.0.0: 3.360 / 720 / 720 |
| Teste sintético (v1.0.0) | 720 frases | 99,6% (otimista) |
| **Teste manual** | **120 frases** | v1.0.0 **93,3%** · v1.2.0 **88,3%** |
| Entidades (F1) | as mesmas 120 | 0,803 → **0,831** |
| Perguntas de detalhe | 40 | 30 → **37** |
| Varredura do limiar | 96 (84 válidas + 12 fora) | 78/84 aceitas · 0/12 aceitas |
| **100 perguntas de validação** | **100** | 58 → 83 → 88 → **90** |
| Inéditas, conjunto realista | 30 | **27/30** |
| Inéditas, conjunto difícil | 30 | 13 → **18/30** |
| Gabarito numérico | 14 consultas, 19 conferências | **19/19** |
| Ablação v1.1.0 / v1.2.0 | 84 / 24 perguntas | modelo 84,5% × regras 20,2% / entidades +0 |
| **Testes automatizados** | **202** | 198 aprovados + 4 de RLS à parte, todos aprovados |
| Isolamento entre empresas | 6 passos | **6/6** |
| Carga | 200 pedidos, 20 usuários / 35 em rajada | p95 2,3 s / 30 ok e 5 bloqueados |
| Tempo de resposta | 100 perguntas | média 0,63 s · p95 1,42 s |
| Backup e restauração | 9 tabelas | contagens idênticas |

---

## 10. Perguntas e respostas sobre os testes

**Quais testes vocês fizeram?**
Três níveis: o **modelo sozinho** (teste manual de 120 frases), o **sistema inteiro** (100
perguntas, perguntas inéditas e gabarito numérico) e o **código** (202 testes automatizados,
isolamento, carga e backup).

**O que é o teste manual?**
120 frases (10 por intenção) escritas à mão, sem olhar os moldes, e de propósito "tortas": sem
acento, com gíria e abreviação. A v1.0.0 acertou 93,3%, e a v1.2.0, 88,3%.

**Por que não usar o teste sintético, com 99,6%?**
Porque as frases saem dos mesmos moldes do treino, e o modelo reconhece o molde. É otimista.

**O que são as 100 perguntas?**
Uma bateria fixa contra o sistema inteiro: 84 por intenção, 6 fora do assunto, 5 sem parâmetro e
5 sem resultado. Começou em 58 e chegou a 90.

**Os 90 de 100 provam generalização?**
Não, porque as mesmas perguntas guiaram as correções. Por isso fizemos perguntas inéditas: 27 de
30 num conjunto realista e 18 de 30 num conjunto difícil.

**O que é o intervalo de Wilson?**
Uma margem de erro para porcentagens em amostras pequenas. Com 30 perguntas, 27 acertos (90%)
significam algo entre 74% e 97%. Mostramos o intervalo para não exagerar a precisão.

**Como vocês sabem que o valor está certo?**
O gabarito numérico recalcula os 14 tipos de consulta de forma independente, em Python, e compara
com o sistema: 19 de 19 corretos.

**O que são os testes automatizados?**
202 programas que verificam o sistema sozinhos a cada mudança de código: entendimento da
pergunta, consultas, valores, importação e segurança. Todos passaram.

**O que é a ablação?**
Tirar uma parte do sistema e medir de novo. Mostrou que o modelo é essencial (84,5% contra 20,2%
só com regras) e que a cabeça de entidades acrescentou +0 no valor final.

**Como provaram o isolamento entre empresas?**
Com duas empresas fictícias: o banco nega por padrão, a empresa A só vê A, pedir B devolve zero,
o app não apaga vendas e a auditoria fica separada. 6 de 6 verificações.

**E o teste de carga?**
200 pedidos com 20 usuários ao mesmo tempo: 95% abaixo de 2,3 s. Em operação normal, o limite de
30 por minuto bloqueou 5 de 35 pedidos em rajada, como esperado. Não prometemos nível de serviço,
porque a hospedagem é gratuita.

**Qual teste mostra a maior limitação?**
As inéditas do conjunto difícil (18 de 30). Quando o sistema não entende, na maioria das vezes
recusa em vez de errar. Testar com perguntas de pessoas de fora é o próximo passo.
