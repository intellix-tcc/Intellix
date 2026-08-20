import { useState, useRef } from "react";
import Icone from "./Icone";
import { filtrarConversas, ultimaPergunta, quando } from "../utils/conversas";

// Seção de histórico DENTRO da sidebar — pesquisa + lista de conversas.
//
// Já foi coluna própria ao lado da sidebar e já foi página com rota. Agora é
// uma região da sidebar única, abaixo da navegação, como nas interfaces de
// chat atuais. O componente continua o mesmo arquivo desde aquelas versões:
// mudou onde ele é montado, não o que ele faz.
//
// É esta região que tem prioridade de espaço: `flex: 1` no CSS, com rolagem
// própria, para que centenas de conversas não estiquem a sidebar.
export default function PainelHistorico({
  conversas,
  atualId,
  onSelecionar,
  onExcluir,
  onFechar,
}) {
  const [busca, setBusca] = useState("");
  const campoBusca = useRef(null);

  const encontradas = filtrarConversas(conversas, busca);
  const buscando = busca.trim().length > 0;

  function abrir(id) {
    onSelecionar(id);
    onFechar?.(); // no mobile a sidebar é gaveta e precisa fechar ao escolher
  }

  return (
    <div className="hist">
      {/* Pesquisa acima da lista. Ícone de traço fino, do mesmo conjunto do
          resto — discreto, e sem nenhuma relação com a marca (a marca é a
          logo, e só ela). */}
      {conversas.length > 0 && (
        <div className="hist-busca">
          <Icone nome="lupa" size={15} className="hist-busca-icone" />
          <input
            ref={campoBusca}
            type="search"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            onKeyDown={(e) => e.key === "Escape" && setBusca("")}
            placeholder="Pesquisar conversas"
            aria-label="Pesquisar conversas"
          />
          {buscando && (
            <button
              type="button"
              className="hist-busca-limpar"
              onClick={() => {
                setBusca("");
                campoBusca.current?.focus();
              }}
              aria-label="Limpar pesquisa"
              title="Limpar pesquisa"
            >
              <Icone nome="fechar" size={13} />
            </button>
          )}
        </div>
      )}

      <p className="hist-titulo">Histórico</p>

      <div className="hist-lista">
        {conversas.length === 0 && (
          <p className="hist-aviso">
            Suas conversas aparecem aqui depois da primeira pergunta.
          </p>
        )}

        {conversas.length > 0 && encontradas.length === 0 && (
          <p className="hist-aviso">Nenhuma conversa encontrada.</p>
        )}

        {encontradas.map((c) => {
          const previa = ultimaPergunta(c);
          return (
            <div
              key={c.id}
              className={`hist-item${c.id === atualId ? " ativo" : ""}`}
            >
              <button
                type="button"
                className="hist-item-abrir"
                onClick={() => abrir(c.id)}
                title={c.titulo}
              >
                <span className="hist-item-topo">
                  <span className="hist-item-titulo">{c.titulo}</span>
                  <span className="hist-item-data">{quando(c.criadoEm)}</span>
                </span>
                {/* prévia só quando acrescenta algo: repetir o título logo
                    abaixo dele seria ruído */}
                {previa && previa !== c.titulo && (
                  <span className="hist-item-previa">{previa}</span>
                )}
              </button>
              <button
                type="button"
                className="hist-item-excluir"
                onClick={() => onExcluir(c.id)}
                aria-label={`Excluir conversa ${c.titulo}`}
                title="Excluir conversa"
              >
                <Icone nome="fechar" size={13} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
