// ATENÇÃO: dado de exemplo, não real.
//
// Usado em dois lugares, e só neles:
//   - a vitrine e a tela de login (Login.jsx), que mostram uma conversa
//     ilustrativa antes de a pessoa ter conta;
//   - o modo de demonstração sem servidor (VITE_MOCK=true), em que
//     servicos/api.js devolve resumoDeExemplo() no lugar do GET /resumo.
//
// Com o backend no ar, a Início mostra o panorama real (GET /resumo,
// backend/app/resumo.py). Os números aqui são fixos de propósito (não
// aleatórios a cada render), para dar para revisar a tela em capturas.

export const RESUMO_EXEMPLO = {
  periodo: { rotulo: "março de 2026" },
  kpis: [{ chave: "faturamento", rotulo: "Faturamento", valor: 128430.5, variacaoPct: 12 }],
};

const MESES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

// 31 dias, pico no dia 14.
const SERIE = [
  2400, 2650, 2100, 3300, 2900, 1800, 1600, 3100, 3400, 2950, 3600, 4100, 5200, 9240, 6100,
  3800, 3200, 2400, 2100, 3500, 3900, 4300, 3700, 2600, 2000, 1900, 3300, 4000, 4600, 3100, 2800,
];
const MENSAL = [
  86200, 79400, 92100, 98800, 104300, 99900, 95100, 101700, 118900, 141200, 114600, 128430.5,
];

/** Panorama no mesmo formato do GET /resumo, para o modo de demonstração. */
export function resumoDeExemplo({ ano = 2026, mes = 3 } = {}) {
  const rotulo = `${MESES[mes - 1]} de ${ano}`;
  const ant = mes === 1 ? { ano: ano - 1, mes: 12 } : { ano, mes: mes - 1 };
  const dias = new Date(ano, mes, 0).getDate();
  const meses = [];
  for (let i = 0; i < 12; i++) {
    const total = ano * 12 + (mes - 1) - i;
    const a = Math.floor(total / 12);
    const m = (total % 12) + 1;
    meses.push({ ano: a, mes: m, rotulo: `${MESES[m - 1]} de ${a}` });
  }

  return {
    periodo: { ano, mes, rotulo },
    periodo_anterior: { ...ant, rotulo: `${MESES[ant.mes - 1]} de ${ant.ano}` },
    meses_disponiveis: meses,
    kpis: [
      { chave: "faturamento", rotulo: "Faturamento", valor: 128430.5, formato: "moeda", variacao_pct: 12 },
      { chave: "ticket_medio", rotulo: "Ticket médio", valor: 375.52, formato: "moeda", variacao_pct: 1.2 },
      { chave: "vendas", rotulo: "Vendas", valor: 342, formato: "numero", variacao_pct: 8 },
      { chave: "itens", rotulo: "Itens vendidos", valor: 861, formato: "numero", variacao_pct: 6.4 },
      { chave: "clientes", rotulo: "Clientes", valor: 211, formato: "numero", variacao_pct: -2.1 },
    ],
    serie_diaria: SERIE.slice(0, dias).map((valor, i) => ({ dia: i + 1, valor })),
    serie_mensal: [...meses].reverse().map((m, i) => ({
      ano: m.ano,
      mes: m.mes,
      rotulo: `${MESES[m.mes - 1].slice(0, 3)}/${String(m.ano).slice(2)}`,
      valor: MENSAL[i],
    })),
    categorias: [
      { nome: "Eletrônicos", valor: 53940.8, pct: 42 },
      { nome: "Calçados", valor: 34676.2, pct: 27 },
      { nome: "Acessórios", valor: 24401.8, pct: 19 },
      { nome: "Vestuário", valor: 15411.7, pct: 12 },
    ],
    canais: [
      { nome: "Loja", valor: 57793.7, pct: 45 },
      { nome: "Site", valor: 32107.6, pct: 25 },
      { nome: "WhatsApp", valor: 25686.1, pct: 20 },
      { nome: "Marketplace", valor: 12843.1, pct: 10 },
    ],
    top_produtos: [
      { nome: "Smartwatch", valor: 36420, pct: 28.4, variacao_pct: 18 },
      { nome: "Bota de couro", valor: 21800, pct: 17, variacao_pct: -9 },
      { nome: "Jaqueta corta-vento", valor: 16216, pct: 12.6, variacao_pct: 4.2 },
      { nome: "Bolsa transversal", valor: 14900, pct: 11.6, variacao_pct: 2 },
      { nome: "Tênis casual", valor: 13061, pct: 10.2, variacao_pct: null },
    ],
    observacoes: [
      { tipo: "alta", texto: `Faturamento 12% acima de ${MESES[ant.mes - 1]}.`, pergunta: `Quanto faturei em ${rotulo}?` },
      { tipo: "alta", texto: "Smartwatch cresceu 18% e lidera o ranking.", pergunta: `Quais os 5 produtos mais vendidos em ${rotulo}?` },
      { tipo: "queda", texto: "Bota de couro caiu 9%.", pergunta: `Quais os 10 produtos mais vendidos em ${rotulo}?` },
      { tipo: "atencao", texto: "3 produtos ficaram sem saída no mês.", pergunta: `Quais produtos não venderam em ${rotulo}?` },
      { tipo: "padrao", texto: "Terça teve a melhor média diária; sábado, a mais fraca.", pergunta: null },
    ],
    resumo_texto: [
      `Em ${rotulo}, a loja faturou R$ 128.430,50 em 342 vendas, com ticket médio de R$ 375,52: 12% acima de ${MESES[ant.mes - 1]}.`,
      "A categoria líder foi Eletrônicos, com 42% do faturamento, e o produto que mais faturou foi Smartwatch (R$ 36.420,00).",
      "A alta veio principalmente do número de vendas.",
    ],
    total_registros: 1248,
    atualizado_em: new Date().toISOString(),
    exemplo: true,
  };
}
