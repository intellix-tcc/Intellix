# Mapeamento dos feedbacks → código

Cruza os **dois** retornos recebidos e separa o que é **código** (prioridade
alta — o que a banca cobra do software) do que é **documento** (prioridade
menor, segundo momento). Para cada ponto de código: onde mexer e o estado.

- **Retorno 1 — Maria** (auditoria TC II): pendências de estrutura/evidência.
- **Retorno 2 — Relatório TC2** (31/10/2026, nota indicativa **72/100**):
  revisão técnica rigorosa em 14 achados (F01–F14). É o mais exigente. Em
  06/11/2026 todos os pontos de código estão aplicados (tabela abaixo); os
  pontos de documento (F06, F07 no texto, F12–F14) ficam para a revisão final
  do texto.

Peso da nota do Retorno 2: Estrutura 25 · Requisitos 20 · **Rigor técnico 40**
· Escrita 15. O que mais sobe a nota é o **rigor técnico** (verificação de
valor, ablação, correção de métrica).

---

## Estado do código em 06/11/2026 (versão final)

Todos os pontos de código do Retorno 2 têm implementação e evidência
versionada. O que resta é levar cada evidência para o texto (coluna "Vira no
texto") e trocar as figuras.

| # | O que a banca pediu | O que foi feito | Evidência | Vira no texto |
|---|---|---|---|---|
| **F01** | Oráculo que confere **valores**, não só status/tipo | ✅ base calculável à mão com valores conferidos no `/chat` real (faturamento, ticket médio, contagem de vendas, ranking, período vazio) e produtos sem saída com recorte | `backend/tests/test_valores_referencia.py`, `test_sem_saida_recorte.py` | descrever o oráculo numérico. Limite honesto: nas 100 perguntas o critério continua sendo status HTTP + template, não o valor |
| **F02** | Intenções fracas | ✅ modelo v1.2.0; 100 perguntas: 58 → 78 → 83 → **88/100** | `docs/avaliacao-correcoes-2026-11-06.md`, `docs/avaliacao-modelo-v1.2.md` | atualizar síntese e cap. 8 com 88/100 |
| **F03** | **Ledger** das 100 perguntas (causa, esperado × observado) | ✅ cada erro com esperado, obtido, causa e "depende de" | `docs/evidencias/avaliacao_api_2026-11-06_versao_final.md` | tabela dos 12 erros e suas causas |
| **F04** | Contribuição da **cabeça de entidades** (ablação) | ✅ modelo × regras × modelo sem BIO × modelo só com regras de slot | `docs/evidencias/ablacao_nlu_2026-11-05_1036.md`, `ia training/ablacao_nlu.py` | resultado: a cabeça BIO soma +0,0 pp; a heurística de vendedor, +3,6 pp |
| **F05** | Limiar, falso-aceite fora de domínio e margem | ✅ medido: limiar 0,70 aceita 78/84 válidas e 0/12 fora de domínio; margens e custo do filtro léxico registrados | `docs/evidencias/confianca_filtro_2026-11-05_1044.md`, `ia training/medir_confianca.py` | justificar o 0,70 com a varredura. Pedir confirmação em caso de margem pequena ficou como trabalho futuro |
| **F07** | DER **real** do schema | ✅ DER refeito das migrations (grão, PK/FK, unicidade), com `conversa` (008) | `docs/diagramas/der.png`, `der.dot`, `der.md` | trocar a figura 4 |
| **F08** | Métrica no grão correto | ✅ `ticket_medio = sum(valor_total)/count(distinct venda_id)`; produto repetido na mesma venda agora é **somado** na importação (`linhas_agrupadas`), não descartado | `app/sql/templates.py`, `app/importacao/etl.py`, `test_valores_referencia.py`, `test_import_carga.py` | atualizar a descrição da métrica e da carga |
| **F09** | Auditoria + isolamento testado | ✅ cada consulta gravada em `log_consulta`; dataset de outra pessoa → 404; **RLS no Postgres** com usuário de privilégio mínimo `intellix_app` (produção conecta com ele); login obrigatório em produção (`AUTH_OBRIGATORIA=true`) | `test_isolamento.py`, `test_auditoria.py`, `test_rls.py` (7/7 como `intellix_app`), migration `006_rls_e_usuario_app.sql` | RNF05 pode deixar de ser "parcial" |
| **F10** | Backup/restore **comprovado** | ✅ dump + restauração em ambiente separado, 91,6 s para ~128 mil linhas; RPO 24 h e RTO < 15 min | `docs/evidencias/backup_restauracao_2026-11-05.md`, `scripts/backup_db.py`, `scripts/restore_db.py` | seção de operação/recuperação |
| **F11** | Rastreabilidade de testes | ✅ 202 testes mapeados por módulo e capacidade; CI com Postgres efêmero e `NLU_BACKEND=modelo` a cada PR | `docs/evidencias/execucao_testes_2026-11-06.md`, `docs/relatorio-execucao-testes.md` | usar o texto do apêndice do relatório (202 testes, 198 aprovados, 4 de RLS à parte) |
| **F12** | Importação indisponível | ✅ importação de Excel funciona, com relatório de linhas rejeitadas e motivos; "minhas planilhas" na conta | `test_import.py`, `test_import_carga.py`, `test_planilhas.py` | virar evidência; limitar conclusões ao cenário sintético |

---

## 📄 Documento — prioridade menor (segundo momento)

- **F06**: reescrever a narrativa da matriz de confusão (linhas=verdade, colunas=predição).
- **F07**: trocar a figura do "DER" (hoje é diagrama de software) pelo DER real.
- **F12**: limitar conclusões ao cenário sintético; separar custo estimado × observado.
- **F13 / Maria**: ficha catalográfica, paginação desde a folha de rosto, listas/sumário, remissões cruzadas, número único da síntese.
- **F14**: declaração de uso de IA nos 4 eixos (modelos/versões, ambiente, datas, prompts/saídas, assinaturas).
