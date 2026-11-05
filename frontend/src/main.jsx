import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Fonte única do projeto: Poppins, nos pesos usados em título e corpo.
// Self-hosted (npm) em vez de CDN — não depende de rede externa na banca.
import '@fontsource/poppins/400.css'
import '@fontsource/poppins/500.css'
import '@fontsource/poppins/600.css'
import '@fontsource/poppins/700.css'
import './estilos/index.css'
import App from './App.jsx'

// Pré-conexão com a API: DNS + TLS já resolvidos quando a primeira pergunta
// sair. Feito aqui, e não no index.html, porque o endereço vem do ambiente.
const urlApi = import.meta.env.VITE_API_URL
if (urlApi) {
  try {
    const link = document.createElement('link')
    link.rel = 'preconnect'
    link.href = new URL(urlApi).origin
    link.crossOrigin = 'anonymous'
    document.head.appendChild(link)
  } catch {
    // VITE_API_URL inválida: o próprio chat avisa quando tentar usar
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
