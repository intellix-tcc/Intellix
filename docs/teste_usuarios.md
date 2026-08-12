# Teste com usuários reais (D15)

Objetivo: observar 2 pessoas de fora do grupo usando o Intellix sem
instruções prévias sobre como ele funciona. Onde elas travarem vira
parágrafo da seção 4.7 (interação humano-computador) do TCC.

Usa a versão publicada na Vercel (modo mock, `VITE_MOCK=true`) — não
precisa esperar o backend real. URL:
https://intellix-454e8bjo3-intellix3.vercel.app

## Regras da sessão

- **Não explique a tela antes.** O objetivo é ver se ela se explica sozinha.
- Peça para a pessoa **pensar em voz alta** enquanto usa.
- Você só observa e anota — não ajuda, a não ser que a pessoa trave por
  completo (>1 min sem saber o que fazer).
- Grave a tela se possível (ou tire prints dos momentos de trava).

## Roteiro (~10 min por pessoa)

Contexto pra dar à pessoa antes de começar:
> "Imagine que você é dona de uma loja e quer entender como as vendas
> foram nos últimos meses. Essa é a ferramenta que você vai usar."

1. **Descubra quanto a loja faturou em março.**
   (testa se ela acha as perguntas de exemplo ou digita livre)
2. **Descubra quais produtos mais venderam.**
   (testa se ela repete o padrão aprendido na tarefa 1)
3. **Baixe esse resultado em Excel ou PDF.**
   (testa se os botões de exportar são achados sem indicação)
4. **Pergunte algo que a ferramenta claramente não vai saber responder**
   (ex.: "qual a capital da França").
   (testa a reação à mensagem de erro — se ela entende que pode
   reformular, ou se acha que quebrou)
5. **Comece um novo chat e depois volte pra conversa anterior.**
   (testa se a sidebar de histórico é descoberta sem explicação)
6. **Pergunta livre, sem sugestão:** "Pergunte qualquer outra coisa
   sobre as vendas que vier à cabeça."
   (mede taxa de acerto natural, fora do roteiro guiado)

## O que anotar durante

- Tempo até a primeira pergunta bem-sucedida
- Ela leu os botões de exemplo ou digitou direto?
- Reação ao "Analisando seus dados…" (achou que travou?)
- Reação à mensagem de erro (heurística 2: sem jargão)
- Achou os botões de exportar sem ajuda?
- Achou a sidebar/histórico sem ajuda?
- Percebeu o indicador de confiança? Soube dizer o que significa?
- Qualquer xingamento, pausa longa, ou "não sei o que fazer agora"

## Perguntas rápidas ao final (1 min)

1. De 1 a 5, quão fácil foi usar sem explicação nenhuma?
2. Teve algum momento que você não sabia o que fazer? Qual?
3. Alguma coisa te confundiu ou pareceu fora do lugar?

## Resultado

Preencher depois das 2 sessões:

| Usuário | Tempo até 1ª resposta | Achou exportar sozinho? | Achou histórico sozinho? | Onde travou |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

**Síntese pro capítulo 4.7:** _(2–3 frases sobre o padrão observado nas
duas sessões — isso vira o parágrafo do TCC)_
