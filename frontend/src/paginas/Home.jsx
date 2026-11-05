import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
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

const ICONE_OBSERVACAO = { alta: "seta-cima", queda: "seta-baixo", atencao: "alerta", padrao: "historico" };

const moeda = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const moedaCurta = (v) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 });
const numero = (v) => v.toLocaleString("pt-BR");
const pct = (v) => `${v.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

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
        <header className="painel-cabecalho anima-entrada">
          <div>
            <h1 className="painel-saudacao">{cumprimento}</h1>
            <p className="painel-subtitulo">
              {r ? (
                <>
                  Aqui está como sua loja foi em <strong>{r.periodo.rotulo}</strong>.
                </>
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

            <section className="painel-secao anima-entrada" aria-labelledby="h-panorama">
              <h2 id="h-panorama" className="eyebrow">Panorama</h2>
              <div className="painel-kpis">
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
            </section>

            <div className="painel-duas-colunas">
              <section className="painel-secao anima-entrada" aria-labelledby="h-diario">
                <h2 id="h-diario" className="eyebrow">Vendas por dia</h2>
                <GraficoDiario serie={r.serie_diaria} mes={r.periodo.mes} />
              </section>

              <section className="painel-secao anima-entrada" aria-labelledby="h-categorias">
                <h2 id="h-categorias" className="eyebrow">Por categoria</h2>
                <Fatias itens={r.categorias} />
              </section>
            </div>

            <div className="painel-duas-colunas">
              <section className="painel-secao anima-entrada" aria-labelledby="h-tendencia">
                <h2 id="h-tendencia" className="eyebrow">Tendência: últimos 12 meses</h2>
                <GraficoTendencia serie={r.serie_mensal} />
              </section>

              <section className="painel-secao anima-entrada" aria-labelledby="h-canais">
                <h2 id="h-canais" className="eyebrow">Por canal</h2>
                <Fatias itens={r.canais} deslocarCor={2} />
              </section>
            </div>

            <section className="painel-secao anima-entrada" aria-labelledby="h-resumo">
              <h2 id="h-resumo" className="eyebrow">Resumo do mês</h2>
              <div className="painel-resumo coluna-leitura">
                {r.resumo_texto.map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>
            </section>

            <div className="painel-duas-colunas">
              <section className="painel-secao anima-entrada" aria-labelledby="h-ranking">
                <h2 id="h-ranking" className="eyebrow">Produtos que mais faturaram</h2>
                {r.top_produtos.length ? (
                  <ol className="painel-ranking">
                    {r.top_produtos.map((p, i) => (
                      <li key={p.nome}>
                        <span className="painel-ranking-pos">{i + 1}</span>
                        <span className="painel-ranking-nome">
                          {p.nome}
                          <span className="painel-ranking-barra" aria-hidden="true">
                            <span style={{ width: `${(p.valor / r.top_produtos[0].valor) * 100}%` }} />
                          </span>
                        </span>
                        <span className="painel-ranking-valor">{moeda(p.valor)}</span>
                        <Variacao valor={p.variacao_pct} compacta />
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="painel-legenda">Nenhum produto vendido no mês.</p>
                )}
              </section>

              <section className="painel-secao anima-entrada" aria-labelledby="h-observacoes">
                <h2 id="h-observacoes" className="eyebrow">Observações</h2>
                {r.observacoes.length ? (
                  <ul className="painel-observacoes">
                    {r.observacoes.map((o, i) => (
                      <li key={i}>
                        {o.pergunta ? (
                          <button
                            type="button"
                            className="painel-observacao"
                            onClick={() => onPerguntar(o.pergunta)}
                            title={`Perguntar: ${o.pergunta}`}
                          >
                            <SeloObservacao tipo={o.tipo} />
                            <span>
                              {o.texto}
                              <span className="painel-observacao-acao">
                                Analisar <Icone nome="seta-direita" size={12} />
                              </span>
                            </span>
                          </button>
                        ) : (
                          <div className="painel-observacao">
                            <SeloObservacao tipo={o.tipo} />
                            <span>{o.texto}</span>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="painel-legenda">Nenhuma mudança relevante em relação ao mês anterior.</p>
                )}
              </section>
            </div>

            <section className="painel-secao anima-entrada" aria-labelledby="h-aprofunde">
              <h2 id="h-aprofunde" className="eyebrow">Aprofunde em {r.periodo.rotulo}</h2>
              <div className="painel-atalhos">
                {atalhos(r.periodo.rotulo).map((a) => (
                  <button key={a.pergunta} type="button" className="painel-atalho" onClick={() => onPerguntar(a.pergunta)}>
                    <Icone nome={a.icone} size={16} />
                    {a.rotulo}
                  </button>
                ))}
              </div>
            </section>
          </div>
        )}

        <section className="painel-secao anima-entrada" aria-labelledby="h-atividade">
          <h2 id="h-atividade" className="eyebrow">Atividade recente</h2>
          <Atividade conversas={conversas} dataset={dataset} onAbrirConversa={onAbrirConversa} onIrPara={onIrPara} />
        </section>
      </div>
    </div>
  );
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

function CartaoKpi({ kpi, indice, anterior, serie }) {
  return (
    <div className={`painel-kpi painel-kpi-cor-${indice % 4}`}>
      <p className="painel-kpi-rotulo">{kpi.rotulo}</p>
      <p className="painel-kpi-valor">{valorKpi(kpi)}</p>
      <Variacao valor={kpi.variacao_pct} referencia={anterior} />
      {serie && (
        <div className="painel-kpi-sparkline" aria-hidden="true">
          <ResponsiveContainer width="100%" height={34}>
            <AreaChart data={serie} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="grad-spark" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.28} />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="valor" stroke="var(--accent)" strokeWidth={1.6} fill="url(#grad-spark)" isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function GraficoDiario({ serie, mes }) {
  const comVenda = serie.filter((d) => d.valor > 0);
  if (!comVenda.length) return <p className="painel-legenda">Sem vendas no período.</p>;
  const pico = serie.reduce((max, d) => (d.valor > max.valor ? d : max), serie[0]);
  const media = serie.reduce((s, d) => s + d.valor, 0) / serie.length;
  const mm = String(mes).padStart(2, "0");
  return (
    <>
      <div role="img" aria-label={`Gráfico de barras do faturamento diário. Pico no dia ${pico.dia}, com ${moeda(pico.valor)}; média de ${moeda(media)} por dia.`}>
        <ResponsiveContainer width="100%" height={210}>
          <BarChart data={serie} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <XAxis dataKey="dia" interval={2} tick={{ fontSize: 11, fill: "var(--text-3)" }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip
              {...TOOLTIP}
              cursor={{ fill: "var(--hover-bg)" }}
              formatter={(v) => [moeda(v), "Faturamento"]}
              labelFormatter={(d) => `Dia ${String(d).padStart(2, "0")}/${mm}`}
            />
            <Bar dataKey="valor" fill="var(--accent-3)" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="painel-legenda">
        Pico no dia {String(pico.dia).padStart(2, "0")}/{mm} ({moeda(pico.valor)}) · média diária {moeda(media)}
      </p>
    </>
  );
}

function GraficoTendencia({ serie }) {
  const comValor = serie.filter((m) => m.valor > 0);
  if (comValor.length < 2) return <p className="painel-legenda">Histórico curto demais para mostrar tendência.</p>;
  const melhor = comValor.reduce((max, m) => (m.valor > max.valor ? m : max), comValor[0]);
  return (
    <>
      <div role="img" aria-label={`Gráfico de área do faturamento mensal dos últimos 12 meses. Melhor mês: ${melhor.rotulo}, com ${moeda(melhor.valor)}.`}>
        <ResponsiveContainer width="100%" height={210}>
          <AreaChart data={serie} margin={{ top: 6, right: 6, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="grad-tendencia" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="rotulo"
              interval={1}
              padding={{ left: 14, right: 14 }}
              tick={{ fontSize: 11, fill: "var(--text-3)" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide domain={[0, "auto"]} />
            <Tooltip {...TOOLTIP} formatter={(v) => [moeda(v), "Faturamento"]} />
            <Area type="monotone" dataKey="valor" stroke="var(--accent)" strokeWidth={2} fill="url(#grad-tendencia)" activeDot={{ r: 4 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="painel-legenda">
        Melhor mês: {melhor.rotulo} ({moedaCurta(melhor.valor)})
      </p>
    </>
  );
}

// Uma cor por fatia — roxo/turquesa/âmbar/marinho/azul, a mesma paleta dos
// diferenciais da Sobre — para diferenciar sem depender só da posição.
const CORES = ["var(--accent-3)", "var(--teal)", "var(--accent-2)", "var(--marinho)", "var(--accent)"];

function Fatias({ itens, deslocarCor = 0 }) {
  if (!itens.length) return <p className="painel-legenda">Sem dados no período.</p>;
  const visiveis = itens.slice(0, 6);
  return (
    <ul className="painel-categorias">
      {visiveis.map((c, i) => (
        <li key={c.nome}>
          <div className="painel-categoria-topo">
            <span>{c.nome}</span>
            <span className="painel-categoria-valor">
              {pct(c.pct)}
              <span className="painel-categoria-moeda">{moedaCurta(c.valor)}</span>
            </span>
          </div>
          <div className="painel-categoria-barra" aria-hidden="true">
            <span
              className="painel-categoria-preenchimento"
              style={{ width: `${c.pct}%`, background: CORES[(i + deslocarCor) % CORES.length] }}
            />
          </div>
        </li>
      ))}
    </ul>
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
      <div className="painel-kpis">
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} className="esqueleto esqueleto-kpi" />
        ))}
      </div>
      <div className="painel-duas-colunas">
        <div className="esqueleto esqueleto-grafico" />
        <div className="esqueleto esqueleto-grafico" />
      </div>
      <div className="esqueleto esqueleto-texto" />
    </div>
  );
}
