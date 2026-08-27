import { useState } from "react";
import { entrar, registrar, solicitarRecuperacao, redefinirSenha } from "../servicos/auth";
import { validarEmail, validarNome, validarSenha, forcaSenha } from "../utils/validacao";
import { EXEMPLOS } from "../utils/exemplos";
import { RESUMO_EXEMPLO } from "../utils/resumoExemplo";
import { DIFERENCIAIS } from "../utils/diferenciais";
import Logo from "../componentes/Logo";
import Icone from "../componentes/Icone";
import CampoSenha from "../componentes/CampoSenha";

const FATURAMENTO_EXEMPLO = RESUMO_EXEMPLO.kpis[0];

// Modos da tela: entrar | registrar | recuperar.
//
// Hierarquia, de cima para baixo: identidade (logo) → frase que diz o que a
// tela faz → formulário → ação principal → caminho secundário.
//
// Não existe mais um título "Entrar" acima do formulário: ele empilhava com
// a logo e com o botão, três elementos disputando a mesma área. A frase
// auxiliar passou a ser o <h1> — visualmente é uma linha de texto, mas
// continua sendo o cabeçalho da página para leitor de tela.
const TEXTOS = {
  entrar: {
    sub: "Acesse sua conta para continuar.",
    acao: "Entrar",
    carregando: "Entrando…",
  },
  registrar: {
    sub: "Crie sua conta para começar.",
    acao: "Criar conta",
    carregando: "Criando conta…",
  },
  recuperar: {
    sub: "Vamos gerar um código para você definir uma nova senha.",
    acao: "Enviar código",
    carregando: "Gerando código…",
  },
};

const VAZIO = { nome: "", email: "", senha: "", confirmarSenha: "" };

export default function Login({ onEntrar, aviso, tema, onAlternarTema }) {
  // "landing" é a vitrine (quem somos, o que fazemos) — quem chega sem sessão
  // vê isso primeiro. "formulario" é a tela de entrar/criar conta de sempre.
  // Sessão expirada (aviso preenchido) pula direto pro formulário: a pessoa
  // já conhece o produto, só precisa entrar de novo.
  const [tela, setTela] = useState(() => (aviso ? "formulario" : "landing"));
  const [modo, setModo] = useState("entrar");
  const [campos, setCampos] = useState(VAZIO);
  const [erros, setErros] = useState({});
  const [erroGeral, setErroGeral] = useState("");
  const [carregando, setCarregando] = useState(false);

  // etapa da recuperação: "pedir" (informa e-mail) -> "redefinir" (código + senha)
  const [etapa, setEtapa] = useState("pedir");
  const [codigo, setCodigo] = useState("");
  const [codigoGerado, setCodigoGerado] = useState("");
  const [sucesso, setSucesso] = useState("");

  const t = TEXTOS[modo];

  function mudar(campo, valor) {
    setCampos((c) => ({ ...c, [campo]: valor }));
    // O erro do campo some assim que a pessoa começa a corrigir.
    if (erros[campo]) setErros((e) => ({ ...e, [campo]: "" }));
    setErroGeral("");
  }

  function trocarModo(novo) {
    setModo(novo);
    setErros({});
    setErroGeral("");
    setSucesso("");
    setEtapa("pedir");
    setCodigo("");
    setCodigoGerado("");
    setCampos((c) => ({ ...VAZIO, email: c.email }));
  }

  function acessar(modoDestino) {
    trocarModo(modoDestino);
    setTela("formulario");
  }

  /** Valida na tela antes de chamar auth.js (que valida de novo). */
  function validarLocal() {
    const novos = {};

    if (modo === "registrar") {
      novos.nome = validarNome(campos.nome);
      novos.email = validarEmail(campos.email);
      novos.senha = validarSenha(campos.senha);
      if (!novos.senha && campos.senha !== campos.confirmarSenha) {
        novos.confirmarSenha = "As senhas não coincidem.";
      }
    } else if (modo === "entrar") {
      novos.email = validarEmail(campos.email);
      novos.senha = campos.senha ? "" : "Digite sua senha.";
    } else if (etapa === "pedir") {
      novos.email = validarEmail(campos.email);
    } else {
      novos.codigo = codigo.trim() ? "" : "Digite o código que você recebeu.";
      novos.senha = validarSenha(campos.senha);
      if (!novos.senha && campos.senha !== campos.confirmarSenha) {
        novos.confirmarSenha = "As senhas não coincidem.";
      }
    }

    const limpos = Object.fromEntries(Object.entries(novos).filter(([, v]) => v));
    setErros(limpos);
    return Object.keys(limpos).length === 0;
  }

  async function enviar(e) {
    e.preventDefault();
    setErroGeral("");
    setSucesso("");
    if (!validarLocal()) return;

    setCarregando(true);
    try {
      if (modo === "entrar") {
        onEntrar(await entrar({ email: campos.email, senha: campos.senha }));
      } else if (modo === "registrar") {
        onEntrar(await registrar(campos));
      } else if (etapa === "pedir") {
        const { codigo: gerado } = await solicitarRecuperacao({ email: campos.email });
        setCodigoGerado(gerado);
        setEtapa("redefinir");
      } else {
        await redefinirSenha({
          email: campos.email,
          codigo,
          novaSenha: campos.senha,
          confirmarSenha: campos.confirmarSenha,
        });
        trocarModo("entrar");
        setSucesso("Senha alterada. Entre com a nova senha.");
      }
    } catch (err) {
      // auth.js devolve { mensagem, campo? } — com campo, o erro aparece
      // colado no input certo em vez de num aviso solto no topo.
      if (err?.campo) setErros((atual) => ({ ...atual, [err.campo]: err.mensagem }));
      else setErroGeral(err?.mensagem || "Algo deu errado. Tente de novo.");
    } finally {
      setCarregando(false);
    }
  }

  const forca = modo !== "entrar" && campos.senha ? forcaSenha(campos.senha) : null;
  const rotuloAcao =
    modo === "recuperar" && etapa === "redefinir" ? "Redefinir senha" : t.acao;

  if (tela === "landing") {
    return (
      <div className="landing-tela">
        <header className="landing-topo">
          {/* Só o símbolo, do jeito que já é usado na sidebar recolhida: a
              "completa" é um lockup empilhado (ícone em cima, "Intellix"
              embaixo), alto demais pra uma faixa de cabeçalho de uma linha
              só, e texto ao lado do ícone virou um lockup novo, inventado. */}
          <Logo variante="simbolo" largura={34} />
          <div className="landing-topo-acoes">
            <button
              type="button"
              className="tema-toggle"
              onClick={onAlternarTema}
              aria-label="Alternar tema claro/escuro"
              title="Alternar tema claro/escuro"
            >
              <Icone nome={tema === "escuro" ? "sol" : "lua"} size={18} />
            </button>
            <button
              type="button"
              className="botao-secundario landing-botao-topo"
              onClick={() => acessar("entrar")}
            >
              Entrar
            </button>
            <button
              type="button"
              className="botao-primario landing-botao-topo"
              onClick={() => acessar("registrar")}
            >
              Criar conta
            </button>
          </div>
        </header>

        {/* Grade de dados: fundo marinho fixo (não segue o tema claro/escuro,
            igual à faixa azul abaixo) — só o wrapper cobre a largura toda
            pra pintar a grade de ponta a ponta; `.landing-hero` continua
            centralizado por dentro dele, do jeito que já era. */}
        <div className="landing-hero-fundo">
          <main className="landing-hero">
            <div className="landing-hero-texto">
              <p className="eyebrow">Insights de vendas por conversa</p>
              <h1 className="landing-titulo">Pergunte às suas vendas.</h1>
              <p className="coluna-leitura sobre-lead">
                Faça a pergunta em português. A resposta vem em segundos, com os
                dados que a produziram, sem planilha, sem esperar o time de
                dados.
              </p>
              <div className="landing-cta">
                <button type="button" className="botao-primario" onClick={() => acessar("registrar")}>
                  Criar conta grátis
                </button>
                <button type="button" className="botao-secundario" onClick={() => acessar("entrar")}>
                  Já tenho conta
                </button>
              </div>
            </div>

            {/* Decorativo (aria-hidden): mesma pergunta e mesmo dado de
                exemplo já usados no painel de marca do formulário e na
                Início (utils/exemplos.js, utils/resumoExemplo.js) — não
                inventa número novo. */}
            <div className="landing-mockup" aria-hidden="true">
              <p className="landing-mockup-pergunta">{EXEMPLOS[0]}</p>
              <div className="landing-mockup-resposta">
                <span className="landing-mockup-avatar">
                  <Logo variante="simbolo" largura={14} />
                </span>
                <p className="landing-mockup-bolha">
                  {FATURAMENTO_EXEMPLO.rotulo} de {RESUMO_EXEMPLO.periodo.rotulo.split(" de ")[0]}:{" "}
                  <strong>
                    {FATURAMENTO_EXEMPLO.valor.toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })}
                  </strong>
                  , {FATURAMENTO_EXEMPLO.variacaoPct}% acima do mês anterior.
                </p>
              </div>
              <span className="landing-mockup-etiqueta">Exemplo</span>
            </div>
          </main>
        </div>

        {/* Faixa azul: fundo sólido fixo (não segue tema claro/escuro), como
            no PDF de referência, pra separar da grade de dados do hero.
            Mesmo princípio do painel de marca do formulário (auth-painel-marca):
            reaproveita os componentes de sempre (.secao, .fluxo, .sobre-fechamento)
            só redefinindo as variáveis de cor dentro do escopo. */}
        <div className="landing-faixa">
          <section className="secao">
            <h2 className="secao-titulo">O que torna o Intellix diferente</h2>
            <ul className="fluxo">
              {DIFERENCIAIS.map((d) => (
                <li key={d.titulo} className="fluxo-item">
                  <Icone nome={d.icone} size={26} className={`fluxo-icone ${d.cor}`} />
                  <div className="fluxo-texto">
                    <h3>{d.titulo}</h3>
                    <p>{d.texto}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="sobre-fechamento">
            <p>Pronto para perguntar às suas vendas?</p>
            <button type="button" className="botao-primario" onClick={() => acessar("registrar")}>
              Criar conta
            </button>
          </section>

          <footer className="landing-rodape">
            <Logo variante="simbolo" largura={18} />
            <p>Intellix, protótipo acadêmico (TCC de Ciência da Computação, UNIP).</p>
          </footer>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-tela">
      {/* Painel de marca — some abaixo de 861px (ver media query em
          App.css); no celular a tela volta a ser só o card, como antes.
          O preview de conversa é decorativo (aria-hidden): repete a mesma
          pergunta de exemplo e o mesmo dado de exemplo já usados na Início
          (utils/exemplos.js, utils/resumoExemplo.js) — não inventa número
          novo. */}
      <aside className="auth-painel-marca">
        <div className="auth-painel-conteudo">
          <Logo largura={148} className="auth-painel-logo" />
          <p className="auth-painel-eyebrow">Insights de vendas por conversa</p>
          <p className="auth-painel-titulo">Pergunte às suas vendas.</p>
          <p className="auth-painel-texto">
            Faça a pergunta em português. A resposta vem em segundos, com os
            dados que a produziram, sem planilha, sem esperar o time de
            dados.
          </p>

          <div className="auth-painel-mockup" aria-hidden="true">
            <p className="mockup-pergunta">{EXEMPLOS[0]}</p>
            <div className="mockup-resposta">
              <span className="mockup-avatar">
                <Logo variante="simbolo" largura={13} />
              </span>
              <p className="mockup-bolha">
                {FATURAMENTO_EXEMPLO.rotulo} de {RESUMO_EXEMPLO.periodo.rotulo.split(" de ")[0]}:{" "}
                <strong>
                  {FATURAMENTO_EXEMPLO.valor.toLocaleString("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  })}
                </strong>
                , {FATURAMENTO_EXEMPLO.variacaoPct}% acima do mês anterior.
              </p>
            </div>
            <span className="mockup-etiqueta">Exemplo</span>
          </div>
        </div>
      </aside>

      <div className="auth-formulario-painel">
        <button type="button" className="auth-voltar" onClick={() => setTela("landing")}>
          ← Voltar
        </button>

        <div className="auth-card anima-entrada">
          {/* 1. Identidade */}
          <div className="auth-marca">
            <Logo largura={158} />
          </div>

          {/* 2. O que esta tela faz. É o <h1> da página, com aparência de
              frase — o cabeçalho existe para quem navega por leitor de tela. */}
          <h1 className="auth-sub">{t.sub}</h1>

          {aviso && <p className="auth-aviso">{aviso}</p>}
          {sucesso && (
            <p className="auth-sucesso" role="status">
              {sucesso}
            </p>
          )}

          {/* Formulário */}
          <form onSubmit={enviar} className="auth-form" noValidate>
            {modo === "registrar" && (
              <Campo
                rotulo="Nome"
                erro={erros.nome}
                dica="Só letras, espaços e acentos, sem números."
              >
                <input
                  value={campos.nome}
                  onChange={(e) => mudar("nome", e.target.value)}
                  placeholder="Seu nome"
                  autoComplete="name"
                  maxLength={60}
                  disabled={carregando}
                  aria-invalid={Boolean(erros.nome)}
                />
              </Campo>
            )}

            {(modo !== "recuperar" || etapa === "pedir") && (
              <Campo rotulo="E-mail" erro={erros.email}>
                <input
                  type="email"
                  value={campos.email}
                  onChange={(e) => mudar("email", e.target.value)}
                  placeholder="voce@empresa.com"
                  autoComplete="email"
                  disabled={carregando}
                  aria-invalid={Boolean(erros.email)}
                />
              </Campo>
            )}

            {modo === "recuperar" && etapa === "redefinir" && (
              <>
                <p className="auth-codigo-aviso">
                  Num sistema com servidor de e-mail este código chegaria na sua
                  caixa de entrada. Como o envio ainda depende do backend, ele
                  aparece aqui: <strong>{codigoGerado}</strong>
                </p>
                <Campo rotulo="Código" erro={erros.codigo}>
                  <input
                    value={codigo}
                    onChange={(e) => {
                      setCodigo(e.target.value);
                      if (erros.codigo) setErros((x) => ({ ...x, codigo: "" }));
                    }}
                    placeholder="000000"
                    inputMode="numeric"
                    maxLength={6}
                    disabled={carregando}
                    aria-invalid={Boolean(erros.codigo)}
                  />
                </Campo>
              </>
            )}

            {(modo !== "recuperar" || etapa === "redefinir") && (
              <CampoSenha
                rotulo={modo === "recuperar" ? "Nova senha" : "Senha"}
                valor={campos.senha}
                onChange={(e) => mudar("senha", e.target.value)}
                erro={erros.senha}
                placeholder="Mínimo de 6 caracteres"
                autoComplete={modo === "entrar" ? "current-password" : "new-password"}
                disabled={carregando}
              />
            )}

            {modo === "entrar" && (
              <div className="auth-esqueci">
                <button
                  type="button"
                  className="link"
                  onClick={() => trocarModo("recuperar")}
                >
                  Esqueci minha senha
                </button>
              </div>
            )}

            {forca && (
              <div className="forca" aria-hidden="true">
                <span className={`forca-barra forca-${forca.nivel}`} />
                <span className="forca-rotulo">{forca.rotulo}</span>
              </div>
            )}

            {(modo === "registrar" || (modo === "recuperar" && etapa === "redefinir")) && (
              <CampoSenha
                rotulo="Confirmar senha"
                valor={campos.confirmarSenha}
                onChange={(e) => mudar("confirmarSenha", e.target.value)}
                erro={erros.confirmarSenha}
                placeholder="Repita a senha"
                autoComplete="new-password"
                disabled={carregando}
              />
            )}

            {erroGeral && (
              <p className="auth-erro" role="alert">
                {erroGeral}
              </p>
            )}

            {/* 3. Ação principal */}
            <button type="submit" className="auth-botao" disabled={carregando}>
              {carregando ? t.carregando : rotuloAcao}
            </button>
          </form>

          {/* 4. Caminho secundário */}
          <div className="auth-rodape">
            {modo === "entrar" ? (
              <p>
                Ainda não possui uma conta?{" "}
                <button type="button" className="link" onClick={() => trocarModo("registrar")}>
                  Criar conta
                </button>
              </p>
            ) : (
              <button type="button" className="link" onClick={() => trocarModo("entrar")}>
                ← Voltar para o login
              </button>
            )}
          </div>

          <p className="auth-nota">
            Protótipo acadêmico: as contas ficam guardadas neste navegador. A
            autenticação com servidor ainda depende do backend.
          </p>
        </div>
      </div>
    </div>
  );
}

function Campo({ rotulo, erro, dica, children }) {
  return (
    <label className={`auth-campo${erro ? " com-erro" : ""}`}>
      <span className="auth-campo-topo">{rotulo}</span>
      {children}
      {erro ? (
        <span className="auth-campo-erro" role="alert">
          {erro}
        </span>
      ) : (
        dica && <span className="auth-campo-dica">{dica}</span>
      )}
    </label>
  );
}
