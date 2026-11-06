# Inventário de pendências do TCC (D10)

Lista viva do que falta no documento escrito. **Regra do plano: uma hora
por semana, desde já.** Toda vez que um dev entrega algo, o capítulo
correspondente é atualizado — se acumular para o mês 5, vira uma semana
perdida na pior hora possível.

Origem: comentários da Maria Luiza no documento + o que o novo escopo
(importação de planilhas) obriga a mudar.

---

## 1. Formatação e revisão

| Item | Onde | Status |
|---|---|---|
| Revisar todos os travessões | documento inteiro | ⬜ |
| Padronizar e legendar as figuras 1 a 6 | ver seção 2 | ⬜ |
| Adequar o MER ao padrão visual do grupo | 6.7 | ⬜ |
| Adequar o diagrama arquitetural ao padrão visual do grupo | 7.2 | ⬜ |
| Preencher os `[data]` de acesso das referências | referências | ⬜ |

### Padrão de figura (conferir contra o guia da UNIP antes de aplicar em massa)

- Legenda **acima** da figura: `Figura 1 – Descrição da figura`
- Fonte **abaixo**: `Fonte: elaborado pelos autores (2026).`
- Numeração sequencial, sem pular
- Toda figura precisa ser **citada no texto antes** de aparecer
- Mesma fonte/tamanho de legenda em todas as seis

---

## 2. Figuras 1 a 6 — mapear antes de padronizar

Preencher com o que cada uma é hoje, para saber o que precisa mudar:

| Figura | O que é | Seção | Precisa de | Status |
|---|---|---|---|---|
| 1 | | | | ⬜ |
| 2 | | | | ⬜ |
| 3 | | | | ⬜ |
| 4 | | | | ⬜ |
| 5 | | | | ⬜ |
| 6 | | | | ⬜ |

Candidatas a virar figura nova, agora que existem: print da tela de chat
com resultado real, print do gráfico de barras, print da mensagem de
hibernação (heurística #1), as 3 telas do wizard de importação.

---

## 3. Referências pendentes (23)

Marcar quando a referência completa estiver na lista **e** citada no corpo
do texto. A coluna "provável seção" é palpite meu a partir do tema de cada
autor — **confirmar antes de usar**, principalmente as marcadas com `?`.

| Autor | Provável seção / tema | Referência completa | Citada no texto |
|---|---|---|---|
| Artstein & Poesio | concordância entre anotadores (dataset NLU) — cap. 8 | ⬜ | ⬜ |
| Beyer | engenharia de confiabilidade / operação `?` | ⬜ | ⬜ |
| Brasil (LGPD) | privacidade e proteção de dados | ⬜ | ⬜ |
| Cohen | kappa — concordância entre anotadores, cap. 8 | ⬜ | ⬜ |
| Gil | metodologia científica — cap. 3 | ⬜ | ⬜ |
| Goodfellow | aprendizado profundo — cap. 7.4 | ⬜ | ⬜ |
| Gruber | ontologias | ⬜ | ⬜ |
| Guarino | ontologias | ⬜ | ⬜ |
| Humble & Farley | entrega contínua / deploy — ADR 003 e cap. 7 | ⬜ | ⬜ |
| Inmon | data warehouse — cap. 6.7 e ADR 001 | ⬜ | ⬜ |
| Kimball & Ross | modelagem dimensional / star schema — cap. 6.7, ADR 001 | ⬜ | ⬜ |
| Machado | `?` a confirmar | ⬜ | ⬜ |
| Noy & McGuinness | construção de ontologias | ⬜ | ⬜ |
| Osterwalder | modelo de negócio / canvas | ⬜ | ⬜ |
| OWASP | segurança de aplicação — cap. 7.7 (SQL injection) | ⬜ | ⬜ |
| Porter | análise competitiva / estratégia | ⬜ | ⬜ |
| Pruitt & Adlin | **personas — seção 5.2.1 (é a sua seção)** | ⬜ | ⬜ |
| Sculley | dívida técnica em sistemas de ML | ⬜ | ⬜ |
| Srivastava | `?` a confirmar (possivelmente dropout/regularização) | ⬜ | ⬜ |
| Stallings & Brown | segurança computacional — cap. 7.7 | ⬜ | ⬜ |
| Young | `?` a confirmar | ⬜ | ⬜ |
| Yu | `?` a confirmar | ⬜ | ⬜ |
| Zhong | `?` a confirmar (possivelmente text-to-SQL / Seq2SQL) | ⬜ | ⬜ |

Os cinco marcados com `?` precisam de definição do grupo: quem indicou a
referência sabe qual obra é e para que serve. Sem isso não dá para
formatar nem citar.

---

## 4. Mudanças obrigadas pelo novo escopo (importação de planilhas)

| Item | Seção | Status |
|---|---|---|
| RFs de importação e exportação | 6.2 | ⬜ |
| Novas entidades no MER: `empresa`, `usuario`, `importacao`, `staging_venda` | 6.7.4 | ⬜ |
| Sexto componente: "Módulo de Ingestão" | 7.2 | ⬜ |
| Novos casos de erro: planilha inválida, coluna faltante | 7.6 | ⬜ |
| Indicador "taxa de sucesso de importação" | 8.4 | ⬜ |
| Risco novo: heterogeneidade de planilhas | 6.8 | ⬜ |

**Atenção em 6.7.4** (atualizado em 06/11/2026): `empresa`, `importacao` e
`staging_venda` existem no banco (`database/migrations/001_schema.sql`). Não
há tabela `usuario` própria: o login é do **Supabase Auth**, e os usuários
ficam em `auth.users`, gerenciada pelo Supabase. O sistema liga os dados a
eles por chave estrangeira: `empresa.dono_id` (migration 005, quem importou a
planilha) e `conversa.dono_id` (migration 008, histórico de conversas). No
MER, representar `auth.users` como entidade externa e descrever `usuario`
assim, não como tabela do Intellix. O DER real está em
`docs/diagramas/der.png` (de `der.dot`, colunas conferidas contra as
migrations; ver `docs/diagramas/README.md`).

---

## 5. Material que já existe para puxar

Coisas prontas no repositório que viram texto, figura ou tabela sem
trabalho novo:

| Fonte | Alimenta |
|---|---|
| `docs/decisoes/003-por-que-render.md` | justificativa da heurística #1 (hibernação de ~30s) — **seção 4.7** |
| `docs/decisoes/001-por-que-star-schema.md` | cap. 6.7 e a defesa do modelo dimensional |
| `docs/decisoes/002-por-que-supabase.md` | cap. 7 / infraestrutura |
| `docs/teste_usuarios.md` | roteiro e resultados do teste — **seção 4.7** |
| `docs/perguntas_validacao.md` | **Tabela 1 do capítulo 8** (taxa de acerto por categoria) |
| `docs/contratos.md` | contratos entre camadas — cap. 7 |
| `docs/migrations_aplicadas.md` | evidência de implantação (datas, volumes) |
| `database/migrations/` e `docs/diagramas/der.png` | schema real — cap. 6.7 |
| `backend/app/sql/templates.py` e `ia training/moldes.py` | as 12 intenções do modelo e as 14 consultas (12 + 2 refinamentos; ver `docs/contratos.md`) — cap. 7 |
| `docs/openapi.json` | contrato completo da API (10 operações) — cap. 7 |
| `docs/evidencias/execucao_testes_2026-11-06.md` | testes da versão final — cap. 8 |
| `docs/avaliacao-correcoes-2026-11-06.md` | 100 perguntas, 88/100 — cap. 8 |

**Números reais já disponíveis para o capítulo 8**: 8.941 itens de venda,
≈ R$ 2,72 milhões, período 2023–2026, 40 produtos, 1.461 linhas em
`dim_data` (3.653 depois da migration 003, que estende o calendário até 2032).
Backend com **202 testes automatizados** (198 aprovados e 4 de RLS ignorados
no CI, aprovados à parte como `intellix_app`; ver
`docs/evidencias/execucao_testes_2026-11-06.md`). 100 perguntas de validação:
**88/100** com o modelo v1.2.0. Frontend publicado em
`intellix-lilac.vercel.app`, backend em `intellix-api.onrender.com`.

---

## 6. Registro semanal (a regra da uma hora)

| Semana | O que foi feito | Tempo |
|---|---|---|
| | | |
