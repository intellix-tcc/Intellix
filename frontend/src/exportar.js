// Gera no cliente, não no servidor — o backend tem 256–512MB e o modelo
// já ocupa quase tudo. O ResultSet estruturado do Dev B basta.
//
// As libs (xlsx, jspdf) são pesadas, então usamos import() dinâmico: elas só
// entram no navegador quando o usuário clica em exportar, não no load inicial.

function nomeArquivo(r) {
  return (r.titulo || "resultado").replace(/\s+/g, "_");
}

function celula(v) {
  return typeof v === "number" ? v.toLocaleString("pt-BR") : v;
}

export async function baixarExcel(r) {
  const XLSX = await import("xlsx");
  const ws = XLSX.utils.aoa_to_sheet([r.colunas, ...r.linhas]);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Resultado");
  XLSX.writeFile(wb, `${nomeArquivo(r)}.xlsx`);
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
    headStyles: { fillColor: [170, 59, 255] },
  });
  doc.save(`${nomeArquivo(r)}.pdf`);
}
