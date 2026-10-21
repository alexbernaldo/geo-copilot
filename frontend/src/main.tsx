import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles/tokens.css'
import './styles/components.css'
import { initTheme } from './lib/theme'

initTheme()

async function start() {
  if (import.meta.env.VITE_MOCK_API === '1') {
    const { worker } = await import('../mocks/browser')
    await worker.start({ onUnhandledFrame: 'bypass' })
  }
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

void start()
