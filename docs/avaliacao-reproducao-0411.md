# Os dois modelos "1.0.0" e a origem das métricas do treino

**Data:** 06/11/2026

## 1. Dois arquivos com o mesmo número de versão

O modelo 1.0.0 foi treinado no Google Colab em 08/09/2026 e retreinado em
21/10/2026 (commit `22f0d17`, "retreinado com o dataset limpo"), **mantendo o
mesmo número de versão**. Os dois arquivos ficam agora versionados com nomes
distintos:

| Arquivo em `ia training/modelos/` | Treino | MD5 | Teste real: intenção · F1 entidades | Usado em |
|---|---|---|---|---|
| `intellix_nlu_v1.0.0_2026-09-08.pt` | 08/09/2026 (commit `cb070bc`) | `8794d5ff…` | 93,3% · 0,838 | seção 5.5 do TCC; avaliação de 13/10 (58%) |
| `intellix_nlu_v1.0.0_2026-10-21_retreino.pt` | 21/10/2026 (commit `22f0d17`) | `26805e17…` | 90,0% · 0,868 | avaliação de 04/11 (73%) |

Os números das duas últimas colunas estão gravados dentro de cada arquivo
(campo `metricas`), junto com a data, os hiperparâmetros e o tamanho dos
subconjuntos. O retreino de 21/10 usou moldes novos, escritos a partir das
formulações que falhavam nas 100 perguntas, e o filtro que remove do
conjunto de treino as frases iguais às perguntas de validação (5 delas
vazavam no conjunto do modelo de 08/09).

## 2. Quanto do ganho de 58% para 73% veio do código e quanto do retreino

A avaliação de 04/11 (`docs/evidencias/avaliacao_api_2026-11-04_2143.md`)
mediu as correções no adaptador e no orquestrador **junto** com o modelo
retreinado. Para separar os dois efeitos, as 100 perguntas foram executadas de
novo em 06/11, com o código exato de 04/11 (commit `3097356`), trocando só o
arquivo do modelo:

| Execução | Modelo | Acerto | Relatório |
|---|---|---:|---|
| 13/10 (original, nuvem) | 1.0.0 de 08/09 | 58% | `evidencias/avaliacao_api_2026-10-13_2034.md` |
| Reprodução: correções de código, sem retreino | 1.0.0 de 08/09 | **69%** | `evidencias/avaliacao_api_2026-11-06_reproducao_0411_modelo_original.md` |
| Reprodução da avaliação de 04/11 | 1.0.0 de 21/10 | **73%** | `evidencias/avaliacao_api_2026-11-06_reproducao_0411_modelo_retreinado.md` |

A reprodução com o modelo de 21/10 deu 73/100 com as mesmas 15 categorias do
relatório de 04/11, o que valida a montagem. Logo:

- as correções de código, sem novo treinamento, levaram de 58% a **69%**
  (variação entre períodos de 0 para 5 acertos, fora de escopo de 4 para 6,
  desempenho do vendedor de 1 para 3, comparação de 2 para 3, sem resultado
  esperado de 3 para 4);
- o retreino de 21/10 somou **4 pontos** (vendas por categoria de 4 para 7,
  vendas por pagamento de 3 para 5; top produtos caiu de 7 para 6).

**Montagem:** Postgres 16 local com `database/local/supabase_minimo.sql`, as
migrations 001 a 004 do commit `3097356` e `database/seed.py` (3.527 vendas,
8.941 itens); API com `NLU_BACKEND=modelo`, `AUTH_OBRIGATORIA=false`,
`LIMITE_REQUISICOES=0`; `scripts/avaliar_100_perguntas.py --modo api`.

## 3. De onde vem cada métrica do modelo 1.0.0 (seção 5.5 do TCC)

| Métrica | Valor | Onde está registrada |
|---|---|---|
| Acurácia de intenção e F1 de entidades no teste real | 93,3% · 0,838 | metadados do modelo de 08/09 (`metricas`) |
| Acurácia e F1 no teste sintético; acurácia de validação | 0,996 · 0,996 · 1,000 | idem |
| Tempo de inferência | 1,72 ms | idem |
| Parâmetros, vocabulário, tamanho do arquivo | 283.887 · 404 · 1,09 MB | o próprio arquivo do modelo |
| Épocas, hiperparâmetros, divisão 3.360/720/720 | 18 épocas | metadados (`treino`) e `ia training/Intellix_NLU_Colab.ipynb` (código) |
| Conjunto de dados (Tabelas 2 e 3, tamanho das frases, 16,5% fora do vocabulário) | — | `evidencias/dataset_v1.0.0_2026-11-06.md`, recriado por `ia training/reproduzir_dataset_v1.0.0.py` |
| Métricas por intenção e por entidade, curvas de treino (Figura 11) e matriz de confusão (Figura 12) | — | execução do notebook no Colab em 08/09/2026; **as saídas não foram salvas** no notebook versionado |

**Verificação independente** (`evidencias/avaliacao_teste_real_2026-11-06_1309.md`):
o modelo de 08/09, avaliado com o arquivo de teste versionado, reproduz a
acurácia de 93,3% e as métricas por intenção (exceto vendas por pagamento,
0,95 em vez de 1,00); a matriz difere em uma célula (uma pergunta de vendas
por categoria prevista como forma de pagamento, e não como desempenho do
vendedor) e o F1 de entidades é 0,803, porque as anotações de entidades do
arquivo foram revisadas depois do treino.
