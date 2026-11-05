import { useEffect, useRef, useState } from "react";
import GraficoResultado from "../componentes/GraficoResultado";
import LimiteErro from "../componentes/LimiteErro";
import EvolucaoMensal from "../componentes/EvolucaoMensal";
import Icone from "../componentes/Icone";
import Logo from "../componentes/Logo";
import { baixarExcel, baixarPdf } from "../utils/exportar";
import { EXEMPLOS } from "../utils/exemplos";
import { datasetAtivo, limparDataset } from "../utils/dataset";
import { SUGESTOES_INICIAIS, sugestoesDeContinuacao } from "../utils/sugestoes";
import {
  formatarValor,
  humanizarColuna,
  indiceMetrica,
  modosDisponiveis,
  naturezaDoResultado,
  rotuloItem,
  serieDoResultado,
} from "../utils/resultado";

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
// Resultado como texto: título + tabela separada por tabulação. Colado numa
// planilha, cada valor cai na sua célula; num e-mail, continua legível.
function resultadoComoTexto(r) {
  const linhas = r.linhas.map((linha) =>
    linha.map((v, j) => (typeof v === "number" ? formatarValor(r.colunas[j], v) : v)).join("\t")
  );
  return [r.titulo, r.colunas.map(humanizarColuna).join("\t"), ...linhas].join("\n");
}

function LinhaMeta({ r }) {
  const alta = r.confianca != null && r.confianca >= 0.8;
  const n = r.linhas?.length ?? 0;
  const [copiado, setCopiado] = useState(false);

  async function copiar() {
    try {
      await navigator.clipboard.writeText(resultadoComoTexto(r));
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1800);
    } catch {
      // sem permissão de área de transferência: o Excel continua disponível
    }
  }
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
      <span className="meta-acoes">
        <button
          type="button"
          className="meta-acao"
          onClick={copiar}
          aria-live="polite"
          title="Copiar o resultado como texto"
        >
          <Icone nome={copiado ? "check" : "copiar"} size={14} />
          {copiado ? "Copiado" : "Copiar"}
        </button>
        <button
          type="button"
          className="meta-acao meta-acao-excel"
          onClick={() => baixarExcel(r)}
        >
          <Icone nome="planilha" size={14} />
          Excel
        </button>
        <button
          type="button"
          className="meta-acao meta-acao-pdf"
          onClick={() => baixarPdf(r)}
        >
          <Icone nome="pdf" size={14} />
          PDF
        </button>
      </span>
    </div>
  );
}

function formatarData(iso) {
  const d = new Date(iso);
  // Datas puras ("2024-03-01") são parseadas como meia-noite UTC; sem fixar
  // timeZone, pt-BR as renderiza em Brasília (UTC-3) e "01/03" vira "29/02".
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("pt-BR", { timeZone: "UTC" });
}

// "Como cheguei nessa resposta": só usa o que o ResultSet já traz — o
// período (quando o backend manda `parametros`, que o modo mock não
// preenche), a métrica e o agrupamento (deduzidos das colunas). Nada de
// número inventado: se o dado não está no ResultSet, a linha não aparece.
function DetalhesResposta({ r }) {
  const periodo =
    r.parametros?.periodo_inicio && r.parametros?.periodo_fim
      ? `${formatarData(r.parametros.periodo_inicio)} a ${formatarData(r.parametros.periodo_fim)}`
      : null;
  const metrica = r.colunas?.[indiceMetrica(r)];
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

// Lista de perguntas clicáveis — usada no erro, na resposta incerta e nas
// sugestões de continuação. Clicar já pergunta; não precisa redigitar.
function PerguntasClicaveis({ perguntas, onPerguntar, desativado }) {
  return (
    <ul className="perguntas-clicaveis">
      {perguntas.map((p) => (
        <li key={p}>
          <button type="button" onClick={() => onPerguntar(p)} disabled={desativado}>
            {p}
            <Icone nome="seta-direita" size={13} />
          </button>
        </li>
      ))}
    </ul>
  );
}

// Frase de fechamento, calculada só sobre as linhas do ResultSet.
function Destaque({ r }) {
  const natureza = naturezaDoResultado(r);
  const serie = serieDoResultado(r);
  const coluna = r.colunas[indiceMetrica(r)];
  const total = serie.reduce((s, p) => s + p.valor, 0);
  if (!serie.length || !total) return null;

  if (natureza === "temporal") {
    const melhor = serie.reduce((a, b) => (b.valor > a.valor ? b : a), serie[0]);
    const primeiro = serie[0];
    const ultimo = serie[serie.length - 1];
    const variacao = primeiro.valor ? ((ultimo.valor - primeiro.valor) / primeiro.valor) * 100 : null;
    return (
      <p className="resultado-destaque">
        Total de <strong>{formatarValor(coluna, total)}</strong> em {serie.length} meses. Melhor mês:{" "}
        <strong>{melhor.rotulo}</strong> ({formatarValor(coluna, melhor.valor)})
        {variacao != null && (
          <>
            ; de {primeiro.rotulo} para {ultimo.rotulo}, {variacao >= 0 ? "alta" : "queda"} de{" "}
            <strong>{Math.abs(variacao).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</strong>
          </>
        )}
        .
      </p>
    );
  }
  if (natureza === "composicao" || natureza === "ranking") {
    const maior = serie.reduce((a, b) => (b.valor > a.valor ? b : a), serie[0]);
    return (
      <p className="resultado-destaque">
        <strong>{maior.rotulo}</strong> lidera com aproximadamente{" "}
        <strong>{Math.round((maior.valor / total) * 100)}%</strong> do total de{" "}
        {humanizarColuna(coluna).toLowerCase()}.
      </p>
    );
  }
  return null;
}

function TabelaResultado({ r }) {
  return (
    // Tabela mantém uma borda leve: sem limite visual, linha e coluna se
    // perdem no texto ao redor — aqui a caixa cumpre função, não decora.
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
                <td key={j} className={typeof v === "number" ? "num" : undefined}>
                  {typeof v === "number" ? formatarValor(r.colunas[j], v) : rotuloItem(r.colunas[j], v)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const MODOS = {
  linha: { rotulo: "Linha", icone: "linha" },
  barra: { rotulo: "Barras", icone: "grafico" },
  pizza: { rotulo: "Rosca", icone: "pizza" },
  comparacao: { rotulo: "Comparação", icone: "grafico" },
  tabela: { rotulo: "Tabela", icone: "planilha" },
};

// Resposta com várias linhas: o formato abre pelo tipo de dado (evolução no
// tempo = linha, composição = rosca, ranking = barras, comparação = barras
// lado a lado) e a pessoa pode trocar em "Ver como".
function ResultadoVisual({ r }) {
  const modos = modosDisponiveis(r);
  const [modo, setModo] = useState(modos[0]);
  const abertura = {
    linha: "Evolução no período:",
    barra: "Do maior para o menor:",
    pizza: "Como o total se divide:",
    comparacao: "Lado a lado:",
    tabela: "Detalhamento, linha a linha:",
  }[modo];

  return (
    <div className="resultado resultado-grafico">
      <div className="resultado-cabecalho">
        <p className="resultado-titulo">{r.titulo}</p>
        {modos.length > 1 && (
          <div className="ver-como" role="group" aria-label="Ver como">
            {modos.map((m) => (
              <button
                key={m}
                type="button"
                className={m === modo ? "ativo" : undefined}
                aria-pressed={m === modo}
                onClick={() => setModo(m)}
                title={`Ver como ${MODOS[m].rotulo.toLowerCase()}`}
              >
                <Icone nome={MODOS[m].icone} size={14} />
                <span>{MODOS[m].rotulo}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      <p className="resultado-abertura">{abertura}</p>
      {modo === "tabela" ? (
        <TabelaResultado r={r} />
      ) : (
        // Se o gráfico falhar com algum dado inesperado, a resposta não some:
        // vira tabela, com um aviso.
        <LimiteErro
          chave={modo}
          alternativo={
            <>
              <p className="aviso-grafico">Não consegui desenhar o gráfico desta resposta; aqui estão os dados.</p>
              <TabelaResultado r={r} />
            </>
          }
        >
          <GraficoResultado r={r} modo={modo} />
        </LimiteErro>
      )}
      <Destaque r={r} />
      <DetalhesResposta r={r} />
      <LinhaMeta r={r} />
    </div>
  );
}

function Resultado({ r, onPerguntar }) {
  // D6 #3 — Prevenção de erros: confiança baixa → não adivinhe, mostre exemplos.
  if (r.confianca != null && r.confianca < CONFIANCA_MINIMA) {
    return (
      <div className="resultado resultado-incerto">
        <p className="resultado-titulo">Não tenho certeza dessa resposta.</p>
        <p>Tente uma dessas perguntas:</p>
        <PerguntasClicaveis perguntas={EXEMPLOS} onPerguntar={onPerguntar} />
      </div>
    );
  }

  const temNumero = r.linhas.some((l) => l.some((v) => typeof v === "number"));

  // Um valor só (faturamento de um mês, ticket médio, variação): número grande.
  if (r.linhas.length === 1 && temNumero && r.tipo_visualizacao !== "tabela") {
    const i = indiceMetrica(r);
    const linha = r.linhas[0];
    const iAtual = r.colunas.indexOf("periodo_atual");
    const iAnterior = r.colunas.indexOf("periodo_anterior");
    return (
      // Sem moldura: um número grande, sozinho, já lê como resposta.
      <div className="resultado resultado-numero">
        <p className="resultado-titulo">{r.titulo}</p>
        <p className="resultado-valor">{formatarValor(r.colunas[i], linha[i])}</p>
        {iAtual >= 0 && iAnterior >= 0 && (
          <p className="resultado-abertura">
            De {formatarValor("faturamento", linha[iAnterior])} para{" "}
            {formatarValor("faturamento", linha[iAtual])}.
          </p>
        )}
        {/* Um mês só: a evolução dos 12 meses até ele, com o mês em destaque. */}
        {r.evolucao && (
          <LimiteErro alternativo={null}>
            <EvolucaoMensal evolucao={r.evolucao} />
          </LimiteErro>
        )}
        <DetalhesResposta r={r} />
        <LinhaMeta r={r} />
      </div>
    );
  }

  // Sem número para desenhar (ex.: lista de produtos sem saída) ou resposta
  // que o backend marcou como tabela: tabela.
  if (!temNumero || r.tipo_visualizacao === "tabela") {
    return (
      <div className="resultado resultado-tabela">
        <p className="resultado-titulo">{r.titulo}</p>
        <p className="resultado-abertura">Aqui está o detalhamento, linha a linha:</p>
        <TabelaResultado r={r} />
        <DetalhesResposta r={r} />
        <LinhaMeta r={r} />
      </div>
    );
  }

  return <ResultadoVisual r={r} />;
}

function Mensagem({ msg, ultima, perguntaAnterior, onPerguntar, ocupado }) {
  if (msg.tipo === "usuario") {
    return <div className="mensagem mensagem-usuario">{msg.texto}</div>;
  }
  if (msg.tipo === "erro") {
    return (
      <div className="linha-ia">
        <AvatarMarca />
        <div className="mensagem mensagem-erro">
          <p>{msg.mensagem}</p>
          {msg.exemplos?.length > 0 && (
            <>
              <p className="mensagem-erro-dica">Você pode tentar, por exemplo:</p>
              <PerguntasClicaveis perguntas={msg.exemplos} onPerguntar={onPerguntar} desativado={ocupado} />
            </>
          )}
          {/* Sem exemplos, o problema foi de rede/servidor: a mesma pergunta
              pode dar certo daqui a pouco. */}
          {ultima && !msg.exemplos?.length && perguntaAnterior && (
            <button
              type="button"
              className="botao-tentar"
              onClick={() => onPerguntar(perguntaAnterior)}
              disabled={ocupado}
            >
              <Icone nome="recarregar" size={14} />
              Tentar de novo
            </button>
          )}
        </div>
      </div>
    );
  }
  const continuar = ultima ? sugestoesDeContinuacao(msg.dados) : [];
  return (
    <div className="linha-ia">
      <AvatarMarca />
      <div className="mensagem mensagem-resultado">
        <Resultado r={msg.dados} onPerguntar={onPerguntar} />
        {continuar.length > 0 && (
          <div className="continuar">
            <p className="continuar-titulo">Continue a análise</p>
            <div className="continuar-opcoes">
              {continuar.map((p) => (
                <button key={p} type="button" className="continuar-opcao" onClick={() => onPerguntar(p)} disabled={ocupado}>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}
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

  // Dataset ativo (planilha importada). Estado local para o botão "usar dados
  // de exemplo" re-renderizar ao limpar. Lê o localStorage na montagem — e a
  // tela remonta ao navegar para o chat (key={rota} em App.jsx), então vem
  // sempre atualizado após uma importação.
  const [dataset, setDataset] = useState(datasetAtivo);

  function usarExemplo() {
    limparDataset();
    setDataset(null);
  }

  function enviar(e) {
    e.preventDefault();
    onPerguntar(texto);
  }

  const vazio = mensagens.length === 0;

  // Rolagem automática para a última mensagem. Só quando a pessoa já está
  // perto do fim: se ela subiu para reler uma resposta antiga, a chegada de
  // uma nova não arranca a leitura dela do lugar.
  const listaRef = useRef(null);
  const pertoDoFim = useRef(true);
  function aoRolar() {
    const el = listaRef.current;
    if (el) pertoDoFim.current = el.scrollHeight - el.scrollTop - el.clientHeight < 160;
  }
  useEffect(() => {
    const el = listaRef.current;
    if (!el || !pertoDoFim.current) return;
    const suave = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollTo({ top: el.scrollHeight, behavior: suave ? "smooth" : "auto" });
  }, [reveladas, carregando, mensagens.length]);

  // Campo de pergunta: Enter envia, Shift+Enter quebra linha, e a caixa
  // cresce com o texto até um limite (depois rola por dentro).
  const campoRef = useRef(null);
  useEffect(() => {
    const el = campoRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [texto]);
  useEffect(() => {
    if (!carregando) campoRef.current?.focus({ preventScroll: true });
  }, [carregando]);

  function aoTeclar(e) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      onPerguntar(texto);
    }
  }

  const perguntaDe = (i) => {
    for (let j = i - 1; j >= 0; j--) if (mensagens[j].tipo === "usuario") return mensagens[j].texto;
    return null;
  };

  return (
    <div className="chat-pagina">
      {dataset && (
        <div className="dataset-ativo">
          <Icone nome="planilha" size={15} className="dataset-ativo-icone" />
          <span className="dataset-ativo-texto">
            Respondendo sobre <strong>{dataset.rotulo}</strong>
          </span>
          <button type="button" className="dataset-ativo-trocar" onClick={usarExemplo}>
            usar dados de exemplo
          </button>
        </div>
      )}
      {/* tabindex=0: a lista rola por dentro, e sem isso o teclado não
          alcança essa rolagem — só o mouse chegaria nas mensagens antigas. */}
      <div
        className="chat"
        tabIndex={0}
        role="log"
        aria-label="Conversa"
        aria-live="polite"
        ref={listaRef}
        onScroll={aoRolar}
      >
        {vazio && !carregando && (
          <div className="tela-inicial anima-entrada">
            <span className="tela-inicial-marca" aria-hidden="true">
              <Logo variante="simbolo" largura={40} />
            </span>
            <h2 className="tela-inicial-titulo">O que você quer saber sobre suas vendas?</h2>
            <p className="tela-inicial-texto">
              Pergunte em português, do seu jeito. Algumas ideias para começar:
            </p>
            <div className="sugestoes-grade">
              {SUGESTOES_INICIAIS.map((g) => (
                <div key={g.tema} className="sugestao-grupo">
                  <p className="sugestao-tema">
                    <Icone nome={g.icone} size={15} />
                    {g.tema}
                  </p>
                  {g.perguntas.map((ex) => (
                    <button key={ex} type="button" className="exemplo" onClick={() => onPerguntar(ex)}>
                      {ex}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {mensagens.slice(0, reveladas).map((msg, i) => (
          <Mensagem
            key={i}
            msg={msg}
            ultima={i === mensagens.length - 1}
            perguntaAnterior={perguntaDe(i)}
            onPerguntar={onPerguntar}
            ocupado={carregando}
          />
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
        <label htmlFor="campo-pergunta" className="sr-only">
          Sua pergunta sobre as vendas
        </label>
        <textarea
          id="campo-pergunta"
          ref={campoRef}
          rows={1}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={aoTeclar}
          placeholder="Pergunte sobre suas vendas..."
          disabled={carregando}
          maxLength={500}
          aria-describedby="dica-pergunta"
        />
        <button type="submit" disabled={carregando || !texto.trim()} aria-label="Enviar pergunta">
          <span className="form-pergunta-rotulo">Enviar</span>
          <Icone nome="seta-direita" size={18} className="form-pergunta-icone" />
        </button>
      </form>
      <p id="dica-pergunta" className="form-pergunta-dica">
        <kbd>Enter</kbd> envia · <kbd>Shift</kbd> + <kbd>Enter</kbd> quebra a linha
      </p>
    </div>
  );
}
