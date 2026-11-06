import { useEffect, useState } from "react";
import Icone from "./Icone";
import { excluirPlanilha, listarPlanilhas } from "../servicos/api";
import { datasetAtivo, limparDataset, salvarDataset } from "../utils/dataset";

// Planilhas que a conta já importou (GET /planilhas). Antes o app só lembrava
// a última importação por um registro no navegador, apagado ao sair: depois
// de entrar de novo, a planilha continuava no banco, mas não havia como
// voltar a ela. Aqui a pessoa escolhe qual usar, volta aos dados de exemplo
// ou apaga o que não quer mais.
//
// Para recarregar a lista (ex.: depois de uma importação), o pai troca a
// `key` deste componente.

function data(iso) {
  return iso ? new Date(iso).toLocaleDateString("pt-BR") : "";
}

function mesAno(iso) {
  if (!iso) return "";
  const [ano, mes] = iso.split("-");
  const nome = new Date(Number(ano), Number(mes) - 1, 1).toLocaleDateString("pt-BR", { month: "short" });
  return `${nome.replace(".", "")}/${ano}`;
}

function periodo(p) {
  if (!p.primeira_venda) return "sem vendas carregadas";
  const de = mesAno(p.primeira_venda);
  const ate = mesAno(p.ultima_venda);
  return de === ate ? `vendas de ${de}` : `vendas de ${de} a ${ate}`;
}

export default function SuasPlanilhas({ onIrParaChat }) {
  const [planilhas, setPlanilhas] = useState(null); // null = carregando
  const [erro, setErro] = useState("");
  const [ativa, setAtiva] = useState(() => datasetAtivo()?.empresaId || null);
  const [confirmando, setConfirmando] = useState(null);
  const [excluindo, setExcluindo] = useState(null);

  useEffect(() => {
    let vivo = true;
    listarPlanilhas()
      .then((lista) => vivo && setPlanilhas(lista))
      .catch((e) => {
        if (!vivo) return;
        setPlanilhas([]);
        setErro(e?.mensagem || "Não consegui carregar suas planilhas.");
      });
    return () => {
      vivo = false;
    };
  }, []);

  function usar(p) {
    salvarDataset(p.empresa_id, p.nome_arquivo);
    setAtiva(p.empresa_id);
  }

  function usarExemplo() {
    limparDataset();
    setAtiva(null);
  }

  async function excluir(p) {
    setExcluindo(p.empresa_id);
    setErro("");
    try {
      await excluirPlanilha(p.empresa_id);
      setPlanilhas((lista) => lista.filter((x) => x.empresa_id !== p.empresa_id));
      if (ativa === p.empresa_id) usarExemplo();
    } catch (e) {
      setErro(e?.mensagem || "Não consegui excluir a planilha. Tente de novo.");
    } finally {
      setExcluindo(null);
      setConfirmando(null);
    }
  }

  return (
    <section className="painel planilhas anima-entrada" style={{ animationDelay: "120ms" }}>
      <h2 className="painel-titulo">Suas planilhas</h2>
      <p className="painel-texto">
        Tudo o que você já importou fica guardado na sua conta. Escolha qual usar
        no chat e na Início, ou volte aos dados de exemplo.
      </p>

      {erro && (
        <div className="aviso aviso-erro" role="alert">
          <p>{erro}</p>
        </div>
      )}

      {planilhas === null && <p className="planilhas-vazio">Carregando…</p>}

      {planilhas?.length === 0 && !erro && (
        <p className="planilhas-vazio">Você ainda não importou nenhuma planilha.</p>
      )}

      {planilhas?.length > 0 && (
        <ul className="planilhas-lista">
          {planilhas.map((p) => {
            const emUso = ativa === p.empresa_id;
            return (
              <li key={p.empresa_id} className={`planilha${emUso ? " em-uso" : ""}`}>
                <Icone nome="planilha" size={22} className="planilha-icone" />
                <div className="planilha-dados">
                  <strong className="planilha-nome">
                    {p.nome_arquivo}
                    {emUso && <span className="etiqueta etiqueta-ok planilha-etiqueta">em uso</span>}
                  </strong>
                  <span className="planilha-meta">
                    Importada em {data(p.importada_em)}
                    {p.linhas_validas != null && ` · ${p.linhas_validas} linhas`} · {periodo(p)}
                  </span>
                </div>
                <div className="planilha-acoes">
                  {confirmando === p.empresa_id ? (
                    <>
                      <button
                        type="button"
                        className="botao-perigo"
                        onClick={() => excluir(p)}
                        disabled={excluindo === p.empresa_id}
                      >
                        {excluindo === p.empresa_id ? "Excluindo…" : "Excluir de vez"}
                      </button>
                      <button type="button" className="link" onClick={() => setConfirmando(null)}>
                        Cancelar
                      </button>
                    </>
                  ) : (
                    <>
                      {emUso ? (
                        <button type="button" className="botao-secundario" onClick={onIrParaChat}>
                          Perguntar
                        </button>
                      ) : (
                        <button type="button" className="botao-secundario" onClick={() => usar(p)}>
                          Usar esta
                        </button>
                      )}
                      <button
                        type="button"
                        className="link planilha-excluir"
                        onClick={() => setConfirmando(p.empresa_id)}
                        aria-label={`Excluir ${p.nome_arquivo}`}
                      >
                        Excluir
                      </button>
                    </>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {ativa && (
        <div className="painel-acoes planilhas-rodape">
          <button type="button" className="link" onClick={usarExemplo}>
            Voltar aos dados de exemplo
          </button>
        </div>
      )}
    </section>
  );
}
