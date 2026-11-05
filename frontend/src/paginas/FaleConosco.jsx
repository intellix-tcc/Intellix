import { useState } from "react";
import Icone from "../componentes/Icone";
import { validarEmail, validarNome } from "../utils/validacao";
import { ASSUNTOS_CONTATO, EMAIL_CONTATO, linkGmail } from "../utils/contato";
import { enviarMensagemContato } from "../servicos/contato";

const MENSAGEM_MIN = 10;
const MENSAGEM_MAX = 2000;

// Fale conosco. A mensagem sai direto da tela (ver servicos/contato.js) e
// chega no e-mail da equipe; a resposta vai para o e-mail informado aqui. O
// endereço da equipe continua visível e copiável como caminho alternativo.
export default function FaleConosco({ usuario }) {
  const [campos, setCampos] = useState(() => ({
    nome: usuario?.nome ?? "",
    email: usuario?.email ?? "",
    assunto: ASSUNTOS_CONTATO[0],
    mensagem: "",
  }));
  const [erros, setErros] = useState({});
  // ocioso | enviando | enviado
  const [estado, setEstado] = useState("ocioso");
  const [erroEnvio, setErroEnvio] = useState("");
  const [copiado, setCopiado] = useState(false);
  // Honeypot: campo escondido que pessoa não vê e robô preenche.
  const [armadilha, setArmadilha] = useState("");
  const enviando = estado === "enviando";

  function mudar(campo, valor) {
    setCampos((c) => ({ ...c, [campo]: valor }));
    if (erros[campo]) setErros((e) => ({ ...e, [campo]: "" }));
    setErroEnvio("");
    if (estado === "enviado") setEstado("ocioso");
  }

  function validar() {
    const texto = campos.mensagem.trim();
    const novos = {
      nome: validarNome(campos.nome),
      email: validarEmail(campos.email),
      mensagem:
        texto.length < MENSAGEM_MIN
          ? `Escreva pelo menos ${MENSAGEM_MIN} caracteres para a gente entender o que houve.`
          : "",
    };
    const limpos = Object.fromEntries(Object.entries(novos).filter(([, v]) => v));
    setErros(limpos);
    return Object.keys(limpos).length === 0;
  }

  async function enviar(e) {
    e.preventDefault();
    if (enviando || !validar()) return;
    setErroEnvio("");
    setEstado("enviando");
    try {
      await enviarMensagemContato({ ...campos, armadilha });
      setEstado("enviado");
      // Limpa só a mensagem: nome e e-mail servem para a próxima.
      setCampos((c) => ({ ...c, mensagem: "" }));
    } catch (err) {
      setEstado("ocioso");
      setErroEnvio(err?.mensagem || "Não conseguimos enviar agora. Tente de novo em instantes.");
    }
  }

  async function copiarEmail() {
    try {
      await navigator.clipboard.writeText(EMAIL_CONTATO);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      // Sem permissão de área de transferência: o e-mail continua visível
      // na tela para copiar à mão.
    }
  }

  return (
    <div className="pagina institucional">
      <header className="pagina-cabecalho anima-entrada">
        <p className="eyebrow">◆ Contato</p>
        <h1 className="pagina-titulo">Fale conosco</h1>
        <p className="pagina-sub">
          Dúvida, problema ou sugestão? Mande uma mensagem para a equipe do Intellix.
          Antes, vale dar uma olhada nas <a href="#/faq">perguntas frequentes</a>: a
          resposta pode já estar lá.
        </p>
      </header>

      <div className="contato-grade">
        <section className="painel anima-entrada" style={{ animationDelay: "60ms" }}>
          <h2 className="painel-titulo">Envie sua mensagem</h2>
          <p className="painel-texto">
            A mensagem vai direto para a equipe do Intellix, e a resposta chega no
            e-mail que você informar.
          </p>

          <form onSubmit={enviar} className="perfil-form contato-form" noValidate>
            <Campo rotulo="Nome" erro={erros.nome}>
              <input
                value={campos.nome}
                onChange={(e) => mudar("nome", e.target.value)}
                placeholder="Seu nome"
                autoComplete="name"
                maxLength={60}
                disabled={enviando}
                aria-invalid={Boolean(erros.nome)}
              />
            </Campo>

            <Campo rotulo="E-mail para resposta" erro={erros.email}>
              <input
                type="email"
                value={campos.email}
                onChange={(e) => mudar("email", e.target.value)}
                placeholder="voce@empresa.com"
                autoComplete="email"
                disabled={enviando}
                aria-invalid={Boolean(erros.email)}
              />
            </Campo>

            <Campo rotulo="Assunto">
              <select
                value={campos.assunto}
                onChange={(e) => mudar("assunto", e.target.value)}
                disabled={enviando}
              >
                {ASSUNTOS_CONTATO.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </Campo>

            <Campo
              rotulo="Mensagem"
              erro={erros.mensagem}
              contador={`${campos.mensagem.length}/${MENSAGEM_MAX}`}
            >
              <textarea
                value={campos.mensagem}
                onChange={(e) => mudar("mensagem", e.target.value)}
                placeholder="Conte o que aconteceu ou o que você gostaria de ver no Intellix."
                rows={6}
                maxLength={MENSAGEM_MAX}
                disabled={enviando}
                aria-invalid={Boolean(erros.mensagem)}
              />
            </Campo>

            <input
              type="text"
              name="_honey"
              className="contato-armadilha"
              value={armadilha}
              onChange={(e) => setArmadilha(e.target.value)}
              tabIndex={-1}
              autoComplete="off"
              aria-hidden="true"
            />

            {estado === "enviado" && (
              <p className="auth-sucesso" role="status">
                Mensagem enviada! A equipe vai responder no e-mail{" "}
                <strong>{campos.email.trim()}</strong>.
              </p>
            )}

            {/* Falhou o envio direto: o texto já digitado não se perde —
                vai pronto para o Gmail no navegador, ou é só copiar o
                endereço. */}
            {erroEnvio && (
              <div className="auth-erro contato-falha" role="alert">
                <p>
                  {erroEnvio} Você pode enviar a mesma mensagem pelo Gmail, ou escrever
                  para <strong>{EMAIL_CONTATO}</strong> pelo e-mail que preferir.
                </p>
                <div className="contato-falha-acoes">
                  <a
                    className="botao-secundario contato-falha-botao"
                    href={linkGmail(campos)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Icone nome="envelope" size={16} />
                    Enviar pelo Gmail
                  </a>
                  <button type="button" className="link" onClick={copiarEmail}>
                    {copiado ? "E-mail copiado!" : "Copiar e-mail"}
                  </button>
                </div>
              </div>
            )}

            <div className="painel-acoes">
              <button type="submit" className="botao-primario" disabled={enviando}>
                {enviando ? "Enviando…" : "Enviar mensagem"}
              </button>
            </div>
          </form>
        </section>

        <aside className="painel contato-canais anima-entrada" style={{ animationDelay: "120ms" }}>
          <h2 className="painel-titulo">Outros caminhos</h2>

          <div className="contato-canal">
            <Icone nome="envelope" size={22} className="contato-canal-icone" />
            <div>
              <h3>E-mail</h3>
              <p>
                <a href={`mailto:${EMAIL_CONTATO}`}>{EMAIL_CONTATO}</a>
              </p>
              <button type="button" className="link contato-copiar" onClick={copiarEmail}>
                {copiado ? "Copiado!" : "Copiar e-mail"}
              </button>
            </div>
          </div>

          <div className="contato-canal">
            <Icone nome="ajuda" size={22} className="contato-canal-icone" />
            <div>
              <h3>Perguntas frequentes</h3>
              <p>
                Importação, tipos de pergunta, conta e senha.{" "}
                <a href="#/faq">Ver o FAQ</a>
              </p>
            </div>
          </div>

          <div className="contato-canal">
            <Icone nome="documento" size={22} className="contato-canal-icone" />
            <div>
              <h3>Privacidade e dados</h3>
              <p>
                Pedidos de acesso, correção ou exclusão de dados: escolha o assunto
                “Privacidade e dados”. Veja também os{" "}
                <a href="#/termos">Termos de uso</a>.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Campo({ rotulo, erro, contador, children }) {
  return (
    <label className={`auth-campo${erro ? " com-erro" : ""}`}>
      <span className="auth-campo-topo">
        {rotulo}
        {contador && <span className="campo-contador">{contador}</span>}
      </span>
      {children}
      {erro && (
        <span className="auth-campo-erro" role="alert">
          {erro}
        </span>
      )}
    </label>
  );
}
