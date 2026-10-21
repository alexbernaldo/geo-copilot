import { defineConfig } from '@playwright/test'

const chromium = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env.PW_CHROMIUM

/** E2E del agente E contra MSW (VITE_MOCK_API=1, Vite en 5175). `npx playwright test -c tests/e2e-analisis/playwright.config.ts` */
export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.ts',
  timeout: 60_000,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5175',
    headless: true,
    // Opcional: `PW_CHROMIUM=/ruta/al/chrome-headless-shell` si la versión descargada no coincide con la de @playwright/test.
    launchOptions: chromium ? { executablePath: chromium } : {},
  },
  webServer: {
    command: 'VITE_MOCK_API=1 npx vite --port 5175 --strictPort',
    url: 'http://localhost:5175',
    reuseExistingServer: true,
    timeout: 60_000,
  },
})
