// Preferências de exibição da pessoa: tema, tamanho do texto e animações.
//
// Ficam no navegador (localStorage), como o tema já ficava, e viram
// atributos no <html> — o CSS faz o resto (ver estilos/index.css e o bloco
// "Preferências de exibição" em estilos/App.css). Nenhuma tela precisa saber
// delas.

const CHAVE = "intellix_preferencias";
const CHAVE_TEMA_ANTIGA = "intellix_tema"; // antes só o tema era guardado

export const OPCOES = {
  tema: [
    { valor: "sistema", rotulo: "Igual ao sistema" },
    { valor: "claro", rotulo: "Claro" },
    { valor: "escuro", rotulo: "Escuro" },
  ],
  texto: [
    { valor: "padrao", rotulo: "Padrão" },
    { valor: "grande", rotulo: "Grande" },
    { valor: "maior", rotulo: "Maior" },
  ],
  movimento: [
    { valor: "normal", rotulo: "Com animações" },
    { valor: "reduzido", rotulo: "Reduzir animações" },
  ],
};

const PADRAO = { tema: "sistema", texto: "padrao", movimento: "normal" };

function valida(chave, valor) {
  return OPCOES[chave].some((o) => o.valor === valor) ? valor : PADRAO[chave];
}

export function carregarPreferencias() {
  try {
    const salvo = JSON.parse(localStorage.getItem(CHAVE) || "null");
    if (salvo) {
      return {
        tema: valida("tema", salvo.tema),
        texto: valida("texto", salvo.texto),
        movimento: valida("movimento", salvo.movimento),
      };
    }
    // Quem já tinha escolhido claro/escuro antes desta tela continua igual.
    const temaAntigo = localStorage.getItem(CHAVE_TEMA_ANTIGA);
    return { ...PADRAO, tema: valida("tema", temaAntigo) };
  } catch {
    return { ...PADRAO };
  }
}

export function salvarPreferencias(p) {
  try {
    localStorage.setItem(CHAVE, JSON.stringify(p));
  } catch {
    // modo privado / storage cheio: vale só nesta aba
  }
}

export function sistemaEscuro() {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

/** Aplica no <html>. "sistema" tira o data-theme e deixa a media query decidir. */
export function aplicarPreferencias(p) {
  const raiz = document.documentElement;
  if (p.tema === "sistema") raiz.removeAttribute("data-theme");
  else raiz.setAttribute("data-theme", p.tema === "escuro" ? "dark" : "light");
  raiz.setAttribute("data-texto", p.texto);
  raiz.setAttribute("data-movimento", p.movimento);
}
