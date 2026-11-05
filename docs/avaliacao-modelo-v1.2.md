# Modelo NLU v1.2.0: retreino e data de referência

**Data:** 05/11/2026 · **Modelo:** `backend/app/nlu/intellix_nlu_v1.2.0.pt` (BiLSTM, 1,1 MB, mesma arquitetura e hiperparâmetros do v1.1.0)

## 1. O que mudou

**Moldes v3** (`ia training/moldes.py`, bloco "VERSÃO 3"), escritos a partir das frases que a v1.1.0 deixava abaixo do limiar de confiança na interface:

- período relativo com preposição ("no mês passado", "do ano passado");
- detalhe de produto em perguntas de vendedor, cliente e canal ("qual vendedor mais vendeu {produto}");
- contagem de peças ("quantas unidades de {produto}");
- "qual mês vendeu mais/menos".

**Duas intenções novas no modelo** (12 → 14): `unidades_vendidas` e `melhor_mes`. Já existiam no backend como refino por regra (`app/refino.py`); agora o próprio modelo as reconhece, e a regra fica como rede de segurança.

**Data de referência** (`app/periodo_dataset.py`, `regras.usar_referencia`): "ano passado", "mês passado", "esse ano", "último trimestre" e mês sem ano partem de hoje (horário de Brasília), limitado à última venda do dataset. Antes partiam de 2024 fixo: "ano passado" era 2023 mesmo em 2026. Em 05/11/2026, na base demo, "ano passado" = 2025, "mês passado" = outubro de 2026 e "último trimestre" = julho a setembro de 2026 (o último completo).

## 2. Como foi medido

- Mesmo código do backend nas duas colunas; só o arquivo do modelo muda (variável `NLU_MODELO`).
- API local com o banco de demonstração (PostgreSQL 16 local, mesmo schema do Supabase).
- As 100 perguntas de validação continuam fora do treino: o gerador remove as frases iguais a elas (7 removidas nesta geração).
- As 40 perguntas de detalhe (seção 4) foram escritas **antes** dos moldes novos e conferidas: nenhuma aparece no dataset de treino.
- O treino local (`ia training/treinar.py`) reproduz exatamente o v1.1.0 de produção (85,6% offline), então a diferença vem dos moldes.

## 3. Resultados

| Conjunto | v1.1.0 | **v1.2.0** |
|---|---:|---:|
| 100 perguntas, só o NLU (90 classificáveis) | 77/90 (85,6%) | **84/90 (93,3%)** |
| 100 perguntas, API ponta a ponta | 77/100 | **84/100** |
| 40 perguntas de detalhe, API ponta a ponta | 29/40 | **35/40** |
| Sugestões que a própria interface mostra (54) | 54/54 | **54/54** |

Detalhes por pergunta: `docs/evidencias/avaliacao_api_2026-11-05_v1.1.0.md` e `..._v1.2.0.md`.

Erros que restam nas 100 e **não são do modelo**:
- nomes que não existem na base demo ("vendedor João", "Maria", "Ana"): a pergunta é entendida e o banco responde "sem resultado";
- "produtos parados": na base demo todos os produtos venderam em todos os períodos.

A pergunta 83 ("Quantas vendas no pix em janeiro de 2024?") responde de propósito a quantidade de vendas no pix, e não a quebra por forma de pagamento que o roteiro esperava.

## 4. As 40 perguntas de detalhe

| n | Pergunta | Esperado | v1.1.0 | v1.2.0 |
|---:|---|---|---|---|
| 1 | Quantas botas de couro a gente vendeu no ano? | unidades_vendidas | ✅ | ✅ |
| 2 | Qual foi o mês do ano que mais vendeu botas de couro? | melhor_mes | ✅ | ✅ |
| 3 | Quanto vendi no mês passado? | total_vendas_periodo | ❌ 422 baixa_confianca | ✅ |
| 4 | Quais vendedores mais venderam smartwatch em 2025? | desempenho_vendedor | ❌ 422 baixa_confianca | ✅ |
| 5 | Quantos smartwatches saíram em 2025? | unidades_vendidas | ❌ 422 baixa_confianca | ❌ 422 baixa_confianca |
| 6 | Em que mês o perfume importado vendeu mais? | melhor_mes | ✅ | ✅ |
| 7 | Quando foi que a gente mais vendeu em 2025? | melhor_mes | ❌ top_produtos | ✅ |
| 8 | Qual foi o mês mais fraco do ano passado? | melhor_mes | ✅ | ✅ |
| 9 | Quantas peças de camiseta básica vendemos esse ano? | unidades_vendidas | ✅ | ✅ |
| 10 | Quantas unidades saíram em outubro? | unidades_vendidas | ✅ | ✅ |
| 11 | Quem vendeu mais jaqueta corta-vento? | desempenho_vendedor | ✅ | ✅ |
| 12 | Qual vendedora mais vendeu kit skincare no ano passado? | desempenho_vendedor | ❌ comparacao_periodos | ❌ 422 baixa_confianca |
| 13 | Quanto faturei com vinho tinto no último trimestre? | total_vendas_periodo | ✅ | ✅ |
| 14 | Quanto entrou de calçados no mês passado? | total_vendas_periodo | ❌ 422 baixa_confianca | ❌ 422 baixa_confianca |
| 15 | Qual o ticket médio no pix esse ano? | ticket_medio | ✅ | ✅ |
| 16 | Quantas vendas pelo whatsapp no mês passado? | quantidade_vendas | ❌ 422 baixa_confianca | ✅ |
| 17 | Faturamento do ano passado | total_vendas_periodo | ✅ | ✅ |
| 18 | Quanto vendi esse mês? | total_vendas_periodo | ✅ | ✅ |
| 19 | Qual foi o faturamento do último mês? | total_vendas_periodo | ✅ | ✅ |
| 20 | Quais clientes mais compraram bota couro em 2025? | top_clientes | ✅ | ✅ |
| 21 | Top 3 produtos de beleza no ano passado | top_produtos | ✅ | ✅ |
| 22 | Quais categorias venderam mais no mês passado? | vendas_por_categoria | ✅ | ✅ |
| 23 | Como a Fernanda foi no mês passado? | desempenho_vendedor | ❌ 422 baixa_confianca | ❌ 422 baixa_confianca |
| 24 | Quanto o Carlos vendeu de smartwatch? | desempenho_vendedor | ✅ | ✅ |
| 25 | Quantos óculos de sol foram vendidos no primeiro semestre? | unidades_vendidas | ✅ | ✅ |
| 26 | Qual o pior mês de vendas de 2026? | melhor_mes | ✅ | ✅ |
| 27 | Em qual mês o faturamento foi maior em 2024? | melhor_mes | ✅ | ✅ |
| 28 | Qual mês teve menos vendas de espumante? | melhor_mes | ✅ | ✅ |
| 29 | Quanto vendi de acessórios pelo site em 2025? | total_vendas_periodo | ✅ | ✅ |
| 30 | Ranking dos vendedores no ano passado | desempenho_vendedor | ❌ 422 baixa_confianca | ✅ |
| 31 | Quem foi o melhor vendedor do mês passado? | desempenho_vendedor | ✅ | ✅ |
| 32 | Quantos itens vendemos no último trimestre? | unidades_vendidas | ❌ 404 sem_resultado | ✅ |
| 33 | Quanto vendemos de café especial em dezembro? | total_vendas_periodo | ❌ 422 baixa_confianca | ❌ 422 baixa_confianca |
| 34 | Quantas vendas no cartão de débito esse ano? | quantidade_vendas | ✅ | ✅ |
| 35 | Vendas por canal no ano passado | vendas_por_canal | ✅ | ✅ |
| 36 | Qual o produto mais vendido do mês passado? | top_produtos | ✅ | ✅ |
| 37 | Qual foi o melhor mês para a bolsa transversal em 2025? | melhor_mes | ✅ | ✅ |
| 38 | Quantas caixas de bombons vendemos em dezembro de 2025? | unidades_vendidas | ✅ | ✅ |
| 39 | Ticket médio de eletrônicos em 2025 | ticket_medio | ✅ | ✅ |
| 40 | Qual canal vendeu mais smartwatch esse ano? | vendas_por_canal | ✅ | ✅ |

As 5 que a v1.2.0 ainda não entende ficam abaixo do limiar e voltam o pedido de reformulação, sem resposta errada. Por exemplo, "Como a Fernanda foi no mês passado?" (e também "Como foi a Fernanda em outubro?") fica abaixo do limiar, enquanto "Como foi o desempenho da Fernanda no mês passado?" e "Quanto a Fernanda vendeu no mês passado?" funcionam. Frases curtas com "como foi a {vendedor}" e "quantos {produto} saíram" pedem mais moldes. São o ponto de partida para os moldes de uma v1.3.

## 5. Como retreinar

```bash
cd "ia training"
python gerar_dataset.py
python validar_dataset.py dados/dataset.jsonl
python treinar.py --versao 1.3.0
python ../scripts/avaliar_100_perguntas.py --modo nlu --backend modelo --modelo intellix_nlu_v1.3.0.pt
```

Para voltar ao modelo anterior em produção sem novo deploy: `NLU_MODELO=app/nlu/intellix_nlu_v1.1.0.pt` no Render.
