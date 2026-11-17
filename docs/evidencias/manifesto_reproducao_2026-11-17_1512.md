# Manifesto de reprodução — versão publicada

Fixa o que é preciso para reproduzir bit a bit os ensaios (parecer da
banca final, F07). Gerado por `scripts/manifesto_reproducao.py`.

- **Data:** 17/11/2026 15:12 (UTC+0000)
- **Commit:** `7cff7aae3e8f99207d866dd38ce99b71371fdd59` (claude/vigilant-mccarthy-wvy9ng, 9 arquivo(s) não commitados)
- **Remoto:** https://github.com/intellix-tcc/Intellix

## 1. Pesos do modelo (SHA-256)

| Arquivo | Bytes | SHA-256 | Métricas embutidas |
|---|---:|---|---|
| `backend/app/nlu/intellix_nlu_v1.1.0.pt` | 1,151,931 | `3e9035468be24901ca82d3fe5d59951c…` | versão 1.1.0; acc_validacao=0.9979 |
| `backend/app/nlu/intellix_nlu_v1.2.0.pt` | 1,169,745 | `ea30338e9626f4b67bbec49ad73adc37…` | versão 1.2.0; acc_validacao=0.9986 |
| `ia training/modelos/intellix_nlu_v1.0.0_2026-09-08.pt` | 1,148,133 | `a48414be184a1ce1ca6f5528eb79befd…` | versão 1.0.0; acc_intencao_teste_real=0.9333, f1_entidades_teste_real=0.8378, acc_intencao_teste_sintetico=0.9958, f1_entidades_teste_sintetico=0.9957 |
| `ia training/modelos/intellix_nlu_v1.0.0_2026-10-21_retreino.pt` | 1,151,077 | `a5be9ea46fccd2efa83b37d684e2d9a8…` | versão 1.0.0; acc_intencao_teste_real=0.9, f1_entidades_teste_real=0.8679, acc_intencao_teste_sintetico=0.9986, f1_entidades_teste_sintetico=0.994 |

## 2. Dataset sintético (determinístico)

Os dados não precisam ser anexados: são reproduzidos por
`database/seed.py` com semente fixa. O fingerprint abaixo é o SHA-256 do
grão da fato gerado; recriar o seed e conferir o hash prova que os dados
são os mesmos.

- **SEED:** `42`  ·  **empresa_id:** `00000000-0000-0000-0000-000000000001`
- **Volume:** 8941 itens em 3527 vendas  ·  faturamento R$ 2,717,797.23
- **Fingerprint SHA-256:** `58d126cf328963d86c9845db5ef1b61189615913427320516864aba3700bec5f`

## 3. Migrações aplicadas (ordem e SHA-256)

| # | Migração | SHA-256 |
|---|---|---|
| 1 | `001_schema.sql` | `82c062c24160ed22ff8e17620b190d89…` |
| 2 | `002_dim_data.sql` | `65881360c80ae5496e77eb915ad2ad32…` |
| 3 | `003_estende_dim_data.sql` | `b3ef487c6509088edee31b7f5cc59ee0…` |
| 4 | `004_views_ranking_desempenho.sql` | `fe55e7c735632d0764a59b81f7659567…` |
| 5 | `005_dono_do_dataset.sql` | `9e800a7c476298bf7ea7f3502c347002…` |
| 6 | `006_protege_api_do_supabase.sql` | `033e491e0b4cfbf99c78da12d2800372…` |
| 7 | `006_rls_e_usuario_app.sql` | `406a10cf1da8cecd28ae46c84085ca72…` |
| 8 | `007_minhas_planilhas.sql` | `0e9bb4aec71a18384ab9adbef0faaab2…` |
| 9 | `008_historico_conversas.sql` | `ab0e4bcc9ce7f03e356466c3e24a21f0…` |

## 4. Artefatos de consulta e avaliação (SHA-256)

| Artefato | SHA-256 |
|---|---|
| `backend/app/sql/templates.py` (14 consultas) | `bf9a201164a7971f6b08385b0448131e…` |
| `docs/perguntas_validacao.md` | `6c6315a980d7523263937247518a6bd0…` |

## 5. Parâmetros de execução (relógio e configuração)

| Parâmetro | Valor do ensaio | Observação |
|---|---|---|
| `NLU_BACKEND` | `modelo` | usa o `.pt` treinado, não o baseline de regras |
| Limiar de confiança | `0,70` | abaixo disso o sistema pede para reformular |
| `AUTH_OBRIGATORIA` | `false` (local) / `true` (produção) | em produção exige login |
| `LIMITE_REQUISICOES` | `0` nos ensaios de carga / vazão | **ligado em operação normal** (ver reteste F05) |
| Relógio | datas fixas 2023–2026 no dataset | perguntas relativas ancoram na última venda (`R.referencia()`) |

## 6. Comandos de reprodução

```bash
# 1. banco (Postgres 16)
createdb intellix
psql -d intellix -f database/local/supabase_minimo.sql
for f in database/migrations/*.sql; do psql -d intellix -v ON_ERROR_STOP=1 -f "$f"; done
DATABASE_URL=postgresql://postgres:***@localhost:5432/intellix python database/seed.py

# 2. gabarito numérico das 14 consultas (F02)
DATABASE_URL=postgresql://... python scripts/gabarito_numerico.py --saida docs/evidencias

# 3. bateria de 100 perguntas (regressão)
cd backend && NLU_BACKEND=modelo uvicorn app.main:app &
python scripts/avaliar_100_perguntas.py --modo api --url http://127.0.0.1:8000

# 4. conjunto inédito (generalização, F01) — quando presente
python scripts/avaliar_ineditas.py --url http://127.0.0.1:8000
```

## 7. Como conferir este manifesto

Rodar `python scripts/manifesto_reproducao.py` na mesma `commit` deve
reproduzir todos os hashes acima. Qualquer divergência em pesos, dataset,
migração ou template indica que o ensaio foi feito sobre outro estado.

