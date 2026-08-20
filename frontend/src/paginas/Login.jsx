import { useState } from "react";
import { entrar, registrar, solicitarRecuperacao, redefinirSenha } from "../servicos/auth";
import { validarEmail, validarNome, validarSenha, forcaSenha } from "../utils/validacao";
import Logo from "../componentes/Logo";
import CampoSenha from "../componentes/CampoSenha";

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

export default function Login({ onEntrar, aviso }) {
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

  return (
    <div className="auth-tela">
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
              dica="Só letras, espaços e acentos — sem números."
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
