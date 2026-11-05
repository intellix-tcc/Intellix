// Envio do Fale conosco.
//
// O backend não envia e-mail, e o mailto: dependia de um aplicativo de
// e-mail configurado no computador (quem usa Gmail só no navegador não via
// nada acontecer). Então a mensagem vai por HTTPS para o FormSubmit, serviço
// gratuito de formulários que entrega no e-mail da equipe — sem conta, sem
// chave e sem servidor nosso no meio.
//
// Na primeira mensagem o FormSubmit manda um e-mail de ativação para
// EMAIL_CONTATO; só depois do clique no link de ativação as mensagens passam
// a ser entregues.
import { EMAIL_CONTATO } from "../utils/contato";

const MOCK = import.meta.env.VITE_MOCK === "true";
const ENDPOINT = `https://formsubmit.co/ajax/${EMAIL_CONTATO}`;
const TEMPO_LIMITE_MS = 15000;

const FALHA = "Não conseguimos enviar agora. Tente de novo em instantes.";

/**
 * Envia a mensagem. Resolve sem valor em caso de sucesso; lança
 * { mensagem } no mesmo formato de erro do resto dos serviços.
 */
export async function enviarMensagemContato({ nome, email, assunto, mensagem, armadilha }) {
  // Campo invisível preenchido = robô. Finge que deu certo e não envia.
  if (armadilha) return;

  if (MOCK) {
    await new Promise((r) => setTimeout(r, 600));
    return;
  }

  const controle = new AbortController();
  const timer = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS);

  let resposta;
  try {
    resposta = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        nome: nome.trim(),
        email: email.trim(),
        assunto,
        mensagem: mensagem.trim(),
        _subject: `[Intellix] ${assunto} — ${nome.trim()}`,
        _replyto: email.trim(), // "Responder" no Gmail vai direto para a pessoa
        _template: "table",
      }),
      signal: controle.signal,
    });
  } catch {
    throw { mensagem: "Sem conexão com o serviço de envio. Confira sua internet e tente de novo." };
  } finally {
    clearTimeout(timer);
  }

  const dados = await resposta.json().catch(() => null);
  // O FormSubmit devolve success como string ("true"/"false").
  if (!resposta.ok || String(dados?.success) !== "true") {
    throw { mensagem: FALHA };
  }
}
