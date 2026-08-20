// Importação de planilhas de venda.
//
// Duas etapas separadas de propósito:
//
//   1) analisarPlanilha() — roda inteira no navegador, com a mesma lib que já
//      usamos para exportar (SheetJS). Abre o arquivo de verdade, conta linhas
//      e confere as colunas contra o que a tabela `staging_venda` espera
//      (database/migrations/001_schema.sql). Isso é validação real, não
//      aparência: um .xlsx corrompido, vazio ou com colunas erradas é barrado
//      aqui, sem gastar viagem ao servidor.
//
//   2) enviarPlanilha() — POST multipart para o backend.
//      >>> DEPENDE DO BACKEND (Dev B/C): o endpoint POST /import NÃO EXISTE
//      hoje. As tabelas `importacao` e `staging_venda` já estão criadas no
//      Supabase, mas estão dormentes (marcadas "semana 14" no schema).
//      Quando o endpoint subir, nada aqui muda: a função já monta o
//      multipart, acompanha o progresso e trata as respostas. Enquanto não
//      existir, ela devolve o motivo "sem-endpoint" e a tela diz isso ao
//      usuário — não fingimos que o envio deu certo.

const API = import.meta.env.VITE_API_URL;

export const TAMANHO_MAX_MB = 10;
const EXTENSOES = [".xlsx", ".xls"];

// Nomes das colunas da staging_venda. A planilha pode usar acento, maiúscula
// ou espaço — normalizamos antes de comparar.
const COLUNAS_OBRIGATORIAS = ["data_venda", "produto", "quantidade"];
const COLUNAS_VALOR = ["valor_unitario", "valor_total"]; // pelo menos uma
const COLUNAS_CONHECIDAS = [
  "data_venda",
  "produto",
  "categoria",
  "cliente",
  "vendedor",
  "canal",
  "forma_pagamento",
  "quantidade",
  "valor_unitario",
  "desconto",
  "valor_total",
];

// Sinônimos aceitos: a planilha de uma loja pequena não vem com o nome exato
// da coluna do banco.
const SINONIMOS = {
  data_venda: ["data", "data da venda", "dt venda", "emissao", "data emissao"],
  produto: ["item", "descricao", "descricao do produto", "mercadoria"],
  categoria: ["grupo", "linha", "departamento"],
  cliente: ["comprador", "nome do cliente"],
  vendedor: ["atendente", "responsavel"],
  canal: ["origem", "canal de venda"],
  forma_pagamento: ["pagamento", "forma de pagamento", "meio de pagamento"],
  quantidade: ["qtd", "qtde", "quant"],
  valor_unitario: ["preco", "preco unitario", "valor unit", "unitario"],
  desconto: ["descontos", "abatimento"],
  valor_total: ["total", "valor", "valor da venda", "faturamento"],
};

function normalizar(texto) {
  return String(texto ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "") // tira acentos separados pelo NFD
    .replace(/[\s-]+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
}

/** Cabeçalho da planilha -> nome da coluna do banco, ou null se não bater. */
function mapearColuna(cabecalho) {
  const alvo = normalizar(cabecalho);
  if (!alvo) return null;
  if (COLUNAS_CONHECIDAS.includes(alvo)) return alvo;
  for (const [coluna, apelidos] of Object.entries(SINONIMOS)) {
    if (apelidos.some((a) => normalizar(a) === alvo)) return coluna;
  }
  return null;
}

// .xlsx é um ZIP  -> "PK\x03\x04"
// .xls  é OLE2    -> D0 CF 11 E0 A1 B1 1A E1
const ZIP = [0x50, 0x4b, 0x03, 0x04];
const OLE2 = [0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1];

function assinaturaValida(buffer) {
  const bytes = new Uint8Array(buffer.slice(0, 8));
  const bate = (assinatura) => assinatura.every((b, i) => bytes[i] === b);
  return bate(ZIP) || bate(OLE2);
}

export function formatarTamanho(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Checagens que não precisam abrir o arquivo. "" quando passa. */
export function validarArquivo(arquivo) {
  if (!arquivo) return "Escolha um arquivo.";
  const nome = arquivo.name.toLowerCase();
  if (!EXTENSOES.some((ext) => nome.endsWith(ext))) {
    return "Só aceitamos planilhas do Excel (.xlsx ou .xls). Se o seu arquivo é CSV, abra no Excel e salve como .xlsx.";
  }
  if (arquivo.size === 0) return "Esse arquivo está vazio.";
  if (arquivo.size > TAMANHO_MAX_MB * 1024 * 1024) {
    return `A planilha precisa ter no máximo ${TAMANHO_MAX_MB} MB.`;
  }
  return "";
}

/**
 * Abre a planilha no navegador e devolve o que encontrou:
 * { abas, aba, totalLinhas, colunasEncontradas, colunasFaltando, extras, amostra }
 * Lança { mensagem } com texto de usuário quando não dá para ler.
 */
export async function analisarPlanilha(arquivo) {
  const problema = validarArquivo(arquivo);
  if (problema) throw { mensagem: problema };

  const XLSX = await import("xlsx");

  let planilha;
  try {
    const buffer = await arquivo.arrayBuffer();
    // Extensão é só o nome do arquivo: qualquer um renomeia .txt para .xlsx.
    // A assinatura nos primeiros bytes diz o que o arquivo é de verdade — sem
    // isso o SheetJS aceita texto solto e o usuário recebe um erro confuso
    // sobre colunas em vez de "esse arquivo não é uma planilha".
    if (!assinaturaValida(buffer)) {
      throw new Error("assinatura");
    }
    planilha = XLSX.read(buffer, { type: "array", cellDates: true });
  } catch {
    // Arquivo truncado, renomeado à mão, protegido por senha…
    throw {
      mensagem:
        "Não conseguimos processar esse arquivo. Verifique se ele está em formato Excel válido e se não está protegido por senha.",
    };
  }

  const abas = planilha.SheetNames || [];
  if (abas.length === 0) throw { mensagem: "Essa planilha não tem nenhuma aba." };

  const aba = abas[0];
  const linhas = XLSX.utils.sheet_to_json(planilha.Sheets[aba], {
    header: 1,
    blankrows: false,
    defval: "",
  });

  if (linhas.length === 0) {
    throw { mensagem: `A aba "${aba}" está vazia. Salve a planilha com os dados e tente de novo.` };
  }
  if (linhas.length === 1) {
    throw {
      mensagem: `A aba "${aba}" só tem o cabeçalho, sem nenhuma linha de venda.`,
    };
  }

  const cabecalho = linhas[0];
  const mapa = cabecalho.map(mapearColuna);
  const encontradas = mapa.filter(Boolean);

  const faltando = [
    ...COLUNAS_OBRIGATORIAS.filter((c) => !encontradas.includes(c)),
    ...(COLUNAS_VALOR.some((c) => encontradas.includes(c)) ? [] : ["valor_total"]),
  ];
  const extras = cabecalho.filter((c, i) => c && !mapa[i]);

  return {
    nome: arquivo.name,
    tamanho: arquivo.size,
    abas,
    aba,
    totalLinhas: linhas.length - 1,
    colunasEncontradas: encontradas,
    colunasFaltando: faltando,
    extras,
    amostra: linhas.slice(0, 6), // cabeçalho + 5 linhas, para a prévia
  };
}

/**
 * Envia para o backend. `onProgresso` recebe 0–100.
 * Resolve com a resposta do servidor; rejeita com { mensagem, motivo? }.
 * motivo === "sem-endpoint" quando o backend ainda não implementou /import.
 */
export function enviarPlanilha(arquivo, onProgresso) {
  return new Promise((resolve, reject) => {
    if (!API) {
      reject({
        mensagem: "O endereço da API não está configurado.",
        motivo: "sem-url",
      });
      return;
    }

    const corpo = new FormData();
    corpo.append("arquivo", arquivo);

    // XMLHttpRequest, não fetch: é o único jeito de ter progresso de upload
    // no navegador hoje.
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API}/import`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgresso) {
        onProgresso(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          resolve({ ok: true });
        }
        return;
      }
      // 404/405/501: a rota não existe ainda. É a situação esperada hoje, e
      // precisa ficar distinguível de um erro de verdade.
      if ([404, 405, 501].includes(xhr.status)) {
        reject({
          mensagem:
            "O envio para o servidor ainda não está disponível — falta o endpoint de importação no backend. Sua planilha foi lida e validada aqui no navegador.",
          motivo: "sem-endpoint",
        });
        return;
      }
      let detalhe;
      try {
        detalhe = JSON.parse(xhr.responseText)?.detail;
      } catch {
        detalhe = null;
      }
      reject({
        mensagem:
          detalhe?.mensagem ||
          "O servidor não conseguiu processar a planilha. Tente de novo em instantes.",
        motivo: "erro-servidor",
      });
    };

    xhr.onerror = () =>
      reject({
        mensagem: "Não consegui falar com o servidor. Verifique sua conexão.",
        motivo: "rede",
      });
    xhr.ontimeout = () =>
      reject({ mensagem: "O envio demorou demais e foi cancelado.", motivo: "timeout" });

    xhr.timeout = 120000; // Render hiberna: a primeira chamada é lenta
    xhr.send(corpo);
  });
}
