# Pendências da apresentação final (V1 → V2)

Lista viva de erros e ajustes. Atualizada a cada rodada de edição no Canva.

Canva: https://www.canva.com/d/2HepJA1QKiZGqnJ

## Inconsistências para resolver na monografia ou na fala

- [ ] **12 × 14 consultas**: o resumo diz "doze modelos de consulta"; o sistema tem 14 (12 intenções + `unidades_vendidas` e `melhor_mes`). O slide 13 explica; alinhar a monografia.
- [ ] **Queda de métricas na v1.2.0**: 93,3% / F1 0,838 (v1.0.0) → 88,3% / F1 0,831 (v1.2.0). O slide 18 mostra os dois. Preparar explicação.
- [ ] **Parâmetros**: slide 12 diz "≈ 289 mil" (medido no modelo v1.2.0: 288.987). Conferir se a monografia cita outro valor (ex.: 283.887) e unificar.
- [ ] **Referências na monografia**: MACHADO (2013) está colada em MICROSOFT (Copilot) sem quebra de linha.
- [ ] **Comparativo LSTM × Transformer**: prometido na pré-banca, ausente na monografia. Decidir se entra na continuidade ou se some.

## Pontos fracos que a banca pode explorar (preparar resposta)

- [ ] **NER fraco**: nomes como "Fernanda" e "pix" vêm das regras e do cadastro (`filtros.py`), não do modelo.
- [ ] **Fora do domínio**: "qual a previsão do tempo amanhã?" passa com 78,4% (acima do limite de 70%); quem barra é o filtro de termos de vendas.
- [ ] **88% não é generalização**: medido no mesmo repertório que guiou as correções. Já sinalizado nos slides 19 e 21.

## Ajustes nos slides

- [x] Agenda (slide 2) agora lista "08 · Referências" (corrigido na rodada 2).
- [ ] V2: slides reserva para perguntas difíceis (pontos acima).
- [ ] Roteiros de fala por slide (30 min).
- [x] Rodada 2: fontes maiores, subtítulos coloridos maiores, logo em todas as páginas, mais detalhes visuais.
- [ ] Validar textos novos da rodada 2:
  - slide 13: caixa "E se não for nenhuma?" (confiança < 70% pede para reformular; fora de vendas é barrado pelo filtro de domínio);
  - slide 21: frase "Contribuição: um agente de análise de vendas em português, leve, local e auditável, com custo zero por pergunta".
- [ ] Slides escuros (17 e 23): o símbolo do logo é escuro e aparece com pouco contraste sobre o fundo petróleo. Avaliar uma versão clara do símbolo.
- [ ] Slide 18: as barras de meta são ilustrativas (preenchimento proporcional ao valor; a de tamanho mostra 1,09 de 256 MB).

## Dia da defesa

- [ ] Abrir o app ~5 min antes (Render hiberna) e ter o vídeo da demonstração como plano B.
