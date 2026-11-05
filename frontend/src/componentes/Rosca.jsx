import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

// Rosca (gráfico de pizza com furo) + legenda com valor e percentual.
// Para composição do todo: categorias, canais, formas de pagamento. A
// legenda é texto de verdade, então o dado continua legível sem o gráfico
// (e para leitor de tela).
export default function Rosca({ itens, formatar, rotuloCentro = "Total", altura = 190 }) {
  const total = itens.reduce((s, i) => s + i.valor, 0);
  const pct = (v) => (total ? (v / total) * 100 : 0);
  const fmtPct = (v) => `${pct(v).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
  const descricao = itens.map((i) => `${i.nome}: ${fmtPct(i.valor)}`).join("; ");

  return (
    <div className="rosca">
      <div className="rosca-grafico" role="img" aria-label={`Gráfico de rosca. ${descricao}.`}>
        <ResponsiveContainer width="100%" height={altura}>
          <PieChart>
            <Pie
              data={itens}
              dataKey="valor"
              nameKey="nome"
              innerRadius="62%"
              outerRadius="96%"
              paddingAngle={itens.length > 1 ? 2 : 0}
              cornerRadius={4}
              stroke="var(--surface)"
              strokeWidth={2}
              isAnimationActive={false}
            >
              {itens.map((i) => (
                <Cell key={i.nome} fill={i.cor} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v, nome) => [`${formatar(v)} · ${fmtPct(v)}`, nome]}
              contentStyle={{
                fontSize: 12.5,
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                boxShadow: "var(--shadow-2)",
              }}
              itemStyle={{ color: "var(--text-h)" }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="rosca-centro" aria-hidden="true">
          <span>{rotuloCentro}</span>
          <strong>{formatar(total, true)}</strong>
        </div>
      </div>
      <ul className="rosca-legenda">
        {itens.map((i) => (
          <li key={i.nome}>
            <span className="rosca-cor" style={{ background: i.cor }} aria-hidden="true" />
            <span className="rosca-nome">{i.nome}</span>
            <span className="rosca-pct">{fmtPct(i.valor)}</span>
            <span className="rosca-valor">{formatar(i.valor)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
