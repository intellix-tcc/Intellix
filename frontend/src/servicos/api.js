const API = import.meta.env.VITE_API_URL;
const MOCK = import.meta.env.VITE_MOCK === "true";

const FALSAS = {
  numero: {
    titulo: "Faturamento em março de 2024",
    colunas: ["periodo", "faturamento"],
    linhas: [["2024-03", 208725.39]],
    tipo_visualizacao: "numero",
    confianca: 0.93,
    gerado_em: new Date().toISOString(),
  },
  barra: {
    titulo: "Produtos mais vendidos",
    colunas: ["produto", "quantidade", "faturamento"],
    linhas: [
      ["Tênis Runner", 142, 42585.8],
      ["Camiseta Básica Branca", 138, 6886.2],
      ["Calça Jeans Slim", 97, 15510.3],
      ["Mochila 20L", 84, 15111.6],
      ["Boné Aba Reta", 71, 4962.9],
    ],
    tipo_visualizacao: "barra",
    confianca: 0.91,
    gerado_em: new Date().toISOString(),
  },
  ticket: {
    titulo: "Ticket médio",
    // Sem coluna de período: o SQL real (backend/app/sql/templates.py)
    // devolve só essa coluna, ao contrário de faturamento (periodo + valor).
    colunas: ["ticket_medio"],
    linhas: [[142.87]],
    tipo_visualizacao: "numero",
    confianca: 0.85,
    gerado_em: new Date().toISOString(),
  },
};

// Erro no formato que a UI entende: { mensagem, exemplos? }. O contrato do
// backend (docs/contratos.md) devolve isso em `detail`; erros de rede não
// devolvem nada, então traduzimos aqui — sem jargão (heurística 2 de Nielsen).
function erroDeRede(causa) {
  return {
    mensagem:
      "Não consegui falar com o servidor. Verifique sua conexão e tente de novo " +
      "em alguns segundos.",
    tecnico: causa,
  };
}

export async function perguntar(pergunta) {
  if (MOCK) {
    await new Promise((r) => setTimeout(r, 600)); // simula a espera real
    if (/produto|vendidos/i.test(pergunta)) return FALSAS.barra;
    if (/ticket/i.test(pergunta)) return FALSAS.ticket;
    if (/capital|tempo/i.test(pergunta))
      throw {
        mensagem: "Não entendi. Tente reformular.",
        exemplos: ["Quanto faturei em março?", "Quais os 5 produtos mais vendidos?"],
      };
    return FALSAS.numero;
  }

  if (!API) {
    throw {
      mensagem:
        "O endereço da API não está configurado. Avise a equipe: falta " +
        "VITE_API_URL no ambiente.",
    };
  }

  // Servidor fora do ar, DNS, CORS: fetch rejeita com TypeError, não com uma
  // resposta. Sem este try o erro cru subia e a UI só dizia "Algo deu errado".
  let r;
  try {
    r = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta }),
    });
  } catch (err) {
    throw erroDeRede(err?.message);
  }

  // 500 do servidor ou proxy costuma devolver HTML, não JSON — r.json()
  // rebentaria aqui e o usuário veria um erro de parser.
  let dados;
  try {
    dados = await r.json();
  } catch {
    throw {
      mensagem: r.ok
        ? "O servidor respondeu num formato que não reconheço."
        : "O servidor está com problemas no momento. Tente de novo em instantes.",
      tecnico: `HTTP ${r.status}`,
    };
  }

  if (!r.ok) throw dados.detail || dados || { mensagem: "Algo deu errado." };
  return dados;
}
