// UI mock — não é autenticação real. O backend ainda não tem login (ver
// backend/CLAUDE.md: "não existe login ainda"), então isso só simula
// cadastro/entrada inteiramente no navegador, mesmo padrão do modo mock em
// api.js: um dublê ocupando o lugar do que ainda não existe. Senha fica em
// texto puro no localStorage de propósito — não há dado real em jogo aqui.
// NÃO reproduzir esse padrão quando o backend de autenticação existir.
const CHAVE_SESSAO = "intellix_sessao";
const CHAVE_USUARIOS = "intellix_usuarios";

const ATRASO_MS = 500;

function carregarUsuarios() {
  try {
    const salvo = localStorage.getItem(CHAVE_USUARIOS);
    return salvo ? JSON.parse(salvo) : [];
  } catch {
    return [];
  }
}

function salvarUsuarios(usuarios) {
  localStorage.setItem(CHAVE_USUARIOS, JSON.stringify(usuarios));
}

function salvarSessao(sessao) {
  localStorage.setItem(CHAVE_SESSAO, JSON.stringify(sessao));
}

export function carregarSessao() {
  try {
    const salvo = localStorage.getItem(CHAVE_SESSAO);
    return salvo ? JSON.parse(salvo) : null;
  } catch {
    return null;
  }
}

export function encerrarSessao() {
  localStorage.removeItem(CHAVE_SESSAO);
}

export async function registrar({ nome, email, senha }) {
  await new Promise((r) => setTimeout(r, ATRASO_MS));
  const usuarios = carregarUsuarios();
  if (usuarios.some((u) => u.email === email)) {
    throw { mensagem: "Já existe uma conta com esse e-mail." };
  }
  salvarUsuarios([...usuarios, { nome, email, senha }]);
  const sessao = { nome, email };
  salvarSessao(sessao);
  return sessao;
}

export async function entrar({ email, senha }) {
  await new Promise((r) => setTimeout(r, ATRASO_MS));
  const usuario = carregarUsuarios().find((u) => u.email === email);
  if (!usuario || usuario.senha !== senha) {
    throw { mensagem: "E-mail ou senha incorretos." };
  }
  const sessao = { nome: usuario.nome, email: usuario.email };
  salvarSessao(sessao);
  return sessao;
}
