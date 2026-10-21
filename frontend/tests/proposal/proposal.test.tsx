import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import { apiClientMock, renderRoute } from '../plan/helpers'
import { server } from '../../mocks/server'
import PropuestaPage from '@/features/proposal/PropuestaPage'
import proposal from '../../mocks/fixtures/proposal.json'

vi.mock('@/api/client', () => apiClientMock())

beforeAll(() => { server.listen({ onUnhandledFrame: 'error' }) })
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const render = () => renderRoute(<PropuestaPage />, '/proyectos/p1/propuesta', '/proyectos/:id/propuesta')

describe('PropuestaPage', () => {
  it('pone en cada sección exactamente el origen que devuelve la API y nunca «IA» por defecto', async () => {
    render()
    expect(await screen.findByRole('heading', { name: '1. Resumen ejecutivo' })).toBeInTheDocument()
    expect(screen.getAllByText('Generado automáticamente')).toHaveLength(proposal.secciones.length)
    expect(screen.queryByText(/Redactado por IA/)).not.toBeInTheDocument()
  })

  it('muestra «Redactado por IA» con el modelo solo cuando la API lo dice', async () => {
    server.use(http.get('/api/projects/:id/proposal', () => HttpResponse.json({
      ...proposal,
      secciones: [{ ...proposal.secciones[0], origen: { origen: 'ia', modelo: 'anthropic/claude-test' } }],
    })))
    render()
    expect(await screen.findByText('Redactado por IA · anthropic/claude-test')).toBeInTheDocument()
  })

  it('enseña el sello del revisor y las incidencias bloqueantes', async () => {
    server.use(http.get('/api/projects/:id/proposal', () => HttpResponse.json({
      ...proposal,
      sello: { ...proposal.sello, aprobado: false, incidencias_normativas: 1, incidencias: [{ tipo: 'normativa', texto: 'Promete resultados garantizados.', sugerencia: 'Usar «puede mejorar».', bloqueante: true }] },
    })))
    render()
    expect(await screen.findByText('Promete resultados garantizados.')).toBeInTheDocument()
    expect(screen.getByText('Bloquea')).toBeInTheDocument()
    expect(screen.getByText(/1 incidencia normativa$/)).toBeInTheDocument()
  })

  it('muestra el estado pendiente si la propuesta aún no existe (409)', async () => {
    server.use(http.get('/api/projects/:id/proposal', () => HttpResponse.json({ error: { code: 'conflicto', message: 'Aún no.', detail: {} } }, { status: 409 })))
    render()
    expect(await screen.findByText(/Disponible cuando termine el paso Redacción/)).toBeInTheDocument()
  })
})
