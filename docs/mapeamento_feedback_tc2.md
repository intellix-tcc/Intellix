# Mapeamento dos feedbacks → código

Cruza os **dois** retornos recebidos e separa o que é **código** (prioridade
alta — o que a banca cobra do software) do que é **documento** (prioridade
menor, segundo momento). Para cada ponto de código: onde mexer e o estado.

- **Retorno 1 — Maria** (auditoria TC II): pendências de estrutura/evidência.
- **Retorno 2 — Relatório TC2** (31/10/2026, nota indicativa **72/100**):
  revisão técnica rigorosa em 14 achados (F01–F14). É o mais exigente, e a
  maior parte ainda não foi aplicada.

Peso da nota do Retorno 2: Estrutura 25 · Requisitos 20 · **Rigor técnico 40**
· Escrita 15. O que mais sobe a nota é o **rigor técnico** (verificação de
valor, ablação, correção de métrica).

---

## 🔴 Código — prioridade alta

| # | O que a banca pede | Onde no código | Estado |
|---|---|---|---|
| **F08** | Métrica por grão correto | `backend/app/sql/templates.py` (`ticket_medio`) | ✅ **feito** — `ticket_medio = sum(valor_total)/count(distinct venda_id)` (era `avg` por item). Falta ainda: regra para produto repetido na mesma venda (chave `unique(empresa,venda,produto)` em `001_schema.sql` descarta a 2ª linha) |
| **F01** | Oráculo que confere **valores**, não só status/tipo | `scripts/avaliar_100_perguntas.py`, `docs/perguntas_validacao.md`, `backend/tests/test_valores_referencia.py` | 🟡 **iniciado** — criada base pequena calculável à mão (`test_valores_referencia.py`, 5 testes de valor). Falta: valor esperado por pergunta nas 100 + anexar divergências |
| **F03** | **Ledger** das 100 perguntas (causa, esperado × observado) | harness do F01 + `docs/evidencias/` | ❌ a fazer |
| **F04** | Demonstrar contribuição da **cabeça de entidades** (ablação) | `backend/app/nlu/adaptador_modelo.py` (slots por regras; modelo só p/ VENDEDOR+intenção), novo script em `ia training/` | ❌ a fazer — ablação modelo-só × regras-só × híbrido; teste por entidade incl. PRODUTO |
| **F05** | Medir limiar, falso-aceite fora de domínio e margem | `backend/app/fallbacks.py` (limiar 0,70), `adaptador_modelo.py` (`_tem_termo_dominio`) | 🟡 parcial — filtro existe; falta medir e medir contra paráfrases válidas sem palavra-chave; pedir confirmação em caso ambíguo |
| **F09** | Auditoria + isolamento testado | `log_consulta` (existe em `001_schema.sql`, **vazia**); `acesso.py`, `main.py` | 🟡 auth já existe; falta **escrever em `log_consulta`** por consulta e **teste de isolamento** (2 empresas, troca de id, acesso direto); avaliar RLS no Postgres |
| **F10** | Backup/restore **comprovado** (não presumir Free) | `scripts/backup_db.py`, `scripts/restore_db.py` | 🟡 scripts existem; falta rodar dump+restore em ambiente separado, registrar tempo/resultado, definir RPO/RTO |
| **F11** | Rastreabilidade de testes | `backend/tests/`, `.github/workflows/`, `docs/relatorio-execucao-testes.md` | 🟡 relatório existe; falta mapear RF01–09/RNF01–08→testes, confirmar modo **modelo**, DB efêmero no CI (opcional) |
| **F07** | DER **real** do schema (não o diagrama de software) | gerar de `database/migrations/` | 🟡 doc, mas o artefato sai do schema real (grão, PK/FK, unicidade) + DDL sanitizado |

---

## ✅ Já resolvido nesta sessão (pontos do Retorno 2 que o código já cobre)

| Ponto | O que foi feito | Vira no texto |
|---|---|---|
| **F02** (intenções fracas) | `variacao_periodo` 0→7, `comparacao` 3→5, `desempenho` melhorou; geral 58→**78%** (modelo v1.1.0) | atualizar síntese/capítulo 8 |
| **F12** (importação indisponível) | importação de Excel **funciona e foi validada** | virar evidência |
| Resolução temporal | ano-de-referência por dataset + períodos relativos | — |
| **F09 (parte)** | autenticação no servidor + autorização por empresa (`auth.py`, `acesso.py`) | classificar RNF05 como parcial |
| **F08** | ticket médio corrigido + verificado por valor | atualizar descrição da métrica |
| **F01 (parte)** | base pequena com verificação de valor (`test_valores_referencia.py`) | descrever o oráculo com conferência numérica |

---

## 📄 Documento — prioridade menor (segundo momento)

- **F06**: reescrever a narrativa da matriz de confusão (linhas=verdade, colunas=predição).
- **F07**: trocar a figura do "DER" (hoje é diagrama de software) pelo DER real.
- **F12**: limitar conclusões ao cenário sintético; separar custo estimado × observado.
- **F13 / Maria**: ficha catalográfica, paginação desde a folha de rosto, listas/sumário, remissões cruzadas, número único da síntese.
- **F14**: declaração de uso de IA nos 4 eixos (modelos/versões, ambiente, datas, prompts/saídas, assinaturas).

---

## Ordem de ataque sugerida (código)

1. **F08** ✅ + **F01** 🟡 (verificação de valor) — iniciado.
2. **F03** — ledger das 100 perguntas a partir do harness do F01.
3. **F04** — ablação do NLU (contribuição da cabeça de entidades).
4. **F05 + F09** — medir limiar/fora-de-domínio; escrever auditoria + teste de isolamento.
5. **F10 / F11 / F07** — evidência de backup, rastreabilidade de testes, DER real.
