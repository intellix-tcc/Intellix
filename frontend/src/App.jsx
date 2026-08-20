import { useState, useRef, useEffect } from "react";
import { perguntar } from "./servicos/api";
import Sidebar from "./componentes/Sidebar";
import Icone from "./componentes/Icone";
import Login from "./paginas/Login";
import Home from "./paginas/Home";
import Sobre from "./paginas/Sobre";
import Chat from "./paginas/Chat";
import Perfil from "./paginas/Perfil";
import Importar from "./paginas/Importar";
import { carregarSessao, encerrarSessao, sessaoExpirou } from "./servicos/auth";
import { carregarConversas, salvarConversas, novoId, tituloFromPergunta } from "./utils/historico";
import "./estilos/App.css";

const ROTAS = ["home", "chat", "importar", "sobre", "perfil"];
const TITULOS = {
  home: "Início",
  chat: "Perguntar",
  importar: "Importar dados",
  sobre: "Sobre",
  perfil: "Meu perfil",
};

const MSG_EXPIRADA = "Sua sessão expirou por inatividade. Entre de novo para continuar.";

// Roteamento por hash: sem dependência extra, sem configuração de rewrite na
// Vercel, e o botão voltar do navegador funciona de graça.
function lerRota() {
  const hash = window.location.hash.replace(/^#\/?/, "");
  return ROTAS.includes(hash) ? hash : "home";
}

function temaInicial() {
  const salvo = localStorage.getItem("intellix_tema");
  if (salvo === "claro" || salvo === "escuro") return salvo;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
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
  const [tema, setTema] = useState(temaInicial);
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
    document.documentElement.setAttribute("data-theme", tema === "escuro" ? "dark" : "light");
    localStorage.setItem("intellix_tema", tema);
  }, [tema]);

  useEffect(() => {
    salvarConversas(conversas);
  }, [conversas]);

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
    window.location.hash = destino === "home" ? "#/" : `#/${destino}`;
  }

  function alternarTema() {
    setTema((t) => (t === "escuro" ? "claro" : "escuro"));
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

  async function perguntarTexto(pergunta) {
    if (!pergunta?.trim() || carregando) return;

    // Pergunta disparada da Home leva o usuário junto para o chat.
    if (rota !== "chat") irPara("chat");

    const idConversa = atualId ?? novoId();
    const primeiraPergunta = mensagens.length === 0;

    const comUsuario = [...mensagens, { tipo: "usuario", texto: pergunta }];
    setMensagens(comUsuario);
    sincronizarHistorico(
      idConversa,
      comUsuario,
      primeiraPergunta ? tituloFromPergunta(pergunta) : undefined
    );
    if (!atualId) setAtualId(idConversa);

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
    return <Login onEntrar={aoEntrar} aviso={avisoSessao} />;
  }

  return (
    // rota-* no layout: o chat precisa de regra de rolagem própria (ver App.css)
    <div
      className={`layout rota-${rota}${recolhida ? " com-sidebar-recolhida" : ""}`}
    >
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
            className="tema-toggle"
            onClick={alternarTema}
            aria-label="Alternar tema claro/escuro"
            title="Alternar tema claro/escuro"
          >
            <Icone nome={tema === "escuro" ? "sol" : "lua"} size={18} />
          </button>
        </header>

        <main className="area" key={rota}>
          {rota === "home" && <Home usuario={usuario} />}
          {rota === "sobre" && <Sobre onIrParaImportar={() => irPara("importar")} />}
          {rota === "importar" && <Importar onIrParaChat={() => irPara("chat")} />}
          {rota === "perfil" && (
            <Perfil usuario={usuario} onAtualizar={setUsuario} onSair={sair} />
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
        </main>
      </div>
    </div>
  );
}
