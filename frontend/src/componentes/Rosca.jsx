import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const RAD = Math.PI / 180;

// Percentual escrito dentro da própria fatia (só nas que têm espaço: 5% ou
// mais). O valor em reais fica na legenda ao lado.
function RotuloFatia({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent == null || percent < 0.05) return null;
  const r = innerRadius + (outerRadius - innerRadius) / 2;
  const x = cx + r * Math.cos(-midAngle * RAD);
  const y = cy + r * Math.sin(-midAngle * RAD);
  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={11}
      fontWeight={700}
      fill="#ffffff"
      style={{ paintOrder: "stroke", stroke: "rgba(0,0,0,0.25)", strokeWidth: 2 }}
    >
      {`${Math.round(percent * 100)}%`}
    </text>
  );
}

// Rosca (gráfico de pizza com furo) + legenda com valor e percentual.
// Para composição do todo: categorias, canais, formas de pagamento. A
// legenda é texto de verdade, então o dado continua legível sem o gráfico
// (e para leitor de tela).
//
// `aoClicarItem` (opcional): quando passado, cada item da legenda que trouxer
// `pergunta` vira um botão que abre aquela análise no chat (drill-down da
// Início). Sem ele, a legenda é só texto — é o caso do uso no chat.
export default function Rosca({ itens, formatar, rotuloCentro = "Total", altura = 190, aoClicarItem }) {
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
              labelLine={false}
              label={RotuloFatia}
            >
              {itens.map((i, k) => (
                <Cell key={`${k}-${i.nome}`} fill={i.cor} />
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
        {itens.map((i, k) => {
          const clicavel = aoClicarItem && i.pergunta;
          return (
            <li key={`${k}-${i.nome}`} className={clicavel ? "rosca-legenda-clicavel" : undefined}>
              {/* Botão em sobreposição: mantém o layout da legenda (que na
                  Início tem duas linhas) intacto e, ainda assim, deixa a
                  linha inteira clicável e focável pelo teclado. */}
              {clicavel && (
                <button
                  type="button"
                  className="rosca-legenda-acao"
                  onClick={() => aoClicarItem(i.pergunta)}
                  aria-label={`Analisar ${i.nome} no chat`}
                />
              )}
              <span className="rosca-cor" style={{ background: i.cor }} aria-hidden="true" />
              <span className="rosca-nome">{i.nome}</span>
              <span className="rosca-pct">{fmtPct(i.valor)}</span>
              <span className="rosca-valor">{formatar(i.valor)}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
