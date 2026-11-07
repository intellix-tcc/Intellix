# ADR 004 — Backend em camadas, com porta e adaptadores para o NLU

- **Status:** aceito
- **Data:** 06/11/2026 (registro de uma decisão tomada em out/2026)
- **Decisores:** equipe Intellix

## Contexto

O backend recebe uma pergunta em português e devolve um resultado consultado no
banco. No início do projeto, a peça central (o modelo de IA que interpreta a
pergunta) **ainda não existia**: o treino seguia em paralelo (Dev A), enquanto o
resto do backend precisava ficar pronto e testável (Dev B e Dev C). Também havia
um requisito de segurança: o texto do usuário nunca pode virar SQL.

Precisávamos de uma organização que permitisse:

1. trocar o interpretador de perguntas (regras → modelo treinado → nova versão
   do modelo) sem mexer no resto do sistema;
2. testar o fluxo inteiro sem o modelo e, em parte, sem banco;
3. manter o acesso ao banco restrito a consultas pré-definidas.

## Decisão

Organizar o backend (`backend/app/`) em camadas, com responsabilidade única por
módulo, e usar o padrão **porta e adaptadores** (a ideia central da arquitetura
hexagonal) no ponto em que a troca de implementação era certa: o NLU.

| Camada | Módulos | O que faz |
|---|---|---|
| Entrada (HTTP) | `main.py`, `models.py`, `auth.py`, `limite.py` | Recebe as requisições, valida os dados (Pydantic), autentica pelo token do Supabase e limita a taxa de requisições |
| Interpretação (NLU) | `nlu/base.py` (porta), `nlu/regras.py` e `nlu/adaptador_modelo.py` (adaptadores) | Transforma o texto em uma `Interpretacao`: intenção, confiança e entidades |
| Regras de negócio | `filtros.py`, `contexto.py`, `refino.py`, `periodo_dataset.py`, `fallbacks.py` | Completam e validam a interpretação: catálogo do dataset, continuação da conversa, período de referência, limiar de confiança |
| Consulta | `sql/templates.py`, `sql/executor.py`, `sql/evolucao.py` | Escolhe um template SQL fixo e o executa com parâmetros |
| Dados | `db.py`, `acesso.py`, `importacao/`, `auditoria.py` | Pool de conexões, isolamento por empresa (RLS), importação de planilhas e registro das consultas |

**A porta do NLU** é o protocolo `NLUService` (`nlu/base.py`), com um único
método, `parse(texto) -> Interpretacao`. Há dois adaptadores:

- `RuleBasedNLU`: regras determinísticas, usado como base de comparação e como
  plano B;
- `ModeloTreinadoNLU`: a rede treinada (arquivo `.pt`).

A escolha é feita na inicialização, pela variável `NLU_BACKEND`
(`regras` ou `modelo`), na função `_criar_nlu()` do `main.py`. Nenhuma outra
parte do código sabe qual adaptador está em uso.

**O contrato entre as camadas** é o modelo `Interpretacao` (`models.py`),
descrito em `docs/contratos.md`. O NLU só escolhe **qual** template usar e
preenche os parâmetros; o SQL é fixo e parametrizado pelo psycopg.

## Justificativa

- **Trabalho em paralelo:** o backend foi construído e testado com o
  `RuleBasedNLU` enquanto o modelo era treinado. Quando o modelo ficou pronto,
  entrou com um adaptador novo e uma variável de ambiente, sem alterar o
  executor, os templates nem o frontend. As versões seguintes do modelo
  (v1.1.0 e v1.2.0) também entraram só pela troca do arquivo `.pt`, que pode ser
  escolhido pela variável `NLU_MODELO`.
- **Comparação justa:** com a mesma porta, as 100 perguntas de validação foram
  executadas com regras e com o modelo (`scripts/avaliar_100_perguntas.py
  --modo nlu`), medindo o ganho do modelo de forma isolada.
- **Segurança:** como a pergunta nunca vira SQL, injeção de SQL pelo chat não é
  possível por construção. Isso se soma ao RLS por empresa (migration 006).
- **Testabilidade:** a maior parte dos testes (`backend/tests/`) roda sem banco
  e sem o modelo, inclusive no CI.
- **Memória:** o PyTorch só é importado com `NLU_BACKEND=modelo`, o que mantém
  o modo de regras leve.

## Alternativas consideradas

- **Arquitetura hexagonal completa** (portas também para o banco, a autenticação
  e a importação): descartada. Só existe um banco (PostgreSQL) e não há troca
  prevista; criar interfaces para ele aumentaria o código sem benefício no
  escopo do TCC. Os testes que precisam de banco rodam contra o Supabase de
  desenvolvimento ou um PostgreSQL local.
- **Gerar SQL com o modelo (text-to-SQL):** descartada por segurança e
  previsibilidade; os templates garantem consultas revisadas e testadas.
- **Tudo no `main.py`:** descartada; dificultaria testar cada etapa e o
  trabalho simultâneo de quatro pessoas.

## Consequências

- Uma nova intenção exige três passos: incluir o exemplo no treino do modelo,
  criar o template em `sql/templates.py` e cobrir com teste.
- O `main.py` ainda importa diretamente as camadas de negócio e de dados; elas
  não são intercambiáveis como o NLU. É uma simplificação consciente (ver
  Alternativas).
- O diagrama `docs/diagramas/arquitetura_camadas.png` representa esta
  organização; os arquivos `arquitetura_hexagonal*.drawio` são a versão de
  outubro de 2026, mantida como histórico.
