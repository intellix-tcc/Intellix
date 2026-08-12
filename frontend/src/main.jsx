import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Fontes da identidade: Inter Bold nos títulos, Roboto no corpo.
// Self-hosted (npm) em vez de CDN — não depende de rede externa na banca.
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/roboto/400.css'
import '@fontsource/roboto/500.css'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
