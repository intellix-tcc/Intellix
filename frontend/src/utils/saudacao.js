// Duas coisas separadas de propósito, porque são conversas diferentes:
//
//   saudacao()     — quem é você e que horas são. Usada no cabeçalho da Início.
//   continuidade() — as últimas conversas com pergunta, se houver.
//
// continuidade() está sem chamador no momento: a Início virou um painel de
// visão geral (panorama, gráfico, resumo, observações — ver
// intellix-home-v2.md) e esse formato não tem nenhum elemento que volte pro
// chat, nem "retomar pergunta". Função ficou, documentada, porque já foi
// usada e desusada mais de uma vez nesta tela — se voltar a fazer sentido,
// é só chamar de novo, a lógica já está pronta e testada.

const MANHA_ATE = 12;
const TARDE_ATE = 18;

function periodoDoDia(agora = new Date()) {
  const h = agora.getHours();
  if (h < MANHA_ATE) return "Bom dia";
  if (h < TARDE_ATE) return "Boa tarde";
  return "Boa noite";
}

/** Só o primeiro nome — "Maria Clara Souza" vira "Maria". */
function primeiroNome(nome) {
  const partes = String(nome || "").trim().split(/\s+/).filter(Boolean);
  return partes[0] || "";
}

/**
 * "Boa tarde, Ilana." — sem emoji, sem exclamação, sem contexto pendurado.
 * Sem nome no cadastro, vira só "Boa tarde." em vez de deixar a vírgula solta.
 */
export function saudacao({ usuario, agora = new Date() } = {}) {
  const periodo = periodoDoDia(agora);
  const nome = primeiroNome(usuario?.nome);
  return nome ? `${periodo}, ${nome}.` : `${periodo}.`;
}

/**
 * Últimas conversas com pergunta de verdade, para a Início oferecer a
 * retomada — até `limite` itens, mais recente primeiro. Lista vazia quando
 * não há histórico, e aí o bloco simplesmente não aparece.
 *
 * @param {Array} conversas histórico local (historico.js), mais recente primeiro
 * @param {number} limite quantas retomadas mostrar (a Início mostra 3)
 */
export function continuidade(conversas = [], limite = 3) {
  const retomadas = [];
  for (const conversa of conversas) {
    const pergunta = conversa?.mensagens?.find((m) => m.tipo === "usuario")?.texto;
    if (!pergunta) continue;
    retomadas.push({
      conversaId: conversa.id,
      titulo: conversa.titulo,
      pergunta,
      criadoEm: conversa.criadoEm,
    });
    if (retomadas.length >= limite) break;
  }
  return retomadas;
}
