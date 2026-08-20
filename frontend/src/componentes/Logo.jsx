import { useState } from "react";

// A marca do Intellix, em duas variantes — e nada além disso é usado como
// símbolo da marca em lugar nenhum da interface.
//
//   "completa" (padrão) -> public/logo.png    lockup inteiro, com o wordmark
//   "simbolo"           -> public/simbolo.png só o símbolo, sem o wordmark
//
// O símbolo é recorte do próprio logo.png (mesmo recorte do favicon), não um
// desenho novo. Existia aqui um componente Monograma com um símbolo inventado;
// ele foi removido: onde a marca aparece, aparece a logo.
//
// Enquanto o arquivo não estiver em public/, cai no desenho vetorial de
// reserva abaixo, para a interface nunca ficar com imagem quebrada.
const ARQUIVOS = {
  completa: "/logo.png",
  simbolo: "/simbolo.png",
};

export default function Logo({ largura = 160, variante = "completa", className = "" }) {
  const [semArquivo, setSemArquivo] = useState(false);

  if (!semArquivo) {
    return (
      <img
        src={ARQUIVOS[variante] || ARQUIVOS.completa}
        alt="Intellix"
        className={`logo logo-${variante} ${className}`}
        style={{ width: largura }}
        onError={() => setSemArquivo(true)}
      />
    );
  }

  return <LogoReserva largura={largura} variante={variante} className={className} />;
}

function LogoReserva({ largura, variante, className }) {
  const soSimbolo = variante === "simbolo";
  return (
    <svg
      viewBox={soSimbolo ? "0 0 64 68" : "0 0 64 84"}
      className={`logo ${className}`}
      style={{ width: largura }}
      role="img"
      aria-label="Intellix"
    >
      <rect x="17" y="30" width="7" height="18" rx="1.5" fill="#9B6FB5" />
      <rect x="26" y="21" width="7" height="27" rx="1.5" fill="#7B3E93" />
      <rect x="35" y="27" width="7" height="21" rx="1.5" fill="#26C9C5" />
      <rect x="44" y="17" width="7" height="31" rx="1.5" fill="#D9A03A" />
      <path d="M32 37 L57 44 L32 51 L7 44 Z" fill="var(--logo-navy-3, #12243a)" />
      <path d="M7 44 L32 51 L32 62 L7 55 Z" fill="var(--logo-navy-2, #2c5a85)" />
      <path d="M57 44 L32 51 L32 62 L57 55 Z" fill="var(--logo-navy-1, #193e60)" />
      <circle cx="42" cy="22" r="11" fill="#ffffff" fillOpacity="0.22" />
      <circle cx="42" cy="22" r="11" stroke="var(--logo-navy-1, #193e60)" strokeWidth="4.5" />
      <path
        d="M50.2 30.2 L57.5 37.5"
        stroke="var(--logo-navy-1, #193e60)"
        strokeWidth="5"
        strokeLinecap="round"
      />
      {!soSimbolo && (
        <text
          x="32"
          y="79"
          textAnchor="middle"
          fontFamily="Poppins, system-ui, sans-serif"
          fontWeight="700"
          fontSize="17"
          fill="var(--logo-navy-1, #193e60)"
        >
          Intellix
        </text>
      )}
    </svg>
  );
}
