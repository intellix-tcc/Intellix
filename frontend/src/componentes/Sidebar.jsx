import Logo from "./Logo";
import Avatar from "./Avatar";
import Icone from "./Icone";
import PainelHistorico from "./PainelHistorico";

// Navegação curta de propósito. "Importar dados" fica porque é a única porta
// para aquela tela; Perfil está logo abaixo, no rodapé.
const NAV = [
  { rota: "home", href: "#/", rotulo: "Início", icone: "inicio" },
  { rota: "chat", href: "#/chat", rotulo: "Perguntar", icone: "perguntar" },
  { rota: "importar", href: "#/importar", rotulo: "Importar dados", icone: "importar" },
  { rota: "sobre", href: "#/sobre", rotulo: "Sobre", icone: "sobre" },
];

// A partir daqui a lista de conversas passa a valer mais que o respiro da
// navegação, e a região de cima entra em modo compacto (ver .sidebar.compacta).
const CONVERSAS_PARA_COMPACTAR = 5;

export default function Sidebar({
  rota,
  aberta,
  recolhida,
  onFechar,
  usuario,
  onSair,
  conversas,
  atualId,
  onSelecionar,
  onExcluir,
  onNovoChat,
}) {
  // Histórico e pesquisa moram na mesma sidebar da navegação — não há segunda
  // coluna nem página própria. Só aparecem na área de perguntas, que é a
  // tela a que as conversas pertencem.
  const comHistorico = rota === "chat" && !recolhida;

  // Recolhida só vale no desktop; no mobile a sidebar vira gaveta e precisa
  // aparecer inteira, senão sobrariam ícones soltos sem rótulo.
  const classe = [
    "sidebar",
    aberta && "aberta",
    recolhida && "recolhida",
    comHistorico && "com-historico",
    // navegação encolhe para ceder espaço à lista, sem sumir
    comHistorico && conversas.length >= CONVERSAS_PARA_COMPACTAR && "compacta",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <>
      {/* fundo escurecido no mobile, fecha ao tocar fora */}
      <div
        className={`sidebar-backdrop${aberta ? " visivel" : ""}`}
        onClick={onFechar}
        aria-hidden="true"
      />

      <aside className={classe}>
        {/* --- Região 1: identidade + navegação. Encolhe quando preciso. --- */}
        <div className="sidebar-nav">
          <a
            className="sidebar-marca"
            href="#/"
            onClick={onFechar}
            title={recolhida ? "Intellix — início" : undefined}
          >
            {recolhida ? (
              <Logo largura={30} variante="simbolo" />
            ) : (
              <Logo largura={112} />
            )}
          </a>

          <nav className="nav" aria-label="Navegação principal">
            {NAV.map((item) => (
              <a
                key={item.rota}
                href={item.href}
                className={`nav-item${rota === item.rota ? " ativo" : ""}`}
                aria-current={rota === item.rota ? "page" : undefined}
                onClick={onFechar}
                title={recolhida ? item.rotulo : undefined}
              >
                <Icone nome={item.icone} size={19} className="nav-icone" />
                <span className="nav-rotulo">{item.rotulo}</span>
              </a>
            ))}
          </nav>
        </div>

        {/* --- Região 2: pesquisa + histórico. Tem a prioridade de espaço. --- */}
        {comHistorico && (
          <>
            <button type="button" className="hist-novo" onClick={onNovoChat}>
              <Icone nome="mais" size={15} />
              Nova conversa
            </button>
            <PainelHistorico
              conversas={conversas}
              atualId={atualId}
              onSelecionar={onSelecionar}
              onExcluir={onExcluir}
              onFechar={onFechar}
            />
          </>
        )}

        {/* Recolhida, a nova conversa continua a um clique. */}
        {rota === "chat" && recolhida && (
          <button
            type="button"
            className="hist-novo hist-novo-icone"
            onClick={onNovoChat}
            title="Nova conversa"
            aria-label="Nova conversa"
          >
            <Icone nome="mais" size={18} />
          </button>
        )}

        {usuario && (
          <div className="sidebar-perfil">
            <a
              href="#/perfil"
              className={`perfil-link${rota === "perfil" ? " ativo" : ""}`}
              onClick={onFechar}
              aria-current={rota === "perfil" ? "page" : undefined}
              title={recolhida ? `${usuario.nome} — meu perfil` : undefined}
            >
              <Avatar usuario={usuario} size={recolhida ? 32 : 34} />
              <span className="perfil-dados">
                <span className="perfil-nome">{usuario.nome}</span>
                <span className="perfil-acao">Minha conta</span>
              </span>
            </a>
            <button
              type="button"
              className="sidebar-sair"
              onClick={onSair}
              title="Sair da conta"
              aria-label="Sair da conta"
            >
              <Icone nome="sair" size={18} />
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
