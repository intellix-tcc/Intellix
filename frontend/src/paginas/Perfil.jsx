import { useRef, useState } from "react";
import { atualizarPerfil, alterarSenha } from "../servicos/auth";
import { validarNome, forcaSenha } from "../utils/validacao";
import { prepararFoto, validarImagem, TAMANHO_MAX_MB } from "../utils/imagem";
import Avatar from "../componentes/Avatar";
import CampoSenha from "../componentes/CampoSenha";

// Página de perfil (rota #/perfil). Duas áreas independentes: dados da conta
// (nome + foto) e troca de senha. Cada uma tem o próprio estado de
// carregando/sucesso/erro, então salvar uma não mexe na outra.
export default function Perfil({ usuario, onAtualizar, onSair }) {
  return (
    <div className="pagina perfil">
      <header className="pagina-cabecalho anima-entrada">
        <h1 className="pagina-titulo">Meu perfil</h1>
        <p className="pagina-sub">
          Ajuste como seu nome e sua foto aparecem no Intellix.
        </p>
      </header>

      <DadosDaConta usuario={usuario} onAtualizar={onAtualizar} />
      <TrocarSenha usuario={usuario} onAtualizar={onAtualizar} />

      <section className="painel anima-entrada" style={{ animationDelay: "160ms" }}>
        <h2 className="painel-titulo">Sessão</h2>
        <p className="painel-texto">
          Você está conectado como <strong>{usuario.email}</strong>. A sessão
          expira automaticamente após 12 horas.
        </p>
        <button type="button" className="botao-perigo" onClick={onSair}>
          Encerrar sessão
        </button>
      </section>
    </div>
  );
}

function DadosDaConta({ usuario, onAtualizar }) {
  const [nome, setNome] = useState(usuario.nome);
  // null = ainda não mexeu; string = nova foto; "" = pediu para remover.
  const [previa, setPrevia] = useState(null);
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [processando, setProcessando] = useState(false);
  const [sucesso, setSucesso] = useState("");
  const inputArquivo = useRef(null);

  const fotoAtual = previa === null ? usuario.foto : previa || null;
  const mudou = nome !== usuario.nome || previa !== null;

  async function escolherArquivo(arquivo) {
    if (!arquivo) return;
    const problema = validarImagem(arquivo);
    if (problema) {
      setErro(problema);
      return;
    }
    setErro("");
    setSucesso("");
    setProcessando(true);
    try {
      // Reduz antes de guardar — foto de celular estoura a cota do navegador.
      setPrevia(await prepararFoto(arquivo));
    } catch {
      setErro("Não consegui abrir essa imagem. Tente outro arquivo.");
    } finally {
      setProcessando(false);
    }
  }

  async function salvar(e) {
    e.preventDefault();
    const problemaNome = validarNome(nome);
    if (problemaNome) {
      setErro(problemaNome);
      return;
    }
    setErro("");
    setSalvando(true);
    try {
      const sessao = await atualizarPerfil({
        email: usuario.email,
        nome,
        // undefined = não mexer na foto; null = remover.
        foto: previa === null ? undefined : previa || null,
      });
      onAtualizar(sessao);
      setPrevia(null);
      setSucesso("Perfil atualizado.");
    } catch (err) {
      setErro(err?.mensagem || "Não consegui salvar. Tente de novo.");
    } finally {
      setSalvando(false);
    }
  }

  function desfazer() {
    setNome(usuario.nome);
    setPrevia(null);
    setErro("");
    setSucesso("");
  }

  return (
    <section className="painel anima-entrada">
      <h2 className="painel-titulo">Dados da conta</h2>

      <form onSubmit={salvar} className="perfil-form" noValidate>
        <div className="perfil-foto">
          <Avatar usuario={{ nome, foto: fotoAtual }} size={96} />
          <div className="perfil-foto-acoes">
            <button
              type="button"
              className="botao-secundario"
              onClick={() => inputArquivo.current?.click()}
              disabled={processando || salvando}
            >
              {processando ? "Preparando…" : fotoAtual ? "Trocar foto" : "Adicionar foto"}
            </button>
            {fotoAtual && (
              <button
                type="button"
                className="link"
                onClick={() => {
                  setPrevia("");
                  setSucesso("");
                }}
                disabled={salvando}
              >
                Remover foto
              </button>
            )}
            <p className="perfil-foto-dica">
              JPG, PNG ou WebP, até {TAMANHO_MAX_MB} MB. Cortamos no centro,
              em formato quadrado.
            </p>
            <input
              ref={inputArquivo}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="input-escondido"
              onChange={(e) => {
                escolherArquivo(e.target.files?.[0]);
                e.target.value = ""; // permite reescolher o mesmo arquivo
              }}
            />
          </div>
        </div>

        <label className="auth-campo">
          <span className="auth-campo-topo">Nome</span>
          <input
            value={nome}
            onChange={(e) => {
              setNome(e.target.value);
              setErro("");
              setSucesso("");
            }}
            maxLength={60}
            disabled={salvando}
            aria-invalid={Boolean(erro)}
          />
          <span className="auth-campo-dica">
            É assim que o Intellix vai te chamar. Sem números.
          </span>
        </label>

        <label className="auth-campo">
          <span className="auth-campo-topo">E-mail</span>
          <input value={usuario.email} disabled readOnly />
          <span className="auth-campo-dica">
            O e-mail identifica a conta e não pode ser alterado por aqui.
          </span>
        </label>

        {erro && (
          <p className="auth-erro" role="alert">
            {erro}
          </p>
        )}
        {sucesso && (
          <p className="auth-sucesso" role="status">
            {sucesso}
          </p>
        )}

        <div className="painel-acoes">
          <button type="submit" className="botao-primario" disabled={!mudou || salvando}>
            {salvando ? "Salvando…" : "Salvar alterações"}
          </button>
          {mudou && !salvando && (
            <button type="button" className="link" onClick={desfazer}>
              Descartar
            </button>
          )}
        </div>
      </form>
    </section>
  );
}

const SENHAS_VAZIAS = { senhaAtual: "", novaSenha: "", confirmarSenha: "" };

function TrocarSenha({ usuario, onAtualizar }) {
  const [campos, setCampos] = useState(SENHAS_VAZIAS);
  const [erros, setErros] = useState({});
  const [erroGeral, setErroGeral] = useState("");
  const [sucesso, setSucesso] = useState("");
  const [salvando, setSalvando] = useState(false);

  function mudar(campo, valor) {
    setCampos((c) => ({ ...c, [campo]: valor }));
    if (erros[campo]) setErros((e) => ({ ...e, [campo]: "" }));
    setErroGeral("");
    setSucesso("");
  }

  async function salvar(e) {
    e.preventDefault();
    setErroGeral("");
    setSucesso("");
    setSalvando(true);
    try {
      // A validação toda (senha atual confere, mínimo, confirmação) mora no
      // auth.js, para valer também fora desta tela.
      const sessao = await alterarSenha({ email: usuario.email, ...campos });
      onAtualizar(sessao);
      setCampos(SENHAS_VAZIAS);
      setErros({});
      setSucesso("Senha alterada. Você continua conectado.");
    } catch (err) {
      if (err?.campo) setErros({ [err.campo]: err.mensagem });
      else setErroGeral(err?.mensagem || "Não consegui alterar a senha.");
    } finally {
      setSalvando(false);
    }
  }

  const preenchido =
    campos.senhaAtual && campos.novaSenha && campos.confirmarSenha;
  const forca = campos.novaSenha ? forcaSenha(campos.novaSenha) : null;

  return (
    <section className="painel anima-entrada" style={{ animationDelay: "80ms" }}>
      <h2 className="painel-titulo">Alterar senha</h2>
      <p className="painel-texto">
        Confirme a senha atual antes de definir uma nova.
      </p>

      <form onSubmit={salvar} className="perfil-form" noValidate>
        <CampoSenha
          rotulo="Senha atual"
          valor={campos.senhaAtual}
          onChange={(e) => mudar("senhaAtual", e.target.value)}
          erro={erros.senhaAtual}
          autoComplete="current-password"
          disabled={salvando}
        />

        <CampoSenha
          rotulo="Nova senha"
          valor={campos.novaSenha}
          onChange={(e) => mudar("novaSenha", e.target.value)}
          erro={erros.novaSenha}
          placeholder="Mínimo de 6 caracteres"
          autoComplete="new-password"
          disabled={salvando}
        />

        {forca && (
          <div className="forca" aria-hidden="true">
            <span className={`forca-barra forca-${forca.nivel}`} />
            <span className="forca-rotulo">{forca.rotulo}</span>
          </div>
        )}

        <CampoSenha
          rotulo="Confirmar nova senha"
          valor={campos.confirmarSenha}
          onChange={(e) => mudar("confirmarSenha", e.target.value)}
          erro={erros.confirmarSenha}
          autoComplete="new-password"
          disabled={salvando}
        />

        {erroGeral && (
          <p className="auth-erro" role="alert">
            {erroGeral}
          </p>
        )}
        {sucesso && (
          <p className="auth-sucesso" role="status">
            {sucesso}
          </p>
        )}

        <div className="painel-acoes">
          <button
            type="submit"
            className="botao-primario"
            disabled={!preenchido || salvando}
          >
            {salvando ? "Alterando…" : "Alterar senha"}
          </button>
        </div>
      </form>
    </section>
  );
}
