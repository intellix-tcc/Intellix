import { Bar, BarChart, CartesianGrid, Cell, LabelList, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatarValor, rotuloPeriodo } from "../utils/resultado";
import { animar, escalaDe, numeroNaEscala } from "../utils/rotulos";

// Evolução de uma resposta de um mês só ("quanto faturei em outubro?"): o
// número sozinho não diz se o mês foi bom. Aqui vão os 12 meses até ele, com
// o mês perguntado em destaque, e três comparações prontas: contra o mês
// anterior, contra a média do período e a posição no ranking dos meses.
export default function EvolucaoMensal({ evolucao }) {
  const coluna = evolucao.colunas[1];
  const serie = evolucao.linhas.map(([periodo, valor]) => ({
    periodo,
    rotulo: rotuloPeriodo(periodo),
    valor: Number(valor) || 0,
  }));
  const i = serie.findIndex((p) => p.periodo === evolucao.destaque);
  if (i < 0 || serie.length < 2) return null;

  const atual = serie[i];
  const anterior = i > 0 ? serie[i - 1] : null;
  const comVenda = serie.filter((p) => p.valor > 0);
  const media = comVenda.reduce((s, p) => s + p.valor, 0) / comVenda.length;
  const posicao = [...comVenda].sort((a, b) => b.valor - a.valor).findIndex((p) => p === atual) + 1;
  const ehMoeda = !/^(quantidade|itens|unidades)/.test(coluna);
  const escala = ehMoeda ? escalaDe(serie.map((p) => p.valor)) : null;
  const rotular = (v) => (escala ? numeroNaEscala(v, escala) : formatarValor(coluna, v, { compacto: true }));
  const fmt = (v) => formatarValor(coluna, v);

  const variacao = (a, b) => (b ? ((a - b) / b) * 100 : null);
  const vsAnterior = anterior ? variacao(atual.valor, anterior.valor) : null;
  const vsMedia = variacao(atual.valor, media);

  return (
    <div className="evolucao-mensal">
      <ul className="evolucao-comparacoes">
        {vsAnterior != null && (
          <li>
            <span className="evolucao-rotulo">vs {anterior.rotulo}</span>
            <Delta valor={vsAnterior} />
          </li>
        )}
        {vsMedia != null && comVenda.length > 1 && (
          <li>
            <span className="evolucao-rotulo">vs média de {comVenda.length} meses</span>
            <Delta valor={vsMedia} />
          </li>
        )}
        {posicao > 0 && comVenda.length > 1 && (
          <li>
            <span className="evolucao-rotulo">posição no período</span>
            <strong className="evolucao-posicao">
              {posicao}º de {comVenda.length}
            </strong>
          </li>
        )}
      </ul>

      <div className="evolucao-cabecalho">
        <p className="evolucao-titulo">{evolucao.titulo}</p>
        {escala && <p className="grafico-unidade">Valores em {escala.unidade}</p>}
      </div>
      <div
        role="img"
        aria-label={`${evolucao.titulo}: ${serie.length} meses. ${atual.rotulo} em destaque, com ${fmt(atual.valor)}; média de ${fmt(media)}.`}
      >
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={serie} margin={{ top: 22, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 4" />
            {/* preserveStartEnd: no celular os 12 rótulos ("abr/23"…) não
                cabem e se sobrepunham; o gráfico pula os que colidiriam,
                mantendo o primeiro e o último. Em tela larga, todos aparecem. */}
            <XAxis
              dataKey="rotulo"
              tick={{ fontSize: 11, fill: "var(--text-3)" }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={6}
            />
            <YAxis hide />
            <Tooltip
              cursor={{ fill: "var(--hover-bg)" }}
              formatter={(v) => [fmt(v), evolucao.titulo.replace(" mês a mês", "")]}
              contentStyle={{
                fontSize: 12.5,
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                boxShadow: "var(--shadow-2)",
              }}
              labelStyle={{ color: "var(--text-h)", fontWeight: 600 }}
            />
            <ReferenceLine y={media} stroke="var(--text-3)" strokeDasharray="5 5" />
            <Bar dataKey="valor" radius={[5, 5, 0, 0]} maxBarSize={44} {...animar()}>
              {serie.map((p, k) => (
                <Cell
                  key={p.periodo}
                  fill={k === i ? "var(--dado-2)" : "var(--dado-4)"}
                  fillOpacity={k === i ? 1 : 0.45}
                />
              ))}
              <LabelList dataKey="valor" content={criarRotuloBarra(rotular, i)} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="evolucao-legenda">
        <span className="legenda-cor" style={{ background: "var(--dado-2)" }} aria-hidden="true" />
        {atual.rotulo}, {evolucao.legenda || "o mês perguntado"}
        <span className="legenda-tracejado" aria-hidden="true" />
        média do período ({fmt(media)})
      </p>
    </div>
  );
}

// Rótulo acima da barra, com contorno da cor do fundo (a linha da média não
// atravessa o número) e o mês perguntado em negrito.
function criarRotuloBarra(rotular, destaque) {
  return function RotuloBarra({ x, y, width, value, index }) {
    if (x == null || value == null) return null;
    const ehDestaque = index === destaque;
    // Barra estreita (celular): os números das vizinhas se encostavam. Fica
    // só o do mês perguntado; os demais seguem no tooltip ao tocar na barra.
    if (!ehDestaque && width < 22) return null;
    return (
      <text
        x={x + width / 2}
        y={y - 7}
        textAnchor="middle"
        fontSize={ehDestaque ? 11.5 : 10.5}
        fontWeight={ehDestaque ? 700 : 500}
        fontFamily="var(--mono)"
        fill={ehDestaque ? "var(--text-h)" : "var(--text)"}
        stroke="var(--surface)"
        strokeWidth={3}
        strokeLinejoin="round"
        paintOrder="stroke"
      >
        {rotular(value)}
      </text>
    );
  };
}

function Delta({ valor }) {
  const sentido = valor > 0.05 ? "positiva" : valor < -0.05 ? "negativa" : "neutra";
  const seta = sentido === "positiva" ? "↑" : sentido === "negativa" ? "↓" : "→";
  return (
    <strong className={`evolucao-delta ${sentido}`}>
      {seta} {Math.abs(valor).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%
    </strong>
  );
}
