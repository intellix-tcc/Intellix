export default function Sidebar({ conversas, atualId, onNovoChat, onSelecionar, onExcluir }) {
  return (
    <aside className="sidebar">
      <button type="button" className="novo-chat" onClick={onNovoChat}>
        + Novo chat
      </button>
      <div className="historico">
        {conversas.length === 0 && (
          <p className="historico-vazio">Nenhuma conversa ainda</p>
        )}
        {conversas.map((c) => (
          <div
            key={c.id}
            className={`historico-item${c.id === atualId ? " ativo" : ""}`}
          >
            <button
              type="button"
              className="historico-titulo"
              onClick={() => onSelecionar(c.id)}
              title={c.titulo}
            >
              {c.titulo}
            </button>
            <button
              type="button"
              className="historico-excluir"
              onClick={() => onExcluir(c.id)}
              aria-label="Excluir conversa"
              title="Excluir conversa"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
