import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import { apiClientMock, renderRoute } from '../plan/helpers'
import { server } from '../../mocks/server'
import CalidadytrazasPage from '@/features/quality/CalidadytrazasPage'
import { labelProblem } from '@/features/quality/LabelingForm'
import { highlight } from '@/features/quality/text'
import quality from '../../mocks/fixtures/quality.json'

vi.mock('@/api/client', () => apiClientMock())

beforeAll(() => { server.listen({ onUnhandledFrame: 'error' }) })
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const render = () => renderRoute(<CalidadytrazasPage />, '/proyectos/p1/calidad', '/proyectos/:id/calidad')

describe('etiquetado humano', () => {
  it('exige los campos de una mención antes de guardar', () => {
    const base = { ejecucion_id: 'EJ-0001', marca: 'A', aparece: true, fuerza: 1, posicion: 1, tipo_mencion: 'Pasiva', sentimiento: 'neutro', tipo_fuente: 'Medio' }
    expect(labelProblem(base)).toBeNull()
    expect(labelProblem({ ...base, tipo_fuente: null })).toBe('falta el tipo de fuente')
    expect(labelProblem({ ...base, aparece: false, tipo_fuente: null })).toBeNull()
  })

  it('el texto resaltado es siempre texto, nunca HTML', () => {
    const nodes = highlight('Visita <img src=x onerror=alert(1)> Alborada', 'alborada')
    expect(JSON.stringify(nodes)).toContain('Alborada')
    expect(JSON.stringify(nodes)).toContain('<img src=x')
  })
})

describe('CalidadytrazasPage', () => {
  it('sin muestra evaluada explica la situación y ofrece evaluar a mano', async () => {
    render()
    expect(await screen.findByText(/Todavía no hay una muestra evaluada por humanos/)).toBeInTheDocument()
    expect(await screen.findByText('Evaluar a mano')).toBeInTheDocument()
  })

  it('con validación disponible muestra exactitud y kappa por campo', async () => {
    server.use(http.get('/api/projects/:id/quality', () => HttpResponse.json({
      ...quality,
      validacion: { disponible: true, n: 67, campos: [{ campo: 'tipo_fuente', exactitud: 0.567, kappa: 0.445 }] },
    })))
    render()
    expect(await screen.findByText('Tipo de fuente')).toBeInTheDocument()
    expect(screen.getByText('56,7 %')).toBeInTheDocument()
    expect(screen.getByText('0,445')).toBeInTheDocument()
  })
})
