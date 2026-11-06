// O que o agente sabe responder, em um lugar só.
//
// A fonte de verdade é o backend: GET /capacidades (backend/app/main.py)
// devolve as intenções com exemplos, as limitações e a dica de período. A
// tela "O que posso perguntar" (paginas/Capacidades.jsx) consome o endpoint;
// a FAQ e os exemplos de fallback do chat consomem a cópia estática abaixo.
//
// A cópia estática existe por dois motivos: (1) o servidor do Render hiberna,
// então a tela precisa mostrar algo na hora, sem esperar o despertar; (2) a
// FAQ é pública e abre sem nenhuma ida ao servidor. Ao mudar os exemplos ou
// as limitações no backend, atualizar aqui — é a mesma disciplina do
// utils/diferenciais.js (uma lista só para não divergir com o tempo).
//
// Os exemplos e os títulos batem com _EXEMPLOS_POR_INTENCAO e os títulos de
// sql/templates.py; as limitações batem com _LIMITACOES; a ordem é a mesma
// que o endpoint devolve.

export const CAPACIDADES_ESTATICAS = {
  total_intencoes: 14,
  intencoes: [
    { chave: "total_vendas_periodo", titulo: "Faturamento no período", exemplos: ["Quanto faturei em março de 2024?", "Qual o faturamento de 2024?"] },
    { chave: "top_produtos", titulo: "Produtos mais vendidos", exemplos: ["Quais os 5 produtos mais vendidos?", "Top 3 produtos de março de 2024?"] },
    { chave: "ticket_medio", titulo: "Ticket médio", exemplos: ["Qual o ticket médio em 2024?", "Ticket médio de janeiro de 2024?"] },
    { chave: "quantidade_vendas", titulo: "Quantidade de vendas no período", exemplos: ["Quantas vendas tiveram em março de 2024?", "Número de vendas em 2024?"] },
    { chave: "top_clientes", titulo: "Clientes que mais compraram", exemplos: ["Quais os 5 clientes que mais compraram em 2024?", "Top 10 clientes do ano?"] },
    { chave: "desempenho_vendedor", titulo: "Desempenho do vendedor", exemplos: ["Como foi o desempenho da Fernanda em março?", "Quanto o vendedor Carlos vendeu em 2024?"] },
    { chave: "produtos_sem_saida", titulo: "Produtos sem saída no período", exemplos: ["Quais produtos não venderam em 2024?", "Produtos parados em março de 2024?"] },
    { chave: "comparacao_periodos", titulo: "Comparação entre períodos", exemplos: ["Compare o faturamento de março com abril de 2024.", "Vendas de 2023 versus 2024?"] },
    { chave: "variacao_periodo", titulo: "Variação entre períodos", exemplos: ["Qual a variação do faturamento de março para abril de 2024?", "Quanto cresceu em relação ao ano passado?"] },
    { chave: "vendas_por_canal", titulo: "Vendas por canal", exemplos: ["Quanto vendi por canal em 2024?", "Qual canal vendeu mais esse ano?"] },
    { chave: "vendas_por_categoria", titulo: "Vendas por categoria", exemplos: ["Quais categorias mais venderam em 2024?", "Faturamento por categoria em março de 2024?"] },
    { chave: "vendas_por_pagamento", titulo: "Vendas por forma de pagamento", exemplos: ["Vendas por forma de pagamento em 2024?", "Quanto foi pago no pix em março de 2024?"] },
    { chave: "unidades_vendidas", titulo: "Unidades vendidas", exemplos: ["Quantas botas de couro vendemos em 2025?", "Quantos itens vendi em março de 2024?"] },
    { chave: "melhor_mes", titulo: "Mês com mais vendas", exemplos: ["Qual foi o melhor mês de 2025?", "Em que mês mais vendemos smartwatch em 2025?"] },
  ],
  limitacoes: [
    "Só respondo sobre os dados de vendas carregados (base demo ou planilha importada).",
    "Não faço previsões nem recomendações — só o que já aconteceu nos dados.",
    "Não respondo perguntas fora de vendas (clima, geografia, conversas gerais).",
    "Sem período na pergunta, uso o da conversa (ou o ano mais recente dos dados).",
    "Filtro por produto, categoria, vendedor, cliente, canal e pagamento pelo nome do cadastro; nome que não existe na base é ignorado.",
  ],
  dica: "Inclua sempre um período (ex.: 'em março de 2024' ou 'em 2024').",
};

// Agrupamento por tema para a tela ficar escaneável: 14 intenções soltas
// cansam; em 4 blocos com um ícone cada, a pessoa acha o que quer de relance.
// A chave da intenção manda; uma intenção nova no backend que não esteja
// aqui ainda aparece, no bloco "Outras análises" (robusto à evolução do
// backend — nenhuma capacidade some da tela por falta de mapeamento).
const TEMAS = [
  {
    id: "resultado",
    tema: "Faturamento e resultado",
    icone: "grafico",
    chaves: ["total_vendas_periodo", "ticket_medio", "melhor_mes", "variacao_periodo", "comparacao_periodos"],
  },
  {
    id: "produtos",
    tema: "Produtos e categorias",
    icone: "selo",
    chaves: ["top_produtos", "vendas_por_categoria", "unidades_vendidas", "produtos_sem_saida"],
  },
  {
    id: "clientes",
    tema: "Clientes e vendas",
    icone: "usuarios",
    chaves: ["top_clientes", "quantidade_vendas", "desempenho_vendedor"],
  },
  {
    id: "canais",
    tema: "Canais e pagamento",
    icone: "cartao",
    chaves: ["vendas_por_canal", "vendas_por_pagamento"],
  },
];

/**
 * Agrupa as intenções (vindas do endpoint ou da cópia estática) nos temas
 * acima, na ordem dos temas. Intenção sem tema conhecido cai em "Outras
 * análises"; tema sem nenhuma intenção some. Devolve [{ id, tema, icone,
 * intencoes: [...] }].
 */
export function agruparPorTema(intencoes = []) {
  const porChave = new Map(intencoes.map((i) => [i.chave, i]));
  const usadas = new Set();
  const grupos = [];

  for (const t of TEMAS) {
    const doTema = t.chaves.map((c) => porChave.get(c)).filter(Boolean);
    doTema.forEach((i) => usadas.add(i.chave));
    if (doTema.length) grupos.push({ id: t.id, tema: t.tema, icone: t.icone, intencoes: doTema });
  }

  const restantes = intencoes.filter((i) => !usadas.has(i.chave));
  if (restantes.length) {
    grupos.push({ id: "outras", tema: "Outras análises", icone: "chip", intencoes: restantes });
  }
  return grupos;
}
