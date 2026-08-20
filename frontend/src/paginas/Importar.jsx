import { useRef, useState } from "react";
import Icone from "../componentes/Icone";
import {
  analisarPlanilha,
  enviarPlanilha,
  validarArquivo,
  formatarTamanho,
  TAMANHO_MAX_MB,
} from "../servicos/importacao";

// Estados possíveis: vazio -> lendo -> lido -> enviando -> (enviado | pendente | erro)
// "pendente" é o caso de hoje: o arquivo passou na validação, mas o endpoint
// de importação ainda não existe no backend. Ver importacao.js.
const PASSOS = [
  { id: "escolher", titulo: "Escolher planilha", texto: "Excel (.xlsx ou .xls) com suas vendas." },
  { id: "conferir", titulo: "Conferir", texto: "Lemos o arquivo aqui e mostramos o que encontramos." },
  { id: "analisar", titulo: "Analisar", texto: "Com os dados no sistema, é só perguntar no chat." },
];

export default function Importar({ onIrParaChat }) {
  const [arquivo, setArquivo] = useState(null);
  const [analise, setAnalise] = useState(null);
  const [estado, setEstado] = useState("vazio");
  const [erro, setErro] = useState("");
  const [progresso, setProgresso] = useState(0);
  const [resultadoEnvio, setResultadoEnvio] = useState(null);
  const [arrastando, setArrastando] = useState(false);
  const inputArquivo = useRef(null);

  function limpar() {
    setArquivo(null);
    setAnalise(null);
    setEstado("vazio");
    setErro("");
    setProgresso(0);
    setResultadoEnvio(null);
  }

  async function receber(novo) {
    if (!novo) return;
    limpar();
    const problema = validarArquivo(novo);
    if (problema) {
      setArquivo(novo);
      setErro(problema);
      setEstado("erro");
      return;
    }

    setArquivo(novo);
    setEstado("lendo");
    try {
      const resultado = await analisarPlanilha(novo);
      setAnalise(resultado);
      setEstado("lido");
    } catch (err) {
      setErro(err?.mensagem || "Não conseguimos ler essa planilha.");
      setEstado("erro");
    }
  }

  async function enviar() {
    setEstado("enviando");
    setErro("");
    setProgresso(0);
    try {
      const resposta = await enviarPlanilha(arquivo, setProgresso);
      setResultadoEnvio(resposta);
      setEstado("enviado");
    } catch (err) {
      setErro(err?.mensagem || "Não consegui enviar a planilha.");
      // Sem endpoint não é falha da usuária nem do arquivo — é integração que
      // falta. A tela precisa dizer isso com todas as letras.
      setEstado(err?.motivo === "sem-endpoint" ? "pendente" : "erro");
    }
  }

  function aoSoltar(e) {
    e.preventDefault();
    setArrastando(false);
    receber(e.dataTransfer.files?.[0]);
  }

  const lendo = estado === "lendo";
  const enviando = estado === "enviando";
  const podeEnviar = estado === "lido" && analise?.colunasFaltando.length === 0;

  return (
    <div className="pagina importar">
      <header className="pagina-cabecalho anima-entrada">
        <h1 className="pagina-titulo">Importar dados</h1>
        <p className="pagina-sub">
          Envie a planilha de vendas da sua loja. Conferimos o arquivo antes de
          qualquer coisa, para você não descobrir o problema depois.
        </p>
      </header>

      <ol className="passos anima-entrada">
        {PASSOS.map((p, i) => (
          <li key={p.id} className="passo">
            <span className="passo-numero">{i + 1}</span>
            <div>
              <strong>{p.titulo}</strong>
              <span>{p.texto}</span>
            </div>
          </li>
        ))}
      </ol>

      <section className="painel anima-entrada" style={{ animationDelay: "80ms" }}>
        {!arquivo && (
          <div
            className={`area-solta${arrastando ? " arrastando" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setArrastando(true);
            }}
            onDragLeave={() => setArrastando(false)}
            onDrop={aoSoltar}
          >
            <Icone nome="importar" size={30} className="area-solta-icone" />
            <p className="area-solta-titulo">Arraste sua planilha para cá</p>
            <p className="area-solta-texto">
              ou escolha um arquivo do computador — .xlsx ou .xls, até{" "}
              {TAMANHO_MAX_MB} MB
            </p>
            <button
              type="button"
              className="botao-primario"
              onClick={() => inputArquivo.current?.click()}
            >
              Escolher arquivo
            </button>
            <input
              ref={inputArquivo}
              type="file"
              accept=".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              className="input-escondido"
              onChange={(e) => {
                receber(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </div>
        )}

        {arquivo && (
          <div className="arquivo">
            <div className="arquivo-linha">
              <Icone nome="planilha" size={22} className="arquivo-icone" />
              <div className="arquivo-dados">
                <strong className="arquivo-nome">{arquivo.name}</strong>
                <span className="arquivo-meta">
                  {formatarTamanho(arquivo.size)}
                  {analise && ` · ${analise.totalLinhas} linhas · aba "${analise.aba}"`}
                  {lendo && " · lendo…"}
                </span>
              </div>
              {!enviando && (
                <button
                  type="button"
                  className="arquivo-remover"
                  onClick={limpar}
                  aria-label="Remover arquivo"
                  title="Remover arquivo"
                >
                  ×
                </button>
              )}
            </div>

            {enviando && (
              <div className="progresso" role="progressbar" aria-valuenow={progresso}>
                <span className="progresso-barra" style={{ width: `${progresso}%` }} />
                <span className="progresso-rotulo">Enviando… {progresso}%</span>
              </div>
            )}
          </div>
        )}

        {erro && estado === "erro" && (
          <div className="aviso aviso-erro" role="alert">
            <p>{erro}</p>
            <button type="button" className="link" onClick={limpar}>
              Escolher outro arquivo
            </button>
          </div>
        )}

        {analise && estado !== "erro" && <Conferencia analise={analise} />}

        {estado === "lido" && (
          <div className="painel-acoes">
            <button
              type="button"
              className="botao-primario"
              onClick={enviar}
              disabled={!podeEnviar}
              title={
                podeEnviar ? undefined : "Corrija as colunas obrigatórias antes de enviar"
              }
            >
              Enviar para análise
            </button>
            <button type="button" className="link" onClick={limpar}>
              Trocar arquivo
            </button>
          </div>
        )}

        {estado === "enviado" && (
          <div className="aviso aviso-sucesso" role="status">
            <span className="check-sucesso anima-pop" aria-hidden="true">
              <Icone nome="check" size={20} />
            </span>
            <p>
              <strong>Planilha enviada.</strong>{" "}
              {resultadoEnvio?.linhas_validas != null
                ? `${resultadoEnvio.linhas_validas} linhas foram aceitas.`
                : "O servidor recebeu o arquivo e vai processar os dados."}
            </p>
            {/* Só números que já temos de verdade — a contagem de linhas veio
                do servidor (ou, na falta dela, da leitura local da planilha);
                colunas sempre vêm da leitura local. Nada estimado. */}
            <ul className="stats-sucesso">
              <li>
                {(resultadoEnvio?.linhas_validas ?? analise?.totalLinhas) != null
                  ? `${resultadoEnvio?.linhas_validas ?? analise?.totalLinhas} registros encontrados`
                  : "Registros processados"}
              </li>
              <li>{analise?.colunasEncontradas?.length ?? 0} colunas identificadas</li>
              <li>Dados prontos para análise</li>
            </ul>
            <button type="button" className="botao-primario" onClick={onIrParaChat}>
              Fazer perguntas sobre esses dados
            </button>
          </div>
        )}

        {estado === "pendente" && (
          <div className="aviso aviso-pendente" role="status">
            <p>
              <strong>Sua planilha está válida</strong> — {analise?.totalLinhas} linhas
              lidas, colunas conferidas. O envio para o servidor ainda não
              acontece porque o endpoint de importação não existe no backend.
            </p>
            <p className="aviso-tecnico">
              Depende do Dev B/C: <code>POST /import</code>. As tabelas{" "}
              <code>importacao</code> e <code>staging_venda</code> já existem no
              banco, mas estão dormentes. O frontend está pronto — quando a rota
              subir, o envio funciona sem mudar código.
            </p>
            <p>
              Enquanto isso, o chat responde sobre a base de demonstração já
              carregada no banco.
            </p>
            <button type="button" className="botao-secundario" onClick={onIrParaChat}>
              Ir para o chat
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function Conferencia({ analise }) {
  const { colunasEncontradas, colunasFaltando, extras, amostra } = analise;

  return (
    <div className="conferencia">
      <h3 className="conferencia-titulo">O que encontramos na planilha</h3>

      <div className="etiquetas">
        {colunasEncontradas.map((c) => (
          <span key={c} className="etiqueta etiqueta-ok">
            {c}
          </span>
        ))}
        {colunasFaltando.map((c) => (
          <span key={c} className="etiqueta etiqueta-falta">
            falta: {c}
          </span>
        ))}
      </div>

      {colunasFaltando.length > 0 && (
        <div className="aviso aviso-erro" role="alert">
          <p>
            Faltam colunas obrigatórias:{" "}
            <strong>{colunasFaltando.join(", ")}</strong>. Renomeie o cabeçalho
            da planilha e envie de novo — aceitamos variações como “data”,
            “qtd”, “preço unitário” e “total”.
          </p>
        </div>
      )}

      {extras.length > 0 && (
        <p className="conferencia-nota">
          Colunas que não reconhecemos e serão ignoradas: {extras.join(", ")}.
        </p>
      )}

      {amostra.length > 1 && (
        <>
          <h4 className="conferencia-subtitulo">Prévia das primeiras linhas</h4>
          <div className="tabela-scroll">
            <table>
              <thead>
                <tr>
                  {amostra[0].map((c, i) => (
                    <th key={i}>{String(c)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {amostra.slice(1).map((linha, i) => (
                  <tr key={i}>
                    {amostra[0].map((_, j) => (
                      <td key={j}>
                        {linha[j] instanceof Date
                          ? linha[j].toLocaleDateString("pt-BR")
                          : String(linha[j] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
