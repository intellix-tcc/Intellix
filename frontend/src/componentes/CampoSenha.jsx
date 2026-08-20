import { useState } from "react";
import Icone from "./Icone";

// Campo de senha com o olho de mostrar/ocultar dentro do próprio input.
//
// Em componente próprio porque existe em quatro lugares — entrar, criar conta,
// redefinir e alterar senha — e cada um deles precisa do mesmo comportamento,
// do mesmo rótulo acessível e do mesmo estado visual. Antes era um botão de
// texto "Mostrar" repetido no cabeçalho do campo.
//
// O estado de visibilidade é local: cada campo decide o seu. Confirmar senha
// não deveria revelar a senha nova junto — são conferências independentes.
export default function CampoSenha({
  rotulo,
  valor,
  onChange,
  erro,
  dica,
  placeholder,
  autoComplete = "current-password",
  disabled,
}) {
  const [visivel, setVisivel] = useState(false);

  return (
    <label className={`auth-campo${erro ? " com-erro" : ""}`}>
      <span className="auth-campo-topo">{rotulo}</span>

      <span className="campo-senha">
        <input
          type={visivel ? "text" : "password"}
          value={valor}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          disabled={disabled}
          aria-invalid={Boolean(erro)}
        />
        <button
          type="button"
          className="olho"
          onClick={() => setVisivel((v) => !v)}
          // aria-pressed diz o estado; o aria-label diz o que o clique faz
          aria-pressed={visivel}
          aria-label={visivel ? "Ocultar senha" : "Mostrar senha"}
          title={visivel ? "Ocultar senha" : "Mostrar senha"}
          disabled={disabled}
          // tabindex -1 tiraria do teclado; fica acessível de propósito
        >
          <Icone nome={visivel ? "olho-fechado" : "olho"} size={18} />
        </button>
      </span>

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
