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

### Pacote de reprodução  ✅ implementado
- **`REPRODUZIR.md`** (guia validado, comando a comando, com resultados esperados)
  e **`scripts/configurar_reproducao.sh`** (configura o banco e semeia em um
  comando). Testados de ponta a ponta. É a contrapartida de repositório do F07.

### Ações não-código da Defesa (da equipe)
- **Tornar o repositório acessível à banca** (o parecer diz que a consulta externa
  não o recuperou): dar acesso ao repositório, ou publicar um *release* apontando
  para o `REPRODUZIR.md`. A parte de repositório já está pronta; falta o acesso.
- **Perguntas de autores externos:** para rigor máximo, coletar perguntas de
  pessoas de fora da equipe e reexecutar `avaliar_ineditas.py` (aceita qualquer
  `perguntas_ineditas.jsonl`).

---

## Fase 2 — DEPÓSITO

### Código  ✅ implementado

| Achado | Pedido da banca | O que foi feito | Evidência | Status |
|---|---|---|---|---|
| **F03** | Repetir **ablação** na v1.2.0 com corpus externo e oráculo numérico | Ablação v1.2.0 sobre o conjunto inédito; cada aceito executado e valor conferido; cobertura × risco por configuração. **Cabeça BIO = +0** de valor; heurística +1 | `ia training/ablacao_nlu_externa.py`, `docs/evidencias/ablacao_nlu_v1.2_externa_*.md` | ✅ |
| **F05** | Reteste de **carga em configuração normal** | Limitador LIGADO; partida fria (55 ms) × quente (17 ms); latência por estado; burst > 30/min → 429 (a proteção que o teste anterior desligou). Sem extrapolar vazão | `scripts/teste_carga_normal.py`, `docs/evidencias/teste_carga_normal_*.md` | ✅ |
| **F06** | Grão da venda e **reconciliação** com planilha de teste | Planilha conhecida × banco: vendas, itens, faturamento, ticket, grão (repetido somado), integridade referencial (0 órfãs), idempotência. Teste no CI | `scripts/reconciliacao_carga.py`, `backend/tests/test_reconciliacao_carga.py`, `docs/evidencias/reconciliacao_carga_*.md` | ✅ |

### Texto do TCC

Documento: **"TCC entrega final"** (Google Docs, dono `intellix3@gmail.com`). Com
permissão de escrita, as correções de texto foram aplicadas como **sugestões** —
a equipe revisa e aceita no próprio documento. Os blocos completos ficam em
`docs/blocos_texto_tcc_banca_final.md`.

| Achado | Pedido da banca | Tipo | Status |
|---|---|---|---|
| **F04 / D2 / D3** | Conclusão: separar versões; rotular 58% histórico e 88% regressão; reportar a generalização | texto TCC | 🟡 3 sugestões no doc — falta **aceitar** |
| **F09** | **Viabilidade** econômica como hipótese; datar fontes dos planos | texto TCC | 🟡 Hipótese + datação do Quadro 10 como sugestões — falta **aceitar** |
| **F08** | **Errata** das remissões de figuras; conferir ficha | texto + físico | 🟢 Remissões **já corretas** no doc atual (Figura 1 = diagrama; §5.9 cita telas 11/19/20); ⬜ ficha com a Biblioteca (físico) |
| **F10** | **Declaração de IA** formalizada (4 autores + orientadora) | físico | ⬜ Assinaturas e datas (físico) |

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
