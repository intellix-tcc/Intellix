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
// A primeira mensagem (a que dispara a ativação) pode demorar bem mais que
// as seguintes.
const TEMPO_LIMITE_MS = 30000;

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

  // FormData, não JSON: com Content-Type application/json o navegador faz
  // antes uma requisição OPTIONS (preflight de CORS), e quando o serviço não
  // responde a ela direito o fetch falha sem nem enviar a mensagem. FormData
  // + Accept é requisição "simples" de CORS: vai direto, sem preflight.
  const corpo = new FormData();
  corpo.append("nome", nome.trim());
  corpo.append("email", email.trim());
  corpo.append("assunto", assunto);
  corpo.append("mensagem", mensagem.trim());
  corpo.append("_subject", `[Intellix] ${assunto} — ${nome.trim()}`);
  corpo.append("_replyto", email.trim()); // "Responder" no Gmail vai direto para a pessoa
  corpo.append("_template", "table");

  let resposta;
  try {
    resposta = await fetch(ENDPOINT, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: corpo,
      signal: controle.signal,
    });
  } catch (e) {
    if (e?.name === "AbortError") {
      throw { mensagem: "O serviço de envio demorou demais para responder." };
    }
    // Falha de rede, bloqueador de anúncios/rastreadores ou serviço fora do ar.
    throw { mensagem: "Não conseguimos falar com o serviço de envio." };
  } finally {
    clearTimeout(timer);
  }

  const dados = await resposta.json().catch(() => null);
  // O FormSubmit devolve success como string ("true"/"false").
  if (!resposta.ok || String(dados?.success) !== "true") {
    throw { mensagem: FALHA };
  }
}
