// Validações compartilhadas entre o cadastro (Login.jsx), a edição de perfil
// (Perfil.jsx) e a camada de persistência (auth.js).
//
// Ficam num módulo só de propósito: a mesma regra precisa valer nos dois
// lugares. Validar só na tela deixaria passar qualquer chamada direta a
// registrar()/atualizarPerfil() — por isso auth.js chama estas funções de
// novo antes de gravar, em vez de confiar no que a tela mandou.

// Limites usados só aqui dentro, nas mensagens de erro.
const NOME_MIN = 2;
const NOME_MAX = 60;
const SENHA_MIN = 6;
const SENHA_MAX = 72;

// Letras de qualquer alfabeto (\p{L}), acentos soltos (\p{M}), espaço,
// hífen, apóstrofo e ponto — cobre "Maria Clara", "João Pedro", "Ana Júlia",
// "D'Ávila", "Silva-Souza", "Antônio Jr.". Não cobre dígito nem símbolo.
const NOME_PERMITIDO = /^[\p{L}\p{M}][\p{L}\p{M}'’.\- ]*$/u;
const TEM_DIGITO = /\d/;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/** Espaços repetidos viram um só, e as pontas são aparadas. */
export function normalizarNome(valor) {
  return String(valor ?? "").trim().replace(/\s+/g, " ");
}

/** E-mail é comparado sempre nesta forma — ver validarEmail e auth.js. */
export function normalizarEmail(valor) {
  return String(valor ?? "").trim().toLowerCase();
}

/** Devolve "" quando válido, ou a mensagem de erro a mostrar ao usuário. */
export function validarNome(valor) {
  const nome = normalizarNome(valor);
  if (!nome) return "Digite seu nome.";
  if (TEM_DIGITO.test(nome)) return "O nome não pode conter números.";
  if (!NOME_PERMITIDO.test(nome))
    return "Use apenas letras, espaços, hífen e apóstrofo no nome.";
  if (nome.replace(/[^\p{L}]/gu, "").length < NOME_MIN)
    return `O nome precisa ter pelo menos ${NOME_MIN} letras.`;
  if (nome.length > NOME_MAX) return `O nome pode ter no máximo ${NOME_MAX} caracteres.`;
  return "";
}

export function validarEmail(valor) {
  const email = normalizarEmail(valor);
  if (!email) return "Digite seu e-mail.";
  if (!EMAIL_RE.test(email)) return "Digite um e-mail válido, como nome@empresa.com.";
  return "";
}

export function validarSenha(valor) {
  const senha = String(valor ?? "");
  if (!senha) return "Digite sua senha.";
  if (senha.length < SENHA_MIN)
    return `A senha precisa ter pelo menos ${SENHA_MIN} caracteres.`;
  if (senha.length > SENHA_MAX)
    return `A senha pode ter no máximo ${SENHA_MAX} caracteres.`;
  return "";
}

/** Força só para o medidor visual — não bloqueia nada além do mínimo acima. */
export function forcaSenha(senha) {
  const s = String(senha ?? "");
  if (s.length < SENHA_MIN) return { nivel: 0, rotulo: "Muito curta" };
  let pontos = 0;
  if (s.length >= 8) pontos++;
  if (s.length >= 12) pontos++;
  if (/[a-zà-ÿ]/.test(s) && /[A-ZÀ-Ý]/.test(s)) pontos++;
  if (/\d/.test(s)) pontos++;
  if (/[^\w\s]/.test(s)) pontos++;
  if (pontos <= 1) return { nivel: 1, rotulo: "Fraca" };
  if (pontos <= 3) return { nivel: 2, rotulo: "Boa" };
  return { nivel: 3, rotulo: "Forte" };
}

/** Iniciais para o avatar quando não há foto: "Maria Clara" -> "MC". */
export function iniciaisDoNome(nome) {
  const partes = normalizarNome(nome).split(" ").filter(Boolean);
  if (partes.length === 0) return "?";
  if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
  return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}
