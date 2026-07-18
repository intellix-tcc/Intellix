import { useState } from "react";
import { perguntar } from "./api";

function Resultado({ r }) {
  if (r.tipo_visualizacao === "numero") {
    const [coluna, valor] = [r.colunas[1], r.linhas[0][1]];
    return (
      <div className="resultado resultado-numero">
        <p className="resultado-titulo">{r.titulo}</p>
        <p className="resultado-valor">
          {typeof valor === "number"
            ? valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
            : valor}
        </p>
      </div>
    );
  }

  if (r.tipo_visualizacao === "barra" || r.tipo_visualizacao === "tabela") {
    return (
      <div className="resultado resultado-tabela">
        <p className="resultado-titulo">{r.titulo}</p>
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
      </div>
    );
  }

  return <p>Tipo de visualização não reconhecido: {r.tipo_visualizacao}</p>;
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

  async function enviar(e) {
    e.preventDefault();
    if (!texto.trim()) return;

    const pergunta = texto;
    setMensagens((m) => [...m, { tipo: "usuario", texto: pergunta }]);
    setTexto("");
    setCarregando(true);

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
      setCarregando(false);
    }
  }

  return (
    <div className="app">
      <h1>Intellix</h1>
      <div className="chat">
        {mensagens.map((msg, i) => (
          <Mensagem key={i} msg={msg} />
        ))}
        {carregando && <p className="carregando">Analisando seus dados…</p>}
      </div>
      <form onSubmit={enviar} className="form-pergunta">
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Pergunte sobre suas vendas..."
        />
        <button type="submit" disabled={carregando}>
          Enviar
        </button>
      </form>
    </div>
  );
}