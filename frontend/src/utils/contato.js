// Canal de contato e versão dos Termos de uso — um lugar só, usado pelo
// Fale conosco, pelos Termos, pelo FAQ e pelo cadastro. Trocar o e-mail ou
// publicar uma revisão dos termos é mudar uma linha aqui.
export const EMAIL_CONTATO = "intellix3@gmail.com";

// Data da versão vigente dos Termos de uso (AAAA-MM-DD). Vai junto com o
// aceite no cadastro, para saber qual versão a pessoa aceitou.
export const TERMOS_VERSAO = "2026-11-05";

export const TERMOS_ATUALIZADO_EM = new Date(`${TERMOS_VERSAO}T12:00:00`).toLocaleDateString(
  "pt-BR",
  { day: "numeric", month: "long", year: "numeric" }
);

export const ASSUNTOS_CONTATO = [
  "Dúvida sobre o uso",
  "Problema técnico",
  "Importação de planilha",
  "Sugestão",
  "Privacidade e dados",
  "Outro",
];

/** Monta o link mailto: com assunto e corpo já preenchidos. */
export function montarMailto({ nome, email, assunto, mensagem }) {
  const corpo = [mensagem.trim(), "", "—", `Nome: ${nome.trim()}`, `E-mail para resposta: ${email.trim()}`].join(
    "\n"
  );
  const params = new URLSearchParams({ subject: `[Intellix] ${assunto}`, body: corpo });
  // URLSearchParams codifica espaço como "+", que alguns clientes de e-mail
  // mostram literalmente; mailto: espera %20.
  return `mailto:${EMAIL_CONTATO}?${params.toString().replace(/\+/g, "%20")}`;
}

// Páginas institucionais, abertas mesmo sem login (ver App.jsx). Usadas no
// cabeçalho e no rodapé da vitrine e das páginas públicas.
export const ROTAS_PUBLICAS = ["faq", "termos", "contato"];

export const LINKS_INSTITUCIONAIS = [
  { rota: "faq", href: "#/faq", rotulo: "Perguntas frequentes" },
  { rota: "termos", href: "#/termos", rotulo: "Termos de uso" },
  { rota: "contato", href: "#/contato", rotulo: "Fale conosco" },
];
