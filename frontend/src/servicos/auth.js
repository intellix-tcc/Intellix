// UI mock — NÃO é autenticação real. O backend ainda não tem login (ver
// backend/CLAUDE.md: "não existe login ainda"), então isto simula
// cadastro/entrada inteiramente no navegador, mesmo padrão do modo mock em
// api.js: um dublê ocupando o lugar do que ainda não existe.
//
// A senha fica em texto puro no localStorage de propósito — não há dado real
// em jogo aqui e o objetivo é a banca ver o fluxo funcionando.
// NÃO reproduzir este padrão quando o backend de autenticação existir: lá a
// senha vira hash (bcrypt/argon2) e nada disso mora no navegador.
//
// ---------------------------------------------------------------------------
// O QUE DEPENDE DO BACKEND (Dev B) para virar real:
//   POST /auth/registrar   -> registrar()
//   POST /auth/entrar      -> entrar()          (devolve token, não sessão local)
//   POST /auth/senha       -> alterarSenha()
//   POST /auth/recuperar   -> solicitarRecuperacao()  (envia e-mail de verdade)
//   PATCH /usuario/eu      -> atualizarPerfil()
// Nenhum existe hoje. As assinaturas abaixo já são assíncronas e lançam
// { mensagem } no mesmo formato do contrato de erro do backend, então a troca
// é substituir o corpo de cada função pela chamada HTTP.
// ---------------------------------------------------------------------------
import {
  normalizarEmail,
  normalizarNome,
  validarEmail,
  validarNome,
  validarSenha,
} from "../utils/validacao";

const CHAVE_SESSAO = "intellix_sessao";
const CHAVE_USUARIOS = "intellix_usuarios";
const CHAVE_RECUPERACAO = "intellix_recuperacao";

const ATRASO_MS = 500;

// Sessão vale 12h. Existe para o app ter o conceito de "sessão expirada"
// pedido no escopo; com token real isso passa a ser a validade do JWT.
const DURACAO_SESSAO_MS = 12 * 60 * 60 * 1000;

const espera = (ms = ATRASO_MS) => new Promise((r) => setTimeout(r, ms));

function erro(mensagem, campo) {
  return { mensagem, campo };
}

function carregarUsuarios() {
  try {
    const salvo = localStorage.getItem(CHAVE_USUARIOS);
    const lista = salvo ? JSON.parse(salvo) : [];
    if (!Array.isArray(lista)) return [];
    // Contas criadas antes da normalização podem ter e-mail com maiúsculas.
    return lista.map((u) => ({ ...u, email: normalizarEmail(u.email) }));
  } catch {
    return [];
  }
}

function salvarUsuarios(usuarios) {
  localStorage.setItem(CHAVE_USUARIOS, JSON.stringify(usuarios));
}

function acharUsuario(usuarios, email) {
  const alvo = normalizarEmail(email);
  return usuarios.find((u) => normalizarEmail(u.email) === alvo);
}

/** O que a interface enxerga do usuário — nunca inclui a senha. */
function paraSessao(usuario) {
  return {
    nome: usuario.nome,
    email: usuario.email,
    foto: usuario.foto || null,
    expiraEm: Date.now() + DURACAO_SESSAO_MS,
  };
}

function salvarSessao(sessao) {
  localStorage.setItem(CHAVE_SESSAO, JSON.stringify(sessao));
  return sessao;
}

/**
 * Devolve a sessão válida ou null. Sessão vencida é apagada aqui mesmo, para
 * não sobrar estado morto no navegador.
 */
export function carregarSessao() {
  try {
    const salvo = localStorage.getItem(CHAVE_SESSAO);
    if (!salvo) return null;
    const sessao = JSON.parse(salvo);
    if (!sessao?.email) return null;
    if (sessao.expiraEm && Date.now() > sessao.expiraEm) {
      localStorage.removeItem(CHAVE_SESSAO);
      return null;
    }
    // A conta pode ter sido apagada em outra aba.
    const usuario = acharUsuario(carregarUsuarios(), sessao.email);
    if (!usuario) {
      localStorage.removeItem(CHAVE_SESSAO);
      return null;
    }
    // Nome/foto vêm sempre do cadastro, não da cópia dentro da sessão: se o
    // perfil mudou em outra aba, a sessão acompanha.
    return { ...sessao, nome: usuario.nome, foto: usuario.foto || null };
  } catch {
    return null;
  }
}

/** true quando existe sessão salva, mas já vencida — App usa para avisar. */
export function sessaoExpirou() {
  try {
    const salvo = localStorage.getItem(CHAVE_SESSAO);
    if (!salvo) return false;
    const sessao = JSON.parse(salvo);
    return Boolean(sessao?.expiraEm && Date.now() > sessao.expiraEm);
  } catch {
    return false;
  }
}

export function encerrarSessao() {
  localStorage.removeItem(CHAVE_SESSAO);
}

export async function registrar({ nome, email, senha, confirmarSenha }) {
  await espera();

  // Revalidação na camada de persistência: a tela já validou, mas não
  // dependemos disso — qualquer chamada direta a registrar() passa por aqui.
  const erroNome = validarNome(nome);
  if (erroNome) throw erro(erroNome, "nome");
  const erroEmail = validarEmail(email);
  if (erroEmail) throw erro(erroEmail, "email");
  const erroSenha = validarSenha(senha);
  if (erroSenha) throw erro(erroSenha, "senha");
  if (confirmarSenha !== undefined && senha !== confirmarSenha) {
    throw erro("As senhas não coincidem.", "confirmarSenha");
  }

  const usuarios = carregarUsuarios();
  const emailNormalizado = normalizarEmail(email);

  // Unicidade pelo e-mail normalizado: antes a comparação era sensível a
  // maiúsculas, então "Ana@x.com" e "ana@x.com" viravam duas contas.
  if (acharUsuario(usuarios, emailNormalizado)) {
    throw erro(
      "Este e-mail já está cadastrado. Faça login ou recupere sua senha.",
      "email"
    );
  }

  const novo = {
    nome: normalizarNome(nome),
    email: emailNormalizado,
    senha,
    foto: null,
    criadoEm: new Date().toISOString(),
  };
  salvarUsuarios([...usuarios, novo]);
  return salvarSessao(paraSessao(novo));
}

export async function entrar({ email, senha }) {
  await espera();

  const erroEmail = validarEmail(email);
  if (erroEmail) throw erro(erroEmail, "email");
  if (!senha) throw erro("Digite sua senha.", "senha");

  const usuario = acharUsuario(carregarUsuarios(), email);

  // Distinguimos "conta não existe" de "senha errada" porque o escopo do TCC
  // pede as duas mensagens. Num sistema real isso vaza quais e-mails têm
  // conta — lá a resposta seria genérica para os dois casos.
  if (!usuario) {
    throw erro("Não encontramos uma conta com este e-mail. Crie uma conta.", "email");
  }
  if (usuario.senha !== senha) {
    throw erro("Senha incorreta. Tente de novo ou recupere sua senha.", "senha");
  }

  return salvarSessao(paraSessao(usuario));
}

export async function alterarSenha({ email, senhaAtual, novaSenha, confirmarSenha }) {
  await espera();

  const usuarios = carregarUsuarios();
  const usuario = acharUsuario(usuarios, email);
  if (!usuario) throw erro("Conta não encontrada. Entre de novo.");

  if (!senhaAtual) throw erro("Digite sua senha atual.", "senhaAtual");
  if (usuario.senha !== senhaAtual) throw erro("A senha atual está incorreta.", "senhaAtual");

  const erroNova = validarSenha(novaSenha);
  if (erroNova) throw erro(erroNova, "novaSenha");
  if (novaSenha === senhaAtual)
    throw erro("A nova senha precisa ser diferente da atual.", "novaSenha");
  if (novaSenha !== confirmarSenha)
    throw erro("A confirmação não corresponde à nova senha.", "confirmarSenha");

  salvarUsuarios(
    usuarios.map((u) => (u.email === usuario.email ? { ...u, senha: novaSenha } : u))
  );
  // Sessão renovada: trocar a senha não derruba quem está usando o sistema.
  return salvarSessao(paraSessao({ ...usuario, senha: novaSenha }));
}

export async function atualizarPerfil({ email, nome, foto }) {
  await espera(300);

  const usuarios = carregarUsuarios();
  const usuario = acharUsuario(usuarios, email);
  if (!usuario) throw erro("Conta não encontrada. Entre de novo.");

  const atualizado = { ...usuario };

  if (nome !== undefined) {
    const erroNome = validarNome(nome);
    if (erroNome) throw erro(erroNome, "nome");
    atualizado.nome = normalizarNome(nome);
  }
  // null remove a foto; undefined significa "não mexer".
  if (foto !== undefined) atualizado.foto = foto;

  try {
    salvarUsuarios(usuarios.map((u) => (u.email === usuario.email ? atualizado : u)));
  } catch {
    // Foto grande demais estoura a cota do localStorage (~5MB).
    throw erro("Não consegui salvar a foto. Tente uma imagem menor.", "foto");
  }
  return salvarSessao(paraSessao(atualizado));
}

// --- Recuperação de senha -------------------------------------------------
// O envio do código por e-mail depende de backend (endpoint inexistente). O
// fluxo em duas etapas abaixo tem a mesma forma do fluxo real — pedir código,
// conferir código, trocar senha — para a integração ser uma troca de corpo de
// função. Enquanto isso o código é devolvido na tela, com aviso explícito.

export async function solicitarRecuperacao({ email }) {
  await espera();

  const erroEmail = validarEmail(email);
  if (erroEmail) throw erro(erroEmail, "email");

  const usuario = acharUsuario(carregarUsuarios(), email);
  if (!usuario) throw erro("Não encontramos uma conta com este e-mail.", "email");

  const codigo = String(Math.floor(100000 + Math.random() * 900000));
  localStorage.setItem(
    CHAVE_RECUPERACAO,
    JSON.stringify({ email: usuario.email, codigo, expiraEm: Date.now() + 10 * 60 * 1000 })
  );
  // `codigo` volta para a tela mostrar. Com backend real, esta função não
  // devolveria o código — ele iria para a caixa de entrada do usuário.
  return { codigo, simulado: true };
}

export async function redefinirSenha({ email, codigo, novaSenha, confirmarSenha }) {
  await espera();

  let pedido;
  try {
    pedido = JSON.parse(localStorage.getItem(CHAVE_RECUPERACAO) || "null");
  } catch {
    pedido = null;
  }
  if (!pedido) throw erro("Pedido de recuperação não encontrado. Comece de novo.");
  if (Date.now() > pedido.expiraEm) {
    localStorage.removeItem(CHAVE_RECUPERACAO);
    throw erro("O código expirou. Peça um novo.");
  }
  if (normalizarEmail(email) !== pedido.email) throw erro("E-mail diferente do pedido.");
  if (String(codigo).trim() !== pedido.codigo) throw erro("Código incorreto.", "codigo");

  const erroNova = validarSenha(novaSenha);
  if (erroNova) throw erro(erroNova, "novaSenha");
  if (novaSenha !== confirmarSenha)
    throw erro("A confirmação não corresponde à nova senha.", "confirmarSenha");

  const usuarios = carregarUsuarios();
  const usuario = acharUsuario(usuarios, pedido.email);
  if (!usuario) throw erro("Conta não encontrada.");

  salvarUsuarios(
    usuarios.map((u) => (u.email === usuario.email ? { ...u, senha: novaSenha } : u))
  );
  localStorage.removeItem(CHAVE_RECUPERACAO);
  return { ok: true };
}
