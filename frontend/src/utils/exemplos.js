import { CAPACIDADES_ESTATICAS } from "./capacidades";

// Pequena amostra de perguntas que o agente responde bem — usada onde cabe
// uma lista curta: a resposta de confiança baixa no chat e a FAQ. Heurística
// 3 (Nielsen): o usuário não deve adivinhar o que a ferramenta entende, então
// a interface mostra.
//
// Deriva da mesma fonte de capacidades (utils/capacidades.js, espelho do GET
// /capacidades) para não virar mais uma lista paralela que diverge com o
// tempo — a lista completa das 14 análises vive na tela "O que posso
// perguntar". Aqui pegamos o 1º exemplo de quatro intenções variadas.
//
// Em módulo próprio porque é usado pelo chat e pela FAQ, e porque arquivo de
// componente só deve exportar componentes (regra do Fast Refresh).
const CHAVES_AMOSTRA = ["total_vendas_periodo", "top_produtos", "ticket_medio", "top_clientes"];

export const EXEMPLOS = CHAVES_AMOSTRA.map(
  (chave) => CAPACIDADES_ESTATICAS.intencoes.find((i) => i.chave === chave)?.exemplos[0]
).filter(Boolean);
