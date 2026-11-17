# Blocos de texto para o TCC — correções da banca final

Textos prontos para colar no documento **"TCC entrega final"** (Google Docs),
atendendo aos pontos de **texto** do parecer (F04/D2/D3, F08, F09, F10). Cada
bloco diz onde entra. Os números vêm das evidências reais (Fase 1/2); os pontos
marcados **`[CONFERIR]`** dependem de conferência de vocês no próprio documento
(números de figura, preços/datas de planos, usos de IA). Register formal, ABNT.

> Base factual destes textos (de `docs/evidencias/`): modelo v1.0.0 de 08/09 —
> 93,3% de acurácia de intenção e F1 0,838 (teste real); v1.2.0 — acurácia de
> validação 0,9986, F1 de entidades 0,831; agente ponta a ponta — 58/100
> (13/10), 83/100 (05/11, v1.2.0), 88/100 (06/11, após correções), confirmado na
> versão publicada de 09/11; generalização em conjunto inédito — ~43% (13/30);
> gabarito numérico das 14 consultas — 19/19; latência média em produção —
> 0,63 s (versão de 09/11).

---

## Bloco 1 — Conclusão reescrita (F04, D2, D3)

> **Onde entra:** substitui os parágrafos de fechamento do Capítulo 6 (Conclusão)
> que hoje destacam "93,3%, 58% e 0,96 s" como um resultado único. Separa os três
> estados do artefato, rotula cada número por versão e encerra o resultado da
> versão entregue, preservando as limitações.

### 6.x Resultados por versão do artefato

Os resultados obtidos referem-se a **três estados distintos** do artefato, que
não devem ser lidos como um único número:

**(a) Modelo de compreensão de linguagem natural, avaliado isoladamente.** A
primeira versão do modelo (1.0.0, treinada em 08/09/2026) obteve, em um conjunto
de teste redigido manualmente, **93,3% de acurácia na classificação de intenção**
e **medida F1 de 0,838 no reconhecimento de entidades**. Esses valores medem a
rede neural isolada, não o sistema integrado, e correspondem ao conjunto de
teste do treino — não a perguntas inéditas. Em reavaliação com as anotações de
entidade revisadas, o F1 do mesmo modelo recai para 0,803; a versão final
(1.2.0) registra F1 de 0,831. Comparações entre modelos exigem fixar rótulos,
versões e repertório, o que é feito no Apêndice [CONFERIR].

**(b) Agente integrado, resultado histórico.** Na avaliação original, de
13/10/2026, o agente completo (modelo 1.0.0 publicado, consulta ponta a ponta
sobre as cem perguntas de validação) obteve **58 de 100** respostas compatíveis
com o status e o tipo esperados. Este é um **resultado histórico**, da primeira
integração, e é mantido como marco de partida, não como desempenho atual.

**(c) Agente integrado, versão publicada.** Após a análise de erros e as
correções no adaptador, no executor e no modelo (retreino para a versão 1.2.0),
o mesmo repertório de cem perguntas, reexecutado em ambiente local, registrou
**83 de 100** em 05/11/2026 e **88 de 100** em 06/11/2026, após o tratamento de
respostas vazias. Esse resultado foi **confirmado na versão publicada em
09/11/2026**, com tempo médio de resposta de **0,63 s**. O valor de 88/100 é,
portanto, uma medida de **regressão e evolução sobre o repertório conhecido** da
versão publicada — e não uma medida de generalização.

### 6.x Alcance e limites da evidência

A distinção acima é essencial para não superestimar o alcance do sistema. A
bateria de cem perguntas guiou as próprias correções e contém formulações
próximas às do treino; por isso ela mede o **repertório coberto**, não a
capacidade de responder a perguntas inéditas. Para dimensionar essa diferença,
um conjunto de perguntas **inéditas**, redigido fora dos moldes de treino e das
cem, foi submetido ao sistema congelado (mesmos pesos, limiar e banco): a taxa de
acerto caiu para cerca de **43%**. Observou-se, porém, que **quando o sistema
reconhece a pergunta, o valor calculado é exato** — verificado por um gabarito
numérico independente que confere as quatorze consultas (19 de 19 provas) — e que,
na maioria dos casos não reconhecidos, o sistema **pede reformulação em vez de
responder incorretamente**, preservando o comportamento seguro previsto na
arquitetura.

Permanecem como limitações, já apontadas: os dados são **sintéticos**, de modo
que a verificação de valor atesta a correção das consultas, não o comportamento
sobre dados reais heterogêneos; e **não houve validação de uso por gestores**, de
forma que os benefícios gerenciais e econômicos permanecem **hipóteses a avaliar**
(Seção [CONFERIR]), não resultados demonstrados. O objetivo de taxa funcional de
80% é atingido sobre o repertório avaliado, segundo o oráculo de status e tipo
adotado; a correção numérica integral e a generalização a perguntas inéditas são
tratadas como trabalho em curso, não como metas encerradas.

---

## Bloco 2 — Errata de remissões de figuras (F08)

> **Onde entra:** como nota de errata e correção na Seção 5.9 (e na lista de
> figuras). O parecer aponta que a Seção 5.9 remete às "Figuras 1 a 6 como telas
> atuais", mas a lista de figuras as apresenta como **diagramas**.

**Correção a aplicar:**

1. Na Seção 5.9, **corrigir a remissão**: as Figuras 1 a 6 [CONFERIR os números
   exatos] são **diagramas** do sistema (arquitetura, casos de uso, fluxograma,
   MER etc.), e **não** capturas das telas atuais. Reescrever a frase para citar
   os diagramas pelo que são, por exemplo: *"conforme os diagramas das Figuras 1
   a 6"* em vez de *"as telas das Figuras 1 a 6"*.
2. Se a intenção era mostrar as telas reais, **inserir figuras novas** com as
   capturas e numerá-las na sequência: tela de chat com resultado, gráfico de
   barras, mensagem de hibernação e as três telas do assistente de importação
   [CONFERIR quais telas incluir].
3. **Conferir a numeração sequencial** de todas as figuras após a inserção e
   garantir que **cada figura seja citada no texto antes de aparecer**, com
   legenda acima (`Figura N – Descrição`) e fonte abaixo (`Fonte: elaborado
   pelos autores (2026).`), conforme o guia da UNIP.
4. **Conferir a ficha catalográfica** com a Biblioteca (contagem de folhas e
   dados) e **completar a folha de aprovação após a defesa** — sem antecipar data
   ou assinaturas.

---

## Bloco 3 — Viabilidade comercial como hipótese (F09)

> **Onde entra:** ajusta os parágrafos de viabilidade/infraestrutura
> (pp. 31–36 e 72–75 [CONFERIR]) e o fechamento econômico da Conclusão. O parecer
> pede datar as fontes primárias dos planos, explicitar premissas e qualificar a
> conclusão econômica como hipótese.

**Texto sugerido (fechamento econômico):**

> A estimativa de custo de operação apoia-se nos valores dos planos gratuitos e
> pagos dos serviços utilizados (Supabase, Render e Vercel), consultados em
> [CONFERIR data] nas páginas oficiais de cada fornecedor [CONFERIR referências].
> Esses valores são **referência temporal** e podem variar; a faixa estimada
> **não representa o custo total de operação**, que depende de premissas de
> **volume de uso, suporte e manutenção** aqui assumidas como [CONFERIR explicitar
> premissas]. Como os dados utilizados são **sintéticos** e os critérios de
> usabilidade foram **heurísticos**, não há demonstração de valor gerencial,
> de aceitação pelos usuários nem de economia frente a concorrentes. A conclusão
> de viabilidade econômica é, portanto, apresentada como **hipótese**, cuja
> verificação depende de avaliação com gestores reais e de medição do custo
> observado em operação — registradas como trabalhos futuros.

---

## Bloco 4 — Declaração de uso de IA formalizada (F10)

> **Onde entra:** ao final da Declaração de uso de IA (pp. 133–136). O parecer
> registra que os usos, ferramentas, períodos, custódia e responsabilidade já
> estão descritos, mas que **os campos de data, assinaturas e ciência estão em
> branco**. Este bloco formaliza; confira também os **identificadores de versão**
> e a **rastreabilidade dos usos** (apresentar apenas registros observáveis e
> sanitizados).

**Checagem antes de assinar:**

- [ ] Ferramentas e **versões** citadas conferem com o uso real [CONFERIR].
- [ ] **Períodos** de uso preenchidos.
- [ ] Custódia de prompts e saídas descrita; apenas registros **sanitizados**.
- [ ] Responsabilidade dos autores pelo conteúdo final afirmada.

**Formalização (preencher e assinar):**

> Declaramos que as ferramentas de inteligência artificial e os usos descritos
> nesta seção correspondem ao efetivamente empregado no desenvolvimento deste
> trabalho, e que os autores são responsáveis pela revisão e pelo conteúdo final
> apresentado.
>
> São Paulo, ____ de ______________ de 2026.
>
> ______________________________    Amanda Eleoterio Silva
>
> ______________________________    Erik Alves Gonçalves
>
> ______________________________    Ilana dos Santos Caetano da Silva
>
> ______________________________    Maria Luiza dos Anjos Santos
>
> **Ciência da orientação:**
>
> ______________________________    Prof.ª Stephany Mendes Oliveira

---

## Roteiro de defesa (apoio — do parecer)

Para a arguição, o parecer sugere um roteiro que os artefatos da Fase 1 já
sustentam:

1. **Identificar versão do código e hash do modelo** → `scripts/manifesto_reproducao.py`.
2. **Importar planilha sintética em duas empresas e conferir total e ticket à mão**
   → `scripts/reconciliacao_carga.py` (grão, faturamento, ticket).
3. **Pergunta inédita com cálculo conferível** → `scripts/avaliar_ineditas.py`
   (intenção + valor; ex.: ticket 2025 = 770,51; variação abr→mai/2025 = 9,81%).
4. **Distinguir retorno vazio × falta de parâmetro × recusa** → bateria inédita
   (404 `sem_resultado`, 422 `parametro_faltando`, 422 `baixa_confianca`).
5. **Isolamento sem contas reais** → `scripts/demo_isolamento.py` (empresas
   fictícias, RLS, auditoria).
6. **Separar a medição conhecida (88/100) do resultado da pergunta nova** → usar a
   conclusão reescrita (Bloco 1) e os relatórios de `docs/evidencias/`.
