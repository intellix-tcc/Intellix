import Logo from "./Logo";
import Icone from "./Icone";
import { LINKS_INSTITUCIONAIS } from "../utils/contato";

// Moldura das páginas institucionais (FAQ, Termos, Fale conosco) para quem
// ainda não entrou: os Termos precisam ser lidos antes de criar a conta, e
// dúvida e contato não podem depender de login. Mesmo cabeçalho da vitrine
// (.landing-topo); quem já tem sessão vê as mesmas páginas dentro do layout
// normal, com a sidebar.
export default function CascaPublica({ rota, tema, onAlternarTema, children }) {
  return (
    <div className="landing-tela casca-publica">
      <header className="landing-topo">
        <a href="#/" className="casca-publica-marca" aria-label="Intellix, voltar ao início">
          <Logo variante="simbolo" largura={34} />
        </a>
        <nav className="casca-publica-nav" aria-label="Páginas institucionais">
          {LINKS_INSTITUCIONAIS.map((l) => (
            <a
              key={l.rota}
              href={l.href}
              className={`casca-publica-link${rota === l.rota ? " ativo" : ""}`}
              aria-current={rota === l.rota ? "page" : undefined}
            >
              {l.rotulo}
            </a>
          ))}
        </nav>
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
          <a href="#/" className="botao-secundario landing-botao-topo">
            Entrar
          </a>
        </div>
      </header>

      <main className="casca-publica-conteudo">{children}</main>

      <RodapeInstitucional />
    </div>
  );
}

/** Rodapé com os links institucionais — vitrine e páginas públicas. */
export function RodapeInstitucional() {
  return (
    <footer className="landing-rodape">
      <Logo variante="simbolo" largura={18} />
      <p>Intellix, protótipo acadêmico (TCC de Ciência da Computação, UNIP).</p>
      <nav className="landing-rodape-links" aria-label="Links institucionais">
        {LINKS_INSTITUCIONAIS.map((l) => (
          <a key={l.rota} href={l.href}>
            {l.rotulo}
          </a>
        ))}
      </nav>
    </footer>
  );
}
