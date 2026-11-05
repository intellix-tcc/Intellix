import { useEffect, useId, useMemo, useRef, useState } from "react";
import Icone from "./Icone";

function normalizar(texto) {
  return String(texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "");
}

// Paleta de comandos (Ctrl+K / ⌘K): ir para qualquer tela, abrir uma conversa
// recente, trocar o tema ou fazer uma pergunta, sem tirar a mão do teclado.
//
// Acessibilidade: padrão combobox + listbox do WAI-ARIA. O foco fica no campo
// o tempo todo; as setas movem a opção ativa (aria-activedescendant), Enter
// executa, Esc fecha e devolve o foco para onde estava.
export default function PaletaComandos({ aberta, onFechar, comandos, onPerguntar }) {
  if (!aberta) return null;
  return <Paleta onFechar={onFechar} comandos={comandos} onPerguntar={onPerguntar} />;
}

function Paleta({ onFechar, comandos, onPerguntar }) {
  const [busca, setBusca] = useState("");
  const [ativo, setAtivo] = useState(0);
  const campoRef = useRef(null);
  const listaRef = useRef(null);
  const focoAnterior = useRef(document.activeElement);
  const id = useId();

  useEffect(() => {
    campoRef.current?.focus();
    const anterior = focoAnterior.current;
    return () => anterior?.focus?.({ preventScroll: true });
  }, []);

  const itens = useMemo(() => {
    const alvo = normalizar(busca).trim();
    const filtrados = alvo
      ? comandos.filter((c) => normalizar(`${c.rotulo} ${c.grupo} ${c.palavras || ""}`).includes(alvo))
      : comandos;
    // Texto digitado sempre pode virar pergunta — é o atalho mais útil.
    const perguntar = busca.trim()
      ? [{
          id: "perguntar",
          grupo: "Perguntar ao Intellix",
          rotulo: `“${busca.trim()}”`,
          icone: "perguntar",
          acao: () => onPerguntar(busca.trim()),
        }]
      : [];
    // Se o texto bate com uma tela ou ação, ela vem primeiro ("ajuda" abre
    // a Ajuda); se não bate com nada, o Enter já pergunta.
    return filtrados.length && alvo.length < 25 ? [...filtrados, ...perguntar] : [...perguntar, ...filtrados];
  }, [busca, comandos, onPerguntar]);

  const indice = Math.min(ativo, Math.max(itens.length - 1, 0));

  useEffect(() => {
    listaRef.current?.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: "nearest" });
  }, [indice]);

  function executar(item) {
    if (!item) return;
    onFechar();
    item.acao();
  }

  function aoTeclar(e) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setAtivo((indice + 1) % Math.max(itens.length, 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setAtivo((indice - 1 + itens.length) % Math.max(itens.length, 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      executar(itens[indice]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      onFechar();
    } else if (e.key === "Tab") {
      e.preventDefault(); // o foco não sai da paleta enquanto ela está aberta
    }
  }

  let grupoAnterior = null;

  return (
    <div className="paleta-fundo" onMouseDown={(e) => e.target === e.currentTarget && onFechar()}>
      <div className="paleta" role="dialog" aria-modal="true" aria-label="Paleta de comandos">
        <div className="paleta-busca">
          <Icone nome="lupa" size={18} />
          <input
            ref={campoRef}
            value={busca}
            onChange={(e) => {
              setBusca(e.target.value);
              setAtivo(0);
            }}
            onKeyDown={aoTeclar}
            placeholder="Ir para uma tela, abrir conversa ou perguntar…"
            role="combobox"
            aria-expanded="true"
            aria-controls={`${id}-lista`}
            aria-activedescendant={itens.length ? `${id}-item-${indice}` : undefined}
            aria-autocomplete="list"
          />
          <kbd>Esc</kbd>
        </div>

        <ul ref={listaRef} id={`${id}-lista`} className="paleta-lista" role="listbox" aria-label="Comandos">
          {itens.length === 0 && <li className="paleta-vazio">Nada encontrado.</li>}
          {itens.map((item, i) => {
            const cabecalho = item.grupo !== grupoAnterior ? item.grupo : null;
            grupoAnterior = item.grupo;
            return (
              <li key={item.id} role="presentation">
                {cabecalho && (
                  <p className="paleta-grupo" aria-hidden="true">
                    {cabecalho}
                  </p>
                )}
                <div
                  id={`${id}-item-${i}`}
                  role="option"
                  aria-selected={i === indice}
                  className={`paleta-item${i === indice ? " ativo" : ""}`}
                  onMouseMove={() => i !== indice && setAtivo(i)}
                  onClick={() => executar(item)}
                >
                  <Icone nome={item.icone} size={17} />
                  <span className="paleta-rotulo">{item.rotulo}</span>
                  {item.atalho && <kbd>{item.atalho}</kbd>}
                </div>
              </li>
            );
          })}
        </ul>

        <p className="paleta-rodape" aria-hidden="true">
          <span><kbd>↑</kbd> <kbd>↓</kbd> navegar</span>
          <span><kbd>Enter</kbd> abrir</span>
          <span><kbd>Ctrl</kbd> <kbd>K</kbd> abre e fecha</span>
        </p>
      </div>
    </div>
  );
}
