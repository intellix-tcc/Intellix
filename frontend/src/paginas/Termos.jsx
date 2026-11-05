import { EMAIL_CONTATO, TERMOS_ATUALIZADO_EM } from "../utils/contato";

// Termos de uso. Texto de um protótipo acadêmico: diz o que o sistema faz
// com os dados de verdade (Supabase Auth, planilha vinculada ao dono,
// histórico no navegador) e não promete nível de serviço que um plano
// gratuito não entrega. Ao publicar uma revisão, atualizar TERMOS_VERSAO em
// utils/contato.js.
const SECOES = [
  {
    id: "aceitacao",
    titulo: "1. Aceitação",
    texto: (
      <p>
        Ao criar uma conta ou usar o Intellix, você declara que leu e concorda com
        estes Termos de uso. Se não concordar com algum ponto, não utilize o
        serviço.
      </p>
    ),
  },
  {
    id: "servico",
    titulo: "2. O que é o Intellix",
    texto: (
      <>
        <p>
          O Intellix é uma ferramenta de análise de vendas que interpreta perguntas
          em português e responde com números, gráficos e tabelas a partir dos dados
          que você importa.
        </p>
        <p>
          O Intellix é um <strong>protótipo acadêmico</strong>, desenvolvido como
          Trabalho de Conclusão de Curso de Ciência da Computação da UNIP. É
          oferecido gratuitamente, sem fins comerciais, e pode mudar, ficar
          indisponível ou ser encerrado a qualquer momento.
        </p>
      </>
    ),
  },
  {
    id: "conta",
    titulo: "3. Conta de acesso",
    texto: (
      <ul>
        <li>Você deve informar um nome e um e-mail verdadeiros no cadastro.</li>
        <li>
          A senha é pessoal. Você é responsável por mantê-la em sigilo e por tudo
          que for feito com a sua conta.
        </li>
        <li>
          A autenticação é feita pelo Supabase Auth: a senha é guardada com
          criptografia e não passa pelo servidor do Intellix.
        </li>
        <li>
          Por segurança, a sessão expira após um período sem uso, e é preciso entrar
          de novo.
        </li>
      </ul>
    ),
  },
  {
    id: "uso",
    titulo: "4. Uso permitido",
    texto: (
      <>
        <p>Ao usar o Intellix, você se compromete a não:</p>
        <ul>
          <li>importar dados de terceiros sem ter autorização para isso;</li>
          <li>
            enviar arquivos com vírus, código malicioso ou conteúdo ilegal;
          </li>
          <li>
            tentar acessar dados de outras contas, burlar a autenticação ou
            explorar falhas do sistema;
          </li>
          <li>
            sobrecarregar o serviço com requisições automatizadas ou em volume
            excessivo.
          </li>
        </ul>
        <p>
          Contas que descumprirem estas regras podem ser suspensas ou removidas.
        </p>
      </>
    ),
  },
  {
    id: "dados",
    titulo: "5. Seus dados",
    texto: (
      <>
        <p>
          <strong>Os dados de vendas que você importa continuam sendo seus.</strong>{" "}
          O Intellix os usa apenas para responder às suas perguntas.
        </p>
        <ul>
          <li>
            Cada planilha importada fica vinculada à sua conta, e as consultas só
            alcançam os dados de quem está logado.
          </li>
          <li>
            Coletamos o mínimo para o serviço funcionar: nome, e-mail, foto de perfil
            (opcional), as planilhas importadas e a data em que você aceitou estes
            termos.
          </li>
          <li>
            O histórico de conversas fica salvo no seu navegador, não no servidor.
          </li>
          <li>
            As mensagens enviadas pelo Fale conosco (nome, e-mail e texto) são
            entregues à equipe pelo FormSubmit, um serviço de envio de formulários,
            e usadas apenas para responder ao seu contato.
          </li>
          <li>
            Não vendemos seus dados nem os compartilhamos com terceiros além dos
            serviços que fazem o Intellix funcionar, citados acima. Para fins
            acadêmicos, podemos usar apenas estatísticas agregadas e anônimas de uso
            (por exemplo, quantas perguntas foram respondidas), sem identificar
            pessoas ou empresas.
          </li>
          <li>
            Em linha com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018), você
            pode pedir a qualquer momento acesso, correção ou exclusão dos seus dados
            e da sua conta pelo e-mail{" "}
            <a href={`mailto:${EMAIL_CONTATO}`}>{EMAIL_CONTATO}</a>.
          </li>
        </ul>
        <p>
          Por ser um protótipo, recomendamos não importar dados pessoais sensíveis
          de clientes (como CPF, endereço ou dados de saúde). Os campos da planilha
          de vendas não exigem esse tipo de informação.
        </p>
      </>
    ),
  },
  {
    id: "respostas",
    titulo: "6. Sobre as respostas",
    texto: (
      <p>
        As respostas são geradas automaticamente a partir da interpretação da sua
        pergunta e dos dados importados. O sistema mostra o grau de confiança de cada
        resposta e pede reformulação quando a certeza é baixa, mas ainda assim pode
        errar. Confira os números antes de usá-los em decisões financeiras, fiscais
        ou contábeis: o Intellix não substitui a orientação de um profissional.
      </p>
    ),
  },
  {
    id: "disponibilidade",
    titulo: "7. Disponibilidade e responsabilidade",
    texto: (
      <>
        <p>
          O Intellix roda em infraestrutura gratuita e é oferecido “no estado em que
          se encontra”, sem garantia de funcionamento contínuo. O servidor pode
          hibernar quando fica sem uso, o que deixa a primeira resposta mais lenta.
        </p>
        <p>
          Mantenha sempre uma cópia das suas planilhas. Na extensão permitida pela
          lei, a equipe do Intellix não se responsabiliza por perdas decorrentes de
          indisponibilidade, perda de dados ou decisões tomadas com base nas
          respostas.
        </p>
      </>
    ),
  },
  {
    id: "propriedade",
    titulo: "8. Propriedade intelectual",
    texto: (
      <p>
        O código-fonte do Intellix é distribuído sob a licença MIT. O nome, a logo e
        a identidade visual do Intellix pertencem à equipe do projeto e não podem ser
        usados para identificar outros produtos sem autorização.
      </p>
    ),
  },
  {
    id: "alteracoes",
    titulo: "9. Alterações destes termos",
    texto: (
      <p>
        Estes termos podem ser atualizados. A data da versão vigente aparece no topo
        desta página e, se a mudança for relevante, avisaremos dentro do sistema.
        Continuar usando o Intellix depois da atualização significa concordar com a
        nova versão.
      </p>
    ),
  },
  {
    id: "contato",
    titulo: "10. Contato",
    texto: (
      <p>
        Dúvidas sobre estes termos ou sobre os seus dados:{" "}
        <a href={`mailto:${EMAIL_CONTATO}`}>{EMAIL_CONTATO}</a>, ou pela página{" "}
        <a href="#/contato">Fale conosco</a>. Estes termos são regidos pelas leis da
        República Federativa do Brasil.
      </p>
    ),
  },
];

export default function Termos() {
  return (
    <div className="pagina institucional">
      <header className="pagina-cabecalho anima-entrada">
        <p className="eyebrow">◆ Institucional</p>
        <h1 className="pagina-titulo">Termos de uso</h1>
        <p className="pagina-sub">Última atualização: {TERMOS_ATUALIZADO_EM}.</p>
      </header>

      {/* Sumário: o texto é longo, e quem volta aqui normalmente procura um
          ponto específico (geralmente "Seus dados"). */}
      <nav className="painel termos-sumario anima-entrada" aria-label="Seções dos termos">
        <h2 className="painel-titulo">Nesta página</h2>
        <ol>
          {SECOES.map((s) => (
            <li key={s.id}>
              {/* Botão, não âncora: o roteamento usa o hash (#/termos), então
                  um href="#dados" trocaria de rota em vez de rolar. */}
              <button
                type="button"
                className="link"
                onClick={() =>
                  document.getElementById(`termos-${s.id}`)?.scrollIntoView({ behavior: "smooth" })
                }
              >
                {s.titulo.replace(/^\d+\.\s*/, "")}
              </button>
            </li>
          ))}
        </ol>
      </nav>

      <article className="painel termos-texto anima-entrada" style={{ animationDelay: "60ms" }}>
        {SECOES.map((s) => (
          <section key={s.id} id={`termos-${s.id}`} className="termos-secao">
            <h2>{s.titulo}</h2>
            {s.texto}
          </section>
        ))}
      </article>
    </div>
  );
}
