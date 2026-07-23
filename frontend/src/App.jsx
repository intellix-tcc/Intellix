import { useState, useRef } from "react";
import { perguntar } from "./api";
import GraficoBarra from "./GraficoBarra";
import { baixarExcel, baixarPdf } from "./exportar";
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

export default function App() {
  const [mensagens, setMensagens] = useState([]);
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(false);
  // D6 #1 — Visibilidade do estado: depois de 5s avisamos da hibernação do Render.
  const [acordando, setAcordando] = useState(false);
  const timerAcordando = useRef(null);

  async function perguntarTexto(pergunta) {
    if (!pergunta.trim() || carregando) return;

    setMensagens((m) => [...m, { tipo: "usuario", texto: pergunta }]);
    setTexto("");
    setCarregando(true);
    timerAcordando.current = setTimeout(() => setAcordando(true), 5000);

    try {
      const dados = await perguntar(pergunta);
      setMensagens((m) => [...m, { tipo: "resultado", dados }]);
    } catch (err) {
      setMensagens((m) => [
        ...m,
        {
          tipo: "erro",
          mensagem: err.mensagem || "Algo deu errado.",
          exemplos: err.exemplos,
        },
      ]);
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
    <div className="app">
      <h1>Intellix</h1>

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
  );
}
