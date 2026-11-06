import { useEffect, useState } from "react";
import Icone from "../componentes/Icone";
import { buscarCapacidades } from "../servicos/api";
import { CAPACIDADES_ESTATICAS, agruparPorTema } from "../utils/capacidades";

// "O que posso perguntar": a vitrine das capacidades do agente, alimentada
// pelo GET /capacidades (backend/app/main.py). Em interface de conversa, o
// problema nº 1 é não saber o que dá para dizer — aqui a pessoa vê tudo que
// o Intellix responde, com exemplos que já perguntam ao clicar, e, lado a
// lado, o que ele NÃO faz (previsões, assunto fora de vendas), para não
// esbarrar nisso por tentativa e erro.
//
// Começa com a cópia estática (utils/capacidades.js) já na tela — o servidor
// do Render hiberna e não dá para deixar a página vazia esperando — e troca
// pela resposta do servidor assim que ela chega. As duas fontes são iguais;
// a troca é imperceptível e só serve para refletir uma intenção nova que o
// backend passe a reconhecer.
export default function Capacidades({ onPerguntar, ocupado = false }) {
  const [capacidades, setCapacidades] = useState(CAPACIDADES_ESTATICAS);

  useEffect(() => {
    let ativo = true;
    buscarCapacidades().then((dados) => {
      if (ativo && dados) setCapacidades(dados);
    });
    return () => {
      ativo = false;
    };
  }, []);

  const grupos = agruparPorTema(capacidades.intencoes);

  function perguntar(pergunta) {
    if (ocupado) return;
    onPerguntar?.(pergunta);
  }

  return (
    <div className="pagina institucional capacidades">
      <header className="pagina-cabecalho anima-entrada">
        <p className="eyebrow">◆ Guia</p>
        <h1 className="pagina-titulo">O que posso perguntar</h1>
        <p className="pagina-sub">
          O Intellix responde sobre as suas vendas em português. São{" "}
          {capacidades.total_intencoes} tipos de análise — toque em um exemplo para
          perguntar na hora. Você não precisa copiar o texto: pode escrever do seu jeito.
        </p>
      </header>

      {capacidades.dica && (
        <p className="capacidades-dica anima-entrada">
          <Icone nome="calendario" size={16} />
          <span>
            <strong>Dica:</strong> {capacidades.dica}
          </span>
        </p>
      )}

      {grupos.map((g, i) => (
        <section
          key={g.id}
          className="painel capacidades-grupo anima-entrada"
          style={{ animationDelay: `${(i + 1) * 50}ms` }}
          aria-labelledby={`cap-${g.id}`}
        >
          <header className="capacidades-grupo-topo">
            <span className="capacidades-grupo-selo" aria-hidden="true">
              <Icone nome={g.icone} size={17} />
            </span>
            <h2 id={`cap-${g.id}`} className="painel-titulo">{g.tema}</h2>
          </header>

          <div className="capacidades-intencoes">
            {g.intencoes.map((it) => (
              <div key={it.chave} className="capacidade-intencao">
                <p className="capacidade-intencao-titulo">{it.titulo}</p>
                <ul className="perguntas-clicaveis">
                  {it.exemplos.map((ex) => (
                    <li key={ex}>
                      <button type="button" onClick={() => perguntar(ex)} disabled={ocupado}>
                        {ex}
                        <Icone nome="seta-direita" size={13} />
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      ))}

      {capacidades.limitacoes?.length > 0 && (
        <section className="painel capacidades-limites anima-entrada" aria-labelledby="cap-limites">
          <header className="capacidades-grupo-topo">
            <span className="capacidades-grupo-selo atencao" aria-hidden="true">
              <Icone nome="alerta" size={17} />
            </span>
            <h2 id="cap-limites" className="painel-titulo">O que ainda não faço</h2>
          </header>
          <p className="painel-texto">
            Saber o limite evita a frustração de perguntar algo que não tem resposta aqui.
          </p>
          <ul className="capacidades-limites-lista">
            {capacidades.limitacoes.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
