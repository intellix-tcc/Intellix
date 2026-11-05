import { useState } from "react";
import Icone from "../componentes/Icone";
import { validarEmail, validarNome } from "../utils/validacao";
import { ASSUNTOS_CONTATO, EMAIL_CONTATO, montarMailto } from "../utils/contato";

const MENSAGEM_MIN = 10;
const MENSAGEM_MAX = 2000;

// Fale conosco. Não existe envio de e-mail no backend, então o formulário
// monta a mensagem e abre o aplicativo de e-mail da pessoa já preenchido
// (mailto:). Validar aqui antes evita abrir um rascunho incompleto; e o
// e-mail fica visível e copiável para quem não tem cliente de e-mail
// configurado no computador.
export default function FaleConosco({ usuario }) {
  const [campos, setCampos] = useState(() => ({
    nome: usuario?.nome ?? "",
    email: usuario?.email ?? "",
    assunto: ASSUNTOS_CONTATO[0],
    mensagem: "",
  }));
  const [erros, setErros] = useState({});
  const [enviado, setEnviado] = useState(false);
  const [copiado, setCopiado] = useState(false);

  function mudar(campo, valor) {
    setCampos((c) => ({ ...c, [campo]: valor }));
    if (erros[campo]) setErros((e) => ({ ...e, [campo]: "" }));
    setEnviado(false);
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

  function enviar(e) {
    e.preventDefault();
    if (!validar()) return;
    window.location.href = montarMailto(campos);
    setEnviado(true);
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
            Ao enviar, abrimos o seu aplicativo de e-mail com a mensagem pronta. É só
            conferir e clicar em enviar.
          </p>

          <form onSubmit={enviar} className="perfil-form contato-form" noValidate>
            <Campo rotulo="Nome" erro={erros.nome}>
              <input
                value={campos.nome}
                onChange={(e) => mudar("nome", e.target.value)}
                placeholder="Seu nome"
                autoComplete="name"
                maxLength={60}
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
                aria-invalid={Boolean(erros.email)}
              />
            </Campo>

            <Campo rotulo="Assunto">
              <select value={campos.assunto} onChange={(e) => mudar("assunto", e.target.value)}>
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
                aria-invalid={Boolean(erros.mensagem)}
              />
            </Campo>

            {enviado && (
              <p className="auth-sucesso" role="status">
                Abrimos o seu aplicativo de e-mail com a mensagem pronta. Se nada abriu,
                envie direto para <strong>{EMAIL_CONTATO}</strong>.
              </p>
            )}

            <div className="painel-acoes">
              <button type="submit" className="botao-primario">
                Enviar mensagem
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
