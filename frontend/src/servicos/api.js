import { obterToken } from "./auth";
import { datasetAtivo } from "../utils/dataset";
import { resumoDeExemplo } from "../utils/resumoExemplo";

const API = import.meta.env.VITE_API_URL;
const MOCK = import.meta.env.VITE_MOCK === "true";

const FALSAS = {
  numero: {
    titulo: "Faturamento em março de 2024",
    colunas: ["periodo", "faturamento"],
    linhas: [["2024-03", 208725.39]],
    tipo_visualizacao: "numero",
    confianca: 0.93,
    evolucao: {
      titulo: "Faturamento mês a mês",
      colunas: ["periodo", "faturamento"],
      linhas: [
        ["2023-04", 151240.1], ["2023-05", 172310.4], ["2023-06", 160980.0], ["2023-07", 149870.2],
        ["2023-08", 155420.9], ["2023-09", 168930.5], ["2023-10", 181220.3], ["2023-11", 236540.8],
        ["2023-12", 302110.6], ["2024-01", 162430.0], ["2024-02", 171905.2], ["2024-03", 208725.39],
      ],
      destaque: "2024-03",
    },
    gerado_em: new Date().toISOString(),
  },
  barra: {
    titulo: "Produtos mais vendidos",
    colunas: ["produto", "quantidade", "faturamento"],
    linhas: [
      ["Tênis Runner", 142, 42585.8],
      ["Camiseta Básica Branca", 138, 6886.2],
      ["Calça Jeans Slim", 97, 15510.3],
      ["Mochila 20L", 84, 15111.6],
      ["Boné Aba Reta", 71, 4962.9],
    ],
    tipo_visualizacao: "barra",
    confianca: 0.91,
    gerado_em: new Date().toISOString(),
  },
  // ano inteiro: um valor por mês -> gráfico de linha
  anual: {
    titulo: "Faturamento no período",
    colunas: ["periodo", "faturamento"],
    linhas: [
      ["2024-01", 31840.2], ["2024-02", 28950.75], ["2024-03", 39275.59], ["2024-04", 41210.3],
      ["2024-05", 52480.9], ["2024-06", 47390.15], ["2024-07", 40125.6], ["2024-08", 43870.0],
      ["2024-09", 45210.85], ["2024-10", 49980.4], ["2024-11", 68420.1], ["2024-12", 81236.45],
    ],
    tipo_visualizacao: "linha",
    parametros: { periodo_inicio: "2024-01-01", periodo_fim: "2024-12-31" },
    confianca: 0.92,
    gerado_em: new Date().toISOString(),
  },
  canal: {
    titulo: "Vendas por canal",
    colunas: ["canal", "faturamento", "quantidade_vendas"],
    linhas: [["loja", 23010.5, 47], ["site", 16124.8, 33], ["whatsapp", 13650.2, 26], ["marketplace", 5791.45, 12]],
    tipo_visualizacao: "pizza",
    confianca: 0.88,
    gerado_em: new Date().toISOString(),
  },
  ticket: {
    titulo: "Ticket médio",
    // Sem coluna de período: o SQL real (backend/app/sql/templates.py)
    // devolve só essa coluna, ao contrário de faturamento (periodo + valor).
    colunas: ["ticket_medio"],
    linhas: [[142.87]],
    tipo_visualizacao: "numero",
    confianca: 0.85,
    gerado_em: new Date().toISOString(),
  },
};

// Erro no formato que a UI entende: { mensagem, exemplos? }. O contrato do
// backend (docs/contratos.md) devolve isso em `detail`; erros de rede não
// devolvem nada, então traduzimos aqui — sem jargão (heurística 2 de Nielsen).
function erroDeRede(causa) {
  return {
    mensagem:
      "Não consegui falar com o servidor. Verifique sua conexão e tente de novo " +
      "em alguns segundos.",
    tecnico: causa,
  };
}

export async function perguntar(pergunta, contexto) {
  if (MOCK) {
    await new Promise((r) => setTimeout(r, 600)); // simula a espera real
    if (/produto|vendidos/i.test(pergunta)) return { ...FALSAS.barra, intencao: "top_produtos" };
    if (/ticket/i.test(pergunta)) return { ...FALSAS.ticket, intencao: "ticket_medio" };
    if (/canal/i.test(pergunta)) return { ...FALSAS.canal, intencao: "vendas_por_canal" };
    if (/faturei em \d{4}\??$/i.test(pergunta.trim())) return { ...FALSAS.anual, intencao: "total_vendas_periodo" };
    if (/capital|tempo/i.test(pergunta))
      throw {
        mensagem: "Não entendi. Tente reformular.",
        exemplos: ["Quanto faturei em março?", "Quais os 5 produtos mais vendidos?"],
      };
    return { ...FALSAS.numero, intencao: "total_vendas_periodo" };
  }

  // Se há um dataset importado ativo, pergunta sobre ele; senão, base demo.
  const dataset = datasetAtivo();
  const corpo = { pergunta };
  if (dataset?.empresaId) corpo.empresa_id = dataset.empresaId;
  // Continuidade da conversa: manda o contexto da resposta anterior (intenção
  // + parâmetros) para o backend resolver frases elípticas como "e em abril?".
  if (contexto?.intencao) corpo.contexto = contexto;
  return chamar("/chat", { metodo: "POST", corpo });
}

// Panorama da Início (GET /resumo). Cache em memória por dataset + mês: voltar
// para a Início ou alternar entre dois meses já vistos é instantâneo, sem
// repetir a ida ao servidor (que pode estar hibernando no Render).
const cacheResumo = new Map();
const VALIDADE_CACHE_MS = 5 * 60 * 1000;

export function resumoEmCache({ ano, mes } = {}) {
  const chave = chaveResumo(ano, mes);
  const item = cacheResumo.get(chave);
  return item && Date.now() - item.em < VALIDADE_CACHE_MS ? item.dados : null;
}

function chaveResumo(ano, mes) {
  return `${datasetAtivo()?.empresaId || "demo"}:${ano || ""}-${mes || ""}`;
}

export async function buscarResumo({ ano, mes } = {}) {
  const emCache = resumoEmCache({ ano, mes });
  if (emCache) return emCache;

  let dados;
  if (MOCK) {
    await new Promise((r) => setTimeout(r, 500));
    dados = resumoDeExemplo({ ano, mes });
  } else {
    const dataset = datasetAtivo();
    const query = new URLSearchParams();
    if (dataset?.empresaId) query.set("empresa_id", dataset.empresaId);
    if (ano && mes) {
      query.set("ano", ano);
      query.set("mes", mes);
    }
    const qs = query.toString();
    dados = await chamar(`/resumo${qs ? `?${qs}` : ""}`);
  }

  cacheResumo.set(chaveResumo(ano, mes), { dados, em: Date.now() });
  // A primeira busca (sem mês) também responde pelo mês que o servidor
  // escolheu — quem pedir esse mês explicitamente depois acerta o cache.
  if (!ano || !mes) {
    cacheResumo.set(chaveResumo(dados.periodo.ano, dados.periodo.mes), { dados, em: Date.now() });
  }
  return dados;
}

/**
 * Acorda o servidor do Render assim que o app abre. O plano gratuito hiberna
 * depois de um tempo parado e a primeira requisição leva vários segundos;
 * disparando /health enquanto a pessoa ainda está lendo a tela (ou digitando
 * a senha), a pergunta de verdade já encontra o servidor acordado.
 * Silencioso de propósito: falhar aqui não é erro para o usuário.
 */
export function aquecerServidor() {
  if (MOCK || !API) return;
  fetch(`${API}/health`, { method: "GET", cache: "no-store" }).catch(() => {});
}

// Ida ao backend com o tratamento de erro que toda tela precisa: token do
// login, falha de rede e resposta que não é JSON viram { mensagem } legível.
async function chamar(caminho, { metodo = "GET", corpo } = {}) {
  if (!API) {
    throw {
      mensagem:
        "O endereço da API não está configurado. Avise a equipe: falta " +
        "VITE_API_URL no ambiente.",
    };
  }

  // Token do login (Supabase Auth): o backend só deixa consultar um dataset
  // importado por quem é dono dele. Sem sessão, segue sem o cabeçalho.
  let token;
  try {
    token = await obterToken();
  } catch (err) {
    throw erroDeRede(err?.mensagem);
  }

  // Servidor fora do ar, DNS, CORS: fetch rejeita com TypeError, não com uma
  // resposta. Sem este try o erro cru subia e a UI só dizia "Algo deu errado".
  let r;
  try {
    r = await fetch(`${API}${caminho}`, {
      method: metodo,
      headers: {
        ...(corpo ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: corpo ? JSON.stringify(corpo) : undefined,
    });
  } catch (err) {
    throw erroDeRede(err?.message);
  }

  // 500 do servidor ou proxy costuma devolver HTML, não JSON — r.json()
  // rebentaria aqui e o usuário veria um erro de parser.
  let dados;
  try {
    dados = await r.json();
  } catch {
    throw {
      mensagem: r.ok
        ? "O servidor respondeu num formato que não reconheço."
        : "O servidor está com problemas no momento. Tente de novo em instantes.",
      tecnico: `HTTP ${r.status}`,
    };
  }

  // Sessão recusada pelo servidor (token vencido ou revogado): não adianta
  // "tentar de novo" na tela — o App escuta este evento e volta ao login.
  if (r.status === 401) {
    window.dispatchEvent(new CustomEvent(EVENTO_SESSAO_RECUSADA, { detail: dados?.detail }));
  }
  if (!r.ok) throw dados.detail || dados || { mensagem: "Algo deu errado." };
  return dados;
}

export const EVENTO_SESSAO_RECUSADA = "intellix:sessao-recusada";
