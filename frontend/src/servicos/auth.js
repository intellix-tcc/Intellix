// Autenticação real, pelo Supabase Auth.
//
// Cadastro, entrada, recuperação e troca de senha falam direto com o Supabase
// Auth (API REST em <projeto>.supabase.co/auth/v1). A senha nunca passa pelo
// nosso backend e nunca é guardada no navegador: o Supabase guarda o hash e
// devolve um token de acesso (JWT, vale 1 h) e um token de renovação. O
// backend confere o token em cada /chat e /import (backend/app/auth.py).
//
// As funções exportadas mantêm os mesmos nomes, parâmetros e formato de erro
// ({ mensagem, campo? }) do dublê que existia antes, para as telas (Login,
// Perfil, App) não precisarem mudar. Com VITE_MOCK=true, tudo é delegado ao
// dublê (authSimulado.js), para desenvolver a interface sem servidor.
//
// Configuração (Vercel e frontend/.env.local):
//   VITE_SUPABASE_URL       https://<ref>.supabase.co
//   VITE_SUPABASE_ANON_KEY  chave pública do projeto ("anon" / "publishable").
//                           É pública por natureza; NUNCA use a service_role.
import * as simulado from "./authSimulado";
import { limparDataset } from "../utils/dataset";
import {
  normalizarEmail,
  normalizarNome,
  validarEmail,
  validarNome,
  validarSenha,
} from "../utils/validacao";

const MOCK = import.meta.env.VITE_MOCK === "true";
const URL_SUPABASE = (import.meta.env.VITE_SUPABASE_URL || "").replace(/\/$/, "");
const CHAVE_ANON = import.meta.env.VITE_SUPABASE_ANON_KEY || "";

const CHAVE_SESSAO = "intellix_sessao";
const prefixoFoto = (id) => `intellix_foto_${id}`;

// Sessão do Intellix dura no máximo 12 h, mesmo com renovação do token: é o
// conceito de "sessão expirada" do escopo. Dentro disso, o token de acesso
// (1 h) é renovado sozinho por obterToken().
const DURACAO_SESSAO_MS = 12 * 60 * 60 * 1000;
// Renova o token quando faltar menos que isto para ele vencer.
const MARGEM_RENOVACAO_S = 60;

function erro(mensagem, campo) {
  return { mensagem, campo };
}

// ---------------------------------------------------------------------------
// Chamada à API do Supabase Auth
// ---------------------------------------------------------------------------

// Traduz os códigos de erro do Supabase para mensagens da interface.
// Mensagens genéricas de propósito onde a específica vazaria quais e-mails têm
// conta (entrar, recuperar).
const MENSAGENS = {
  invalid_credentials: ["E-mail ou senha incorretos.", "senha"],
  invalid_grant: ["E-mail ou senha incorretos.", "senha"],
  email_not_confirmed: [
    "Confirme seu e-mail antes de entrar: enviamos um link para a sua caixa de entrada.",
    "email",
  ],
  user_already_exists: ["Este e-mail já está cadastrado. Faça login ou recupere sua senha.", "email"],
  email_exists: ["Este e-mail já está cadastrado. Faça login ou recupere sua senha.", "email"],
  weak_password: ["Senha fraca demais. Use uma senha mais longa.", "senha"],
  same_password: ["A nova senha precisa ser diferente da atual.", "novaSenha"],
  otp_expired: ["Código incorreto ou expirado. Peça um novo.", "codigo"],
  over_request_rate_limit: ["Muitas tentativas seguidas. Espere um minuto e tente de novo."],
  over_email_send_rate_limit: [
    "Muitos e-mails enviados em pouco tempo. Espere alguns minutos e tente de novo.",
  ],
  signup_disabled: ["O cadastro de novas contas está desativado no momento."],
};

function configurado() {
  if (!URL_SUPABASE || !CHAVE_ANON) {
    throw erro(
      "O login não está configurado: falta VITE_SUPABASE_URL ou VITE_SUPABASE_ANON_KEY. Avise a equipe."
    );
  }
}

async function chamar(caminho, { metodo = "POST", corpo, token } = {}) {
  configurado();
  let r;
  try {
    r = await fetch(`${URL_SUPABASE}/auth/v1${caminho}`, {
      method: metodo,
      headers: {
        apikey: CHAVE_ANON,
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw erro("Não consegui falar com o servidor de login. Verifique sua conexão.");
  }

  let dados;
  try {
    dados = await r.json();
  } catch {
    dados = null; // corpo vazio (ex.: /logout devolve 204)
  }
  if (!r.ok) {
    // O Supabase usa dois formatos: { error_code, msg } e { error, error_description }.
    const codigo = dados?.error_code || dados?.error || "";
    const [mensagem, campo] = MENSAGENS[codigo] || [
      "Não foi possível concluir agora. Tente de novo em instantes.",
    ];
    throw { ...erro(mensagem, campo), codigo, status: r.status };
  }
  return dados;
}

// ---------------------------------------------------------------------------
// Sessão local
// ---------------------------------------------------------------------------

function lerSessaoBruta() {
  try {
    const salvo = localStorage.getItem(CHAVE_SESSAO);
    return salvo ? JSON.parse(salvo) : null;
  } catch {
    return null;
  }
}

function lerFoto(id) {
  try {
    return localStorage.getItem(prefixoFoto(id)) || null;
  } catch {
    return null;
  }
}

/** O que a interface enxerga do usuário: nunca inclui os tokens. */
function paraInterface(bruta) {
  return {
    id: bruta.id,
    nome: bruta.nome,
    email: bruta.email,
    foto: lerFoto(bruta.id),
    expiraEm: bruta.expiraEm,
  };
}

/** Guarda a resposta de login do Supabase e devolve a visão da interface. */
function salvarSessao(resposta, anterior = null) {
  const usuario = resposta.user || {};
  const bruta = {
    id: usuario.id,
    email: normalizarEmail(usuario.email),
    nome: normalizarNome(usuario.user_metadata?.nome || anterior?.nome || usuario.email),
    tokenAcesso: resposta.access_token,
    tokenRenovacao: resposta.refresh_token,
    tokenVenceEm: resposta.expires_at || Math.floor(Date.now() / 1000) + (resposta.expires_in || 3600),
    // renovar o token não estende a sessão de 12 h
    expiraEm: anterior?.expiraEm || Date.now() + DURACAO_SESSAO_MS,
  };
  localStorage.setItem(CHAVE_SESSAO, JSON.stringify(bruta));
  return paraInterface(bruta);
}

/**
 * Devolve a sessão válida ou null. Sessão vencida é apagada aqui mesmo.
 * Síncrona de propósito (o App usa no estado inicial): não chama a rede.
 */
export function carregarSessao() {
  if (MOCK) return simulado.carregarSessao();
  const bruta = lerSessaoBruta();
  if (!bruta?.tokenRenovacao) return null;
  if (bruta.expiraEm && Date.now() > bruta.expiraEm) {
    localStorage.removeItem(CHAVE_SESSAO);
    return null;
  }
  return paraInterface(bruta);
}

/** true quando existe sessão salva, mas já vencida: o App usa para avisar. */
export function sessaoExpirou() {
  if (MOCK) return simulado.sessaoExpirou();
  const bruta = lerSessaoBruta();
  return Boolean(bruta?.expiraEm && Date.now() > bruta.expiraEm);
}

export function encerrarSessao() {
  if (MOCK) return simulado.encerrarSessao();
  const bruta = lerSessaoBruta();
  localStorage.removeItem(CHAVE_SESSAO);
  // o dataset importado é de quem saiu; o próximo usuário começa na base demo
  limparDataset();
  if (bruta?.tokenAcesso) {
    // invalida o token de renovação no Supabase; falha aqui não impede a saída
    chamar("/logout", { token: bruta.tokenAcesso }).catch(() => {});
  }
}

/**
 * Token de acesso válido para mandar ao backend, renovando se estiver para
 * vencer. null quando não há sessão. Se a renovação for recusada (sessão
 * revogada), apaga a sessão local: o App percebe e volta para o login.
 */
export async function obterToken() {
  if (MOCK) return null;
  const bruta = lerSessaoBruta();
  if (!bruta?.tokenRenovacao || (bruta.expiraEm && Date.now() > bruta.expiraEm)) return null;

  const agora = Math.floor(Date.now() / 1000);
  if (bruta.tokenVenceEm - agora > MARGEM_RENOVACAO_S) return bruta.tokenAcesso;

  try {
    const resposta = await chamar("/token?grant_type=refresh_token", {
      corpo: { refresh_token: bruta.tokenRenovacao },
    });
    salvarSessao(resposta, bruta);
    return resposta.access_token;
  } catch (e) {
    if (e?.status === 400 || e?.status === 401) {
      localStorage.removeItem(CHAVE_SESSAO);
      return null;
    }
    throw e; // rede: não derruba a sessão por instabilidade
  }
}

// ---------------------------------------------------------------------------
// Ações das telas
// ---------------------------------------------------------------------------

export async function registrar({ nome, email, senha, confirmarSenha }) {
  if (MOCK) return simulado.registrar({ nome, email, senha, confirmarSenha });

  const erroNome = validarNome(nome);
  if (erroNome) throw erro(erroNome, "nome");
  const erroEmail = validarEmail(email);
  if (erroEmail) throw erro(erroEmail, "email");
  const erroSenha = validarSenha(senha);
  if (erroSenha) throw erro(erroSenha, "senha");
  if (confirmarSenha !== undefined && senha !== confirmarSenha) {
    throw erro("As senhas não coincidem.", "confirmarSenha");
  }

  const resposta = await chamar("/signup", {
    corpo: {
      email: normalizarEmail(email),
      password: senha,
      data: { nome: normalizarNome(nome) },
    },
  });

  // Com "Confirm email" ligado no Supabase, o cadastro não devolve sessão:
  // a conta só vale depois do clique no link do e-mail.
  if (!resposta?.access_token) {
    throw erro(
      "Conta criada. Enviamos um link de confirmação para o seu e-mail: confirme e depois entre."
    );
  }
  return salvarSessao(resposta);
}

export async function entrar({ email, senha }) {
  if (MOCK) return simulado.entrar({ email, senha });

  const erroEmail = validarEmail(email);
  if (erroEmail) throw erro(erroEmail, "email");
  if (!senha) throw erro("Digite sua senha.", "senha");

  const resposta = await chamar("/token?grant_type=password", {
    corpo: { email: normalizarEmail(email), password: senha },
  });
  return salvarSessao(resposta);
}

export async function alterarSenha({ email, senhaAtual, novaSenha, confirmarSenha }) {
  if (MOCK) return simulado.alterarSenha({ email, senhaAtual, novaSenha, confirmarSenha });

  if (!senhaAtual) throw erro("Digite sua senha atual.", "senhaAtual");
  const erroNova = validarSenha(novaSenha);
  if (erroNova) throw erro(erroNova, "novaSenha");
  if (novaSenha === senhaAtual)
    throw erro("A nova senha precisa ser diferente da atual.", "novaSenha");
  if (novaSenha !== confirmarSenha)
    throw erro("A confirmação não corresponde à nova senha.", "confirmarSenha");

  const anterior = lerSessaoBruta();
  // O Supabase troca a senha só com o token. Conferimos a senha atual
  // entrando de novo com ela, para quem pegou o computador destravado não
  // conseguir trocar a senha de outra pessoa.
  let sessao;
  try {
    sessao = await chamar("/token?grant_type=password", {
      corpo: { email: normalizarEmail(email), password: senhaAtual },
    });
  } catch (e) {
    if (e?.codigo === "invalid_credentials" || e?.codigo === "invalid_grant") {
      throw erro("A senha atual está incorreta.", "senhaAtual");
    }
    throw e;
  }

  await chamar("/user", {
    metodo: "PUT",
    token: sessao.access_token,
    corpo: { password: novaSenha },
  });
  // Trocar a senha não derruba quem está usando o sistema.
  return salvarSessao(sessao, anterior);
}

export async function atualizarPerfil({ email, nome, foto }) {
  if (MOCK) return simulado.atualizarPerfil({ email, nome, foto });

  const anterior = lerSessaoBruta();
  if (!anterior) throw erro("Sua sessão terminou. Entre de novo.");

  if (nome !== undefined) {
    const erroNome = validarNome(nome);
    if (erroNome) throw erro(erroNome, "nome");
    const token = await obterToken();
    if (!token) throw erro("Sua sessão terminou. Entre de novo.");
    await chamar("/user", {
      metodo: "PUT",
      token,
      corpo: { data: { nome: normalizarNome(nome) } },
    });
    anterior.nome = normalizarNome(nome);
  }

  // A foto fica só neste navegador: imagem não vai para o cadastro do
  // Supabase (os metadados do usuário viajam dentro de todo token).
  // null remove a foto; undefined significa "não mexer".
  if (foto !== undefined) {
    try {
      if (foto === null) localStorage.removeItem(prefixoFoto(anterior.id));
      else localStorage.setItem(prefixoFoto(anterior.id), foto);
    } catch {
      throw erro("Não consegui salvar a foto. Tente uma imagem menor.", "foto");
    }
  }

  localStorage.setItem(CHAVE_SESSAO, JSON.stringify(anterior));
  return paraInterface(anterior);
}

// --- Recuperação de senha -------------------------------------------------
// Fluxo em duas etapas, como a tela já espera: o Supabase envia um código de
// 6 dígitos por e-mail (o modelo "Reset Password" do projeto precisa conter
// {{ .Token }}); a pessoa digita o código e a nova senha.

export async function solicitarRecuperacao({ email }) {
  if (MOCK) return simulado.solicitarRecuperacao({ email });

  const erroEmail = validarEmail(email);
  if (erroEmail) throw erro(erroEmail, "email");

  // A resposta é a mesma exista ou não a conta, para não revelar quem é
  // cliente. Sem `codigo` no retorno: ele vai para o e-mail.
  await chamar("/recover", { corpo: { email: normalizarEmail(email) } });
  return { simulado: false };
}

export async function redefinirSenha({ email, codigo, novaSenha, confirmarSenha }) {
  if (MOCK) return simulado.redefinirSenha({ email, codigo, novaSenha, confirmarSenha });

  if (!String(codigo || "").trim()) throw erro("Digite o código que você recebeu.", "codigo");
  const erroNova = validarSenha(novaSenha);
  if (erroNova) throw erro(erroNova, "novaSenha");
  if (novaSenha !== confirmarSenha)
    throw erro("A confirmação não corresponde à nova senha.", "confirmarSenha");

  const sessao = await chamar("/verify", {
    corpo: { type: "recovery", email: normalizarEmail(email), token: String(codigo).trim() },
  });
  await chamar("/user", {
    metodo: "PUT",
    token: sessao.access_token,
    corpo: { password: novaSenha },
  });
  // A tela manda a pessoa entrar com a senha nova; encerramos a sessão
  // temporária aberta pelo código.
  chamar("/logout", { token: sessao.access_token }).catch(() => {});
  return { ok: true };
}
