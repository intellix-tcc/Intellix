// Cor fixa por item de dado: cada categoria, canal e forma de pagamento tem
// sempre a mesma cor, em qualquer gráfico (Início, chat, rosca ou barra).
// Assim "Eletrônicos" é azul no panorama e azul na resposta do chat, e a
// pessoa reconhece a fatia sem ler a legenda.
//
// As cores são tokens CSS (--dado-1 a --dado-10, em estilos/visual.css), com
// variantes para o tema claro e o escuro. Os nomes conhecidos têm cor
// definida; qualquer outro recebe uma cor estável calculada a partir do
// próprio nome (o mesmo nome dá sempre a mesma cor).

const TOTAL_CORES = 10;

const FIXAS = {
  // categorias
  vestuario: 1, // roxo
  eletronicos: 4, // azul
  calcados: 3, // âmbar
  acessorios: 2, // turquesa
  beleza: 9, // rosa
  casa: 6, // verde
  bebidas: 5, // coral
  alimentos: 10, // ardósia
  // canais
  loja: 4,
  site: 2,
  whatsapp: 6,
  marketplace: 3,
  // formas de pagamento
  pix: 2,
  cartao_credito: 4,
  cartao_de_credito: 4,
  cartao_debito: 7, // lilás
  cartao_de_debito: 7,
  dinheiro: 6,
  boleto: 3,
};

function chave(nome) {
  return String(nome ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .replace(/[\s-]+/g, "_");
}

function indiceEstavel(texto) {
  let h = 0;
  for (const ch of texto) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return (h % TOTAL_CORES) + 1;
}

/** Índice (1..10) da cor de um item. */
export function indiceCor(nome) {
  const k = chave(nome);
  return FIXAS[k] ?? indiceEstavel(k);
}

/** Cor CSS de um item, para usar em fill/stroke/background. */
export function corDe(nome) {
  return `var(--dado-${indiceCor(nome)})`;
}

/**
 * Cores para uma lista de itens sem repetir cor dentro do mesmo gráfico:
 * quem tem cor fixa fica com ela; os demais pegam a próxima cor livre.
 */
export function coresDistintas(nomes) {
  const usadas = new Set();
  const resultado = new Array(nomes.length);
  nomes.forEach((n, i) => {
    const k = chave(n);
    if (FIXAS[k] && !usadas.has(FIXAS[k])) {
      resultado[i] = FIXAS[k];
      usadas.add(FIXAS[k]);
    }
  });
  nomes.forEach((n, i) => {
    if (resultado[i]) return;
    let c = indiceEstavel(chave(n));
    for (let t = 0; t < TOTAL_CORES && usadas.has(c); t++) c = (c % TOTAL_CORES) + 1;
    resultado[i] = c;
    usadas.add(c);
  });
  return resultado.map((c) => `var(--dado-${c})`);
}
