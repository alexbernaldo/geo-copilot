import { expect, test } from '@playwright/test'

const P = '/proyectos/p_20261021_153012_ab12cd'
const PANTALLAS = [
  { nombre: 'resumen', ruta: P },
  { nombre: 'ficha', ruta: `${P}/ficha` },
  { nombre: 'datos', ruta: `${P}/datos` },
  { nombre: 'competencia', ruta: `${P}/competencia` },
  { nombre: 'diagnostico', ruta: `${P}/diagnostico` },
  { nombre: 'diagnostico-asistida', ruta: `${P}/diagnostico?ambito=asistida` },
  { nombre: 'hallazgos', ruta: `${P}/hallazgos` },
]
const ANCHOS = [1024, 1280, 1440]
const TEMAS = ['light', 'dark'] as const

for (const pantalla of PANTALLAS) {
  for (const tema of TEMAS) {
    for (const ancho of ANCHOS) {
      test(`${pantalla.nombre} · ${tema} · ${ancho}`, async ({ page }) => {
        const errores: string[] = []
        const peticiones: string[] = []
        page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errores.push(`${m.type()}: ${m.text()}`) })
        page.on('pageerror', (e) => errores.push(`pageerror: ${e.message}`))
        page.on('request', (r) => peticiones.push(`${r.method()} ${r.url()}`))
        await page.emulateMedia({ colorScheme: tema })
        await page.setViewportSize({ width: ancho, height: 900 })
        await page.goto(pantalla.ruta)
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(400)
        await page.screenshot({ path: `design-shots/E/${pantalla.nombre}-${tema}-${ancho}.png`, fullPage: true })
        expect(errores, errores.join('\n')).toEqual([])
        const prohibidas = peticiones.filter((r) => /openrouter\.ai|:8765/.test(r) || (r.startsWith('POST') && r.includes('/api/')))
        expect(prohibidas, prohibidas.join('\n')).toEqual([])
      })
    }
  }
}
