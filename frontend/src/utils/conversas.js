// Funções de leitura sobre o histórico guardado por historico.js.
//
// Ficam separadas da persistência de propósito: historico.js só sabe gravar e
// ler o localStorage; aqui é onde se decide o que mostrar de cada conversa e
// como filtrar.

/** Última pergunta feita — serve de prévia do ponto onde a conversa parou. */
export function ultimaPergunta(conversa) {
  const perguntas = (conversa?.mensagens || []).filter((m) => m.tipo === "usuario");
  return perguntas.length ? perguntas[perguntas.length - 1].texto : "";
}

const DIA_MS = 24 * 60 * 60 * 1000;

/** "Hoje", "Ontem", "Há 3 dias" ou a data cheia. */
export function quando(iso, agora = new Date()) {
  if (!iso) return "";
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return "";

  // Compara por dia do calendário, não por 24h corridas: 23h de ontem para
  // 1h de hoje são 2 horas, mas continuam sendo "ontem".
  const meiaNoite = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const dias = Math.round((meiaNoite(agora) - meiaNoite(data)) / DIA_MS);

  if (dias <= 0) return "Hoje";
  if (dias === 1) return "Ontem";
  if (dias < 7) return `Há ${dias} dias`;
  return data.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}

function normalizar(texto) {
  return String(texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, ""); // "março" acha "marco", e vice-versa
}

/**
 * Filtra o histórico real — título e o texto de todas as perguntas da conversa.
 * Busca sem acento e sem caixa. Termo vazio devolve a lista inteira.
 */
export function filtrarConversas(conversas, termo) {
  const alvo = normalizar(termo).trim();
  if (!alvo) return conversas;

  return conversas.filter((c) => {
    if (normalizar(c.titulo).includes(alvo)) return true;
    return (c.mensagens || []).some(
      (m) => m.tipo === "usuario" && normalizar(m.texto).includes(alvo)
    );
  });
}
