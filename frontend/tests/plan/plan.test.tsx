import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { apiClientMock, echartsStub, renderRoute } from './helpers'
import { server } from '../../mocks/server'
import { buildBaseline, buildCambios } from '@/features/plan/baseline'
import PlanPage from '@/features/plan/PlanPage'
import t2 from '../../mocks/fixtures/tables/T2.json'

vi.mock('echarts', () => ({ ...echartsStub }))
vi.mock('@/api/client', () => apiClientMock())

beforeAll(() => { server.listen({ onUnhandledFrame: 'error' }) })
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('líneas base del simulador', () => {
  it('toma las tasas de la tabla del backend sin recalcularlas', () => {
    const b = buildBaseline('Grupo Hospitalario Valdecruz', undefined, t2 as never)
    const chatgpt = b.motores.find((m) => m.nombre === 'ChatGPT')
    expect(chatgpt?.tasa).toBeCloseTo(0.8833, 3)
  })

  it('convierte los controles en porcentaje a fracciones del contrato de simulate', () => {
    expect(buildCambios({ Madrid: 60 }, { ChatGPT: 35 }, 1.5, 40)).toEqual({
      aparicion_por_ciudad: { Madrid: 0.6 },
      aparicion_por_motor: { ChatGPT: 0.35 },
      fuerza_media_objetivo: 1.5,
      pct_fuentes_calidad: 0.4,
    })
  })
})

describe('PlanPage con la API simulada', () => {
  it('muestra el plan, la etiqueta del simulador y detecta cambios sin guardar', async () => {
    renderRoute(<PlanPage />, '/proyectos/p1/plan', '/proyectos/:id/plan')
    expect(await screen.findByRole('heading', { name: 'Objetivos' })).toBeInTheDocument()
    expect(screen.getAllByText('Escenario hipotético, no una predicción').length).toBeGreaterThan(0)

    const guardar = screen.getByRole('button', { name: 'Guardar cambios' })
    expect(guardar).toBeDisabled()

    const titulo = await screen.findByLabelText('Título de A1')
    fireEvent.change(titulo, { target: { value: 'Título editado' } })
    expect(screen.getByText('Cambios sin guardar')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar cambios' })).toBeEnabled()
    expect(screen.getByText('Guarda los cambios para poder aprobar el plan.')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByLabelText('Título de A1')).toHaveValue('Título editado'))
  })
})
