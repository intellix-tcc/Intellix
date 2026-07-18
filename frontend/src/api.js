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
};

export async function perguntar(pergunta) {
  if (MOCK) {
    await new Promise((r) => setTimeout(r, 600)); // simula a espera real
    if (/produto|vendidos/i.test(pergunta)) return FALSAS.barra;
    if (/capital|tempo/i.test(pergunta))
      throw {
        mensagem: "Não entendi. Tente reformular.",
        exemplos: ["Quanto faturei em março?", "Quais os 5 produtos mais vendidos?"],
      };
    return FALSAS.numero;
  }

  const r = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pergunta }),
  });
  const dados = await r.json();
  if (!r.ok) throw dados.detail || { mensagem: "Algo deu errado." };
  return dados;
}