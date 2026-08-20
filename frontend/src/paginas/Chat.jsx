import { useEffect, useRef, useState } from "react";
import GraficoBarra from "../componentes/GraficoBarra";
import Logo from "../componentes/Logo";
import { baixarExcel, baixarPdf } from "../utils/exportar";
import { EXEMPLOS } from "../utils/exemplos";

// Quanto tempo a mensagem "Encontrei N registros" fica na tela antes de dar
// lugar à resposta completa — ver `reveladas` em Chat, mais abaixo.
const PAUSA_REVELACAO_MS = 550;

// Avatar do Intellix nas respostas. É a logo — variante símbolo, a mesma da
// sidebar recolhida — nunca um ícone inventado (ver regra da marca no
// CLAUDE.md). Decorativo: quem identifica o autor da mensagem é a posição
// (à esquerda) mais o texto que o leitor de tela já anuncia.
function AvatarMarca() {
  return (
    <span className="avatar-marca" aria-hidden="true">
      <Logo variante="simbolo" largura={18} />
    </span>
  );
}

// Abaixo disto não adivinhamos o resultado — mostramos exemplos (D6 #3).
const CONFIANCA_MINIMA = 0.5;

// Linha de meta única, no fim da resposta: confiança, quantos registros
// voltaram e as ações de exportar — três informações que antes viviam em
// três lugares (selo no cabeçalho, frase solta, botões embaixo). Texto
// discreto com um ponto colorido, não um badge — a cor já diz "confiança",
// não precisa de uma caixa em volta pra parecer importante. `baixa` nunca
// chega aqui: essa faixa já vira o bloco `resultado-incerto` acima.
function LinhaMeta({ r }) {
  const alta = r.confianca != null && r.confianca >= 0.8;
  const n = r.linhas?.length ?? 0;
  return (
    <div className="linha-meta">
      {r.confianca != null && (
        <>
          <span className={`meta-confianca ${alta ? "meta-confianca-alta" : "meta-confianca-media"}`}>
            <span className="meta-ponto" aria-hidden="true" />
            {alta ? "Alta confiabilidade" : "Confiabilidade média"}
          </span>
          <span className="meta-sep" aria-hidden="true">·</span>
        </>
      )}
      <span className="meta-registros">
        {n === 1 ? "1 registro" : `${n} registros`}
      </span>
      <span className="meta-sep" aria-hidden="true">·</span>
      <button type="button" className="meta-acao" onClick={() => baixarExcel(r)}>
        Excel
      </button>
      <button type="button" className="meta-acao" onClick={() => baixarPdf(r)}>
        PDF
      </button>
    </div>
  );
}

// "valor_total" -> "Valor total". Não é um dicionário de tradução por coluna
// (o backend tem dezenas delas, em templates que ainda vão crescer) — só
// tira o snake_case, que já é mais legível que o nome cru da coluna.
function humanizarColuna(nome) {
  const s = String(nome || "").replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function formatarData(iso) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("pt-BR");
}

// "Como cheguei nessa resposta": só usa o que o ResultSet já traz — o
// período (quando o backend manda `parametros`, que o modo mock não
// preenche), a métrica e o agrupamento (deduzidos das colunas). Quantos
// registros voltaram já aparece na linha de meta (`LinhaMeta`) — repetir
// aqui seria a mesma frase duas vezes na mesma resposta. Nada de campo novo
// na API, nada de número inventado: se o dado não está no ResultSet, a
// linha simplesmente não aparece.
function DetalhesResposta({ r }) {
  const periodo =
    r.parametros?.periodo_inicio && r.parametros?.periodo_fim
      ? `${formatarData(r.parametros.periodo_inicio)} a ${formatarData(r.parametros.periodo_fim)}`
      : null;
  const metrica = r.colunas?.[r.colunas.length - 1];
  const agrupamento = r.colunas?.length > 1 ? r.colunas[0] : null;

  if (!periodo && !agrupamento && !metrica) return null;

  return (
    <details className="como-cheguei">
      <summary>Como cheguei nessa resposta</summary>
      <ul>
        {periodo && <li>Período analisado: {periodo}</li>}
        {agrupamento && <li>Agrupado por: {humanizarColuna(agrupamento)}</li>}
        {metrica && <li>Métrica: {humanizarColuna(metrica)}</li>}
      </ul>
    </details>
  );
}

// Mesmas linhas do gráfico, ordenadas da maior para a menor — o gráfico
// mostra a comparação visual, a lista dá o valor exato de cada item, sem
// precisar posicionar o mouse em cima da barra.
function listaOrdenada(r) {
  if (!r.linhas?.length || r.colunas.length < 2) return [];
  const idx = r.colunas.length - 1;
  return [...r.linhas].sort((a, b) => (Number(b[idx]) || 0) - (Number(a[idx]) || 0));
}

// O item que mais pesa na métrica, e sua fatia do total — puro cálculo em
// cima de `r.linhas`, nada vindo de fora do ResultSet. Usado só para dar uma
// frase de fechamento a gráficos de barra ("X lidera com Y% do total").
function maiorItem(r) {
  if (!r.linhas?.length || r.colunas.length < 2) return null;
  const idx = r.colunas.length - 1;
  const total = r.linhas.reduce((soma, linha) => soma + (Number(linha[idx]) || 0), 0);
  if (!total) return null;
  const maior = [...r.linhas].sort(
    (a, b) => (Number(b[idx]) || 0) - (Number(a[idx]) || 0)
  )[0];
  if (typeof maior[0] !== "string") return null;
  return { rotulo: maior[0], pct: Math.round((Number(maior[idx]) / total) * 100) };
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
    // Última coluna, não índice fixo: "faturamento" vem como [periodo, valor],
    // mas "ticket_medio" vem sozinho, sem coluna de período antes.
    const valor = r.linhas[0][r.colunas.length - 1];
    return (
      // Sem moldura: um número grande, sozinho, já lê como resposta — uma
      // caixa ao redor não ajuda a entender o dado, só imita um "widget".
      <div className="resultado resultado-numero">
        <p className="resultado-titulo">{r.titulo}</p>
        <p className="resultado-valor">
          {typeof valor === "number"
            ? valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
            : valor}
        </p>
        <DetalhesResposta r={r} />
        <LinhaMeta r={r} />
      </div>
    );
  }

  if (r.tipo_visualizacao === "barra") {
    const destaque = maiorItem(r);
    const metrica = r.colunas[r.colunas.length - 1];
    const lista = listaOrdenada(r);
    return (
      // Sem moldura de card: o gráfico entra como continuação do texto da
      // resposta — explicação, gráfico, lista com os valores exatos e a
      // frase de destaque formam uma sequência só, não widgets isolados.
      <div className="resultado resultado-grafico">
        <p className="resultado-titulo">{r.titulo}</p>
        <p className="resultado-abertura">Do maior para o menor:</p>
        <GraficoBarra r={r} />
        {lista.length > 1 && (
          <ol className="resultado-lista">
            {lista.map((linha, i) => {
              const valor = linha[r.colunas.length - 1];
              return (
                <li key={linha[0] ?? i}>
                  <span className="resultado-lista-rotulo">{linha[0]}</span>
                  <span className="resultado-lista-valor">
                    {typeof valor === "number" ? valor.toLocaleString("pt-BR") : valor}
                  </span>
                </li>
              );
            })}
          </ol>
        )}
        {destaque && (
          <p className="resultado-destaque">
            <strong>{destaque.rotulo}</strong> lidera com aproximadamente{" "}
            <strong>{destaque.pct}%</strong> do total
            {metrica ? ` de ${humanizarColuna(metrica).toLowerCase()}.` : "."}
          </p>
        )}
        <DetalhesResposta r={r} />
        <LinhaMeta r={r} />
      </div>
    );
  }

  if (r.tipo_visualizacao === "tabela") {
    return (
      // Tabela mantém uma borda leve: sem limite visual, linha e coluna se
      // perdem no texto ao redor — aqui a caixa cumpre função, não decora.
      <div className="resultado resultado-tabela">
        <p className="resultado-titulo">{r.titulo}</p>
        <p className="resultado-abertura">Aqui está o detalhamento, linha a linha:</p>
        <div className="tabela-scroll">
          <table>
            <thead>
              <tr>
                {r.colunas.map((c) => (
                  <th key={c}>{humanizarColuna(c)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {r.linhas.map((linha, i) => (
                <tr key={i}>
                  {linha.map((v, j) => (
                    <td key={j}>{typeof v === "number" ? v.toLocaleString("pt-BR") : v}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <DetalhesResposta r={r} />
        <LinhaMeta r={r} />
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
      <div className="linha-ia">
        <AvatarMarca />
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
      </div>
    );
  }
  return (
    <div className="linha-ia">
      <AvatarMarca />
      <div className="mensagem mensagem-resultado">
        <Resultado r={msg.dados} />
      </div>
    </div>
  );
}

// Coluna única: a conversa ocupa a área toda. Pesquisa e histórico moram na
// sidebar, junto da navegação (componentes/Sidebar.jsx) — aqui não há segunda
// coluna, e a rolagem interna da conversa continua sendo desta tela.
export default function Chat({
  mensagens,
  texto,
  setTexto,
  carregando,
  acordando,
  onPerguntar,
}) {
  // Microinteração de duas etapas: quando uma resposta chega, primeiro mostra
  // "Encontrei N registros" por um instante, só depois revela o card inteiro
  // — em vez de o resultado aparecer de golpe assim que os pontinhos somem.
  //
  // `reveladas` é quantas mensagens, do início da lista, já estão liberadas
  // para o render completo. Um `useRef` guarda o `carregando` do render
  // anterior porque só queremos o atraso na borda true→false de UM ciclo de
  // busca — trocar de conversa ou abrir um chat novo (que também mexe em
  // `mensagens`) precisa continuar instantâneo, sem essa pausa.
  const [reveladas, setReveladas] = useState(mensagens.length);
  const carregandoAntes = useRef(carregando);

  useEffect(() => {
    const acabouDeChegar = carregandoAntes.current && !carregando;
    carregandoAntes.current = carregando;

    const pendente = mensagens[reveladas];
    const merecePausa = acabouDeChegar && pendente?.tipo === "resultado";

    if (!merecePausa) {
      setReveladas(mensagens.length); // troca de conversa, erro, novo chat: sem atraso
      return;
    }
    const t = setTimeout(() => setReveladas(mensagens.length), PAUSA_REVELACAO_MS);
    return () => clearTimeout(t);
    // `reveladas` fica de fora de propósito: é o próprio estado sendo
    // calculado aqui dentro — incluí-lo reprocessaria o efeito no instante
    // em que ele muda, criando um laço.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mensagens, carregando]);

  const pendente = reveladas < mensagens.length ? mensagens[reveladas] : null;
  const registrosPendentes = pendente?.dados?.linhas?.length ?? 0;

  function enviar(e) {
    e.preventDefault();
    onPerguntar(texto);
  }

  const vazio = mensagens.length === 0;

  return (
    <div className="chat-pagina">
      {/* tabindex=0: a lista rola por dentro, e sem isso o teclado não
          alcança essa rolagem — só o mouse chegaria nas mensagens antigas. */}
      <div
        className="chat"
        tabIndex={0}
        role="log"
        aria-label="Conversa"
        aria-live="polite"
      >
        {vazio && !carregando && (
          <div className="tela-inicial anima-entrada">
            <p>Pergunte sobre suas vendas. Por exemplo:</p>
            <div className="exemplos">
              {EXEMPLOS.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  className="exemplo"
                  onClick={() => onPerguntar(ex)}
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {mensagens.slice(0, reveladas).map((msg, i) => (
          <Mensagem key={i} msg={msg} />
        ))}

        {pendente && (
          <div className="linha-ia anima-entrada">
            <AvatarMarca />
            <div className="bolha-revelando">
              {registrosPendentes === 1
                ? "Encontrei 1 registro."
                : `Encontrei ${registrosPendentes} registros.`}
            </div>
          </div>
        )}

        {carregando && (
          <div className="linha-ia anima-entrada">
            <AvatarMarca />
            <div className="bolha-carregando">
              <span className="pontinhos" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
              {/* Um texto só, que troca de conteúdo em vez de somar um
                  segundo elemento — a lista já tem aria-live, então dois nós
                  mudando ao mesmo tempo seria a mesma notícia anunciada
                  duas vezes. Some visualmente até a hibernação do Render
                  aparecer (D6 #1: visibilidade do estado do sistema). */}
              <span className={acordando ? "carregando-texto" : "sr-only"}>
                {acordando
                  ? "O servidor está acordando, isso leva alguns segundos…"
                  : "Analisando seus dados…"}
              </span>
            </div>
          </div>
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
