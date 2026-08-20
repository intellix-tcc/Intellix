// Ícones de linha, desenhados no mesmo traço para o conjunto parecer uma
// família só: grade de 24, traço de 1.7, pontas arredondadas, cor herdada via
// currentColor (então tema claro/escuro e estado ativo funcionam sozinhos).
//
// Sem biblioteca de ícones de propósito — é a mesma decisão do resto do
// projeto (CSS puro, sem biblioteca de componentes), e são poucos ícones.

const DESENHOS = {
  // casa
  inicio: (
    <>
      <path d="M4 10.4 12 4l8 6.4" />
      <path d="M6 9.6V19a1 1 0 0 0 1 1h3.5v-4.6h3V20H17a1 1 0 0 0 1-1V9.6" />
    </>
  ),
  // balão de conversa com as três reticências da resposta
  perguntar: (
    <>
      <path d="M20 12.6c0 3.7-3.6 6.7-8 6.7a9.5 9.5 0 0 1-2.6-.35L5 20.5l1.2-3.2A6.3 6.3 0 0 1 4 12.6C4 8.9 7.6 6 12 6s8 2.9 8 6.6Z" />
      <path d="M9 12.5h.01M12 12.5h.01M15 12.5h.01" />
    </>
  ),
  // planilha entrando na bandeja
  importar: (
    <>
      <path d="M12 3.8v9.4" />
      <path d="M8.4 7.4 12 3.8l3.6 3.6" />
      <path d="M4.5 15v3.6a1.6 1.6 0 0 0 1.6 1.6h11.8a1.6 1.6 0 0 0 1.6-1.6V15" />
    </>
  ),
  // "i" de informação
  sobre: (
    <>
      <circle cx="12" cy="12" r="8.2" />
      <path d="M12 11v5.2" />
      <path d="M12 7.9h.01" />
    </>
  ),
  // painel lateral — o retângulo é a tela, a divisória é a própria sidebar
  painel: (
    <>
      <rect x="3.6" y="4.6" width="16.8" height="14.8" rx="2.2" />
      <path d="M9.6 4.6v14.8" />
    </>
  ),
  // sair
  sair: (
    <>
      <path d="M14.5 4.8h3.1a1.6 1.6 0 0 1 1.6 1.6v11.2a1.6 1.6 0 0 1-1.6 1.6h-3.1" />
      <path d="M10 15.6 13.8 12 10 8.4" />
      <path d="M13.8 12H4.6" />
    </>
  ),
  // nova conversa
  mais: (
    <>
      <path d="M12 5.6v12.8" />
      <path d="M5.6 12h12.8" />
    </>
  ),
  // planilha: folha com a grade de células
  planilha: (
    <>
      <rect x="4.4" y="3.6" width="15.2" height="16.8" rx="2" />
      <path d="M4.4 9h15.2" />
      <path d="M9.6 9v11.4" />
    </>
  ),
  // olho aberto — senha oculta, clicar revela
  olho: (
    <>
      <path d="M2.6 12S6 6.2 12 6.2 21.4 12 21.4 12 18 17.8 12 17.8 2.6 12 2.6 12Z" />
      <circle cx="12" cy="12" r="2.9" />
    </>
  ),
  // olho cortado — senha visível, clicar esconde
  "olho-fechado": (
    <>
      <path d="M9.9 6.5A8.9 8.9 0 0 1 12 6.2c6 0 9.4 5.8 9.4 5.8a17 17 0 0 1-2.8 3.4" />
      <path d="M6.4 8A16.7 16.7 0 0 0 2.6 12s3.4 5.8 9.4 5.8a9.4 9.4 0 0 0 3.6-.7" />
      <path d="M10 10a2.9 2.9 0 0 0 4.1 4.1" />
      <path d="M4 4l16 16" />
    </>
  ),
  // histórico: relógio com a seta de voltar no tempo
  historico: (
    <>
      <path d="M3.6 12a8.4 8.4 0 1 0 2.5-6" />
      <path d="M3.4 4.2v4.2h4.2" />
      <path d="M12 7.8V12l3.2 1.9" />
    </>
  ),
  // lupa de pesquisa — traço fino e aberto, para não confundir com o
  // monograma da marca, que também é uma lupa mas sólida e fechada
  lupa: (
    <>
      <circle cx="10.8" cy="10.8" r="6.6" />
      <path d="M15.6 15.6 L20.2 20.2" />
    </>
  ),
  fechar: <path d="M6.2 6.2 17.8 17.8M17.8 6.2 6.2 17.8" />,
  sol: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4" />
    </>
  ),
  lua: <path d="M20 13.6A8.2 8.2 0 1 1 10.4 4a6.4 6.4 0 0 0 9.6 9.6Z" />,
  // check — confirmação de sucesso (planilha aceita, upload concluído)
  check: <path d="M5 12.6 9.8 17.4 19 7" />,
  // alta/queda — variação de KPI e observações do painel
  "seta-cima": <path d="M12 18.4V5.6M6.2 11.4 12 5.6l5.8 5.8" />,
  "seta-baixo": <path d="M12 5.6v12.8M6.2 12.6 12 18.4l5.8-5.8" />,
  // conector de fluxo — entre os passos do "como funciona" e as camadas da
  // arquitetura; gira 90° via CSS quando a fileira vira coluna no mobile
  "seta-direita": <path d="M4 12h14.4M13.4 6.2l5.8 5.8-5.8 5.8" />,
  // alerta — observação que pede atenção, não é erro do sistema
  alerta: (
    <>
      <path d="M12 4 21.5 20H2.5Z" />
      <path d="M12 10.2v3.6" />
      <path d="M12 16.8h.01" />
    </>
  ),
  // exportar — seta saindo de uma bandeja, mesma família do ícone "importar"
  exportar: (
    <>
      <path d="M12 13.2V3.8" />
      <path d="M8.4 6.4 12 3.8l3.6 2.6" />
      <path d="M4.5 15v3.6a1.6 1.6 0 0 0 1.6 1.6h11.8a1.6 1.6 0 0 0 1.6-1.6V15" />
    </>
  ),
  // gráfico de barras — "a resposta" no fluxo, e o diferencial de visualização
  grafico: (
    <>
      <rect x="4.2" y="12.6" width="4" height="7.2" rx="1" />
      <rect x="10" y="7.6" width="4" height="12.2" rx="1" />
      <rect x="15.8" y="10.2" width="4" height="9.6" rx="1" />
    </>
  ),
  // idioma — "pergunte em português", globo com meridiano
  idioma: (
    <>
      <circle cx="12" cy="12" r="8.2" />
      <path d="M3.8 12h16.4" />
      <path d="M12 3.8c2.6 2.3 4 5.2 4 8.2s-1.4 5.9-4 8.2c-2.6-2.3-4-5.2-4-8.2s1.4-5.9 4-8.2Z" />
    </>
  ),
  // selo com check — "confiança visível"
  selo: (
    <>
      <path d="M12 3.4 19 6v5c0 5-3.2 7.8-7 9-3.8-1.2-7-4-7-9V6Z" />
      <path d="M9 12l2 2 4-4" />
    </>
  ),
  // monitor — camada de interface
  monitor: (
    <>
      <rect x="3.6" y="5" width="16.8" height="12" rx="1.6" />
      <path d="M9 20.4h6M12 17v3.4" />
    </>
  ),
  // troca de ida e volta — camada de API (pergunta / resposta)
  api: (
    <>
      <path d="M4 9.2h13.4" />
      <path d="M13.6 5.4l3.8 3.8-3.8 3.8" />
      <path d="M20 15.4H6.6" />
      <path d="M10.4 19.2l-3.8-3.8 3.8-3.8" />
    </>
  ),
  // chip — camada de interpretação
  chip: (
    <>
      <rect x="7.2" y="7.2" width="9.6" height="9.6" rx="1.6" />
      <path d="M9.4 7.2V4M12 7.2V4M14.6 7.2V4M9.4 20v-3.2M12 20v-3.2M14.6 20v-3.2M7.2 9.4H4M7.2 12H4M7.2 14.6H4M20 9.4h-3.2M20 12h-3.2M20 14.6h-3.2" />
    </>
  ),
  // banco de dados — camada de dados
  banco: (
    <>
      <ellipse cx="12" cy="5.6" rx="7.6" ry="2.8" />
      <path d="M4.4 5.6v12.8c0 1.5 3.4 2.8 7.6 2.8s7.6-1.3 7.6-2.8V5.6" />
      <path d="M4.4 12c0 1.5 3.4 2.8 7.6 2.8s7.6-1.3 7.6-2.8" />
    </>
  ),
  // capelo — trabalho acadêmico
  capelo: (
    <>
      <path d="M12 4.4 2.6 9.2 12 14l9.4-4.8Z" />
      <path d="M6.6 11.4V16c0 1.4 2.4 2.6 5.4 2.6s5.4-1.2 5.4-2.6v-4.6" />
      <path d="M21.4 9.2v5.6" />
    </>
  ),
};

export default function Icone({ nome, size = 20, className = "" }) {
  const desenho = DESENHOS[nome];
  if (!desenho) return null;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`icone ${className}`}
      aria-hidden="true"
      focusable="false"
    >
      {desenho}
    </svg>
  );
}
