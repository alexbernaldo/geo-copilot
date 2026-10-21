import { expect, test } from '@playwright/test'

const P = '/proyectos/p_20261021_153012_ab12cd'

test('Diagnóstico: cambia entre espontánea y asistida y abre la evidencia', async ({ page }) => {
  await page.goto(`${P}/diagnostico`)
  await expect(page.getByRole('heading', { name: 'Diagnóstico' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Espontánea' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('heading', { name: 'Ranking de marcas por score' })).toBeVisible()
  // Los duelos solo existen en asistida.
  await expect(page.getByRole('heading', { name: 'Duelos 1 a 1' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Asistida' }).click()
  await expect(page).toHaveURL(/ambito=asistida/)
  await expect(page.getByRole('button', { name: 'Asistida' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('heading', { name: 'Duelos 1 a 1' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Score asistido' }).or(page.getByText('Score asistido'))).toBeVisible()

  await page.getByRole('link', { name: 'Ver evidencia' }).first().click()
  await expect(page).toHaveURL(/\/datos\?ids=/)
  await expect(page.getByRole('heading', { name: 'Datos del estudio' })).toBeVisible()
  await expect(page.getByRole('status').filter({ hasText: 'Mostrando solo la evidencia' })).toBeVisible()
})

test('Datos del estudio: abre una ejecución con la marca resaltada', async ({ page }) => {
  await page.goto(`${P}/datos`)
  await page.getByRole('row').nth(1).click()
  await expect(page.getByRole('heading', { name: 'Respuesta' })).toBeVisible()
  await expect(page.locator('mark[data-marca]').first()).toBeVisible()
})
