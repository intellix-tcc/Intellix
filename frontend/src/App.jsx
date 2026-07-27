import { useState, useRef, useEffect } from "react";
import { perguntar } from "./api";
import GraficoBarra from "./GraficoBarra";
import { baixarExcel, baixarPdf } from "./exportar";
import Sidebar from "./Sidebar";
import { carregarConversas, salvarConversas, novoId, tituloFromPergunta } from "./historico";
import "./App.css";

// Perguntas que o sistema sabe responder. Heurística 3 (Nielsen): o usuário
// não deve adivinhar o que a ferramenta entende — a gente mostra.
const EXEMPLOS = [
  "Quanto faturei em março?",
  "Quais os 5 produtos mais vendidos?",
];

// Abaixo disto não adivinhamos o resultado — mostramos exemplos (D6 #3).
const CONFIANCA_MINIMA = 0.5;

function Confianca({ valor }) {
  if (valor == null) return null;
  const pct = Math.round(valor * 100);
  const nivel = valor >= 0.8 ? "alta" : valor >= 0.5 ? "media" : "baixa";
  return (
    <span className={`confianca confianca-${nivel}`} title="Confiança da resposta">
      {pct}% de confiança
    </span>
  );
}

function BotoesExportar({ r }) {
  return (
    <div className="exportar">
      <button type="button" onClick={() => baixarExcel(r)}>
        ⬇ Excel
      </button>
      <button type="button" onClick={() => baixarPdf(r)}>
        ⬇ PDF
      </button>
    </div>
  );
}

function Resultado({ r }) {
  // D6 #3 — Prevenção de erros: confiança baixa → não adivinhe, mostre exemplos.
  if (r.confianca != null && r.confianca < CONFIANCA_MINIMA) {
    return (
      <div className="resultado resultado-incerto">
        <p className="resultado-titulo">Não tenho certeza dessa resposta.</p>
        <p>Tente uma dessas perguntas:</p>
        <ul>
          {EXEMPLOS.map((ex) => (
            <li key={ex}>{ex}</li>
          ))}
        </ul>
      </div>
    );
  }

  if (r.tipo_visualizacao === "numero") {
    const valor = r.linhas[0][1];
    return (
      <div className="resultado resultado-numero">
        <div className="resultado-cabecalho">
          <p className="resultado-titulo">{r.titulo}</p>
          <Confianca valor={r.confianca} />
        </div>
        <p className="resultado-valor">
          {typeof valor === "number"
            ? valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
            : valor}
        </p>
        <BotoesExportar r={r} />
      </div>
    );
  }

  if (r.tipo_visualizacao === "barra") {
    return (
      <div className="resultado resultado-grafico">
        <div className="resultado-cabecalho">
          <p className="resultado-titulo">{r.titulo}</p>
          <Confianca valor={r.confianca} />
        </div>
        <GraficoBarra r={r} />
        <BotoesExportar r={r} />
      </div>
    );
  }

  if (r.tipo_visualizacao === "tabela") {
    return (
      <div className="resultado resultado-tabela">
        <div className="resultado-cabecalho">
          <p className="resultado-titulo">{r.titulo}</p>
          <Confianca valor={r.confianca} />
        </div>
        <table>
          <thead>
            <tr>
              {r.colunas.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {r.linhas.map((linha, i) => (
              <tr key={i}>
                {linha.map((v, j) => (
                  <td key={j}>
                    {typeof v === "number" ? v.toLocaleString("pt-BR") : v}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <BotoesExportar r={r} />
      </div>
    );
  }
}

function Mensagem({ msg }) {
  if (msg.tipo === "usuario") {
    return <div className="mensagem mensagem-usuario">{msg.texto}</div>;
  }
  if (msg.tipo === "erro") {
    return (
      <div className="mensagem mensagem-erro">
        <p>{msg.mensagem}</p>
        {msg.exemplos && (
          <ul>
            {msg.exemplos.map((ex) => (
              <li key={ex}>{ex}</li>
            ))}
          </ul>
        )}
      </div>
    );
  }
  return (
    <div className="mensagem mensagem-resultado">
      <Resultado r={msg.dados} />
    </div>
  );
}

function temaInicial() {
  const salvo = localStorage.getItem("intellix_tema");
  if (salvo === "claro" || salvo === "escuro") return salvo;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
}

export default function App() {
  const [tema, setTema] = useState(temaInicial);
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

  function alternarTema() {
    setTema((t) => (t === "escuro" ? "claro" : "escuro"));
  }

  function novoChat() {
    setAtualId(null);
    setMensagens([]);
  }

  function selecionarConversa(id) {
    const c = conversas.find((c) => c.id === id);
    if (!c) return;
    setAtualId(id);
    setMensagens(c.mensagens);
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
        { id, titulo: tituloNovo || "Nova conversa", mensagens: novasMensagens, criadoEm: new Date().toISOString() },
        ...atual,
      ];
    });
  }

  async function perguntarTexto(pergunta) {
    if (!pergunta.trim() || carregando) return;

    const idConversa = atualId ?? novoId();
    const primeiraPergunta = mensagens.length === 0;

    const comUsuario = [...mensagens, { tipo: "usuario", texto: pergunta }];
    setMensagens(comUsuario);
    sincronizarHistorico(idConversa, comUsuario, primeiraPergunta ? tituloFromPergunta(pergunta) : undefined);
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

  function enviar(e) {
    e.preventDefault();
    perguntarTexto(texto);
  }

  const vazio = mensagens.length === 0;

  return (
    <>
      <Sidebar
        conversas={conversas}
        atualId={atualId}
        onNovoChat={novoChat}
        onSelecionar={selecionarConversa}
        onExcluir={excluirConversa}
      />
      <div className="app">
        <div className="app-header">
          <h1>Intellix</h1>
          <button
            type="button"
            className="tema-toggle"
            onClick={alternarTema}
            aria-label="Alternar tema claro/escuro"
            title="Alternar tema claro/escuro"
          >
            {tema === "escuro" ? "☀️" : "🌙"}
          </button>
        </div>

        <div className="chat">
          {vazio && !carregando && (
            <div className="tela-inicial">
              <p>Pergunte sobre suas vendas. Por exemplo:</p>
              <div className="exemplos">
                {EXEMPLOS.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    className="exemplo"
                    onClick={() => perguntarTexto(ex)}
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {mensagens.map((msg, i) => (
            <Mensagem key={i} msg={msg} />
          ))}

          {carregando && (
            <p className="carregando">
              {acordando
                ? "O servidor está acordando, isso leva alguns segundos…"
                : "Analisando seus dados…"}
            </p>
          )}
        </div>

        <form onSubmit={enviar} className="form-pergunta">
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Pergunte sobre suas vendas..."
            disabled={carregando}
          />
          <button type="submit" disabled={carregando}>
            Enviar
          </button>
        </form>
      </div>
    </>
  );
}
