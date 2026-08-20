// Ainda não existe endpoint de histórico no backend, então guardamos as
// conversas no localStorage — mesma lógica do modo mock: o frontend não
// espera o servidor para ter uma funcionalidade completa.
const CHAVE = "intellix_conversas";

export function carregarConversas() {
  try {
    const salvo = localStorage.getItem(CHAVE);
    return salvo ? JSON.parse(salvo) : [];
  } catch {
    return [];
  }
}

export function salvarConversas(conversas) {
  localStorage.setItem(CHAVE, JSON.stringify(conversas));
}

export function novoId() {
  return `c_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export function tituloFromPergunta(pergunta) {
  return pergunta.length > 42 ? `${pergunta.slice(0, 42)}…` : pergunta;
}
