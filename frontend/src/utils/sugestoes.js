// Sugestões de pergunta do chat.
//
// Duas listas, com o mesmo critério: só perguntas no formato que o NLU
// reconhece bem (docs/perguntas_validacao.md e a avaliação das 100 perguntas
// em docs/avaliacao-100-perguntas.md). Sugerir uma pergunta que o sistema
// erra seria pior que não sugerir nada.

/** Chat vazio: o que dá para perguntar, agrupado por tema. */
export const SUGESTOES_INICIAIS = [
  {
    tema: "Faturamento",
    icone: "grafico",
    perguntas: ["Quanto faturei em março?", "Qual foi o melhor mês do ano?"],
  },
  {
    tema: "Produtos",
    icone: "selo",
    perguntas: ["Quais os 5 produtos mais vendidos?", "Quais categorias mais venderam em 2024?"],
  },
  {
    tema: "Clientes e vendas",
    icone: "usuarios",
    perguntas: ["Quais os clientes que mais compraram?", "Quantas vendas eu fiz em março?"],
  },
  {
    tema: "Canais e pagamento",
    icone: "cartao",
    perguntas: ["Quanto vendi por canal em março de 2024?", "Vendas por forma de pagamento em 2024?"],
  },
];

const MESES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

/**
 * O período da resposta em palavras ("março de 2024", "2024"), lido dos
 * parâmetros que o backend devolve. Vazio quando não é um mês ou um ano
 * inteiro — aí a sugestão vai sem período e o backend usa o padrão.
 */
export function periodoEmPalavras(parametros) {
  const ini = parametros?.periodo_inicio;
  const fim = parametros?.periodo_fim;
  if (!ini || !fim) return "";
  const [ai, mi, di] = ini.split("-").map(Number);
  const [af, mf, df] = fim.split("-").map(Number);
  if (ai === af && mi === 1 && di === 1 && mf === 12 && df === 31) return String(ai);
  const ultimoDia = new Date(af, mf, 0).getDate();
  if (ai === af && mi === mf && di === 1 && df === ultimoDia) return `${MESES[mi - 1]} de ${ai}`;
  return "";
}

// Próximo passo natural de cada tipo de resposta. `{p}` vira " em <período>".
const CONTINUACOES = {
  total_vendas_periodo: [
    "Qual o ticket médio{p}?",
    "Quais os 5 produtos mais vendidos{p}?",
    "Quanto vendi por canal{p}?",
  ],
  ticket_medio: [
    "Quantas vendas eu fiz{p}?",
    "Quanto faturei{p}?",
    "Quais os clientes que mais compraram{p}?",
  ],
  quantidade_vendas: ["Qual o ticket médio{p}?", "Quanto faturei{p}?"],
  top_produtos: [
    "Quais categorias mais venderam{p}?",
    "Quais os clientes que mais compraram{p}?",
    "Quanto faturei{p}?",
  ],
  top_clientes: ["Quais os 5 produtos mais vendidos{p}?", "Qual o ticket médio{p}?"],
  vendas_por_categoria: ["Quais os 5 produtos mais vendidos{p}?", "Quanto vendi por canal{p}?"],
  vendas_por_canal: ["Vendas por forma de pagamento{p}?", "Quanto faturei{p}?"],
  vendas_por_pagamento: ["Quanto vendi por canal{p}?", "Qual o ticket médio{p}?"],
  produtos_sem_saida: ["Quais os 5 produtos mais vendidos{p}?", "Quais categorias mais venderam{p}?"],
  desempenho_vendedor: ["Quanto faturei{p}?", "Quais os clientes que mais compraram{p}?"],
  comparacao_periodos: ["Quais os 5 produtos mais vendidos{p}?", "Qual o ticket médio{p}?"],
  variacao_periodo: ["Quais os 5 produtos mais vendidos{p}?", "Qual o ticket médio{p}?"],
  unidades_vendidas: ["Qual o ticket médio{p}?", "Quanto faturei{p}?"],
  melhor_mes: ["Quais os 5 produtos mais vendidos{p}?", "Qual foi o pior mês{p}?"],
};

// Com um produto em foco (o recorte da resposta, ou o 1º do ranking), o
// próximo passo natural é aprofundar nele: quantas unidades, em que mês
// vendeu mais, quem vendeu. São as perguntas de detalhe que o backend
// entende (filtros do catálogo, app/filtros.py).
function produtoEmFoco(r) {
  if (r?.parametros?.produto) return r.parametros.produto;
  if (r?.intencao === "top_produtos" && r.colunas?.[0] === "produto") return r.linhas?.[0]?.[0] || "";
  return "";
}

function detalhesDoProduto(produto, intencao) {
  const todas = {
    unidades_vendidas: `Quantas unidades de ${produto} vendemos{p}?`,
    melhor_mes: `Qual mês mais vendeu ${produto}{p}?`,
    desempenho_vendedor: `Quem mais vendeu ${produto}{p}?`,
  };
  return Object.entries(todas)
    .filter(([chave]) => chave !== intencao)
    .map(([, pergunta]) => pergunta);
}

/** Até 3 perguntas para continuar a partir de uma resposta. */
export function sugestoesDeContinuacao(resultado) {
  const produto = produtoEmFoco(resultado);
  const modelos = [
    ...(produto ? detalhesDoProduto(produto, resultado.intencao) : []),
    ...(CONTINUACOES[resultado?.intencao] || []),
  ];
  if (!modelos.length) return [];
  const periodo = periodoEmPalavras(resultado.parametros);
  return modelos.slice(0, 3).map((m) => m.replace("{p}", periodo ? ` em ${periodo}` : ""));
}
