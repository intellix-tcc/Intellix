import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

// Nomes de produto às vezes passam disso ("Jaqueta corta-vento", "Camiseta
// Básica Branca") — sem cortar, o rótulo colidiria com o vizinho e o
// Recharts simplesmente omitiria um dos dois (era o que sumia no gráfico).
const TAMANHO_MAX_ROTULO = 14;

function truncar(texto) {
  const s = String(texto ?? "");
  return s.length > TAMANHO_MAX_ROTULO ? `${s.slice(0, TAMANHO_MAX_ROTULO - 1)}…` : s;
}

export default function GraficoBarra({ r }) {
  // ResultSet vem como matriz de linhas; Recharts quer lista de objetos
  const dados = r.linhas.map((linha) =>
    Object.fromEntries(r.colunas.map((c, i) => [c, linha[i]]))
  );

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={dados} margin={{ top: 4, right: 8, left: 0, bottom: 8 }}>
        <XAxis
          dataKey={r.colunas[0]}
          // interval={0}: mostra a barra inteira, mesmo apertado — sem isso
          // o Recharts descarta rótulos que colidiriam, e ficava faltando
          // nome embaixo de algumas barras.
          interval={0}
          angle={-30}
          textAnchor="end"
          height={54}
          tick={{ fontSize: 12 }}
          tickFormatter={truncar}
        />
        <YAxis tick={{ fontSize: 11 }} />
        {/* nome completo no tooltip, mesmo truncado embaixo do eixo */}
        <Tooltip
          formatter={(v) => Number(v).toLocaleString("pt-BR")}
          contentStyle={{
            fontSize: 12.5,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            boxShadow: "var(--shadow-2)",
          }}
          labelStyle={{ color: "var(--text-h)", fontWeight: 600 }}
        />
        {/* roxo de destaque — a cor do dado nos gráficos, uma só (design
            system v2). var(--accent-3) em vez de hex fixo: no escuro o
            roxo clareia para manter contraste contra o fundo marinho.
            No hover a barra passa para o azul de ação, reforçando que é
            ali que o tooltip com o valor exato está respondendo. */}
        <Bar dataKey={r.colunas[2]} fill="var(--accent-3)" activeBar={{ fill: "var(--accent)" }} />
      </BarChart>
    </ResponsiveContainer>
  );
}