// ATENÇÃO: dado de exemplo, não real.
//
// A Início virou um painel de visão geral (panorama, gráfico de vendas,
// categorias, resumo em texto, ranking, observações, atividade) — mas
// nenhuma dessas informações existe hoje em lugar nenhum do sistema. O
// backend não tem endpoint de agregação por período, não expõe categoria de
// produto, e "resumo em texto" pediria geração de linguagem livre, que o
// NLU deste projeto não faz (ele só classifica intenção e roda SQL fixo).
//
// Este arquivo existe só para dar forma à tela enquanto esse contrato não é
// avaliado pelo Dev B/A — ver a proposta em docs/contratos.md (`GET /resumo`).
// Os números aqui são fixos de propósito (não aleatórios a cada render), pra
// dar pra revisar a tela em capturas de tela sem o conteúdo pular. Quando o
// endpoint existir, isto é substituído por `buscarResumo()` em servicos/api.js
// e o Home.jsx muda uma importação, não a estrutura.
export const RESUMO_EH_EXEMPLO = true;

export const RESUMO_EXEMPLO = {
  periodo: { rotulo: "março de 2026" },
  atualizadoEm: "2026-03-19T14:32:00",
  totalRegistros: 1248,

  kpis: [
    { chave: "faturamento", rotulo: "Faturamento", valor: 128430.5, formato: "moeda", variacaoPct: 12 },
    { chave: "ticket_medio", rotulo: "Ticket médio", valor: 375.52, formato: "moeda", variacaoPct: 1 },
    { chave: "vendas", rotulo: "Vendas", valor: 342, formato: "numero", variacaoPct: 8 },
    { chave: "produtos_ativos", rotulo: "Produtos ativos", valor: 38, formato: "numero", variacaoPct: null },
  ],

  // 31 dias, pico no dia 14 — bate com a legenda do gráfico.
  serieVendas: [
    2400, 2650, 2100, 3300, 2900, 1800, 1600, 3100, 3400, 2950, 3600, 4100, 5200, 9240, 6100,
    3800, 3200, 2400, 2100, 3500, 3900, 4300, 3700, 2600, 2000, 1900, 3300, 4000, 4600, 3100, 2800,
  ].map((valor, i) => ({ dia: String(i + 1).padStart(2, "0"), valor })),

  // Uma cor por categoria — roxo/turquesa/âmbar/marinho, a mesma paleta
  // usada nos diferenciais da Sobre — pra diferenciar as barras sem
  // depender só da posição. Ordem importa: é a ordem de --pct, maior
  // primeiro, então as cores mais "de ação" (roxo) puxam a mais relevante.
  categorias: [
    { nome: "Eletrônicos", pct: 42, cor: "var(--accent-3)" },
    { nome: "Calçados", pct: 27, cor: "var(--teal)" },
    { nome: "Acessórios", pct: 19, cor: "var(--accent-2)" },
    { nome: "Vestuário", pct: 12, cor: "var(--marinho)" },
  ],

  resumoTexto: [
    "Março fechou em R$ 128.430,50, 12% acima de fevereiro e o melhor mês do trimestre. O crescimento veio principalmente de eletrônicos: o Smartwatch, sozinho, respondeu por 28% do faturamento do topo e cresceu 18% na última semana do mês.",
    "O ticket médio ficou praticamente estável (R$ 375,52), o que indica que o ganho veio de volume, não de preço — foram 342 vendas, 8% a mais que em fevereiro. As terças concentraram os melhores dias; os sábados, os mais fracos.",
    "No lado de atenção, a Bota de couro caiu 9% e saiu do top 3 pela primeira vez, e 3 produtos não tiveram nenhuma venda no mês. Vale revisar estoque e exposição desses itens.",
  ],

  topProdutos: [
    { nome: "Smartwatch", faturamento: 56420, pct: 28 },
    { nome: "Bota de couro", faturamento: 41800, pct: 21 },
    { nome: "Jaqueta corta-vento", faturamento: 36216, pct: 18 },
    { nome: "Bolsa transversal", faturamento: 34900, pct: 17 },
    { nome: "Tênis casual", faturamento: 33061, pct: 16 },
  ],

  observacoes: [
    { tipo: "alta", texto: "Smartwatch cresceu 18% na semana e lidera o topo." },
    { tipo: "padrao", texto: "Terça foi seu melhor dia; sábado, o mais fraco." },
    { tipo: "queda", texto: "Bota de couro caiu 9% e saiu do top 3." },
    { tipo: "atencao", texto: "3 produtos ficaram sem giro no mês." },
  ],

  atividade: [
    { texto: "vendas_marco.xlsx importado", quando: "há 3 dias" },
    { texto: "Relatório de março gerado", quando: "ontem" },
  ],
};
