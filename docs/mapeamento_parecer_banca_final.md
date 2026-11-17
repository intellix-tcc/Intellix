# Mapeamento do parecer da banca final → ações

Terceira rodada de retorno (**parecer da banca final**, nota indicativa
**73,50/100**), depois da auditoria da Maria (TC II) e do Relatório TC2 (72/100).
Este painel cruza cada achado do parecer com a ação, separando o que é **código/
repositório** (executável agora) do que é **texto do TCC** (depende do documento
no Google Docs) e do que é **físico/processo** (assinaturas, Biblioteca).

A própria orientadora ordenou as entregas em três prioridades; usamos isso como
as três fases.

| Prioridade (parecer) | Entrega verificável |
|---|---|
| **Defesa** | consulta inédita com gabarito de valor · teste de isolamento · manifesto da versão publicada |
| **Depósito** | conclusão revisada · errata de remissões · conferência da ficha · declaração formalizada |
| **Seguimento** | teste independente + estudo com gestores · ensaio operacional em configuração normal |

Onde a nota mais sangra: **C — Rigor técnico (28/40)** e **D — Escrita/conclusão
(8,75/15)**. A Fase 1 ataca C; a Fase 2 ataca D.

---

## Fase 1 — DEFESA  ✅ implementada (código/repositório)

Tudo abaixo roda neste repositório contra um Postgres local semeado com
`database/seed.py` (ver README). As evidências datadas ficam em `docs/evidencias/`.

| Achado | Pedido da banca | O que foi feito | Evidência | Status |
|---|---|---|---|---|
| **F02** | Oráculo confere **valores**, não só status/tipo | Gabarito numérico independente das **14 consultas**: verdade recomputada em Python puro (seed determinístico) × templates SQL reais; separa técnico/semântico/numérico; cobre valor, filtro, grupo, ordenação, unidade, nulos, fronteira de período e venda multi-item | `scripts/gabarito_numerico.py`, `backend/tests/test_gabarito_numerico.py`, `docs/evidencias/gabarito_numerico_*.md` — **19/19** | ✅ |
| **F01** + defesa nº 1 | **Consulta inédita** (generalização), com cálculo conferível | Conjunto inédito (fora dos moldes e das 100), com gabarito de intenção **e de valor**; runner congela commit+hash do modelo e reporta por intenção, recusas e **IC95% de Wilson** | `docs/perguntas_ineditas.jsonl`, `scripts/avaliar_ineditas.py`, `docs/evidencias/avaliacao_ineditas_{app,nlu}_*.md` — **app 13/30, nlu 10/26** | ✅ |
| **F05/F09** | Demonstrar **isolamento** com dados fictícios | Demo ao vivo: 2 empresas fictícias, `intellix_app` (privilégio mínimo); RLS nega por padrão, A só vê A, pedir B é barrado, não apaga vendas, auditoria isolada | `scripts/demo_isolamento.py`, `docs/evidencias/demo_isolamento_*.md` — **6/6** | ✅ |
| **F07** | **Pacote de reprodução** (repo não recuperado) | Manifesto: commit, SHA-256 dos pesos + métricas embutidas, **fingerprint determinístico do dataset**, hash de migrações/templates, parâmetros e comandos | `scripts/manifesto_reproducao.py`, `docs/evidencias/manifesto_reproducao_*.md` | ✅ |

**A descoberta mais importante (F01):** em perguntas genuinamente inéditas a
acurácia cai para ~43% (IC95% 27–61%), contra 88/100 na bateria reutilizada —
confirmando, com honestidade, que **88/100 reflete o repertório, não
generalização aberta**. Quando o sistema entende a pergunta, o **valor é
exatamente conferível** (ticket, contagem, desempenho de vendedor, variação,
canal); quando não entende, na maioria **recusa com segurança** (422), em vez de
responder errado.

### Ações não-código da Defesa (da equipe)
- **Tornar o repositório recuperável pela banca** (o parecer diz que a consulta
  externa não o recuperou): dar acesso à banca, ou publicar um *release* com o
  pacote de reprodução. É a contrapartida humana do F07.
- **Perguntas de autores externos:** para rigor máximo, coletar perguntas de
  pessoas de fora da equipe e reexecutar `avaliar_ineditas.py` (aceita qualquer
  `perguntas_ineditas.jsonl`).

---

## Fase 2 — DEPÓSITO  ⏳ (depende do TCC no Google Docs)

Documento: **"TCC entrega final"** (Google Docs, dono `intellix3@gmail.com`).
Edição pelo conector exige permissão de escrita, ou a equipe cola os blocos que
eu redigir.

| Achado | Pedido da banca | Tipo | Status |
|---|---|---|---|
| **F03** | Repetir **ablação** na v1.2.0 com corpus externo e oráculo numérico | código | ⬜ a fazer |
| **F06** | Grão da venda e **reconciliação** com planilha de teste | código + texto | ⬜ a fazer |
| **F05** | Reteste de **carga em configuração normal** (limitador ligado, partida fria/quente) | código | ⬜ a fazer |
| **F04 / D2 / D3** | Reescrever a **conclusão**: separar modelo inicial/final/agente; rotular 58% histórico e 88% regressão; qualificar números por versão | texto TCC | ⬜ a fazer |
| **F09** | **Viabilidade comercial**: datar fontes dos planos, premissas, conclusão econômica como hipótese | texto TCC | ⬜ a fazer |
| **F08** | **Errata** das remissões (Figuras 1–6 descritas como telas × listadas como diagramas); conferir ficha | texto + físico | ⬜ a fazer |
| **F10** | **Declaração de IA** formalizada (4 autores + orientadora) | físico (texto preparável) | ⬜ a fazer |

---

## Fase 3 — SEGUIMENTO  🔭 (trabalhos futuros)

| Pedido da banca | Observação |
|---|---|
| Teste independente por terceiros + estudo com **gestores reais** | provável "trabalhos futuros" no texto, não entrega executada |
| Ensaio operacional prolongado em configuração de produção normal | idem; a banca pede para **não extrapolar** vazão/disponibilidade |

---

## Reproduzir a Fase 1

```bash
# banco local (ver README) + seed determinístico
createdb intellix
psql -d intellix -f database/local/supabase_minimo.sql
for f in database/migrations/*.sql; do psql -d intellix -v ON_ERROR_STOP=1 -f "$f"; done
DATABASE_URL=postgresql://... python database/seed.py

DATABASE_URL=postgresql://... python scripts/gabarito_numerico.py --saida docs/evidencias
DATABASE_URL=postgresql://... python scripts/demo_isolamento.py  --saida docs/evidencias
DATABASE_URL=postgresql://... python scripts/manifesto_reproducao.py --saida docs/evidencias
DATABASE_URL=postgresql://... NLU_BACKEND=modelo EMPRESA_ID=00000000-0000-0000-0000-000000000001 \
    python scripts/avaliar_ineditas.py --modo app --saida docs/evidencias
```
