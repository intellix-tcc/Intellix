// Leitura do ResultSet do /chat: qual coluna é o rótulo, qual é a métrica,
// que tipo de resposta é (evolução no tempo, composição, ranking,
// comparação) e quais formas de visualizar fazem sentido para ela.
//
// Separado do Chat.jsx para o gráfico, a lista e o texto de destaque
// usarem exatamente a mesma decisão.

const MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

/** "valor_total" -> "Valor total" (só tira o snake_case). */
export function humanizarColuna(nome) {
  const s = String(nome || "").replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// Nem todo número é dinheiro: "quantidade_vendas" é contagem e
// "variacao_percentual" é porcentagem. Decide pelo nome da coluna (o mesmo
// dos templates SQL).
export function formatarValor(coluna, valor, { compacto = false } = {}) {
  if (valor === null || valor === undefined) return "—";
  if (typeof valor !== "number") return valor;
  const nome = String(coluna || "").toLowerCase();
  if (nome.includes("percentual")) {
    return `${valor.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%`;
  }
  if (nome.startsWith("quantidade") || nome.startsWith("itens") || nome.startsWith("unidades")) {
    return valor.toLocaleString("pt-BR", {
      maximumFractionDigits: 0,
      ...(compacto ? { notation: "compact" } : {}),
    });
  }
  return valor.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    ...(compacto ? { notation: "compact", maximumFractionDigits: 1 } : {}),
  });
}

/** "2024-03" -> "mar/24"; outros textos passam como estão. */
export function rotuloPeriodo(valor) {
  const m = /^(\d{4})-(\d{2})$/.exec(String(valor));
  return m ? `${MESES_CURTOS[Number(m[2]) - 1]}/${m[1].slice(2)}` : String(valor);
}

/** "2024-03-01".."2024-03-31" -> "mar/2024"; ano inteiro -> "2024". */
export function rotuloIntervalo(inicio, fim) {
  if (!inicio || !fim) return null;
  const [ai, mi, di] = inicio.split("-").map(Number);
  const [af, mf, df] = fim.split("-").map(Number);
  if (ai === af && mi === 1 && di === 1 && mf === 12 && df === 31) return String(ai);
  const ultimo = new Date(af, mf, 0).getDate();
  if (ai === af && mi === mf && di === 1 && df === ultimo) return `${MESES_CURTOS[mi - 1]}/${ai}`;
  const curto = (a, m, d) => `${String(d).padStart(2, "0")}/${String(m).padStart(2, "0")}/${a}`;
  return `${curto(ai, mi, di)} a ${curto(af, mf, df)}`;
}

/** Índice da coluna da métrica: faturamento quando existe, senão a última numérica. */
export function indiceMetrica(r) {
  const i = r.colunas.indexOf("faturamento");
  if (i >= 0) return i;
  for (let j = r.colunas.length - 1; j >= 0; j--) {
    if (r.linhas.some((l) => typeof l[j] === "number")) return j;
  }
  return r.colunas.length - 1;
}

/** Tipo de resposta, pelo formato dos dados. */
export function naturezaDoResultado(r) {
  const primeira = r.colunas[0];
  const rotulos = r.linhas.map((l) => l[0]);
  if (primeira === "periodo" && rotulos.every((v) => v === "periodo_a" || v === "periodo_b")) {
    return "comparacao";
  }
  if (primeira === "periodo" && r.linhas.length > 1 && rotulos.every((v) => /^\d{4}-\d{2}$/.test(String(v)))) {
    return "temporal";
  }
  if (["canal", "categoria", "forma_pagamento"].includes(primeira)) return "composicao";
  if (r.linhas.length > 1 && typeof rotulos[0] === "string") return "ranking";
  return "outro";
}

/**
 * Formas de ver uma resposta, na ordem de preferência. A primeira é a que
 * abre; o seletor "Ver como" oferece as outras.
 */
export function modosDisponiveis(r) {
  const natureza = naturezaDoResultado(r);
  const m = indiceMetrica(r);
  const positivos = r.linhas.every((l) => typeof l[m] === "number" && l[m] >= 0);
  const cabeEmRosca = positivos && r.linhas.length >= 2 && r.linhas.length <= 8;
  switch (natureza) {
    case "temporal":
      return ["linha", "barra", "tabela"];
    case "comparacao":
      return ["comparacao", "tabela"];
    case "composicao":
      return cabeEmRosca ? ["pizza", "barra", "tabela"] : ["barra", "tabela"];
    case "ranking":
      return cabeEmRosca ? ["barra", "pizza", "tabela"] : ["barra", "tabela"];
    default:
      return r.linhas.length > 1 ? ["barra", "tabela"] : ["tabela"];
  }
}

/** Linhas como objetos { rotulo, valor, original } para os gráficos. */
export function serieDoResultado(r) {
  const m = indiceMetrica(r);
  const vistos = new Map();
  return r.linhas.map((linha) => {
    // Rótulo repetido (duas categorias vazias viram "Não informado", ou
    // "Casa" e "casa" no cadastro): o eixo de categorias do gráfico juntaria
    // as duas barras numa só. Numera a repetição.
    let rotulo = rotuloItem(r.colunas[0], linha[0]);
    const n = (vistos.get(rotulo) || 0) + 1;
    vistos.set(rotulo, n);
    if (n > 1) rotulo = `${rotulo} (${n})`;
    const valor = Number(linha[m]);
    return {
      chave: linha[0] == null ? "" : String(linha[0]), // valor cru: decide a cor
      rotulo,
      valor: Number.isFinite(valor) ? valor : 0,
      original: linha,
    };
  });
}

const NOMES_PAGAMENTO = {
  pix: "Pix",
  cartao_credito: "Cartão de crédito",
  cartao_debito: "Cartão de débito",
  dinheiro: "Dinheiro",
  boleto: "Boleto",
};

/** Rótulo legível de um item: "cartao_credito" -> "Cartão de crédito", "whatsapp" -> "WhatsApp". */
export function rotuloItem(coluna, valor) {
  if (valor == null || valor === "") return "Não informado";
  const v = String(valor);
  if (coluna === "forma_pagamento") return NOMES_PAGAMENTO[v] ?? humanizarColuna(v);
  if (coluna === "canal") return v.toLowerCase() === "whatsapp" ? "WhatsApp" : humanizarColuna(v);
  if (coluna === "periodo") return rotuloPeriodo(v);
  return v;
}
