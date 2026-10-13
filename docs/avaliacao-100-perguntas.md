# Avaliação ponta a ponta com o modelo treinado: 100 perguntas

**Projeto:** Intellix, agente inteligente de análise de vendas
**Atende:** crítica nº 2 do parecer de orientação (*integrar o modelo treinado à API,
executar as cem perguntas e consolidar taxa funcional, latência e verificação dos objetivos*)
**Data da execução:** 13/10/2026, 19:19 a 19:53 (UTC−3)
**Versão:** `main`, commit `9c8c62a`, modelo `intellix_nlu_v1.0.0.pt` (BiLSTM, 1,09 MB)
**Responsável:** Erik Alves Gonçalves (dados e infraestrutura)

---

## 1. Como foi medido

| Item | Configuração |
|---|---|
| Perguntas | `docs/perguntas_validacao.md`: 12 intenções × 7 perguntas, mais 6 fora de escopo, 5 com parâmetro faltando e 5 sem resultado (100 no total) |
| Executor | `scripts/avaliar_100_perguntas.py` (só biblioteca padrão do Python) |
| API | FastAPI local (`uvicorn`), `NLU_BACKEND=modelo`, Windows 11, Python 3.12.0 |
| Banco | Supabase `intellix-dev` (PostgreSQL, São Paulo), Transaction pooler 6543 |
| Critério de acerto | HTTP 200 com o título do template da intenção esperada; para fora de escopo, HTTP 422 `baixa_confianca`; para parâmetro faltando, HTTP 422; para sem resultado, HTTP 404 `sem_resultado` |

Foram feitas três rodadas:

1. **NLU por regras, offline** (linha de base): só o classificador, sem servidor nem banco.
2. **NLU com o modelo, offline**: mesmo conjunto, para isolar a qualidade da classificação.
3. **API completa com o modelo**: cada pergunta enviada a `POST /chat`, passando por NLU,
   resolução de parâmetros, template SQL e banco.

As rodadas 1 e 2 cobrem as 90 perguntas das seções 1 a 13 (as seções 14 e 15 dependem do banco).

## 2. Resultados por categoria

| # | Categoria | Regras (NLU) | Modelo (NLU) | **API ponta a ponta** |
|---|---|---:|---:|---:|
| 1 | total_vendas_periodo | 5/7 | 5/7 | **5/7** |
| 2 | top_produtos | 6/7 | 7/7 | **7/7** |
| 3 | ticket_medio | 6/7 | 7/7 | **7/7** |
| 4 | quantidade_vendas | 0/7 | 6/7 | **6/7** |
| 5 | top_clientes | 0/7 | 6/7 | **6/7** |
| 6 | desempenho_vendedor | 0/7 | 4/7 | **1/7** |
| 7 | produtos_sem_saida | 0/7 | 7/7 | **2/7** |
| 8 | comparacao_periodos | 0/7 | 4/7 | **2/7** |
| 9 | variacao_periodo | 0/7 | 5/7 | **0/7** |
| 10 | vendas_por_canal | 0/7 | 5/7 | **5/7** |
| 11 | vendas_por_categoria | 0/7 | 4/7 | **4/7** |
| 12 | vendas_por_pagamento | 0/7 | 3/7 | **3/7** |
| 13 | fora_de_escopo | 6/6 | 4/6 | **4/6** |
| 14 | parametro_faltando | n/a | n/a | **3/5** |
| 15 | sem_resultado | n/a | n/a | **3/5** |
| | **Total** | **23/90 (25,6%)** | **67/90 (74,4%)** | **58/100 (58,0%)** |

O modelo treinado triplica a cobertura em relação às regras (de 3 para 12 intenções
reconhecidas) e é o que torna o sistema utilizável. A taxa ponta a ponta, porém, fica
abaixo da classificação isolada: 16 pontos se perdem **depois** do NLU, na resolução dos
parâmetros e no tratamento do resultado do banco (seção 4).

## 3. Recursos e latência

### 3.1 Memória

Com `NLU_BACKEND=modelo`, o processo da API (Python, FastAPI, PyTorch CPU e o modelo
carregado) ocupou **222 MB** de memória (227.280 KB, medidos pelo `tasklist` após as 100
requisições). Isso cabe no plano gratuito do Render (512 MB), com folga de cerca de 290 MB,
e afasta o risco de estouro de memória registrado na análise de riscos.

### 3.2 Latência

| Rodada | Mediana | p95 | Máxima | Média | Abaixo de 3 s |
|---|---:|---:|---:|---:|---:|
| NLU com modelo (inferência isolada) | 0 ms | 1 ms | 82 ms | 1 ms | 90/90 |
| **API completa, `http://127.0.0.1:8000`** | **181 ms** | **208 ms** | **232 ms** | **154 ms** | **100/100** |

Separando por tipo de resposta (rodada das 19:30):

| Resposta | Qtde. | Mediana | Faixa | O que inclui |
|---|---:|---:|---|---|
| 200 (consulta respondida) | 59 | 185 ms | 167 a 232 ms | NLU, conexão ao banco, consulta |
| 404 `sem_resultado` | 12 | 182 ms | 175 a 198 ms | NLU, conexão ao banco, consulta |
| 422 `parametro_faltando` | 15 | 127 ms | 114 a 144 ms | NLU e **conexão ao banco aberta sem necessidade** |
| 422 `baixa_confianca` | 14 | 2 ms | 1,7 a 25 ms | só NLU |

Três conclusões:

1. **O modelo não pesa na latência:** a recusa por baixa confiança, que só passa pelo
   modelo, levou cerca de 2 ms.
2. **O custo dominante é abrir a conexão com o banco (cerca de 120 ms por pergunta).**
   A consulta em si leva cerca de 60 ms. A API abre uma conexão nova a cada requisição;
   um pool de conexões (`psycopg_pool`) reduziria a resposta típica para menos de 100 ms.
3. **Melhoria simples no `main.py`:** o 422 `parametro_faltando` abre a conexão antes de
   verificar os parâmetros. Validar os obrigatórios antes de `get_connection()` faria essas
   respostas caírem de cerca de 127 ms para cerca de 2 ms.

Observação de método: uma primeira rodada (19:23) usou `http://localhost:8000` e mediu
cerca de 2,2 s por pergunta, inclusive nas recusas que não tocam o banco. No Windows,
`localhost` é tentado primeiro em IPv6 (`::1`), o `uvicorn` escuta só em IPv4, e o cliente
perde cerca de 2 s antes de tentar o IPv4. As taxas de acerto das duas rodadas são
idênticas, pergunta a pergunta; vale a da 19:30 para a latência. Em produção (Render,
acessado por domínio) esse atraso não existe.

A medição foi feita com a API local acessando o banco em São Paulo pela internet
doméstica. Em produção, a latência depende da região do serviço no Render em relação ao banco, e o
plano gratuito "dorme" após 15 minutos sem uso (a primeira requisição depois disso é
lenta). A medição em produção fica como próximo passo.

### 3.3 Produção (Render)

Às 19:50 a variável `NLU_BACKEND=modelo` foi ativada no serviço `intellix-api` do Render
(plano gratuito: 512 MB de RAM e 0,15 de CPU), que acessa o banco `intellix-prod`.

**Antes e depois.** A pergunta "Quantas vendas eu fiz em março?" devolvia HTTP 422 com o
NLU por regras. Com o modelo, devolveu HTTP 200: intenção `quantidade_vendas`, período
de 01/03/2024 a 31/03/2024, 54 vendas, confiança 0,9998.

**As 100 perguntas contra `https://intellix-api.onrender.com` (19:53):** 58/100 acertos,
**idênticos pergunta a pergunta** aos da execução local. O comportamento do sistema é o
mesmo nos dois ambientes.

| Resposta | Qtde. | Mediana | Faixa |
|---|---:|---:|---|
| 200 (consulta respondida) | 59 | 1.938 ms | 1.850 a 2.817 ms |
| 404 `sem_resultado` | 12 | 1.901 ms | 1.866 a 3.276 ms |
| 422 `parametro_faltando` | 15 | 1.406 ms | 1.341 a 2.628 ms |
| 422 `baixa_confianca` | 14 | 323 ms | 280 a 923 ms |
| **Total** | **100** | **1.900 ms** | média **1.782 ms**; p95 2.647 ms; 99/100 abaixo de 3 s |

Como os tempos se decompõem (medianas):

| Parcela | Tempo aproximado | Como foi estimada |
|---|---:|---|
| Rede do cliente até o Render, mais inferência do modelo | ~320 ms | recusa por baixa confiança, que não toca o banco |
| Abertura da conexão com o banco | ~1.080 ms | `parametro_faltando` menos `baixa_confianca` |
| Execução da consulta | ~500 ms | resposta 200 menos `parametro_faltando` |

A meta de tempo médio inferior a 3 s foi atingida também em produção (1,78 s), mas com
margem menor. Uma resposta (1%) passou de 3 s (3.276 ms). **O principal custo é abrir uma
conexão nova com o banco a cada pergunta**: o Render não tem região na América do Sul, e
cada conexão nova exige várias idas e voltas de rede até São Paulo (TCP, TLS e
autenticação). Com um pool de conexões, a conexão é aberta uma vez e reaproveitada, o que
eliminaria a maior parte desse segundo; o tempo típico esperado ficaria abaixo de 1 s.

**Memória em produção.** O plano gratuito do Render não exibe métricas de memória
(recurso de planos pagos). A evidência disponível é indireta: durante o deploy e as mais de
100 requisições, a linha do tempo de eventos do serviço registrou apenas o início e a
conclusão do deploy, sem reinício por falta de memória. Somada à medição local (222 MB
com o mesmo código e modelo), isso indica que a aplicação opera dentro do limite de 512 MB.

## 4. Análise dos 42 erros

| Causa | Erros | Onde se corrige |
|---|---:|---|
| A. Intenção classificada errada pelo modelo | 21 | Dataset e retreino (Dev A) |
| B. Fora de escopo aceito com confiança alta | 2 | Filtro de domínio antes do modelo (Dev A/B) |
| C. Intenção certa, parâmetros não resolvidos (422 `parametro_faltando`) | 9 | `adaptador_modelo.py` (Dev A) |
| D. Intenção certa, resultado vazio tratado como "sem resultado" | 5 | `executor.py` (Dev B) |
| E. Seções 14 e 15 (comportamento de fallback) | 4 | `executor.py` e adaptador |
| F. Intenção certa, vendedor não encontrado no banco | 1 | Dados de teste / normalização de nome |

**A. Classificação (21).** Concentrada nas intenções com vocabulário parecido:
`vendas_por_pagamento` (4 erros), `comparacao_periodos` e `variacao_periodo` confundidas
entre si e com `total_vendas_periodo`, e `vendas_por_categoria`/`vendas_por_canal`
confundidas com `top_produtos` ("Quais categorias mais venderam"). O modelo obteve 93,3%
de acurácia no conjunto de teste real (120 frases); nas 100 perguntas, 74,4%. A diferença
indica que as perguntas de validação usam formulações pouco representadas no treino
(por exemplo "pix", "método de pagamento", "versus", "ranking").

**B. Fora de escopo (2).** "Qual a capital da França?" saiu como `variacao_periodo` com
confiança 0,92 e "Me conta uma piada." como `produtos_sem_saida` com 0,85. Um classificador
fechado em 12 classes sempre escolhe uma delas, e o limiar de 0,70 não protege quando ele
erra com convicção. As regras rejeitaram 6/6 dessas perguntas, o que sugere um filtro
híbrido: exigir ao menos um termo do domínio (venda, faturamento, produto, cliente…)
antes de aceitar a classificação.

**C. Parâmetros não resolvidos (9).** O adaptador resolve dois períodos apenas quando a
frase cita dois meses por extenso. Ficam sem resolução: "mês anterior", "mês passado",
"ano passado", "esse mês", trimestres e comparações entre anos ("2023 com 2024"). Por isso
`variacao_periodo` caiu de 5/7 no NLU para 0/7 na API. Em `desempenho_vendedor`, o nome
não é extraído quando o modelo não marca a entidade (Carlos) e não há resposta para a
pergunta sem nome ("Quem vendeu mais entre os vendedores?"), que poderia listar todos.
O comportamento é seguro (o sistema pede reformulação em vez de rodar SQL errado), mas
reduz a taxa funcional.

**D. Resultado vazio que é resposta (5).** Em `produtos_sem_saida`, a consulta devolve os
produtos **sem** vendas; lista vazia significa "nenhum produto ficou parado", que é uma
resposta válida. O executor trata qualquer lista vazia como 404 `sem_resultado`.
O caso inverso também ocorre (contado no grupo E): "Qual o ticket médio de 2018?" devolveu HTTP 200, porque
`avg()` sobre zero linhas retorna uma linha com valor nulo, que o executor não reconhece
como vazia.

**E. Fallbacks (4).** O ticket médio de 2018 (acima); "Quanto vendi?" foi respondida com o
ano padrão (o adaptador completa o período ausente, decisão de projeto que deve ser
documentada ou revista); "Como foi o desempenho do vendedor?" chegou ao banco em vez de
pedir o nome; e a pergunta sobre "Roberto em 2015" foi recusada por baixa confiança antes
de chegar ao banco.

## 5. Verificação dos objetivos (Tabela 1 da documentação)

| Indicador | Meta | Resultado | Situação |
|---|---|---|---|
| Acurácia de intenção (conjunto de teste real) | ≥ 85% | 93,3% | atingida |
| F1 de entidades (conjunto de teste real) | ≥ 0,80 | 0,838 | atingida |
| Taxa de acerto funcional ponta a ponta | ≥ 80% | **58,0%** (100 perguntas) | **não atingida** |
| Tempo médio de resposta | < 3 s | local: 154 ms; **produção: 1,78 s** (p95 2,65 s; 99/100 abaixo de 3 s) | atingida |
| Memória em produção | ≤ 512 MB (Render) | 222 MB (local); sem reinício por memória no Render | atingida |
| 12 intenções reconhecidas | 12 | 12 (todas com ao menos 1 acerto offline) | atingida |

## 6. Plano de correção e ganho esperado

Ordenado por custo. O item 0 melhora a latência; os itens 1 a 3 não exigem retreino.

| # | Ação | Responsável | Erros endereçados | Taxa esperada |
|---|---|---|---:|---:|
| 0 | Pool de conexões no `db.py` e validação dos parâmetros antes de conectar (latência, não acerto) | Dev B/C | n/a | n/a |
| 1 | Executor: lista vazia em `produtos_sem_saida` vira 200 com mensagem; linha só com nulos vira 404 | Dev B | 6 | 64% |
| 2 | Adaptador: resolver "mês anterior/passado", "ano passado", anos e trimestres; vendedor sem nome lista todos | Dev A | 9 a 10 | 73 a 74% |
| 3 | Filtro de domínio para fora de escopo | Dev A/B | 2 | 75 a 76% |
| 4 | Ampliar o dataset com as formulações que falharam e retreinar | Dev A | até 21 | ≥ 80% |

O teto sem retreino fica em torno de 76%. Para cruzar a meta de 80%, o item 4 é
necessário. Cuidado metodológico: as 100 perguntas não podem entrar no treino, ou
deixam de medir generalização. O retreino deve usar formulações **parecidas**, e a
avaliação final deve ser repetida com o mesmo conjunto.

## 7. Evidências e reprodução

- `docs/evidencias/avaliacao_nlu-regras_2026-10-13_1922.{md,csv}`
- `docs/evidencias/avaliacao_nlu-modelo_2026-10-13_1919.{md,csv}`
- `docs/evidencias/avaliacao_api_2026-10-13_1953.{md,csv}` (produção, Render)
- `docs/evidencias/avaliacao_api_2026-10-13_1930.{md,csv}` (local, rodada de referência)
- `docs/evidencias/avaliacao_api_2026-10-13_1923.{md,csv}` (mesmos acertos; latência afetada pelo `localhost`)

```bash
# offline (sem servidor nem banco)
python scripts/avaliar_100_perguntas.py --modo nlu --backend regras
python scripts/avaliar_100_perguntas.py --modo nlu --backend modelo
# ponta a ponta (terminal 1: API; terminal 2: executor)
cd backend && NLU_BACKEND=modelo uvicorn app.main:app
python scripts/avaliar_100_perguntas.py --modo api --url http://127.0.0.1:8000
# produção (com NLU_BACKEND=modelo no Render)
python scripts/avaliar_100_perguntas.py --modo api --url https://intellix-api.onrender.com
```

---

## Apêndice: texto sugerido para o TCC (seção de resultados)

> Para verificar o funcionamento integrado do sistema, o modelo treinado foi conectado à
> API e as 100 perguntas do conjunto de validação foram submetidas ao endpoint de chat,
> percorrendo o fluxo completo: interpretação, resolução de parâmetros, consulta SQL
> parametrizada e resposta. A Tabela 5 apresenta a taxa de acerto por categoria,
> comparada à classificação isolada e ao classificador por regras usado como linha de base.
>
> O modelo treinado elevou a taxa de classificação de 25,6% (regras) para 74,4%,
> reconhecendo as 12 intenções previstas. A taxa funcional ponta a ponta foi de 58,0%,
> abaixo da meta de 80%. A análise dos 42 erros mostrou que metade decorre da
> classificação e a outra metade de etapas posteriores ao modelo: períodos relativos
> ("mês anterior", "ano passado") ainda não resolvidos pelo adaptador e o tratamento de
> resultados vazios no executor. Em todos esses casos o sistema recusou a pergunta ou
> pediu reformulação, sem executar consultas incorretas, o que confirma o comportamento
> seguro previsto na arquitetura. A diferença entre a acurácia no conjunto de teste
> (93,3%) e nas perguntas de validação (74,4%) reforça a observação da seção 4.5.4 sobre
> a distância entre dados de treino e uso real.
>
> Quanto aos recursos, o processo da API com o modelo carregado ocupou 222 MB de memória,
> dentro do limite de 512 MB da hospedagem gratuita. O mesmo conjunto foi executado contra a
> versão publicada no Render, com resultado idêntico de acertos (58/100). O tempo médio de
> resposta foi de 154 ms no ambiente local e de 1,78 s em produção (99 das 100 respostas
> abaixo de 3 s), atendendo à meta de 3 segundos. A inferência do modelo levou cerca de
> 2 ms; em produção, a maior parcela do tempo (cerca de 1,1 s) correspondeu à abertura da
> conexão com o banco de dados, ponto de melhoria identificado para a versão final.
>
> **Tabela 5 – Taxa de acerto por categoria nas 100 perguntas de validação**
>
> | Categoria | Regras | Modelo (NLU) | Ponta a ponta |
> |---|---:|---:|---:|
> | (copiar as linhas da seção 2) | | | |
> | **Total** | **25,6%** | **74,4%** | **58,0%** |
>
> Fonte: Elaborado pelos autores (2026).
