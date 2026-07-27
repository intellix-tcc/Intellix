export default function Sidebar({ conversas, atualId, onNovoChat, onSelecionar }) {
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
          <button
            key={c.id}
            type="button"
            className={`historico-item${c.id === atualId ? " ativo" : ""}`}
            onClick={() => onSelecionar(c.id)}
            title={c.titulo}
          >
            {c.titulo}
          </button>
        ))}
      </div>
    </aside>
  );
}
