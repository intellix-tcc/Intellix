import { EXEMPLOS } from "../utils/exemplos";
import { EMAIL_CONTATO } from "../utils/contato";

// Perguntas frequentes. <details>/<summary> nativo: abre e fecha com teclado
// e leitor de tela sem nenhum JS, e a busca do navegador (Ctrl+F) encontra
// texto mesmo dentro das respostas fechadas.
//
// As respostas descrevem só o que o produto faz hoje — nada de promessa de
// recurso futuro. Ao mudar regra de importação ou de sessão, atualizar aqui.
const GRUPOS = [
  {
    titulo: "Primeiros passos",
    itens: [
      {
        p: "O que é o Intellix?",
        r: (
          <p>
            Uma ferramenta de análise de vendas em que você pergunta em português e
            recebe a resposta como número, gráfico ou tabela, sem montar relatório.
            Ela foi pensada para pequenas empresas que têm os dados, mas não têm
            tempo nem time para analisá-los.
          </p>
        ),
      },
      {
        p: "O Intellix é pago?",
        r: (
          <p>
            Não. O Intellix é um protótipo acadêmico, desenvolvido como Trabalho de
            Conclusão de Curso de Ciência da Computação da UNIP, e o uso é gratuito.
          </p>
        ),
      },
      {
        p: "Que tipo de pergunta posso fazer?",
        r: (
          <>
            <p>
              Perguntas sobre as suas vendas: faturamento de um período, produtos mais
              vendidos, ticket médio, quantidade de vendas, melhores clientes e
              comparação entre períodos, por exemplo:
            </p>
            <ul>
              {EXEMPLOS.map((e) => (
                <li key={e}>“{e}”</li>
              ))}
            </ul>
            <p>
              Não precisa de palavra-chave nem de formato especial: escreva como
              perguntaria a alguém do time. No app, a lista completa por tema — e o
              que o Intellix ainda não responde — fica em{" "}
              <a href="#/capacidades">O que posso perguntar</a>.
            </p>
          </>
        ),
      },
      {
        p: "E se o Intellix não entender a minha pergunta?",
        r: (
          <p>
            Cada resposta mostra o quanto o sistema entendeu. Quando a certeza é
            baixa, ele não arrisca um número: pede para você reformular e sugere
            perguntas parecidas que ele sabe responder. Tente ser específico sobre o
            período (“em março”, “no último trimestre”) e sobre o que quer medir.
          </p>
        ),
      },
    ],
  },
  {
    titulo: "Importação de dados",
    itens: [
      {
        p: "Como envio as minhas vendas?",
        r: (
          <p>
            Em <a href="#/importar">Importar dados</a>, arraste ou escolha uma
            planilha do Excel (.xlsx ou .xls) de até 10 MB. Antes de enviar, o
            Intellix confere o arquivo e mostra uma prévia, para você corrigir
            qualquer problema na hora.
          </p>
        ),
      },
      {
        p: "Quais colunas a planilha precisa ter?",
        r: (
          <>
            <p>
              Obrigatórias: <strong>data da venda</strong>, <strong>produto</strong>,{" "}
              <strong>quantidade</strong> e pelo menos um valor (
              <strong>valor unitário</strong> ou <strong>valor total</strong>). Colunas
              como cliente, vendedor, categoria, canal e forma de pagamento são
              opcionais e liberam mais tipos de pergunta.
            </p>
            <p>
              O mais fácil é partir do{" "}
              <a href="/template_importacao_intellix.xlsx" download>
                modelo de planilha
              </a>
              . Acento e maiúscula no cabeçalho não atrapalham.
            </p>
          </>
        ),
      },
      {
        p: "Outras pessoas conseguem ver os meus dados?",
        r: (
          <p>
            Não. Cada planilha importada fica vinculada à sua conta, e as perguntas
            só consultam os dados de quem está logado. Veja os detalhes em{" "}
            <a href="#/termos">Termos de uso</a>.
          </p>
        ),
      },
    ],
  },
  {
    titulo: "Respostas e resultados",
    itens: [
      {
        p: "Posso exportar o resultado?",
        r: (
          <p>
            Sim. Toda resposta tem os botões de exportar em Excel e em PDF, com os
            mesmos dados mostrados na tela.
          </p>
        ),
      },
      {
        p: "Por que a primeira resposta demora um pouco?",
        r: (
          <p>
            O servidor do Intellix roda em um plano gratuito que hiberna quando fica
            um tempo sem uso. A primeira pergunta depois disso “acorda” o servidor e
            pode levar alguns segundos a mais. As seguintes voltam ao normal.
          </p>
        ),
      },
      {
        p: "Onde fica o histórico de conversas?",
        r: (
          <p>
            No próprio navegador. Ele aparece na barra lateral da tela Perguntar e
            pode ser apagado conversa por conversa. Se você trocar de navegador ou
            limpar os dados do site, o histórico não vai junto.
          </p>
        ),
      },
    ],
  },
  {
    titulo: "Conta e acesso",
    itens: [
      {
        p: "Esqueci minha senha. E agora?",
        r: (
          <p>
            Na tela de entrar, use “Esqueci minha senha”. Enviamos um link para o seu
            e-mail; abra-o no mesmo navegador para criar a nova senha. Confira também
            a caixa de spam.
          </p>
        ),
      },
      {
        p: "Por que fui desconectado sozinho?",
        r: (
          <p>
            Por segurança, a sessão expira depois de um período sem uso. É só entrar
            de novo: suas planilhas continuam lá.
          </p>
        ),
      },
      {
        p: "Como altero meu nome, foto ou senha?",
        r: (
          <p>
            Em <a href="#/perfil">Meu perfil</a>, pelo menu lateral (seu nome, no
            rodapé da barra).
          </p>
        ),
      },
    ],
  },
];

export default function Faq() {
  return (
    <div className="pagina institucional">
      <header className="pagina-cabecalho anima-entrada">
        <p className="eyebrow">◆ Ajuda</p>
        <h1 className="pagina-titulo">Perguntas frequentes</h1>
        <p className="pagina-sub">
          As dúvidas mais comuns sobre o Intellix. Não achou a sua?{" "}
          <a href="#/contato">Fale com a gente</a>.
        </p>
      </header>

      {GRUPOS.map((g, i) => (
        <section
          key={g.titulo}
          className="painel anima-entrada"
          style={{ animationDelay: `${(i + 1) * 60}ms` }}
        >
          <h2 className="painel-titulo">{g.titulo}</h2>
          <div className="faq-lista">
            {g.itens.map((item) => (
              <details key={item.p} className="faq-item">
                <summary>{item.p}</summary>
                <div className="faq-resposta">{item.r}</div>
              </details>
            ))}
          </div>
        </section>
      ))}

      <section className="painel faq-contato anima-entrada">
        <h2 className="painel-titulo">Ainda com dúvida?</h2>
        <p className="painel-texto">
          Escreva para <a href={`mailto:${EMAIL_CONTATO}`}>{EMAIL_CONTATO}</a> ou use o
          formulário de contato.
        </p>
        <div className="painel-acoes">
          <a href="#/contato" className="botao-primario">
            Fale conosco
          </a>
        </div>
      </section>
    </div>
  );
}
