# Intellix

**Agente inteligente para análise de vendas em pequenas empresas.**
Quem vende pergunta em português ("quanto faturei em março de 2024?",
"quais os 5 produtos mais vendidos?") e recebe a resposta calculada sobre os
próprios dados, com gráfico, tabela e exportação para Excel e PDF, sem
montar relatório nem escrever consulta.

Trabalho de Conclusão de Curso em Ciência da Computação, UNIP, 2026.

**Equipe**

| Nome | RA |
|---|---|
| Amanda Eleoterio Silva | N9514H5 |
| Erik Alves Gonçalves | N2246A3 |
| Ilana dos Santos Caetano da Silva | N0810C0 |
| Maria Luiza dos Anjos Santos | F353478 |

| | |
|---|---|
| Aplicação | <https://intellix-lilac.vercel.app> |
| API | <https://intellix-api.onrender.com> (`/health`; documentação interativa em `/docs`) |
| Contrato da API | [`docs/openapi.json`](docs/openapi.json) e [`docs/contratos.md`](docs/contratos.md) |

> No plano gratuito do Render, o servidor "dorme" depois de um tempo parado:
> a primeira pergunta pode levar cerca de 30 s. A tela avisa enquanto ele acorda
> ([decisão 003](docs/decisoes/003-por-que-render.md)).

---

## O que o sistema faz

- **Perguntar** — chat em linguagem natural sobre as vendas, com continuidade
  da conversa ("e em abril?", "e de calçados?"), filtros por produto,
  categoria, vendedor, cliente, canal e forma de pagamento, e explicação de
  "como cheguei nessa resposta".
- **Início** — panorama do mês: indicadores, evolução de 12 meses, categorias,
  canais, produtos em destaque e observações automáticas.
- **Importar dados** — envio de uma planilha `.xlsx` de vendas (há um
  [modelo para baixar](docs/templates/template_importacao_intellix.xlsx)),
  com relatório das linhas aceitas e rejeitadas e o motivo de cada rejeição.
  Sem importar nada, o sistema responde sobre uma base de demonstração.
- **Minhas planilhas** e **histórico de conversas** guardados na conta, para
  reencontrar em outro aparelho.
- **O que posso perguntar** — os 14 tipos de pergunta, com exemplos, e o que
  está fora do escopo (previsões, recomendações, assuntos fora de vendas).

## Como funciona

![Arquitetura em camadas](docs/diagramas/arquitetura_camadas.png)

```
pergunta ──► NLU (modelo treinado) ──► filtros pelo catálogo do dataset
         ──► contexto da conversa ──► refino ──► template SQL parametrizado
         ──► PostgreSQL (RLS por empresa) ──► ResultSet ──► tela, Excel, PDF
```

1. **Interpretação.** Uma rede neural treinada pelo grupo
   (`backend/app/nlu/intellix_nlu_v1.2.0.pt`, PyTorch) classifica a pergunta
   em uma das **12 intenções** e marca os trechos relevantes (período,
   produto, vendedor...). Abaixo de 70% de confiança, o sistema pede para
   reformular em vez de arriscar uma resposta.
2. **Detalhes e contexto.** O trecho marcado vira o valor exato do cadastro
   ("botas de couro" → "Bota couro"); perguntas curtas completam a anterior;
   dois **refinamentos** sem retreino (`unidades_vendidas` e `melhor_mes`)
   tornam a pergunta mais específica. Por isso são 12 intenções no modelo e
   **14 consultas** no sistema.
3. **Consulta.** A pergunta **nunca vira SQL**: a intenção escolhe uma de 14
   consultas fixas ([`templates.py`](backend/app/sql/templates.py)) e os
   valores entram como parâmetros. Não há como o texto do usuário mudar a
   estrutura da consulta.
4. **Resposta.** Números saem como número (nunca texto formatado), com o tipo
   de visualização sugerido; a tela formata, desenha e exporta.

Os dados ficam num modelo dimensional (star schema: `fato_item_venda` e as
dimensões de data, produto, cliente e vendedor —
[decisão 001](docs/decisoes/001-por-que-star-schema.md)).

## Tecnologias

| Camada | Tecnologia | Hospedagem |
|---|---|---|
| Frontend | React 19 + Vite | Vercel |
| Backend | Python 3.12, FastAPI | Render |
| NLU | PyTorch (modelo próprio) | junto do backend |
| Banco | PostgreSQL 16 | Supabase |
| Login | Supabase Auth (JWT) | Supabase |
| CI | GitHub Actions | — |

## Segurança

- **Login obrigatório em produção** (`AUTH_OBRIGATORIA=true`). O backend não
  vê senha: confere a assinatura e a validade do token do Supabase Auth.
- **Cada um só vê os próprios dados.** Planilha, conversa ou dataset de outra
  pessoa responde 404, sem revelar se o id existe.
- **Isolamento no próprio banco:** a aplicação conecta com um usuário de
  privilégio mínimo (`intellix_app`) e o PostgreSQL filtra as linhas por
  empresa (RLS, [migration 006](database/migrations/006_rls_e_usuario_app.sql)).
- **SQL só por template parametrizado**, auditoria de cada consulta em
  `log_consulta`, limite de requisições por IP e cabeçalhos de segurança
  (CSP, HSTS) no frontend.

## Resultados

| Indicador | Valor | Evidência |
|---|---|---|
| 100 perguntas de validação, ponta a ponta | **88/100** | [`avaliacao-correcoes-2026-11-06.md`](docs/avaliacao-correcoes-2026-11-06.md) |
| Testes automatizados do backend | **202** (198 aprovados; 4 de RLS rodados à parte como `intellix_app`, 7/7) | [`execucao_testes_2026-11-06.md`](docs/evidencias/execucao_testes_2026-11-06.md) |
| Backup e restauração em ambiente separado | 91,6 s para ~128 mil linhas | [`backup_restauracao_2026-11-05.md`](docs/evidencias/backup_restauracao_2026-11-05.md) |

Os 12 erros das 100 perguntas estão explicados um a um no mesmo relatório:
3 vendedores que não existem na base de teste, 5 frases que o modelo não
reconhece com confiança (o sistema pede para reformular), 3 intenções trocadas
e 1 pergunta sem período respondida com o ano corrente em vez de pedir o
período.

## Estrutura do repositório

```
backend/            API FastAPI
  app/main.py         rotas (/chat, /import, /resumo, /planilhas, /conversas...)
  app/nlu/            modelo treinado e baseline por regras
  app/sql/            templates SQL e executor
  app/importacao/     leitura e carga das planilhas (ETL)
  tests/              202 testes (pytest)
frontend/           aplicação React (Vite)
database/
  migrations/         schema, em ordem (001 a 008)
  seed.py             base de demonstração (8.941 itens, 2023 a 2026)
ia training/        geração do dataset, treino e avaliação do modelo NLU
scripts/            avaliação das 100 perguntas, backup/restauração, OpenAPI
docs/               contratos, decisões, avaliações, evidências e diagramas
```

## Rodar localmente

Precisa de Python 3.12, Node 22 e PostgreSQL 16.

**1. Banco** (a mesma montagem do CI):

```bash
createdb intellix
psql -d intellix -f database/local/supabase_minimo.sql
for f in database/migrations/*.sql; do psql -d intellix -v ON_ERROR_STOP=1 -f "$f"; done
DATABASE_URL=postgresql://postgres:SENHA@localhost:5432/intellix python database/seed.py
```

**2. Backend** (copie `backend/.env.example` para `backend/.env` e preencha
`DATABASE_URL`; com `AUTH_OBRIGATORIA=false` ele responde sem login):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**3. Frontend** (copie `frontend/.env.example` para `frontend/.env.local`):

```bash
cd frontend
npm ci
npm run dev
```

O login usa o Supabase Auth, então precisa de `VITE_SUPABASE_URL` e
`VITE_SUPABASE_ANON_KEY`. Para ver a interface sem servidor nenhum, use
`VITE_MOCK=true` (login e respostas simulados).

## Testes

```bash
cd backend && pytest -q -rs     # com DATABASE_URL apontando para o banco acima
cd frontend && npm run lint && npm run build
python scripts/avaliar_100_perguntas.py --modo api --url http://127.0.0.1:8000
```

O CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) roda em todo
pull request: `ruff`, a suíte completa contra um PostgreSQL temporário com o
modelo treinado ativo, e lint e build do frontend.

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/contratos.md`](docs/contratos.md) | formatos trocados entre as camadas e todas as rotas da API |
| [`docs/decisoes/`](docs/decisoes/) | por que star schema, Supabase e Render |
| [`docs/diagramas/`](docs/diagramas/README.md) | figuras do TCC, geradas a partir do código |
| [`docs/perguntas_validacao.md`](docs/perguntas_validacao.md) | as 100 perguntas de validação |
| [`docs/avaliacao-modelo-v1.2.md`](docs/avaliacao-modelo-v1.2.md) | avaliação do modelo NLU |
| [`docs/relatorio-execucao-testes.md`](docs/relatorio-execucao-testes.md) | execução dos testes automatizados |
| [`docs/migrations_aplicadas.md`](docs/migrations_aplicadas.md) | o que está aplicado em cada banco |
| [`docs/mapeamento_feedback_tc2.md`](docs/mapeamento_feedback_tc2.md) | cada ponto da orientação e onde está a evidência |
| [`ia training/README.md`](ia%20training/README.md) | como o modelo foi treinado |

## Licença

[MIT](LICENSE).
