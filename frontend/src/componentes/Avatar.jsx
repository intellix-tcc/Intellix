import { iniciaisDoNome } from "../utils/validacao";

// Foto do usuário, com as iniciais do nome como reserva — nunca fica um
// buraco cinza. A cor de fundo das iniciais é derivada do próprio nome, então
// cada pessoa tem sempre a mesma, e todas saem da paleta da marca (as 4
// cores oficiais: azul, roxo, turquesa, âmbar).
//
// Texto por par, não fixo em branco: turquesa e âmbar são claras nos dois
// temas (mesmo problema já documentado em ".exemplo:hover" — "o âmbar é
// claro nos dois temas, texto sempre escuro") — branco em cima delas cai
// pra ~2:1 de contraste, bem abaixo do mínimo de 3:1 pra texto grande.
const CORES = [
  { bg: "var(--accent)", texto: "#fff" },
  { bg: "var(--accent-3)", texto: "#fff" },
  { bg: "var(--teal)", texto: "#12243a" },
  { bg: "var(--accent-2)", texto: "#12243a" },
];

function corDoNome(nome) {
  const texto = String(nome || "");
  let soma = 0;
  for (let i = 0; i < texto.length; i++) soma += texto.charCodeAt(i);
  return CORES[soma % CORES.length];
}

export default function Avatar({ usuario, size = 40, className = "" }) {
  const nome = usuario?.nome || "";
  const estilo = { width: size, height: size, fontSize: Math.round(size * 0.38) };

  if (usuario?.foto) {
    return (
      <img
        src={usuario.foto}
        alt={`Foto de ${nome}`}
        className={`avatar avatar-foto ${className}`}
        style={estilo}
      />
    );
  }

  const cor = corDoNome(nome);
  return (
    <span
      className={`avatar avatar-iniciais ${className}`}
      style={{ ...estilo, background: cor.bg, color: cor.texto }}
      aria-hidden="true"
      title={nome}
    >
      {iniciaisDoNome(nome)}
    </span>
  );
}
