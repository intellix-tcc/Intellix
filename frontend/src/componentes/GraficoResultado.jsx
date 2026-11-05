import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Rosca from "./Rosca";
import { coresDistintas } from "../utils/cores";
import { formatarValor, indiceMetrica, rotuloIntervalo, serieDoResultado } from "../utils/resultado";

// Gráfico da resposta do chat. Quem decide o formato é `modo` (ver
// modosDisponiveis em utils/resultado.js): linha para evolução no tempo,
// rosca para composição, barras para ranking, barras lado a lado para
// comparação de períodos. Cada item tem a sua cor fixa (utils/cores.js).

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
const EIXO = { fontSize: 11, fill: "var(--text-3)" };

// Animação de entrada curta, e nenhuma para quem pediu menos movimento (no
// sistema ou nas preferências do Intellix).
function animar() {
  if (typeof window === "undefined") return { isAnimationActive: false };
  const reduzir =
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ||
    document.documentElement.dataset.movimento === "reduzido";
  return reduzir ? { isAnimationActive: false } : { animationDuration: 650 };
}

function truncar(texto, max) {
  const s = String(texto ?? "");
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

export default function GraficoResultado({ r, modo }) {
  const coluna = r.colunas[indiceMetrica(r)];
  const fmt = (v) => formatarValor(coluna, v);
  const fmtCurto = (v) => formatarValor(coluna, v, { compacto: true });
  const serie = serieDoResultado(r);

  if (modo === "linha") return <Linha serie={serie} fmt={fmt} fmtCurto={fmtCurto} />;
  if (modo === "pizza") {
    const cores = coresDistintas(serie.map((s) => s.chave));
    return (
      <Rosca
        itens={serie.map((s, i) => ({ nome: s.rotulo, valor: s.valor, cor: cores[i] }))}
        formatar={(v, centro) => (centro ? fmtCurto(v) : fmt(v))}
        altura={210}
      />
    );
  }
  if (modo === "comparacao") return <Comparacao r={r} serie={serie} fmt={fmt} fmtCurto={fmtCurto} />;
  return <Barras serie={serie} fmt={fmt} fmtCurto={fmtCurto} />;
}

function Linha({ serie, fmt, fmtCurto }) {
  const media = serie.reduce((s, p) => s + p.valor, 0) / serie.length;
  const maior = serie.reduce((a, b) => (b.valor > a.valor ? b : a), serie[0]);
  return (
    <div role="img" aria-label={`Gráfico de linha com ${serie.length} períodos. Maior valor em ${maior.rotulo}: ${fmt(maior.valor)}. Média de ${fmt(media)}.`}>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={serie} margin={{ top: 12, right: 16, left: 4, bottom: 4 }}>
          <defs>
            <linearGradient id="grad-chat-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--teal)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="grad-chat-linha" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--accent)" />
              <stop offset="100%" stopColor="var(--teal)" />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 4" />
          <XAxis dataKey="rotulo" tick={EIXO} axisLine={false} tickLine={false} padding={{ left: 8, right: 8 }} />
          <YAxis tick={EIXO} tickFormatter={fmtCurto} axisLine={false} tickLine={false} width={64} />
          <Tooltip {...TOOLTIP} formatter={(v) => [fmt(v), "Valor"]} />
          <ReferenceLine
            y={media}
            stroke="var(--accent-3)"
            strokeDasharray="5 5"
            label={{ value: "média", position: "insideTopRight", fill: "var(--accent-3)", fontSize: 11 }}
          />
          <Area
            type="monotone"
            dataKey="valor"
            stroke="url(#grad-chat-linha)"
            strokeWidth={2.5}
            fill="url(#grad-chat-area)"
            dot={{ r: 3, fill: "var(--surface)", stroke: "var(--teal)", strokeWidth: 2 }}
            activeDot={{ r: 5, fill: "var(--teal)", stroke: "var(--surface)", strokeWidth: 2 }}
            {...animar()}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// Barras: horizontais quando os rótulos são longos ou numerosos (nomes de
// produto e cliente cabem inteiros), verticais quando são poucos e curtos.
function Barras({ serie, fmt, fmtCurto }) {
  const cores = coresDistintas(serie.map((s) => s.chave));
  const dados = serie.map((s, i) => ({ ...s, cor: cores[i] }));
  const horizontal = serie.length > 6 || serie.some((s) => s.rotulo.length > 12);
  const descricao = dados.map((d) => `${d.rotulo}: ${fmt(d.valor)}`).join("; ");

  if (horizontal) {
    return (
      <div role="img" aria-label={`Gráfico de barras. ${descricao}.`}>
        <ResponsiveContainer width="100%" height={Math.max(160, dados.length * 40 + 24)}>
          <BarChart data={dados} layout="vertical" margin={{ top: 4, right: 72, left: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="rotulo"
              width={150}
              tick={{ fontSize: 12.5, fill: "var(--text-h)" }}
              tickFormatter={(t) => truncar(t, 22)}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip {...TOOLTIP} cursor={{ fill: "var(--hover-bg)" }} formatter={(v) => [fmt(v), "Valor"]} />
            <Bar dataKey="valor" radius={[0, 6, 6, 0]} barSize={22} {...animar()}>
              {dados.map((d) => (
                <Cell key={d.rotulo} fill={d.cor} />
              ))}
              <LabelList dataKey="valor" position="right" formatter={fmtCurto} style={{ fontSize: 12, fill: "var(--text)" }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div role="img" aria-label={`Gráfico de barras. ${descricao}.`}>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={dados} margin={{ top: 22, right: 8, left: 4, bottom: 4 }}>
          <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 4" />
          <XAxis dataKey="rotulo" tick={{ fontSize: 12, fill: "var(--text)" }} axisLine={false} tickLine={false} interval={0} />
          <YAxis tick={EIXO} tickFormatter={fmtCurto} axisLine={false} tickLine={false} width={64} />
          <Tooltip {...TOOLTIP} cursor={{ fill: "var(--hover-bg)" }} formatter={(v) => [fmt(v), "Valor"]} />
          <Bar dataKey="valor" radius={[6, 6, 0, 0]} maxBarSize={64} {...animar()}>
            {dados.map((d) => (
              <Cell key={d.rotulo} fill={d.cor} />
            ))}
            <LabelList dataKey="valor" position="top" formatter={fmtCurto} style={{ fontSize: 11.5, fill: "var(--text)" }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Dois períodos lado a lado, com a diferença em destaque.
function Comparacao({ r, serie, fmt, fmtCurto }) {
  const p = r.parametros || {};
  const nomes = {
    periodo_a: rotuloIntervalo(p.periodo_a_inicio, p.periodo_a_fim) || "Período A",
    periodo_b: rotuloIntervalo(p.periodo_b_inicio, p.periodo_b_fim) || "Período B",
  };
  const dados = serie.map((s, i) => ({
    ...s,
    rotulo: nomes[s.chave] || s.rotulo,
    cor: i === 0 ? "var(--dado-8)" : "var(--dado-2)",
  }));
  const [a, b] = dados;
  const variacao = a && b && a.valor ? ((b.valor - a.valor) / a.valor) * 100 : null;

  return (
    <div className="comparacao">
      {variacao != null && (
        <p className={`comparacao-delta ${variacao >= 0 ? "positiva" : "negativa"}`}>
          {b.rotulo} ficou{" "}
          <strong>
            {variacao >= 0 ? "+" : "−"}
            {Math.abs(variacao).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%
          </strong>{" "}
          {variacao >= 0 ? "acima" : "abaixo"} de {a.rotulo} ({fmt(b.valor - a.valor)}).
        </p>
      )}
      <div role="img" aria-label={`Comparação: ${dados.map((d) => `${d.rotulo} ${fmt(d.valor)}`).join(", ")}.`}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={dados} margin={{ top: 24, right: 8, left: 4, bottom: 4 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 4" />
            <XAxis dataKey="rotulo" tick={{ fontSize: 12.5, fill: "var(--text-h)" }} axisLine={false} tickLine={false} />
            <YAxis tick={EIXO} tickFormatter={fmtCurto} axisLine={false} tickLine={false} width={64} />
            <Tooltip {...TOOLTIP} cursor={{ fill: "var(--hover-bg)" }} formatter={(v) => [fmt(v), "Faturamento"]} />
            <Bar dataKey="valor" radius={[8, 8, 0, 0]} maxBarSize={110} {...animar()}>
              {dados.map((d) => (
                <Cell key={d.rotulo} fill={d.cor} />
              ))}
              <LabelList dataKey="valor" position="top" formatter={fmtCurto} style={{ fontSize: 12.5, fill: "var(--text-h)", fontWeight: 600 }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
