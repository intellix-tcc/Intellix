import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { saudacao } from "../utils/saudacao";
import { RESUMO_EXEMPLO, RESUMO_EH_EXEMPLO } from "../utils/resumoExemplo";
import Icone from "../componentes/Icone";

const ICONE_OBSERVACAO = { alta: "seta-cima", queda: "seta-baixo", atencao: "alerta", padrao: "historico" };

function formatarMoeda(v) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
function formatarValorKpi(kpi) {
  return kpi.formato === "moeda" ? formatarMoeda(kpi.valor) : kpi.valor.toLocaleString("pt-BR");
}
function formatarAtualizadoEm(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const hoje = new Date();
  const mesmoDia = d.toDateString() === hoje.toDateString();
  const hora = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return mesmoDia ? `hoje, ${hora}` : `${d.toLocaleDateString("pt-BR")}, ${hora}`;
}

// A Início virou um painel de visão geral (panorama, gráfico de vendas,
// categorias, resumo em texto, ranking, observações, atividade) em vez de
// tela de entrada de pergunta — por pedido explícito, esta versão não tem
// NENHUM elemento que volte pro chat (nem campo, nem "continuar pergunta").
//
// Quase todo bloco abaixo depende de um dado que não existe em lugar
// nenhum do sistema hoje: o backend não agrega por período, não expõe
// categoria de produto, e "resumo em texto" pediria geração de linguagem
// livre, que este projeto não faz (o NLU só classifica intenção e roda SQL
// fixo). Em vez de inventar número na hora de renderizar — o que este
// projeto proíbe em todo lugar — os dados de exemplo ficam isolados em
// `utils/resumoExemplo.js`, claramente marcados, e a tela avisa que é
// exemplo (ver `.painel-status`). Contrato proposto em docs/contratos.md
// (`GET /resumo`), pronto pra avaliação do Dev B/A.
export default function Home({ usuario }) {
  const cumprimento = saudacao({ usuario });
  const r = RESUMO_EXEMPLO;

  const pico = r.serieVendas.reduce((max, d) => (d.valor > max.valor ? d : max), r.serieVendas[0]);
  const mediaDiaria = r.serieVendas.reduce((soma, d) => soma + d.valor, 0) / r.serieVendas.length;

  return (
    <div className="pagina home">
      <div className="painel-inicio">
        <header className="painel-cabecalho anima-entrada">
          <div>
            <h1 className="painel-saudacao">{cumprimento}</h1>
            <p className="painel-subtitulo">Aqui está como sua loja foi em {r.periodo.rotulo}.</p>
            <p className="painel-status">
              <span className="painel-status-ponto" aria-hidden="true" />
              {RESUMO_EH_EXEMPLO ? "Dados de exemplo" : `Dados atualizados ${formatarAtualizadoEm(r.atualizadoEm)}`}
              {" · "}
              {r.totalRegistros.toLocaleString("pt-BR")} registros
            </p>
          </div>
          <div className="painel-acoes-topo">
            <button type="button" className="painel-botao-secundario" disabled title="Em breve">
              Este mês
            </button>
            <button type="button" className="painel-botao-secundario" disabled title="Em breve">
              <Icone nome="exportar" size={15} />
              Exportar
            </button>
          </div>
        </header>

        <section className="painel-secao anima-entrada">
          <p className="eyebrow">Panorama</p>
          <div className="painel-kpis">
            {r.kpis.map((kpi) => (
              <div key={kpi.chave}>
                <p className="painel-kpi-valor">{formatarValorKpi(kpi)}</p>
                <p className="painel-kpi-rotulo">{kpi.rotulo}</p>
                {kpi.variacaoPct != null && (
                  <p className={`painel-kpi-variacao ${kpi.variacaoPct >= 0 ? "positiva" : "negativa"}`}>
                    <Icone nome={kpi.variacaoPct >= 0 ? "seta-cima" : "seta-baixo"} size={11} />
                    {Math.abs(kpi.variacaoPct)}%
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>

        <div className="painel-duas-colunas">
          <section className="painel-secao anima-entrada">
            <p className="eyebrow">Vendas no período</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={r.serieVendas} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <XAxis dataKey="dia" interval={2} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis hide />
                <Tooltip
                  formatter={(v) => formatarMoeda(v)}
                  labelFormatter={(d) => `Dia ${d}`}
                  contentStyle={{
                    fontSize: 12.5,
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    boxShadow: "var(--shadow-2)",
                  }}
                  labelStyle={{ color: "var(--text-h)", fontWeight: 600 }}
                />
                <Bar dataKey="valor" fill="var(--accent-3)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p className="painel-legenda">
              Pico em {pico.dia}/mar ({formatarMoeda(pico.valor)}) · média diária{" "}
              {formatarMoeda(Math.round(mediaDiaria))}
            </p>
          </section>

          <section className="painel-secao anima-entrada">
            <p className="eyebrow">Por categoria</p>
            <ul className="painel-categorias">
              {r.categorias.map((c) => (
                <li key={c.nome}>
                  <div className="painel-categoria-topo">
                    <span>{c.nome}</span>
                    <span>{c.pct}%</span>
                  </div>
                  <div className="painel-categoria-barra">
                    <span style={{ width: `${c.pct}%`, background: c.cor }} />
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <section className="painel-secao anima-entrada">
          <p className="eyebrow">Resumo do mês</p>
          <div className="painel-resumo coluna-leitura">
            {r.resumoTexto.map((paragrafo, i) => (
              <p key={i}>{paragrafo}</p>
            ))}
          </div>
        </section>

        <div className="painel-duas-colunas">
          <section className="painel-secao anima-entrada">
            <p className="eyebrow">Produtos mais vendidos</p>
            <ol className="painel-ranking">
              {r.topProdutos.map((p, i) => (
                <li key={p.nome}>
                  <span className="painel-ranking-pos">{i + 1}</span>
                  <span className="painel-ranking-nome">{p.nome}</span>
                  <span className="painel-ranking-valor">{formatarMoeda(p.faturamento)}</span>
                  <span className="painel-ranking-pct">{p.pct}%</span>
                </li>
              ))}
            </ol>
          </section>

          <section className="painel-secao anima-entrada">
            <p className="eyebrow">Observações</p>
            <ul className="painel-observacoes">
              {r.observacoes.map((o, i) => (
                <li key={i}>
                  <Icone
                    nome={ICONE_OBSERVACAO[o.tipo]}
                    size={15}
                    className={`painel-observacao-icone ${o.tipo}`}
                  />
                  <span>{o.texto}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <section className="painel-secao anima-entrada">
          <p className="eyebrow">Atividade recente</p>
          <ul className="painel-atividade">
            {r.atividade.map((a, i) => (
              <li key={i}>
                <span>{a.texto}</span>
                <span className="painel-atividade-tempo">{a.quando}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
