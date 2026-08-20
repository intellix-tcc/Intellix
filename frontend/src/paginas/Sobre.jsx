import Logo from "../componentes/Logo";
import Icone from "../componentes/Icone";

const PASSOS = [
  { titulo: "Seus dados", texto: "Você importa a planilha de vendas (.xlsx).", icone: "importar" },
  { titulo: "Sua pergunta", texto: "Você pergunta usando linguagem natural.", icone: "perguntar" },
  { titulo: "A análise", texto: "O Intellix interpreta a intenção e consulta os dados.", icone: "lupa" },
  { titulo: "A resposta", texto: "Volta como número, gráfico ou tabela, pronta para exportar.", icone: "grafico" },
];

// Mesmo conteúdo de sempre, só que "Banco" virou "Dados" no rótulo: o nome
// da camada e a tecnologia por trás dela não precisam ocupar o mesmo lugar
// na frase.
const CAMADAS = [
  { nome: "Interface", texto: "React + Vite. Lê o formato da resposta e decide sozinha como desenhar.", icone: "monitor" },
  { nome: "API", texto: "FastAPI. Interpreta a pergunta, escolhe a consulta e devolve o dado bruto.", icone: "api" },
  { nome: "Interpretação", texto: "Modelo de linguagem que classifica a intenção e extrai período, produto e limite.", icone: "chip" },
  { nome: "Dados", texto: "PostgreSQL em modelagem estrela, para consulta analítica rápida.", icone: "banco" },
];

// Era "O que o Intellix faz" na Home antiga; aqui vira diferencial — mesmo
// conteúdo, contexto diferente (institucional, não convite de produto). A
// cor troca por item só no ícone (não numa caixa): é o único lugar da tela
// com mais de uma cor de destaque ao mesmo tempo, e de propósito contido.
const DIFERENCIAIS = [
  {
    titulo: "Pergunte em português",
    texto: "Nada de menu, filtro ou relatório pronto. Você digita como falaria.",
    icone: "idioma",
    cor: "cor-marinho",
  },
  {
    titulo: "Gráfico na medida",
    texto: "A resposta escolhe sozinha o formato: valor, gráfico ou tabela.",
    icone: "grafico",
    cor: "cor-roxo",
  },
  {
    titulo: "Leve para onde precisar",
    texto: "Todo resultado sai em Excel ou PDF com um clique.",
    icone: "exportar",
    cor: "cor-teal",
  },
  {
    titulo: "Confiança visível",
    texto: "Cada resposta mostra o quanto o sistema entendeu. Se a certeza for baixa, ele não inventa.",
    icone: "selo",
    cor: "cor-ambar",
  },
];

// Ordem: o que é → problema/solução → como funciona → diferenciais →
// como é construído (discreto) → por que existe → TCC (discreto) →
// fechamento. Texto é o conteúdo principal em toda seção; ícone é só
// acento ao lado do texto, sem caixa nem círculo em volta — e nenhum deles
// é a marca: a marca continua sendo só a logo (ver regra no CLAUDE.md).
export default function Sobre({ onIrParaImportar }) {
  return (
    <div className="pagina sobre">
      <section className="sobre-cabecalho anima-entrada">
        <div className="sobre-cabecalho-topo">
          <div>
            <p className="eyebrow">◆ Sobre o Intellix</p>
            <h1 className="sobre-titulo">Suas vendas viram respostas, não relatórios.</h1>
            <p className="coluna-leitura sobre-lead">
              O Intellix é uma ferramenta de análise de vendas em que você conversa com
              seus dados em português — e recebe número, gráfico ou tabela na hora, sem
              montar relatório.
            </p>
          </div>
          <Logo variante="simbolo" largura={52} className="sobre-simbolo" />
        </div>
      </section>

      <div className="sobre-dupla">
        <section className="sobre-cartao anima-entrada">
          <Icone nome="planilha" size={28} className="sobre-cartao-icone" />
          <div>
            <h2>O problema</h2>
            <p>
              <strong>O dado existe, a resposta não.</strong> Pequenas empresas acumulam
              vendas todos os dias, mas raramente conseguem transformar esses números em
              decisão. Falta tempo, falta ferramenta e falta alguém dedicado a montar
              relatório.
            </p>
          </div>
        </section>
        <section className="sobre-cartao anima-entrada" style={{ animationDelay: "70ms" }}>
          <Icone nome="perguntar" size={28} className="sobre-cartao-icone" />
          <div>
            <h2>A solução</h2>
            <p>
              <strong className="sobre-destaque-acao">Você pergunta, o Intellix responde.</strong>{" "}
              Em vez de aprender a operar um painel, a pessoa simplesmente pergunta, em
              português, do jeito que perguntaria a alguém do time.
            </p>
          </div>
        </section>
      </div>

      <section className="secao anima-entrada">
        <h2 className="secao-titulo">Como funciona</h2>
        <ol className="fluxo">
          {PASSOS.map((p, i) => (
            <li key={p.titulo} className="fluxo-item anima-entrada" style={{ animationDelay: `${i * 70}ms` }}>
              <Icone nome={p.icone} size={26} className="fluxo-icone" />
              <div className="fluxo-texto">
                <span className="etapa-num">{String(i + 1).padStart(2, "0")}</span>
                <h3>{p.titulo}</h3>
                <p>{p.texto}</p>
              </div>
              {i < PASSOS.length - 1 && (
                <Icone nome="seta-direita" size={16} className="fluxo-seta" aria-hidden="true" />
              )}
            </li>
          ))}
        </ol>
      </section>

      <section className="secao anima-entrada">
        <h2 className="secao-titulo">O que torna o Intellix diferente</h2>
        <ul className="fluxo">
          {DIFERENCIAIS.map((d, i) => (
            <li key={d.titulo} className="fluxo-item anima-entrada" style={{ animationDelay: `${i * 70}ms` }}>
              <Icone nome={d.icone} size={26} className={`fluxo-icone ${d.cor}`} />
              <div className="fluxo-texto">
                <h3>{d.titulo}</h3>
                <p>{d.texto}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* Daqui pra baixo é a parte discreta: como o produto é construído e o
          contexto acadêmico. Quem só queria entender o produto já leu o que
          precisava lá em cima. */}
      <section className="secao secao-discreta anima-entrada">
        <h2 className="secao-titulo">Como está montado</h2>
        <ol className="fluxo fluxo-discreto">
          {CAMADAS.map((c, i) => (
            <li key={c.nome} className="fluxo-item anima-entrada" style={{ animationDelay: `${i * 70}ms` }}>
              <Icone nome={c.icone} size={20} className="fluxo-icone" />
              <div className="fluxo-texto">
                <span className="camada-num">{String(i + 1).padStart(2, "0")}</span>
                <h3>{c.nome}</h3>
                <p>{c.texto}</p>
              </div>
              {i < CAMADAS.length - 1 && (
                <Icone nome="seta-direita" size={14} className="fluxo-seta" aria-hidden="true" />
              )}
            </li>
          ))}
        </ol>
        <p className="sobre-tecnologias">
          <span>Tecnologias</span> React · FastAPI · Modelo de linguagem · PostgreSQL
        </p>
      </section>

      <section className="secao anima-entrada">
        <h2 className="secao-titulo">Por que o Intellix existe</h2>
        <p className="coluna-leitura sobre-lead">
          O Intellix nasce para <strong>encurtar a distância entre a dúvida e o número</strong>.
          Não é sobre ter mais um painel — é sobre não precisar de nenhum. Quem conhece o
          negócio nem sempre conhece ferramenta de dados; aqui, conhecer o negócio basta.
        </p>
      </section>

      <section className="secao secao-discreta anima-entrada sobre-academico">
        <Icone nome="capelo" size={24} className="sobre-cartao-icone" />
        <div className="coluna-leitura texto-longo">
          <h2 className="secao-titulo">Trabalho acadêmico</h2>
          <p>
            O Intellix é o Trabalho de Conclusão de Curso de Ciência da Computação
            da UNIP, dividido em quatro frentes: modelo de linguagem, backend e
            banco de dados, infraestrutura e implantação, e interface com
            experiência do usuário.
          </p>
        </div>
      </section>

      <section className="sobre-fechamento anima-entrada">
        <p>Pronto para ver isso funcionando com os seus dados?</p>
        <button type="button" className="botao-primario" onClick={onIrParaImportar}>
          Importar dados
        </button>
      </section>
    </div>
  );
}
