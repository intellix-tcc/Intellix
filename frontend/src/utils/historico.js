// O localStorage é o espelho local do histórico: resposta instantânea, modo
// mock e funcionamento offline. Com a conta logada, as conversas também vão
// para o banco (migration 008) e voltam em qualquer aparelho — a sincronização
// mora no App (servicos/api.js: listarConversas/salvarConversaRemota/
// excluirConversaRemota); aqui ficam só o armazenamento local e os utilitários.
//
// Uma chave POR USUÁRIO. Antes era uma chave só para o navegador inteiro e o
// "Sair" não a apagava: quem entrasse depois no mesmo computador via as
// perguntas e os números de vendas de quem tinha saído.
const CHAVE_LEGADA = "intellix_conversas";
const PREFIXO = "intellix_conversas:";

// Se o navegador recusar gravar tudo (cota cheia), guarda só as mais recentes.
const MAXIMO_SE_FALTAR_ESPACO = 20;

/** Identifica o dono do histórico: id do Supabase ou, no modo mock, o e-mail. */
export function donoDe(usuario) {
  return usuario?.id || usuario?.email?.trim().toLowerCase() || null;
}

function ler(chave) {
  try {
    const salvo = localStorage.getItem(chave);
    const lista = salvo ? JSON.parse(salvo) : [];
    return Array.isArray(lista) ? lista : [];
  } catch {
    return [];
  }
}

function remover(chave) {
  try {
    localStorage.removeItem(chave);
  } catch {
    // storage indisponível: nada a apagar
  }
}

/**
 * Conversas de `dono` (sem dono: nenhuma).
 *
 * `adotarLegado`: só na abertura do app com uma sessão já aberta. O histórico
 * antigo, sem dono, foi criado por quem está com a sessão aberta neste
 * navegador, então passa para ele. Em qualquer outro caso (um login novo) o
 * histórico antigo é descartado, porque não dá para saber de quem era.
 */
export function carregarConversas(dono, { adotarLegado = false } = {}) {
  if (!dono) return [];
  const proprias = ler(PREFIXO + dono);
  const legado = ler(CHAVE_LEGADA);
  remover(CHAVE_LEGADA);
  if (adotarLegado && proprias.length === 0 && legado.length > 0) return legado;
  return proprias;
}

export function salvarConversas(dono, conversas) {
  if (!dono) return;
  const chave = PREFIXO + dono;
  try {
    localStorage.setItem(chave, JSON.stringify(conversas));
  } catch {
    // Cota cheia (respostas guardam as tabelas inteiras) ou modo privado:
    // tenta com as mais recentes; se nem assim couber, segue sem salvar em
    // vez de derrubar a tela.
    try {
      localStorage.setItem(chave, JSON.stringify(conversas.slice(0, MAXIMO_SE_FALTAR_ESPACO)));
    } catch {
      // sem espaço nenhum: o histórico vale só para esta aba
    }
  }
}

// UUID de verdade: é o id que vai para o banco (conversa.id uuid, migration
// 008) quando o histórico sincroniza com a conta. crypto.randomUUID existe em
// contexto seguro (https e localhost); o fallback cobre o resto.
export function novoId() {
  try {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  } catch {
    // sem crypto: usa o fallback abaixo
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

const RE_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** O id serve para o banco? (conversas locais antigas usavam outro formato.) */
export function ehUuid(id) {
  return typeof id === "string" && RE_UUID.test(id);
}

/** Momento para ordenar: a última atualização, ou a criação. */
function quandoDe(c) {
  return c?.atualizadoEm || c?.criadoEm || "";
}

/**
 * Junta conversas de duas origens (servidor e local), sem duplicar por id —
 * a primeira origem vence —, da mais recente para a mais antiga. Usado na
 * sincronização do histórico com a conta.
 */
export function juntarConversas(preferida, outra) {
  const vistos = new Set();
  const todas = [];
  for (const c of [...preferida, ...outra]) {
    if (!c?.id || vistos.has(c.id)) continue;
    vistos.add(c.id);
    todas.push(c);
  }
  return todas.sort((a, b) => quandoDe(b).localeCompare(quandoDe(a)));
}

export function tituloFromPergunta(pergunta) {
  return pergunta.length > 42 ? `${pergunta.slice(0, 42)}…` : pergunta;
}
