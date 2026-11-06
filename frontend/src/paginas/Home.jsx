import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { saudacao } from "../utils/saudacao";
import { buscarResumo, resumoEmCache } from "../servicos/api";
import { datasetAtivo } from "../utils/dataset";
import { quando } from "../utils/conversas";
import Icone from "../componentes/Icone";
import Rosca from "../componentes/Rosca";
import LimiteErro from "../componentes/LimiteErro";
import { animar, criarRotuloDePonto, escalaDe, numeroNaEscala } from "../utils/rotulos";
import { coresDistintas } from "../utils/cores";

const ICONE_OBSERVACAO = { alta: "seta-cima", queda: "seta-baixo", atencao: "alerta", padrao: "historico" };

const moeda = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const moedaCurta = (v) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 });
const numero = (v) => v.toLocaleString("pt-BR");
const pct = (v) => `${v.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

// "2026-11-04" -> "04/11", sem passar por Date (evita o deslocamento de fuso).
function dataCurta(iso) {
  const [, m, d] = String(iso).split("-");
  return `${d}/${m}`;
}

function valorKpi(kpi) {
  return kpi.formato === "moeda" ? moeda(kpi.valor) : numero(kpi.valor);
}

// Mesmo estilo de tooltip nos dois gráficos, nas cores do tema.
const TOOLTIP = {
  contentStyle: {
    fontSize: 12.5,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    boxShadow: "var(--shadow-2)",
  },
  labelStyle: { color: "var(--text-h)", fontWeight: 600 },
  itemStyle: { color: "var(--text)" },
};

// A Início é o panorama do mês: indicadores, gráficos, resumo em texto,
// ranking e observações, tudo calculado no backend (GET /resumo,
// backend/app/resumo.py) sobre o dataset ativo — a planilha importada ou a
// base de demonstração. Cada observação e cada atalho do fim da página vira
// uma pergunta no chat: o panorama aponta, o chat aprofunda.
export default function Home({ usuario, conversas = [], onPerguntar, onAbrirConversa, onIrPara }) {
  const [mesEscolhido, setMesEscolhido] = useState(null); // { ano, mes } | null = padrão do servidor
  const [resumo, setResumo] = useState(() => resumoEmCache());
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(() => !resumoEmCache());
  const [tentativa, setTentativa] = useState(0);
  const [exportando, setExportando] = useState(false);
  const dataset = datasetAtivo();

  useEffect(() => {
    let ativo = true;
    buscarResumo(mesEscolhido ?? undefined)
      .then((dados) => {
        if (!ativo) return;
        setResumo(dados);
        setErro(null);
      })
      .catch((e) => ativo && setErro(e))
      .finally(() => ativo && setCarregando(false));
    return () => {
      ativo = false;
    };
  }, [mesEscolhido, tentativa]);

  // Estado de "carregando" ligado no próprio evento, não no efeito: com
  // cache, a troca é instantânea e não pisca nada.
  function escolherMes(ano, mes) {
    if (!resumoEmCache({ ano, mes })) setCarregando(true);
    setMesEscolhido({ ano, mes });
  }

  function tentarDeNovo() {
    setErro(null);
    setCarregando(true);
    setTentativa((t) => t + 1);
  }

  async function exportar() {
    if (!resumo) return;
    setExportando(true);
    try {
      const { baixarResumoPdf } = await import("../utils/exportar");
      await baixarResumoPdf(resumo, dataset?.rotulo);
    } finally {
      setExportando(false);
    }
  }

  const cumprimento = saudacao({ usuario });
  const r = resumo;
  const semDados = erro?.tipo === "sem_resultado";

  return (
    <div className="pagina home">
      <div className="painel-inicio">
        {/* Cabeçalho "centro de comando": marinho fixo com a grade de dados da
            vitrine (mesma linguagem do login), saudação, controles e os
            indicadores do mês em cartões de vidro. */}
        <section className="painel-hero anima-entrada" aria-labelledby="h-saudacao">
        <header className="painel-cabecalho">
          <div>
            <h1 id="h-saudacao" className="painel-saudacao">{cumprimento}</h1>
            <p className="painel-subtitulo">
              {r ? (
                r.periodo.parcial ? (
                  <>
                    Assim está sua loja em <strong>{r.periodo.rotulo}</strong>, mês em andamento
                    (até {dataCurta(r.periodo.fim)}). As variações comparam com os mesmos dias de{" "}
                    {r.periodo_anterior.rotulo.split(" de ")[0]}.
                  </>
                ) : (
                  <>
                    Aqui está como sua loja foi em <strong>{r.periodo.rotulo}</strong>.
                  </>
                )
              ) : (
                "Preparando o panorama das suas vendas…"
              )}
            </p>
            <p className="painel-status">
              <span className={`painel-status-ponto${erro && !semDados ? " erro" : ""}`} aria-hidden="true" />
              <Icone nome="planilha" size={13} />
              {dataset ? dataset.rotulo : "Base de demonstração"}
              {r && (
                <>
                  {" · "}
                  {numero(r.total_registros)} {r.total_registros === 1 ? "registro" : "registros"} no mês
                  {r.exemplo && " · dados de exemplo"}
                </>
              )}
            </p>
          </div>

          {r && (
            <div className="painel-acoes-topo">
              <label className="painel-seletor-mes">
                <span className="sr-only">Mês do panorama</span>
                <Icone nome="calendario" size={15} />
                <select
                  value={`${r.periodo.ano}-${r.periodo.mes}`}
                  onChange={(e) => {
                    const [ano, mes] = e.target.value.split("-").map(Number);
                    escolherMes(ano, mes);
                  }}
                  disabled={carregando}
                >
                  {r.meses_disponiveis.map((m) => (
                    <option key={`${m.ano}-${m.mes}`} value={`${m.ano}-${m.mes}`}>
                      {m.rotulo.charAt(0).toUpperCase() + m.rotulo.slice(1)}
                      {m.parcial ? " (em andamento)" : ""}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="painel-botao-secundario"
                onClick={exportar}
                disabled={exportando}
              >
                <Icone nome="pdf" size={15} />
                {exportando ? "Gerando…" : "Exportar PDF"}
              </button>
            </div>
          )}
        </header>

        {r && !semDados && (
          <div
            className={`painel-kpis${carregando ? " atualizando" : ""}`}
            role="group"
            aria-label={`Indicadores de ${r.periodo.rotulo}`}
          >
            {r.kpis.map((kpi, i) => (
              <CartaoKpi
                key={kpi.chave}
                kpi={kpi}
                indice={i}
                anterior={r.periodo_anterior.rotulo.split(" de ")[0]}
                serie={kpi.chave === "faturamento" ? r.serie_mensal : null}
              />
            ))}
          </div>
        )}
        {carregando && !r && !erro && (
          <div className="painel-kpis" aria-hidden="true">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="esqueleto esqueleto-kpi" />
            ))}
          </div>
        )}
        </section>

        {semDados && (
          <EstadoVazio
            icone="importar"
            titulo="Ainda não há vendas para mostrar"
            texto="Importe a planilha de vendas da sua loja e o panorama do mês aparece aqui, com indicadores, gráficos e observações."
            acao="Importar dados"
            onAcao={() => onIrPara("importar")}
          />
        )}

        {erro && !semDados && !r && (
          <EstadoVazio
            icone="alerta"
            titulo="Não conseguimos carregar o panorama"
            texto={erro.mensagem || "Algo deu errado ao buscar os dados."}
            acao="Tentar de novo"
            onAcao={tentarDeNovo}
          />
        )}

        {carregando && !r && !erro && <Esqueleto />}

        {r && !semDados && (
          <div className={`painel-conteudo${carregando ? " atualizando" : ""}`} aria-busy={carregando}>
            {erro && (
              <p className="painel-aviso" role="alert">
                {erro.mensagem || "Não foi possível atualizar."} Mostrando o último panorama carregado.
              </p>
            )}

            {/* A Início conta a história do mês em capítulos: o resultado e o
                que o explica, o ritmo das vendas, o que vendeu, como os
                clientes compraram, a evolução, e por onde aprofundar. */}
            <Capitulo numero="01" titulo="O mês em resumo" descricao="O resultado, o que puxou e por quê." />
            <HistoriaDoMes r={r} />
            {r.observacoes.length > 0 && <Destaques observacoes={r.observacoes} onPerguntar={onPerguntar} />}

            <Capitulo numero="02" titulo="Ritmo de vendas" descricao="Em que dias o faturamento aconteceu." />
            <div className="painel-grade grade-2-1">
              <Cartao id="h-diario" titulo="Vendas por dia" icone="grafico" cor="var(--dado-4)">
                <LimiteErro alternativo={<p className="painel-legenda">Não foi possível desenhar este gráfico.</p>}>
                  <GraficoDiario serie={r.serie_diaria} mes={r.periodo.mes} />
                </LimiteErro>
              </Cartao>
              {r.dias_semana && (
                <Cartao id="h-semana" titulo="Média por dia da semana" icone="calendario" cor="var(--dado-2)">
                  <LimiteErro alternativo={<p className="painel-legenda">Não foi possível desenhar este gráfico.</p>}>
                    <GraficoSemana dias={r.dias_semana} />
                  </LimiteErro>
                </Cartao>
              )}
            </div>

            <Capitulo numero="03" titulo="O que vendeu" descricao="Os produtos e as categorias que fizeram o mês." />
            <div className="painel-grade grade-1-1">
              <Cartao id="h-ranking" titulo="Produtos que mais faturaram" icone="selo" cor="var(--dado-1)">
                {r.top_produtos.length ? (
                  <ol className="painel-ranking">
                    {r.top_produtos.map((p, i) => (
                      <li key={p.nome}>
                        <button
                          type="button"
                          className="painel-ranking-link"
                          onClick={() => onPerguntar(perguntaDeProduto(p.nome, r.periodo.rotulo))}
                          title={`Analisar ${p.nome} no chat`}
                        >
                          <span className="painel-ranking-pos">{i + 1}</span>
                          <span className="painel-ranking-nome">
                            {p.nome}
                            <span className="painel-ranking-barra" aria-hidden="true">
                              <span style={{ width: `${(p.valor / r.top_produtos[0].valor) * 100}%` }} />
                            </span>
                          </span>
                          <span className="painel-ranking-valor">{moeda(p.valor)}</span>
                          <Variacao valor={p.variacao_pct} compacta />
                          <Icone nome="seta-direita" size={13} className="painel-ranking-seta" />
                        </button>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="painel-legenda">Nenhum produto vendido no mês.</p>
                )}
              </Cartao>
              <Cartao id="h-categorias" titulo="Por categoria" icone="pizza" cor="var(--dado-3)">
                <Fatias itens={r.categorias} tipo="categoria" periodoRotulo={r.periodo.rotulo} onPerguntar={onPerguntar} />
              </Cartao>
            </div>

            <Capitulo numero="04" titulo="Como os clientes compraram" descricao="Canais de venda e formas de pagamento." />
            <div className="painel-grade grade-1-1">
              <Cartao id="h-canais" titulo="Por canal" icone="api" cor="var(--dado-6)">
                <Fatias itens={r.canais} tipo="canal" periodoRotulo={r.periodo.rotulo} onPerguntar={onPerguntar} />
              </Cartao>
              {r.pagamentos && (
                <Cartao id="h-pagamentos" titulo="Formas de pagamento" icone="cartao" cor="var(--dado-7)">
                  <Fatias itens={r.pagamentos} tipo="pagamento" periodoRotulo={r.periodo.rotulo} onPerguntar={onPerguntar} />
                </Cartao>
              )}
            </div>

            <Capitulo numero="05" titulo="Evolução" descricao="Como este mês se compara aos últimos 12." />
            <Cartao id="h-tendencia" titulo="Faturamento dos últimos 12 meses" icone="linha" cor="var(--dado-8)">
              <LimiteErro alternativo={<p className="painel-legenda">Não foi possível desenhar este gráfico.</p>}>
                <GraficoTendencia serie={r.serie_mensal} />
              </LimiteErro>
            </Cartao>

            <Capitulo numero="06" titulo={`Aprofunde em ${r.periodo.rotulo}`} descricao="Cada atalho abre a análise pronta no chat." />
            <div className="painel-atalhos" role="group" aria-label="Perguntas prontas sobre o mês">
              {atalhos(r.periodo.rotulo).map((a) => (
                <button key={a.pergunta} type="button" className="painel-atalho" onClick={() => onPerguntar(a.pergunta)}>
                  <span className="painel-atalho-icone" aria-hidden="true">
                    <Icone nome={a.icone} size={18} />
                  </span>
                  <span className="painel-atalho-rotulo">{a.rotulo}</span>
                  <span className="painel-atalho-acao" aria-hidden="true">
                    Perguntar <Icone nome="seta-direita" size={13} />
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <Cartao id="h-atividade" titulo="Atividade recente" icone="historico" cor="var(--dado-10)">
          <Atividade conversas={conversas} dataset={dataset} onAbrirConversa={onAbrirConversa} onIrPara={onIrPara} />
        </Cartao>
      </div>
    </div>
  );
}

// Título de capítulo: mesma linguagem do cabeçalho (fonte mono, linha de
// luz turquesa -> roxo), para o painel escuro e os cartões claros lerem como
// uma peça só. O número é a ordem de leitura da história do mês.
function Capitulo({ numero, titulo, descricao }) {
  return (
    <div className="capitulo anima-entrada">
      <span className="capitulo-numero" aria-hidden="true">{numero}</span>
      <div className="capitulo-texto">
        <h2>{titulo}</h2>
        {descricao && <p>{descricao}</p>}
      </div>
      <span className="capitulo-linha" aria-hidden="true" />
    </div>
  );
}

// Cartão de seção com selo de ícone colorido (o mesmo selo dos indicadores
// do cabeçalho).
function Cartao({ id, titulo, icone, cor, children, className = "" }) {
  return (
    <section className={`painel-secao cartao anima-entrada ${className}`} aria-labelledby={id} style={{ "--cor-cartao": cor }}>
      <header className="cartao-topo">
        <span className="cartao-selo" aria-hidden="true">
          <Icone nome={icone} size={15} />
        </span>
        <h3 id={id}>{titulo}</h3>
      </header>
      {children}
    </section>
  );
}

// O mês em três cartões com hierarquia: o resultado (principal, número
// grande), o que puxou (categoria e produto líderes) e por quê (vendas x
// ticket). Tudo calculado no /resumo; aqui é só a forma de ler.
function HistoriaDoMes({ r }) {
  const kpi = (chave) => r.kpis.find((k) => k.chave === chave);
  const fat = kpi("faturamento");
  const vendas = kpi("vendas");
  const ticket = kpi("ticket_medio");
  const categoria = r.categorias[0];
  const produto = r.top_produtos[0];
  const anterior = r.periodo_anterior.rotulo.split(" de ")[0];
  const conclusao = r.resumo_texto.find((t) => t.startsWith("A alta") || t.startsWith("A queda"));
  const corCategoria = categoria ? coresDistintas([categoria.nome])[0] : null;

  return (
    <div className="historia">
      <article className="historia-cartao historia-principal anima-entrada">
        <p className="historia-rotulo">Resultado do mês</p>
        <p className="historia-numero">{fat ? moeda(fat.valor) : "—"}</p>
        {fat && <Variacao valor={fat.variacao_pct} referencia={anterior} />}
        <p className="historia-texto">{r.resumo_texto[0]}</p>
      </article>

      <article className="historia-cartao anima-entrada" style={{ animationDelay: "60ms" }}>
        <p className="historia-rotulo">O que puxou</p>
        {categoria ? (
          <div className="historia-item">
            <span className="historia-ponto" style={{ background: corCategoria }} aria-hidden="true" />
            <div>
              <p className="historia-item-titulo">{categoria.nome}</p>
              <p className="historia-item-sub">categoria líder · {pct(categoria.pct)} do faturamento</p>
            </div>
          </div>
        ) : (
          <p className="historia-texto">Sem vendas por categoria no mês.</p>
        )}
        {produto && (
          <div className="historia-item">
            <span className="historia-ponto historia-ponto-produto" aria-hidden="true">
              <Icone nome="selo" size={12} />
            </span>
            <div>
              <p className="historia-item-titulo">{produto.nome}</p>
              <p className="historia-item-sub">produto que mais faturou · {moeda(produto.valor)}</p>
            </div>
          </div>
        )}
      </article>

      <article className="historia-cartao anima-entrada" style={{ animationDelay: "120ms" }}>
        <p className="historia-rotulo">Por quê</p>
        <ul className="historia-fatores">
          {vendas && (
            <li>
              <span>Número de vendas</span>
              <Variacao valor={vendas.variacao_pct} />
            </li>
          )}
          {ticket && (
            <li>
              <span>Ticket médio</span>
              <Variacao valor={ticket.variacao_pct} />
            </li>
          )}
        </ul>
        <p className="historia-texto">
          {conclusao || `Comparação com ${anterior}: veja os indicadores acima.`}
        </p>
      </article>
    </div>
  );
}

// Destaques e alertas do mês (as observações do /resumo), em cartões
// clicáveis lado a lado: cada um leva à análise no chat.
function Destaques({ observacoes, onPerguntar }) {
  return (
    <ul className="destaques" aria-label="Destaques e alertas do mês">
      {observacoes.map((o, i) => (
        <li key={i} className={`destaque destaque-${o.tipo}`}>
          {o.pergunta ? (
            <button type="button" onClick={() => onPerguntar(o.pergunta)} title={`Perguntar: ${o.pergunta}`}>
              <SeloObservacao tipo={o.tipo} />
              <span className="destaque-texto">{o.texto}</span>
              <span className="destaque-acao">
                Analisar <Icone nome="seta-direita" size={12} />
              </span>
            </button>
          ) : (
            <div>
              <SeloObservacao tipo={o.tipo} />
              <span className="destaque-texto">{o.texto}</span>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}

// Drill-down da Início: clicar num item da composição (categoria, canal,
// pagamento) ou num produto do ranking abre a análise daquele recorte no
// chat. As frases seguem os exemplos que o backend reconhece bem (filtros de
// produto/categoria/canal/pagamento — ver backend/app/filtros.py). Itens sem
// recorte possível não viram link.
const SEM_RECORTE = new Set(["Sem categoria", "Não informado", "Outros"]);

function perguntaDeFatia(tipo, nome, rotulo) {
  if (SEM_RECORTE.has(nome)) return null;
  if (tipo === "categoria") return `Quanto faturei em ${nome} em ${rotulo}?`;
  // "no canal X": a palavra "canal" é a pista que o filtro usa e mantém a
  // frase correta seja qual for o gênero do canal (no canal Loja/Site/...).
  if (tipo === "canal") return `Quanto vendi no canal ${nome} em ${rotulo}?`;
  // Mesma forma do exemplo do backend ("Quanto foi pago no pix em março…").
  if (tipo === "pagamento") return `Quanto foi pago no ${nome} em ${rotulo}?`;
  return null;
}

function perguntaDeProduto(nome, rotulo) {
  return `Quantas unidades de ${nome} vendemos em ${rotulo}?`;
}

function atalhos(rotulo) {
  return [
    { rotulo: "Faturamento do mês", pergunta: `Quanto faturei em ${rotulo}?`, icone: "grafico" },
    { rotulo: "Top 10 produtos", pergunta: `Quais os 10 produtos mais vendidos em ${rotulo}?`, icone: "selo" },
    { rotulo: "Melhores clientes", pergunta: `Quais clientes mais gastaram em ${rotulo}?`, icone: "usuarios" },
    { rotulo: "Vendas por canal", pergunta: `Quanto vendi por canal em ${rotulo}?`, icone: "api" },
    { rotulo: "Formas de pagamento", pergunta: `Vendas por forma de pagamento em ${rotulo}?`, icone: "cartao" },
    { rotulo: "Produtos parados", pergunta: `Quais produtos não venderam em ${rotulo}?`, icone: "alerta" },
  ];
}

function Variacao({ valor, compacta = false, referencia }) {
  if (valor == null) {
    return compacta ? <span className="painel-variacao neutra">—</span> : null;
  }
  const sentido = valor > 0 ? "positiva" : valor < 0 ? "negativa" : "neutra";
  const icone = valor > 0 ? "seta-cima" : valor < 0 ? "seta-baixo" : null;
  const descricao = `${valor > 0 ? "alta" : valor < 0 ? "queda" : "estável"} de ${pct(Math.abs(valor))}${
    referencia ? ` em relação a ${referencia}` : ""
  }`;
  return (
    <span className={`painel-variacao ${sentido}`} title={descricao}>
      {icone && <Icone nome={icone} size={11} />}
      <span aria-hidden="true">{pct(Math.abs(valor))}</span>
      <span className="sr-only">{descricao}</span>
      {referencia && !compacta && <span className="painel-variacao-ref" aria-hidden="true">vs {referencia.slice(0, 3)}</span>}
    </span>
  );
}

const ICONE_KPI = {
  faturamento: "grafico",
  ticket_medio: "cartao",
  vendas: "selo",
  itens: "planilha",
  clientes: "usuarios",
};

function CartaoKpi({ kpi, indice, anterior, serie }) {
  return (
    <div className={`painel-kpi painel-kpi-cor-${indice % 5}`}>
      <div className="painel-kpi-topo">
        <span className="painel-kpi-icone" aria-hidden="true">
          <Icone nome={ICONE_KPI[kpi.chave] || "grafico"} size={16} />
        </span>
        <p className="painel-kpi-rotulo">{kpi.rotulo}</p>
      </div>
      <p className="painel-kpi-valor">{valorKpi(kpi)}</p>
      <Variacao valor={kpi.variacao_pct} referencia={anterior} />
      {serie && (
        <div className="painel-kpi-sparkline" aria-hidden="true">
          <ResponsiveContainer width="100%" height={34}>
            <AreaChart data={serie} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="grad-spark" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#26c9c5" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#26c9c5" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="valor" stroke="#26c9c5" strokeWidth={1.8} fill="url(#grad-spark)" isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// Rótulo vertical acima da barra (vendas por dia): "5,7 mil". Dia sem venda
// fica sem rótulo.
function criarRotuloVertical(escala) {
  return function RotuloVertical({ x, y, width, value }) {
  if (!value || x == null) return null;
  const cx = x + width / 2;
  return (
    <text
      x={cx}
      y={y - 6}
      transform={`rotate(-90 ${cx} ${y - 6})`}
      textAnchor="start"
      dominantBaseline="central"
      fontSize={9.5}
      fill="var(--text-3)"
      fontFamily="var(--mono)"
    >
      {numeroNaEscala(value, escala)}
    </text>
  );
  };
}

function GraficoDiario({ serie, mes }) {
  const comVenda = serie.filter((d) => d.valor > 0);
  if (!comVenda.length) return <p className="painel-legenda">Sem vendas no período.</p>;
  const pico = serie.reduce((max, d) => (d.valor > max.valor ? d : max), serie[0]);
  const media = serie.reduce((s, d) => s + d.valor, 0) / serie.length;
  const mm = String(mes).padStart(2, "0");
  const escalaDiaria = escalaDe(serie.map((d) => d.valor));
  return (
    <>
      <p className="grafico-unidade">Valores em {escalaDiaria.unidade}</p>
      <div role="img" aria-label={`Gráfico de barras do faturamento diário. Pico no dia ${pico.dia}, com ${moeda(pico.valor)}; média de ${moeda(media)} por dia.`}>
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={serie} margin={{ top: 30, right: 4, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 4" />
            <XAxis dataKey="dia" interval={2} tick={{ fontSize: 11, fill: "var(--text-3)" }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip
              {...TOOLTIP}
              cursor={{ fill: "var(--hover-bg)" }}
              formatter={(v) => [moeda(v), "Faturamento"]}
              labelFormatter={(d) => `Dia ${String(d).padStart(2, "0")}/${mm}`}
            />
            <ReferenceLine y={media} stroke="var(--text-3)" strokeDasharray="5 5" />
            {/* Cor fixa (azul da marca); o dia de pico em turquesa. */}
            <Bar dataKey="valor" radius={[4, 4, 0, 0]} {...animar()}>
              {serie.map((d) => (
                <Cell key={d.dia} fill={d === pico ? "var(--dado-2)" : "var(--dado-4)"} />
              ))}
              {/* rótulo de valor na vertical, acima de cada barra: com 31
                  dias não cabe na horizontal */}
              <LabelList dataKey="valor" content={criarRotuloVertical(escalaDiaria)} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="painel-legenda">
        <span className="legenda-cor" style={{ background: "var(--dado-2)" }} aria-hidden="true" />
        Pico no dia {String(pico.dia).padStart(2, "0")}/{mm} ({moeda(pico.valor)})
        <span className="legenda-tracejado" aria-hidden="true" />
        média diária {moeda(media)}
      </p>
    </>
  );
}

function GraficoTendencia({ serie }) {
  const comValor = serie.filter((m) => m.valor > 0);
  if (comValor.length < 2) return <p className="painel-legenda">Histórico curto demais para mostrar tendência.</p>;
  const melhor = comValor.reduce((max, m) => (m.valor > max.valor ? m : max), comValor[0]);
  const escala = escalaDe(serie.map((m) => m.valor));
  return (
    <>
      <p className="grafico-unidade">Valores em {escala.unidade}</p>
      <div role="img" aria-label={`Gráfico de área do faturamento mensal dos últimos 12 meses. Melhor mês: ${melhor.rotulo}, com ${moeda(melhor.valor)}.`}>
        <ResponsiveContainer width="100%" height={230}>
          <AreaChart data={serie} margin={{ top: 30, right: 20, left: 20, bottom: 16 }}>
            <defs>
              <linearGradient id="grad-tendencia" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--teal)" stopOpacity={0.35} />
                <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="grad-linha" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="var(--accent)" />
                <stop offset="100%" stopColor="var(--teal)" />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="rotulo"
              interval={1}
              padding={{ left: 20, right: 20 }}
              tick={{ fontSize: 11, fill: "var(--text-3)" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide domain={[0, "auto"]} />
            <Tooltip {...TOOLTIP} formatter={(v) => [moeda(v), "Faturamento"]} />
            <Area
              type="monotone"
              dataKey="valor"
              stroke="url(#grad-linha)"
              strokeWidth={2.5}
              fill="url(#grad-tendencia)"
              activeDot={{ r: 5, fill: "var(--teal)", stroke: "var(--surface)", strokeWidth: 2 }}
              dot={{ r: 2.5, fill: "var(--surface)", stroke: "var(--teal)", strokeWidth: 1.5 }}
              {...animar()}
            >
              <LabelList
                dataKey="valor"
                content={criarRotuloDePonto(serie.map((m) => m.valor), (v) => numeroNaEscala(v, escala))}
              />
            </Area>
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="painel-legenda">
        Melhor mês, em destaque: {melhor.rotulo} ({moedaCurta(melhor.valor)})
      </p>
    </>
  );
}

// Composição do mês em rosca, com a cor fixa de cada item (utils/cores.js):
// "Eletrônicos" tem a mesma cor aqui e nas respostas do chat. Até 6 fatias;
// o resto vira "Outros" para a rosca continuar legível. Cada item da legenda
// abre, no chat, a análise daquele recorte (`tipo` + `periodoRotulo` montam a
// pergunta); "Outros" e itens sem cadastro não viram link.
function Fatias({ itens, tipo, periodoRotulo, onPerguntar }) {
  if (!itens.length) return <p className="painel-legenda">Sem dados no período.</p>;
  const visiveis = itens.length > 6 ? [...itens.slice(0, 5), {
    nome: "Outros",
    valor: itens.slice(5).reduce((s, i) => s + i.valor, 0),
  }] : itens;
  const cores = coresDistintas(visiveis.map((i) => i.nome));
  return (
    <LimiteErro alternativo={<p className="painel-legenda">Não foi possível desenhar este gráfico.</p>}>
      <Rosca
        itens={visiveis.map((i, k) => ({
          nome: i.nome,
          valor: i.valor,
          cor: cores[k],
          pergunta: onPerguntar ? perguntaDeFatia(tipo, i.nome, periodoRotulo) : null,
        }))}
        aoClicarItem={onPerguntar}
        formatar={(v, centro) => (centro ? moedaCurta(v) : moeda(v))}
        rotuloCentro="No mês"
        altura={170}
      />
    </LimiteErro>
  );
}

// Faturamento médio por dia da semana: o melhor dia em turquesa, o resto no
// azul da marca — o destaque é a informação, não a decoração.
function GraficoSemana({ dias }) {
  const melhor = dias.reduce((a, b) => (b.valor > a.valor ? b : a), dias[0]);
  const pior = dias.reduce((a, b) => (b.valor < a.valor ? b : a), dias[0]);
  if (!melhor.valor) return <p className="painel-legenda">Sem vendas no período.</p>;
  const escala = escalaDe(dias.map((d) => d.valor));
  return (
    <>
      <p className="grafico-unidade">Valores em {escala.unidade}</p>
      <div
        role="img"
        aria-label={`Gráfico de barras do faturamento médio por dia da semana. Melhor: ${melhor.dia}, ${moeda(melhor.valor)}. Mais fraco: ${pior.dia}, ${moeda(pior.valor)}.`}
      >
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={dias} margin={{ top: 30, right: 4, left: 0, bottom: 0 }}>
            <XAxis dataKey="dia" tick={{ fontSize: 12, fill: "var(--text)" }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip
              {...TOOLTIP}
              cursor={{ fill: "var(--hover-bg)" }}
              formatter={(v) => [moeda(v), "Média por dia"]}
            />
            <Bar dataKey="valor" radius={[6, 6, 0, 0]} maxBarSize={46} {...animar()}>
              {dias.map((d) => (
                <Cell key={d.dia} fill={d === melhor ? "var(--dado-2)" : "var(--dado-4)"} />
              ))}
              <LabelList
                dataKey="valor"
                position="top"
                formatter={(v) => numeroNaEscala(v, escala)}
                style={{ fontSize: 11, fill: "var(--text)", fontFamily: "var(--mono)" }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="painel-legenda">
        <span className="legenda-cor" style={{ background: "var(--dado-2)" }} aria-hidden="true" />
        Melhor dia: {melhor.dia} ({moeda(melhor.valor)} em média) · mais fraco: {pior.dia}
      </p>
    </>
  );
}

function SeloObservacao({ tipo }) {
  return (
    <span className={`painel-observacao-badge ${tipo}`} aria-hidden="true">
      <Icone nome={ICONE_OBSERVACAO[tipo] || "historico"} size={14} />
    </span>
  );
}

function Atividade({ conversas, dataset, onAbrirConversa, onIrPara }) {
  const recentes = conversas.slice(0, 4);
  if (!recentes.length && !dataset) {
    return (
      <p className="painel-legenda">
        Suas últimas perguntas aparecem aqui.{" "}
        <button type="button" className="link" onClick={() => onIrPara("chat")}>
          Fazer a primeira pergunta
        </button>
      </p>
    );
  }
  return (
    <ul className="painel-atividade">
      {dataset && (
        <li>
          <Icone nome="importar" size={14} />
          <span>{dataset.rotulo} importado</span>
          <span className="painel-atividade-tempo">{quando(new Date(dataset.em).toISOString())}</span>
        </li>
      )}
      {recentes.map((c) => (
        <li key={c.id}>
          <button type="button" className="painel-atividade-item" onClick={() => onAbrirConversa(c.id)}>
            <Icone nome="perguntar" size={14} />
            <span>{c.titulo}</span>
          </button>
          <span className="painel-atividade-tempo">{quando(c.criadoEm)}</span>
        </li>
      ))}
    </ul>
  );
}

function EstadoVazio({ icone, titulo, texto, acao, onAcao }) {
  return (
    <section className="painel-vazio anima-entrada">
      <span className="painel-vazio-icone" aria-hidden="true">
        <Icone nome={icone} size={26} />
      </span>
      <h2>{titulo}</h2>
      <p>{texto}</p>
      <button type="button" className="botao-primario" onClick={onAcao}>
        {acao}
      </button>
    </section>
  );
}

// Esqueleto do painel enquanto o primeiro panorama carrega — a pessoa vê a
// forma da tela de imediato, em vez de uma área vazia (o Render pode levar
// alguns segundos para acordar).
function Esqueleto() {
  return (
    <div className="painel-esqueleto" aria-busy="true" aria-label="Carregando o panorama">
      <div className="painel-duas-colunas">
        <div className="esqueleto esqueleto-grafico" />
        <div className="esqueleto esqueleto-grafico" />
      </div>
      <div className="esqueleto esqueleto-texto" />
    </div>
  );
}
