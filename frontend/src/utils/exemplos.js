// Perguntas que o sistema sabe responder hoje — as 3 intenções reconhecidas
// pelo NLU de regras. Heurística 3 (Nielsen): o usuário não deve adivinhar o
// que a ferramenta entende, então a interface mostra.
//
// Em módulo próprio porque é usado pelo chat e pela home, e porque arquivo de
// componente só deve exportar componentes (regra do Fast Refresh).
export const EXEMPLOS = [
  "Quanto faturei em março?",
  "Quais os 5 produtos mais vendidos?",
  "Qual o ticket médio em março?",
];
