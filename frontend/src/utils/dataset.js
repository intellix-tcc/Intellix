// Dataset ativo do chat.
//
// Quando o usuário importa uma planilha, o backend cria uma empresa própria
// (dataset isolado) e devolve o `empresa_id`. Guardamos ele aqui para o chat
// perguntar sobre ESSES dados em vez da base de demonstração. Mora no
// localStorage porque precisa sobreviver à troca de tela (Importar -> Chat),
// e some com "usar dados de exemplo".

const CHAVE = "intellix_dataset_ativo";

export function salvarDataset(empresaId, rotulo) {
  if (!empresaId) return;
  try {
    localStorage.setItem(CHAVE, JSON.stringify({ empresaId, rotulo, em: Date.now() }));
  } catch {
    // modo privado / storage cheio: segue sem persistir
  }
}

export function datasetAtivo() {
  try {
    const bruto = localStorage.getItem(CHAVE);
    return bruto ? JSON.parse(bruto) : null;
  } catch {
    return null;
  }
}

export function limparDataset() {
  try {
    localStorage.removeItem(CHAVE);
  } catch {
    // ignore
  }
}
