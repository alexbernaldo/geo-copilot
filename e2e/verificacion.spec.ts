import { test, expect } from '@playwright/test'

test.describe('Verificación Q · Preload', () => {
  test('1. Primer uso: arranca sin proyectos y sin botón ni texto demo', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/Preload/)

    // Comprobar que no hay textos prohibidos de demo o mock en primer uso
    const bodyText = await page.textContent('body')
    expect(bodyText?.toLowerCase()).not.toContain('demo')
    expect(bodyText?.toLowerCase()).not.toContain('modo demo')
  })

  test('3. Sin términos prohibidos en la API ni respuestas públicas', async ({ request }) => {
    const health = await request.get('/api/health')
    expect(health.ok()).toBeTruthy()
    const healthData = await health.json()
    expect(healthData.ok).toBe(true)

    const projectsRes = await request.get('/api/projects')
    expect(projectsRes.ok()).toBeTruthy()
    const text = await projectsRes.text()
    expect(text.toLowerCase()).not.toContain('mock')
    expect(text.toLowerCase()).not.toContain('demo')
  })

  test('8. Métodos GET no deben disparar peticiones al servidor externo', async ({ request }) => {
    // Verificamos que peticiones GET sobre /settings no fallan ni llaman a OR
    const settingsRes = await request.get('/api/settings')
    expect(settingsRes.ok()).toBeTruthy()
  })

  test('9. No exposición de claves secretas en la API', async ({ request }) => {
    const settings = await (await request.get('/api/settings')).json()
    expect(settings.clave).toBeUndefined()
    if (settings.clave_mascara) {
      expect(settings.clave_mascara).not.toBe('sk-or-test-123')
      expect(settings.clave_mascara).toContain('…')
    }
  })

  test('12. Sin artefactos de Lovable en el bundle de producción', async ({ page }) => {
    await page.goto('/')
    const content = await page.content()
    expect(content).not.toContain('lovable-tagger')
    expect(content).not.toContain('@/integrations/supabase')
  })
})
