// Capturas y comprobaciones de navegador (equivalente a la verificación H3.2 con Playwright).
// Uso: node design-shots/D/shots.mjs [ruta ...]   (servidor de desarrollo en 5174 con VITE_MOCK_API=1)
import { chromium } from '@playwright/test'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const BASE = process.env.BASE ?? 'http://localhost:5174'
const OUT = fileURLToPath(new URL('./', import.meta.url))
const routes = process.argv.slice(2).length ? process.argv.slice(2) : ['/_kit']
const widths = (process.env.WIDTHS ?? '1024,1280,1440').split(',').map(Number)
const themes = ['light', 'dark']
const report = []

// Si la versión de Chromium de Playwright no está descargada, usa el headless shell de la caché local.
const cached = `${process.env.HOME}/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell`
const browser = await chromium.launch({ executablePath: process.env.CHROME_BIN || (existsSync(cached) ? cached : undefined) })
for (const route of routes) {
  const name = route === '/' ? 'proyectos' : route.replace(/^\//, '').replace(/[/]/g, '-')
  for (const theme of themes) {
    for (const width of widths) {
      const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: theme, reducedMotion: 'reduce' })
      const page = await ctx.newPage()
      const errors = []
      const requests = []
      page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) errors.push(`${m.type()}: ${m.text()}`) })
      page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))
      page.on('request', (r) => requests.push(`${r.method()} ${r.url()}`))
      await page.goto(BASE + route, { waitUntil: 'networkidle' })
      await page.waitForTimeout(600)
      await page.screenshot({ path: `${OUT}${name}-${theme}-${width}.png`, fullPage: true })
      const bad = requests.filter((r) => /openrouter\.ai/.test(r) || (r.startsWith('GET') === false && /\/api\//.test(r) && !/events/.test(r)))
      report.push({ route, theme, width, errors, paid: bad, scrollX: await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth) })
      await ctx.close()
    }
  }
}
await browser.close()
mkdirSync(OUT, { recursive: true })
writeFileSync(`${OUT}informe-${Date.now()}.json`, JSON.stringify(report, null, 2))
for (const r of report) console.log(r.route, r.theme, r.width, 'errores:', r.errors.length, 'POST/pago:', r.paid.length, 'scrollH:', r.scrollX, r.errors.slice(0, 3).join(' | '))
