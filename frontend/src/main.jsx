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

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
