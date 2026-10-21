// Captura de las 3 pantallas de F en claro y oscuro, a 1024/1280/1440, con recuento de errores de consola
// y de peticiones que no son GET. Uso: node design-shots/F/capture.mjs [puerto] [subcarpeta]
import { chromium } from '@playwright/test'
import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const port = process.argv[2] ?? '5176'
const sub = process.argv[3] ?? 'actual'
const out = join(dirname(fileURLToPath(import.meta.url)), sub)
mkdirSync(out, { recursive: true })

const routes = { plan: '/proyectos/p_demo/plan', propuesta: '/proyectos/p_demo/propuesta', calidad: '/proyectos/p_demo/calidad' }
const sizes = [1024, 1280, 1440]
const report = []

// Usa el Chromium ya descargado en la caché si el de esta versión de Playwright no está instalado.
const cached = `${process.env.HOME}/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell`
const browser = await chromium.launch({ executablePath: process.env.PW_CHROMIUM ?? cached })
for (const scheme of ['light', 'dark']) {
  const ctx = await browser.newContext({ colorScheme: scheme, viewport: { width: 1280, height: 900 } })
  for (const [name, path] of Object.entries(routes)) {
    const page = await ctx.newPage()
    const errors = []
    const writes = []
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
    page.on('pageerror', (e) => errors.push(String(e)))
    page.on('request', (r) => { if (r.url().includes('/api/') && r.method() !== 'GET') writes.push(`${r.method()} ${r.url()}`) })
    for (const w of sizes) {
      await page.setViewportSize({ width: w, height: 900 })
      await page.goto(`http://localhost:${port}${path}`, { waitUntil: 'networkidle' })
      await page.waitForTimeout(500)
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
      await page.screenshot({ path: join(out, `${name}_${scheme}_${w}.png`), fullPage: true })
      report.push({ name, scheme, width: w, errors: [...errors], writesOnLoad: [...writes], horizontalOverflow: overflow })
    }
    await page.close()
  }
  await ctx.close()
}
await browser.close()
writeFileSync(join(out, 'informe.json'), JSON.stringify(report, null, 1))
console.log(JSON.stringify(report.map((r) => ({ ...r, errors: r.errors.length, writesOnLoad: r.writesOnLoad.length })), null, 0))
