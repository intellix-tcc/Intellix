// Gera no cliente, não no servidor — o backend tem 256–512MB e o modelo
// já ocupa quase tudo. O ResultSet estruturado do Dev B basta.
//
// As libs (xlsx, jspdf) são pesadas, então usamos import() dinâmico: elas só
// entram no navegador quando o usuário clica em exportar, não no load inicial.

// Nome de arquivo só com letras sem acento, números, "_" e "-": nome com
// acento ("período") chega a virar "download", sem extensão, em alguns
// navegadores e sistemas.
function nomeArquivo(r) {
  return (r.titulo || "resultado")
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .replace(/\s+/g, "_")
    .replace(/[^A-Za-z0-9_-]/g, "");
}

function celula(v) {
  return typeof v === "number" ? v.toLocaleString("pt-BR") : v;
}

// Download de um Blob com nome de arquivo garantido. O XLSX.writeFile da
// SheetJS remove o link no mesmo instante do clique, e em alguns navegadores
// o arquivo saía com o nome genérico "download", sem a extensão .xlsx.
function baixarBlob(blob, nome) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nome;
  a.rel = "noopener";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    a.remove();
    URL.revokeObjectURL(url);
  }, 1000);
}

export async function baixarExcel(r) {
  const XLSX = await import("xlsx");
  const ws = XLSX.utils.aoa_to_sheet([r.colunas, ...r.linhas]);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Resultado");
  const dados = XLSX.write(wb, { bookType: "xlsx", type: "array" });
  baixarBlob(
    new Blob([dados], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }),
    `${nomeArquivo(r)}.xlsx`
  );
}

export async function baixarPdf(r) {
  const { jsPDF } = await import("jspdf");
  const { default: autoTable } = await import("jspdf-autotable");
  const doc = new jsPDF();
  doc.setFontSize(14);
  doc.text(r.titulo || "Resultado", 14, 18);
  autoTable(doc, {
    startY: 26,
    head: [r.colunas],
    body: r.linhas.map((linha) => linha.map(celula)),
    styles: { fontSize: 10 },
    headStyles: { fillColor: [25, 62, 96] }, // #193E60, o marinho da marca
  });
  doc.save(`${nomeArquivo(r)}.pdf`);
}

const MOEDA = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const PCT = (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${v.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`);

/**
 * Relatório do panorama da Início em PDF: indicadores, resumo, ranking,
 * categorias, canais e observações — o mesmo GET /resumo que está na tela.
 */
export async function baixarResumoPdf(r, origem) {
  const { jsPDF } = await import("jspdf");
  const { default: autoTable } = await import("jspdf-autotable");
  const doc = new jsPDF();
  const marinho = [25, 62, 96]; // #193E60, o marinho da marca
  const largura = doc.internal.pageSize.getWidth();

  doc.setFillColor(...marinho);
  doc.rect(0, 0, largura, 26, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(16);
  doc.text("Intellix · Panorama de vendas", 14, 12);
  doc.setFontSize(10.5);
  const periodo = r.periodo.rotulo.charAt(0).toUpperCase() + r.periodo.rotulo.slice(1);
  doc.text(`${periodo} · ${origem || "Base de demonstração"}`, 14, 20);

  doc.setTextColor(22, 35, 47);
  let y = 36;

  const tabela = (titulo, head, body) => {
    if (!body.length) return;
    doc.setFontSize(12);
    doc.text(titulo, 14, y);
    autoTable(doc, {
      startY: y + 3,
      head: [head],
      body,
      styles: { fontSize: 9.5 },
      headStyles: { fillColor: marinho },
      margin: { left: 14, right: 14 },
    });
    y = doc.lastAutoTable.finalY + 10;
  };

  tabela(
    "Indicadores",
    ["Indicador", "Valor", `vs ${r.periodo_anterior.rotulo}`],
    r.kpis.map((k) => [
      k.rotulo,
      k.formato === "moeda" ? MOEDA(k.valor) : k.valor.toLocaleString("pt-BR"),
      PCT(k.variacao_pct),
    ])
  );

  doc.setFontSize(12);
  doc.text("Resumo do mês", 14, y);
  doc.setFontSize(10);
  y += 6;
  for (const paragrafo of r.resumo_texto) {
    const linhas = doc.splitTextToSize(paragrafo, largura - 28);
    doc.text(linhas, 14, y);
    y += linhas.length * 5 + 3;
  }
  y += 4;

  tabela(
    "Produtos que mais faturaram",
    ["#", "Produto", "Faturamento", "% do mês", "Variação"],
    r.top_produtos.map((p, i) => [i + 1, p.nome, MOEDA(p.valor), `${p.pct.toLocaleString("pt-BR")}%`, PCT(p.variacao_pct)])
  );
  tabela(
    "Por categoria",
    ["Categoria", "Faturamento", "%"],
    r.categorias.map((c) => [c.nome, MOEDA(c.valor), `${c.pct.toLocaleString("pt-BR")}%`])
  );
  tabela(
    "Por canal",
    ["Canal", "Faturamento", "%"],
    r.canais.map((c) => [c.nome, MOEDA(c.valor), `${c.pct.toLocaleString("pt-BR")}%`])
  );
  tabela("Observações", ["Observação"], r.observacoes.map((o) => [o.texto]));

  const paginas = doc.getNumberOfPages();
  for (let i = 1; i <= paginas; i++) {
    doc.setPage(i);
    doc.setFontSize(8.5);
    doc.setTextColor(135, 150, 162);
    doc.text(
      `Gerado em ${new Date().toLocaleString("pt-BR")} · página ${i} de ${paginas}`,
      14,
      doc.internal.pageSize.getHeight() - 8
    );
  }

  doc.save(`Panorama_${r.periodo.ano}-${String(r.periodo.mes).padStart(2, "0")}.pdf`);
}
