// Rótulo de valor sobre os pontos de um gráfico de linha.
//
// Para os números não brigarem com a própria linha: ponto de vale (menor que
// os vizinhos) leva o rótulo embaixo, os demais em cima. O contorno na cor
// do fundo separa o texto da linha e da média tracejada. Com muitos pontos,
// mostra um sim um não (sempre o primeiro e o último).
export function criarRotuloDePonto(valores, formatar, { maxRotulos = 14, tamanho = 11 } = {}) {
  const total = valores.length;
  const passo = Math.max(1, Math.ceil(total / maxRotulos));
  return function RotuloDePonto({ x, y, value, index }) {
    if (x == null || y == null || value == null) return null;
    if (index % passo !== 0 && index !== total - 1) return null;
    const anterior = valores[index - 1];
    const proximo = valores[index + 1];
    const vale =
      (anterior == null || value <= anterior) && (proximo == null || value <= proximo) && total > 1;
    return (
      <text
        x={x}
        y={vale ? y + 16 : y - 10}
        textAnchor="middle"
        dominantBaseline={vale ? "hanging" : "auto"}
        fontSize={tamanho}
        fontFamily="var(--mono)"
        fill="var(--text-h)"
        stroke="var(--surface)"
        strokeWidth={3}
        strokeLinejoin="round"
        paintOrder="stroke"
      >
        {formatar(value)}
      </text>
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
