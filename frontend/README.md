# Intellix — frontend

Aplicação React (Vite) do Intellix. Visão geral do projeto no
[README da raiz](../README.md).

## Rodar

```bash
npm ci
cp .env.example .env.local   # e preencha
npm run dev
```

| Variável | Para quê |
|---|---|
| `VITE_API_URL` | endereço do backend (FastAPI) |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | login pelo Supabase Auth (a chave "anon" é pública por natureza) |
| `VITE_MOCK` | `true` simula login e respostas, sem servidor nenhum |

Antes de abrir um pull request: `npm run lint` e `npm run build` (o CI roda os
dois).

## Organização

```
src/
  App.jsx          rotas (por hash: #/chat, #/importar...), sessão e layout
  paginas/         uma tela por arquivo (Início, Chat, Importar, Perfil...)
  componentes/     gráficos, barra lateral, histórico, paleta de comandos...
  servicos/        api.js (backend), auth.js (Supabase Auth), importacao.js
  utils/           formatação, exportação Excel/PDF, sugestões, histórico local
public/            ícones, logo e o modelo de planilha para importação
vercel.json        cabeçalhos de segurança (CSP, HSTS) e cache
```

Cada página é carregada só quando a rota abre (`React.lazy`). O contrato com o
backend está em [`docs/contratos.md`](../docs/contratos.md).
