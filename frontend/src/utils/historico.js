// Ainda não existe endpoint de histórico no backend, então guardamos as
// conversas no localStorage — mesma lógica do modo mock: o frontend não
// espera o servidor para ter uma funcionalidade completa.
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

export function novoId() {
  return `c_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export function tituloFromPergunta(pergunta) {
  return pergunta.length > 42 ? `${pergunta.slice(0, 42)}…` : pergunta;
}
