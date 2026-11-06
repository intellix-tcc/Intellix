# Diagramas do TCC

Cada figura do capítulo 4 tem a fonte versionada aqui e é gerada por
ferramenta, a partir do código e do banco atuais (06/11/2026).

| Figura | Fonte | Imagem | Como gerar |
|---|---|---|---|
| 1 – Casos de uso | `casos_de_uso.dot` (+ `ator.png`) | `casos_de_uso.png` | `dot -Tpng -Gdpi=200 casos_de_uso.dot -o casos_de_uso.png` |
| 2 – Classes | `classes.dot` | `classes.png` | `dot -Tpng -Gdpi=200 classes.dot -o classes.png` |
| 3 – Sequência | `sequencia.py` | `sequencia.png` | `python sequencia.py` (precisa de matplotlib) |
| 4 – Modelo entidade-relacionamento | `der.dot` / `der.md` | `der.png` | `dot -Tpng -Gdpi=200 der.dot -o der.png` (colunas conferidas contra as migrações) |
| 5 – Fluxograma | `fluxograma.dot` | `fluxograma.png` | `dot -Tpng -Gdpi=200 fluxograma.dot -o fluxograma.png` |
| 6 – Arquitetura em camadas | `arquitetura_camadas.dot` | `arquitetura_camadas.png` | `dot -Tpng -Gdpi=200 arquitetura_camadas.dot -o arquitetura_camadas.png` |

O que cada diagrama segue no código:

- **Sequência e fluxograma:** a ordem de `backend/app/main.py::chat` e de
  `backend/app/sql/executor.py` (recusa por confiança, filtros, contexto e
  refino, parâmetro ausente, sem resultado, registro em `log_consulta`).
- **Classes:** os nomes reais (`NLUService.parse`, `RuleBasedNLU`,
  `ModeloTreinadoNLU`, `ModeloIntellix`, `executar_template`, `TEMPLATES`...).
  Assinaturas resumidas, sem a conexão com o banco.
- **Arquitetura:** só o que está implantado. A segurança em nível de linha e o
  usuário com privilégio mínimo (`006_rls_e_usuario_app.sql`) estão aplicados
  no ambiente de desenvolvimento (ver `docs/migrations_aplicadas.md`).

`arquitetura_hexagonal*.drawio` são a versão de outubro de 2026, anterior à
importação de planilhas e ao login; ficam como histórico.
