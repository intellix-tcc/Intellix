import { useState, useRef, useEffect, lazy, Suspense } from "react";
import { perguntar, aquecerServidor, EVENTO_SESSAO_RECUSADA } from "./servicos/api";
import Sidebar from "./componentes/Sidebar";
import Icone from "./componentes/Icone";
import Login from "./paginas/Login";
import CascaPublica from "./componentes/CascaPublica";
import PaletaComandos from "./componentes/PaletaComandos";
import {
  aplicarPreferencias,
  carregarPreferencias,
  salvarPreferencias,
  sistemaEscuro,
} from "./utils/preferencias";

// Cada página vira um arquivo próprio, baixado só quando a rota abre. Antes
// tudo (gráficos, leitor de planilha, páginas institucionais) vinha num
// pacote único de ~700 kB antes de a primeira tela aparecer. A tela de login
// continua no pacote principal: é a primeira coisa que quem chega vê.
const carregar = {
  home: () => import("./paginas/Home"),
  chat: () => import("./paginas/Chat"),
  importar: () => import("./paginas/Importar"),
  sobre: () => import("./paginas/Sobre"),
  perfil: () => import("./paginas/Perfil"),
  faq: () => import("./paginas/Faq"),
  termos: () => import("./paginas/Termos"),
  contato: () => import("./paginas/FaleConosco"),
};
const Home = lazy(carregar.home);
const Chat = lazy(carregar.chat);
const Importar = lazy(carregar.importar);
const Sobre = lazy(carregar.sobre);
const Perfil = lazy(carregar.perfil);
const Faq = lazy(carregar.faq);
const Termos = lazy(carregar.termos);
const FaleConosco = lazy(carregar.contato);

/** Baixa as páginas mais usadas no tempo ocioso, depois da primeira tela. */
function preCarregarPaginas() {
  const agendar = window.requestIdleCallback || ((fn) => setTimeout(fn, 1500));
  agendar(() => {
    carregar.home();
    carregar.chat();
  });
}
import { ROTAS_PUBLICAS } from "./utils/contato";
import { carregarSessao, encerrarSessao, sessaoExpirou } from "./servicos/auth";
import { carregarConversas, salvarConversas, novoId, tituloFromPergunta } from "./utils/historico";
import "./estilos/App.css";

const ROTAS = ["home", "chat", "importar", "sobre", "perfil", ...ROTAS_PUBLICAS];
const TITULOS = {
  home: "Início",
  chat: "Perguntar",
  importar: "Importar dados",
  sobre: "Sobre",
  perfil: "Meu perfil",
  faq: "Perguntas frequentes",
  termos: "Termos de uso",
  contato: "Fale conosco",
};

const MSG_EXPIRADA = "Sua sessão expirou por inatividade. Entre de novo para continuar.";

// Roteamento por hash: sem dependência extra, sem configuração de rewrite na
// Vercel, e o botão voltar do navegador funciona de graça.
function lerRota() {
  const hash = window.location.hash.replace(/^#\/?/, "");
  return ROTAS.includes(hash) ? hash : "home";
}

// Três estados, não dois. "auto" é o padrão: a sidebar recolhe sozinha
// quando a página desce e volta quando sobe. Assim que a pessoa usa o botão,
// vira escolha explícita ("aberta"/"fechada") e a rolagem para de mandar —
// senão o sistema desfaria a decisão dela no scroll seguinte.
function sidebarInicial() {
  const salvo = localStorage.getItem("intellix_sidebar");
  return salvo === "aberta" || salvo === "fechada" ? salvo : "auto";
}

// Altura a partir da qual a sidebar recolhe. Alto o bastante para um ajuste
// pequeno de rolagem não ficar piscando a barra.
const ROLAGEM_PARA_RECOLHER = 140;

export default function App() {
  // Declarado antes de `usuario` de propósito: carregarSessao() apaga a sessão
  // vencida, então a checagem tem que rodar primeiro.
  const [avisoSessao, setAvisoSessao] = useState(() => (sessaoExpirou() ? MSG_EXPIRADA : ""));
  const [usuario, setUsuario] = useState(carregarSessao);
  // Tema, tamanho do texto e animações (utils/preferencias.js). `tema` abaixo
  // é o efetivo: com "igual ao sistema", acompanha o sistema operacional.
  const [preferencias, setPreferencias] = useState(carregarPreferencias);
  const [escuroNoSistema, setEscuroNoSistema] = useState(sistemaEscuro);
  const tema =
    preferencias.tema === "sistema" ? (escuroNoSistema ? "escuro" : "claro") : preferencias.tema;
  const [paletaAberta, setPaletaAberta] = useState(false);
  const [rota, setRota] = useState(lerRota);
  const [menuAberto, setMenuAberto] = useState(false);
  const [modoSidebar, setModoSidebar] = useState(sidebarInicial);
  const [rolouPagina, setRolouPagina] = useState(false);
  // No modo automático quem decide é a rolagem; nos outros, a escolha da pessoa.
  const recolhida = modoSidebar === "auto" ? rolouPagina : modoSidebar === "fechada";

  const [conversas, setConversas] = useState(carregarConversas);
  const [atualId, setAtualId] = useState(null);
  const [mensagens, setMensagens] = useState([]);
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(false);
  // D6 #1 — Visibilidade do estado: depois de 5s avisamos da hibernação do Render.
  const [acordando, setAcordando] = useState(false);
  const timerAcordando = useRef(null);

  useEffect(() => {
    aplicarPreferencias(preferencias);
    salvarPreferencias(preferencias);
  }, [preferencias]);

  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const aoMudar = (e) => setEscuroNoSistema(e.matches);
    mq.addEventListener("change", aoMudar);
    return () => mq.removeEventListener("change", aoMudar);
  }, []);

  // Título da aba acompanha a tela — é o que o leitor de tela anuncia e o
  // que aparece no histórico do navegador.
  useEffect(() => {
    document.title = usuario || ROTAS_PUBLICAS.includes(rota) ? `${TITULOS[rota]} · Intellix` : "Intellix";
  }, [rota, usuario]);

  // Foco vai para o conteúdo novo a cada troca de tela (menos na primeira
  // carga): sem isso, quem navega por teclado ou leitor de tela continua
  // "parado" no link do menu e não percebe que a página mudou.
  // Compara com a rota anterior (e não com um "primeira vez"): no modo de
  // desenvolvimento o React roda o efeito duas vezes na montagem.
  const rotaAnterior = useRef(rota);
  useEffect(() => {
    if (rotaAnterior.current === rota) return;
    rotaAnterior.current = rota;
    if (rota === "chat") return; // o chat foca o campo de pergunta sozinho
    document.getElementById("conteudo")?.focus({ preventScroll: true });
  }, [rota]);

  // Ctrl+K / ⌘K abre a paleta de comandos de qualquer tela.
  useEffect(() => {
    if (!usuario) return;
    function aoTeclar(e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletaAberta((a) => !a);
      }
    }
    window.addEventListener("keydown", aoTeclar);
    return () => window.removeEventListener("keydown", aoTeclar);
  }, [usuario]);

  useEffect(() => {
    salvarConversas(conversas);
  }, [conversas]);

  // Acorda o servidor e adianta o download das páginas principais enquanto a
  // pessoa ainda está na primeira tela (vitrine, login ou Início).
  useEffect(() => {
    aquecerServidor();
    preCarregarPaginas();
  }, []);

  useEffect(() => {
    localStorage.setItem("intellix_sidebar", modoSidebar);
  }, [modoSidebar]);

  // Recolhimento por rolagem. Só faz sentido no modo automático e nas páginas
  // que rolam — o chat tem altura fixa de viewport, então lá nunca dispara.
  useEffect(() => {
    if (modoSidebar !== "auto") return;
    function aoRolar() {
      setRolouPagina(window.scrollY > ROLAGEM_PARA_RECOLHER);
    }
    aoRolar(); // a rota pode ter mudado com a página já rolada
    window.addEventListener("scroll", aoRolar, { passive: true });
    return () => window.removeEventListener("scroll", aoRolar);
  }, [modoSidebar, rota]);

  useEffect(() => {
    const aoTrocar = () => {
      setRota(lerRota());
      setMenuAberto(false);
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", aoTrocar);
    return () => window.removeEventListener("hashchange", aoTrocar);
  }, []);

  // Servidor recusou o token (vencido/revogado): volta ao login com aviso.
  useEffect(() => {
    function aoRecusar(e) {
      encerrarSessao();
      setUsuario(null);
      setAvisoSessao(e.detail?.mensagem || MSG_EXPIRADA);
    }
    window.addEventListener(EVENTO_SESSAO_RECUSADA, aoRecusar);
    return () => window.removeEventListener(EVENTO_SESSAO_RECUSADA, aoRecusar);
  }, []);

  // Sessão que vence com a aba aberta: derruba na hora, sem esperar o F5.
  useEffect(() => {
    if (!usuario) return;
    function conferir() {
      if (!carregarSessao()) {
        setUsuario(null);
        setAvisoSessao(MSG_EXPIRADA);
      }
    }
    const id = setInterval(conferir, 60000);
    document.addEventListener("visibilitychange", conferir);
    return () => {
      clearInterval(id);
      document.removeEventListener("visibilitychange", conferir);
    };
  }, [usuario]);

  function irPara(destino) {
    // assign() com só o fragmento: navegação dentro da página, sem recarregar
    // (equivale a trocar location.hash, que a regra do React Compiler não
    // aceita quando a função também é usada pelos comandos da paleta).
    window.location.assign(destino === "home" ? "#/" : `#/${destino}`);
  }

  // O botão do topo fixa o oposto do que está na tela (sai do "sistema").
  function alternarTema() {
    setPreferencias((p) => ({ ...p, tema: tema === "escuro" ? "claro" : "escuro" }));
  }

  function novoChat() {
    setAtualId(null);
    setMensagens([]);
    if (rota !== "chat") irPara("chat");
  }

  function selecionarConversa(id) {
    const c = conversas.find((c) => c.id === id);
    if (!c) return;
    setAtualId(id);
    setMensagens(c.mensagens);
    setMenuAberto(false);
  }

  function excluirConversa(id) {
    setConversas((atual) => atual.filter((c) => c.id !== id));
    if (atualId === id) {
      setAtualId(null);
      setMensagens([]);
    }
  }

  // Salva/atualiza a conversa atual no histórico a cada troca de mensagens.
  function sincronizarHistorico(id, novasMensagens, tituloNovo) {
    setConversas((atual) => {
      if (atual.some((c) => c.id === id)) {
        return atual.map((c) => (c.id === id ? { ...c, mensagens: novasMensagens } : c));
      }
      return [
        {
          id,
          titulo: tituloNovo || "Nova conversa",
          mensagens: novasMensagens,
          criadoEm: new Date().toISOString(),
        },
        ...atual,
      ];
    });
  }

  // `nova`: começa uma conversa em vez de continuar a aberta — é o caso das
  // perguntas disparadas pela Início, que não têm nada a ver com a última
  // conversa do chat.
  async function perguntarTexto(pergunta, { nova = false } = {}) {
    if (!pergunta?.trim() || carregando) return;

    // Pergunta disparada da Home leva o usuário junto para o chat.
    if (rota !== "chat") irPara("chat");

    const base = nova ? [] : mensagens;
    const idConversa = nova ? novoId() : atualId ?? novoId();
    const primeiraPergunta = base.length === 0;

    const comUsuario = [...base, { tipo: "usuario", texto: pergunta }];
    setMensagens(comUsuario);
    sincronizarHistorico(
      idConversa,
      comUsuario,
      primeiraPergunta ? tituloFromPergunta(pergunta) : undefined
    );
    if (nova || !atualId) setAtualId(idConversa);

    setTexto("");
    setCarregando(true);
    timerAcordando.current = setTimeout(() => setAcordando(true), 5000);

    try {
      const dados = await perguntar(pergunta);
      const comResultado = [...comUsuario, { tipo: "resultado", dados }];
      setMensagens(comResultado);
      sincronizarHistorico(idConversa, comResultado);
    } catch (err) {
      const comErro = [
        ...comUsuario,
        {
          tipo: "erro",
          mensagem: err.mensagem || "Algo deu errado.",
          exemplos: err.exemplos,
        },
      ];
      setMensagens(comErro);
      sincronizarHistorico(idConversa, comErro);
    } finally {
      clearTimeout(timerAcordando.current);
      setCarregando(false);
      setAcordando(false);
    }
  }

  function sair() {
    encerrarSessao();
    setUsuario(null);
    setAvisoSessao("");
    irPara("home");
  }

  function aoEntrar(sessao) {
    setUsuario(sessao);
    setAvisoSessao("");
  }

  // Guarda de rota: sem sessão, nenhuma tela interna renderiza. O hash é
  // preservado, então depois de entrar a pessoa cai na página que pediu.
  if (!usuario) {
    // FAQ, Termos e Fale conosco abrem sem login (os Termos são lidos antes
    // do cadastro). Qualquer outra rota cai na vitrine/login.
    if (ROTAS_PUBLICAS.includes(rota)) {
      return (
        <CascaPublica rota={rota} tema={tema} onAlternarTema={alternarTema}>
          <Suspense fallback={<CarregandoPagina />}>
            <PaginaInstitucional rota={rota} usuario={null} />
          </Suspense>
        </CascaPublica>
      );
    }
    return (
      <Login onEntrar={aoEntrar} aviso={avisoSessao} tema={tema} onAlternarTema={alternarTema} />
    );
  }

  const comandos = [
    ...[
      ["home", "inicio", "panorama painel dashboard"],
      ["chat", "perguntar", "chat conversa"],
      ["importar", "importar", "planilha excel upload"],
      ["perfil", "usuarios", "conta senha foto preferencias tema texto"],
      ["sobre", "sobre", ""],
      ["faq", "ajuda", "ajuda faq duvidas perguntas frequentes"],
      ["contato", "envelope", "fale conosco contato suporte"],
      ["termos", "documento", "termos de uso privacidade lgpd"],
    ].map(([r, icone, palavras]) => ({
      id: `ir-${r}`,
      grupo: "Ir para",
      rotulo: TITULOS[r],
      icone,
      palavras,
      acao: () => irPara(r),
    })),
    { id: "nova", grupo: "Ações", rotulo: "Nova conversa", icone: "mais", acao: novoChat },
    {
      id: "tema",
      grupo: "Ações",
      rotulo: tema === "escuro" ? "Usar tema claro" : "Usar tema escuro",
      icone: tema === "escuro" ? "sol" : "lua",
      palavras: "tema escuro claro modo noturno",
      acao: alternarTema,
    },
    {
      id: "menu",
      grupo: "Ações",
      rotulo: recolhida ? "Expandir menu lateral" : "Recolher menu lateral",
      icone: "painel",
      acao: () => setModoSidebar(recolhida ? "aberta" : "fechada"),
    },
    { id: "sair", grupo: "Ações", rotulo: "Sair da conta", icone: "sair", palavras: "logout", acao: sair },
    ...conversas.slice(0, 6).map((c) => ({
      id: `conversa-${c.id}`,
      grupo: "Conversas recentes",
      rotulo: c.titulo,
      icone: "historico",
      acao: () => {
        selecionarConversa(c.id);
        irPara("chat");
      },
    })),
  ];

  return (
    // rota-* no layout: o chat precisa de regra de rolagem própria (ver App.css)
    <div
      className={`layout rota-${rota}${recolhida ? " com-sidebar-recolhida" : ""}`}
    >
      {/* Primeiro item do Tab: pula a navegação e vai direto ao conteúdo. */}
      <a
        className="pular-conteudo"
        href="#conteudo"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("conteudo")?.focus();
        }}
      >
        Pular para o conteúdo
      </a>

      <Sidebar
        rota={rota}
        aberta={menuAberto}
        recolhida={recolhida}
        onFechar={() => setMenuAberto(false)}
        usuario={usuario}
        onSair={sair}
        conversas={conversas}
        atualId={atualId}
        onSelecionar={selecionarConversa}
        onExcluir={excluirConversa}
        onNovoChat={novoChat}
      />

      <PaletaComandos
        aberta={paletaAberta}
        onFechar={() => setPaletaAberta(false)}
        comandos={comandos}
        onPerguntar={(p) => perguntarTexto(p, { nova: true })}
      />

      <div className="conteudo">
        <header className="topo">
          {/* Mobile: abre a gaveta. Desktop: some, e quem manda é o botão
              de recolher abaixo. */}
          <button
            type="button"
            className="menu-toggle"
            onClick={() => setMenuAberto((a) => !a)}
            aria-label="Abrir menu de navegação"
            aria-expanded={menuAberto}
          >
            <Icone nome="painel" size={19} />
          </button>
          {/* Recolher/expandir mora aqui, e não colado na logo: fica sempre no
              mesmo lugar, com ou sem a sidebar aberta. */}
          <button
            type="button"
            className="painel-toggle"
            // Clicar tira do automático: a partir daqui manda a pessoa.
            onClick={() => setModoSidebar(recolhida ? "aberta" : "fechada")}
            aria-label={recolhida ? "Expandir menu lateral" : "Recolher menu lateral"}
            aria-expanded={!recolhida}
            title={recolhida ? "Expandir menu lateral" : "Recolher menu lateral"}
          >
            <Icone nome="painel" size={19} />
          </button>
          <span className="topo-titulo">{TITULOS[rota]}</span>
          <button
            type="button"
            className="topo-busca"
            onClick={() => setPaletaAberta(true)}
            aria-label="Abrir paleta de comandos (Ctrl+K)"
            aria-keyshortcuts="Control+K Meta+K"
          >
            <Icone nome="lupa" size={16} />
            <span className="topo-busca-texto">Buscar ou perguntar…</span>
            <kbd className="topo-busca-atalho">Ctrl K</kbd>
          </button>
          <button
            type="button"
            className="tema-toggle"
            onClick={alternarTema}
            aria-label="Alternar tema claro/escuro"
            title="Alternar tema claro/escuro"
          >
            <Icone nome={tema === "escuro" ? "sol" : "lua"} size={18} />
          </button>
        </header>

        <main className="area" key={rota} id="conteudo" tabIndex={-1}>
          <Suspense fallback={<CarregandoPagina />}>
          {rota === "home" && (
            <Home
              usuario={usuario}
              conversas={conversas}
              onPerguntar={(p) => perguntarTexto(p, { nova: true })}
              onAbrirConversa={(id) => {
                selecionarConversa(id);
                irPara("chat");
              }}
              onIrPara={irPara}
            />
          )}
          {rota === "sobre" && <Sobre onIrParaImportar={() => irPara("importar")} />}
          {rota === "importar" && <Importar onIrParaChat={() => irPara("chat")} />}
          {rota === "perfil" && (
            <Perfil
              usuario={usuario}
              onAtualizar={setUsuario}
              onSair={sair}
              preferencias={preferencias}
              onPreferencias={setPreferencias}
            />
          )}
          {ROTAS_PUBLICAS.includes(rota) && (
            <PaginaInstitucional rota={rota} usuario={usuario} />
          )}
          {rota === "chat" && (
            <Chat
              mensagens={mensagens}
              texto={texto}
              setTexto={setTexto}
              carregando={carregando}
              acordando={acordando}
              onPerguntar={perguntarTexto}
            />
          )}
          </Suspense>
        </main>
      </div>
    </div>
  );
}

// Enquanto o arquivo da página chega. Quase sempre imperceptível (as
// principais já foram pré-carregadas); em rede lenta, evita tela em branco.
function CarregandoPagina() {
  return (
    <div className="carregando-pagina" role="status">
      <span className="carregando-pagina-anel" aria-hidden="true" />
      <span className="sr-only">Carregando…</span>
    </div>
  );
}

function PaginaInstitucional({ rota, usuario }) {
  if (rota === "faq") return <Faq />;
  if (rota === "termos") return <Termos />;
  return <FaleConosco usuario={usuario} />;
}
