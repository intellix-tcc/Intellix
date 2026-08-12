import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function GraficoBarra({ r }) {
  // ResultSet vem como matriz de linhas; Recharts quer lista de objetos
  const dados = r.linhas.map((linha) =>
    Object.fromEntries(r.colunas.map((c, i) => [c, linha[i]]))
  );

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={dados}>
        <XAxis dataKey={r.colunas[0]} />
        <YAxis />
        <Tooltip formatter={(v) => Number(v).toLocaleString("pt-BR")} />
        {/* roxo da marca — é a primeira série nos gráficos da identidade */}
        <Bar dataKey={r.colunas[2]} fill="#7B3E93" />
      </BarChart>
    </ResponsiveContainer>
  );
}