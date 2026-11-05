// Rótulos de dados dos gráficos.
//
// Em vez de repetir "R$ 89,4 mil" em cada ponto (largo, e os vizinhos se
// atropelavam), o rótulo mostra só o número na escala do gráfico ("89,4") e
// a unidade aparece uma vez, no canto do gráfico ("valores em R$ mil").

/** Escala para os rótulos de uma série: R$, R$ mil ou R$ mi, pelo maior valor. */
export function escalaDe(valores) {
  const maior = Math.max(0, ...valores.map((v) => Math.abs(Number(v) || 0)));
  if (maior >= 1e6) return { divisor: 1e6, unidade: "R$ mi" };
  if (maior >= 1e3) return { divisor: 1e3, unidade: "R$ mil" };
  return { divisor: 1, unidade: "R$" };
}

/** Número na escala, curto: 89430 -> "89,4"; 125000 -> "125". */
export function numeroNaEscala(valor, escala) {
  const v = (Number(valor) || 0) / escala.divisor;
  return v.toLocaleString("pt-BR", { maximumFractionDigits: Math.abs(v) >= 100 ? 0 : 1 });
}

const ALTURA_PILULA = 18;
const LARGURA_CARACTERE = 6.4; // JetBrains Mono 10.5px

/**
 * Rótulo em "pílula" sobre os pontos de uma linha: fundo da cor do cartão e
 * borda fina, para o texto nunca se misturar com a linha ou com a média
 * tracejada. Ponto de vale leva a pílula embaixo; o resto, em cima. O maior
 * valor ganha pílula preenchida (destaque). Com muitos pontos, mostra um sim
 * um não (sempre o primeiro, o último e o maior).
 */
export function criarRotuloDePonto(valores, formatar, { maxRotulos = 14 } = {}) {
  const total = valores.length;
  const passo = Math.max(1, Math.ceil(total / maxRotulos));
  const iMaior = valores.reduce((m, v, i) => (v > valores[m] ? i : m), 0);

  return function RotuloDePonto({ x, y, value, index }) {
    if (x == null || y == null || value == null) return null;
    const destaque = index === iMaior;
    if (index % passo !== 0 && index !== total - 1 && !destaque) return null;

    const anterior = valores[index - 1];
    const proximo = valores[index + 1];
    const vale =
      total > 1 && !destaque &&
      (anterior == null || value <= anterior) && (proximo == null || value <= proximo);

    const texto = formatar(value);
    const largura = texto.length * LARGURA_CARACTERE + 12;
    const topo = vale ? y + 8 : y - 8 - ALTURA_PILULA;

    return (
      <g className="rotulo-pilula" pointerEvents="none">
        <rect
          x={x - largura / 2}
          y={topo}
          width={largura}
          height={ALTURA_PILULA}
          rx={ALTURA_PILULA / 2}
          fill={destaque ? "var(--teal)" : "var(--surface)"}
          stroke={destaque ? "none" : "var(--border-2)"}
          strokeWidth={1}
        />
        <text
          x={x}
          y={topo + ALTURA_PILULA / 2 + 0.5}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={10.5}
          fontWeight={600}
          fontFamily="var(--mono)"
          fill={destaque ? "#ffffff" : "var(--text-h)"}
        >
          {texto}
        </text>
      </g>
    );
  };
}

// Animação de entrada curta, e nenhuma para quem pediu menos movimento (no
// sistema ou nas preferências do Intellix). Também garante que os rótulos,
// que a biblioteca só desenha no fim da animação, apareçam logo.
export function animar() {
  if (typeof window === "undefined") return { isAnimationActive: false };
  const reduzir =
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ||
    document.documentElement.dataset.movimento === "reduzido";
  return reduzir ? { isAnimationActive: false } : { animationDuration: 650 };
}
