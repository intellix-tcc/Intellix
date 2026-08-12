// Marca do Intellix: caixa aberta (os dados brutos) com um gráfico de barras
// saindo dela sob uma lupa (a análise). Recriação vetorial da folha de
// identidade — se o arquivo oficial for exportado, é só trocar por <img>.
//
// Os tons de marinho vêm de tokens CSS (--logo-navy-*) porque o marinho
// #193E60 sumiria no tema escuro; as cores secundárias funcionam nos dois.
export default function Logo({ size = 40, className }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      role="img"
      aria-label="Intellix"
    >
      {/* barras: a análise saindo da caixa */}
      <rect x="17" y="30" width="7" height="18" rx="1.5" fill="#9B6FB5" />
      <rect x="26" y="21" width="7" height="27" rx="1.5" fill="#7B3E93" />
      <rect x="35" y="27" width="7" height="21" rx="1.5" fill="#26C9C5" />
      <rect x="44" y="17" width="7" height="31" rx="1.5" fill="#D9A03A" />

      {/* caixa aberta — desenhada depois das barras para cobrir a base delas */}
      <path d="M32 37 L57 44 L32 51 L7 44 Z" fill="var(--logo-navy-3, #12243a)" />
      <path d="M7 44 L32 51 L32 62 L7 55 Z" fill="var(--logo-navy-2, #2c5a85)" />
      <path d="M57 44 L32 51 L32 62 L57 55 Z" fill="var(--logo-navy-1, #193e60)" />
      {/* pega lateral */}
      <rect
        x="12"
        y="47.5"
        width="9"
        height="2.6"
        rx="1.3"
        fill="var(--logo-navy-3, #12243a)"
        transform="rotate(12 12 47.5)"
      />

      {/* lupa */}
      <circle cx="42" cy="22" r="11" fill="#ffffff" fillOpacity="0.22" />
      <circle
        cx="42"
        cy="22"
        r="11"
        stroke="var(--logo-navy-1, #193e60)"
        strokeWidth="4.5"
      />
      <path
        d="M50.2 30.2 L57.5 37.5"
        stroke="var(--logo-navy-1, #193e60)"
        strokeWidth="5"
        strokeLinecap="round"
      />
    </svg>
  );
}
