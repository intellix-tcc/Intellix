import { useState } from "react";
import { entrar, registrar } from "./auth";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Login({ onEntrar }) {
  const [modo, setModo] = useState("entrar"); // "entrar" | "registrar"
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  function validar() {
    if (!EMAIL_RE.test(email)) return "Digite um e-mail válido.";
    if (senha.length < 6) return "A senha precisa ter pelo menos 6 caracteres.";
    if (modo === "registrar") {
      if (!nome.trim()) return "Digite seu nome.";
      if (senha !== confirmarSenha) return "As senhas não coincidem.";
    }
    return "";
  }

  async function enviar(e) {
    e.preventDefault();
    const mensagemErro = validar();
    if (mensagemErro) {
      setErro(mensagemErro);
      return;
    }
    setErro("");
    setCarregando(true);
    try {
      const sessao =
        modo === "registrar" ? await registrar({ nome, email, senha }) : await entrar({ email, senha });
      onEntrar(sessao);
    } catch (err) {
      setErro(err.mensagem || "Algo deu errado.");
    } finally {
      setCarregando(false);
    }
  }

  function alternarModo() {
    setModo((m) => (m === "entrar" ? "registrar" : "entrar"));
    setErro("");
  }

  return (
    <div className="auth-tela">
      <div className="auth-card">
        <h1 className="auth-titulo">Intellix</h1>
        <p className="auth-sub">{modo === "entrar" ? "Entre para ver suas vendas" : "Crie sua conta"}</p>

        <form onSubmit={enviar} className="auth-form">
          {modo === "registrar" && (
            <label className="auth-campo">
              Nome
              <input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Seu nome" />
            </label>
          )}

          <label className="auth-campo">
            E-mail
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="voce@empresa.com"
            />
          </label>

          <label className="auth-campo">
            Senha
            <input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              placeholder="••••••••"
            />
          </label>

          {modo === "registrar" && (
            <label className="auth-campo">
              Confirmar senha
              <input
                type="password"
                value={confirmarSenha}
                onChange={(e) => setConfirmarSenha(e.target.value)}
                placeholder="••••••••"
              />
            </label>
          )}

          {erro && <p className="auth-erro">{erro}</p>}

          <button type="submit" className="auth-botao" disabled={carregando}>
            {carregando ? "Aguarde…" : modo === "entrar" ? "Entrar" : "Criar conta"}
          </button>
        </form>

        <button type="button" className="auth-alternar" onClick={alternarModo}>
          {modo === "entrar" ? "Não tem conta? Criar conta" : "Já tem conta? Entrar"}
        </button>
      </div>
    </div>
  );
}
