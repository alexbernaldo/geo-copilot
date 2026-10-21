import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { CheckpointBar, Chip, CostConfirm, EmptyState, ErrorState, EvidenceLink, KpiStrip, OriginTag, PendingState, ScopeToggle } from '@/components'
import { applyEvent } from '@/components/ProgressPanel'
import type { Estimate, Progress } from '@/api/types'
import { formatDate, formatEur, formatNum, formatPct } from '@/lib/format'

const estimate: Estimate = {
  pasos: [{ id: 'judge', nombre: 'Juez', llamadas: 624, eur: 1.1 }],
  total_llamadas: 624,
  total_eur: 1.1,
  minutos: 6.5,
  supera_tope: false,
  tope_eur: 15,
}

describe('KpiStrip', () => {
  it('muestra etiqueta, valor, unidad, nota y marca el ámbito', () => {
    const { container } = render(<KpiStrip scope="asistida" items={[{ label: 'Score', value: '27,97', unit: '/ 100', note: 'Puesto 7 de 10', highlight: true }]} />)
    expect(screen.getByText('Score')).toBeInTheDocument()
    expect(screen.getByText('27,97')).toBeInTheDocument()
    expect(screen.getByText('/ 100')).toBeInTheDocument()
    expect(screen.getByText('Puesto 7 de 10')).toBeInTheDocument()
    expect(container.querySelector('dl')).toHaveAttribute('data-scope', 'asistida')
  })
})

describe('ScopeToggle', () => {
  it('cambia de ámbito y refleja el seleccionado con aria-pressed', async () => {
    const onChange = vi.fn()
    render(<ScopeToggle value="espontanea" onChange={onChange} />)
    expect(screen.getByRole('button', { name: 'Espontánea' })).toHaveAttribute('aria-pressed', 'true')
    await userEvent.click(screen.getByRole('button', { name: 'Asistida' }))
    expect(onChange).toHaveBeenCalledWith('asistida')
  })
})

describe('CostConfirm', () => {
  it('muestra la estimación y confirma', async () => {
    const onConfirm = vi.fn()
    render(<CostConfirm estimate={estimate} onConfirm={onConfirm} onCancel={() => {}} />)
    expect(screen.getAllByText('1,10 €').length).toBeGreaterThan(0)
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar coste' }))
    expect(onConfirm).toHaveBeenCalledOnce()
  })
  it('bloquea la confirmación si supera el tope', () => {
    render(<CostConfirm estimate={{ ...estimate, supera_tope: true, total_eur: 21 }} onConfirm={() => {}} onCancel={() => {}} />)
    expect(screen.getByRole('button', { name: 'Confirmar coste' })).toBeDisabled()
    expect(screen.getByRole('alert')).toHaveTextContent('tope de gasto')
  })
})

describe('etiquetas de origen (regla 0.1)', () => {
  it.each([
    ['calculado', undefined, 'Calculado'],
    ['automatico', undefined, 'Generado automáticamente'],
    ['editado', undefined, 'Editado'],
    ['ia', 'openai/gpt-4o', 'Redactado por IA · openai/gpt-4o'],
  ] as const)('%s', (origen, modelo, texto) => {
    render(<OriginTag origen={origen} modelo={modelo} />)
    expect(screen.getByText(texto)).toBeInTheDocument()
  })
  it('no atribuye a un modelo si el origen no es IA', () => {
    render(<OriginTag origen="automatico" modelo="openai/gpt-4o" />)
    expect(screen.queryByText(/openai/)).toBeNull()
  })
})

describe('estados y puntos de control', () => {
  it('PendingState indica el paso', () => {
    render(<PendingState step="Hallazgos" />)
    expect(screen.getByText('Disponible cuando termine el paso Hallazgos.')).toBeInTheDocument()
  })
  it('ErrorState lee el mensaje de la API y reintenta', async () => {
    const retry = vi.fn()
    render(<ErrorState error={{ error: { code: 'x', message: 'Sin saldo en OpenRouter.' } }} onRetry={retry} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Sin saldo en OpenRouter.')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(retry).toHaveBeenCalled()
  })
  it('EmptyState muestra la acción', () => {
    render(<EmptyState title="Vacío" description="Descripción" action={<button>Crear</button>} />)
    expect(screen.getByRole('button', { name: 'Crear' })).toBeInTheDocument()
  })
  it('CheckpointBar aprueba y, aprobado, ya no ofrece el botón', async () => {
    const approve = vi.fn()
    const { rerender } = render(<CheckpointBar n={2} approved={false} onApprove={approve} summary="Resumen" />)
    await userEvent.click(screen.getByRole('button', { name: 'Aprobar' }))
    expect(approve).toHaveBeenCalled()
    rerender(<CheckpointBar n={2} approved onApprove={approve} summary="Resumen" />)
    expect(screen.queryByRole('button', { name: 'Aprobar' })).toBeNull()
    expect(screen.getByText('Aprobado')).toBeInTheDocument()
  })
  it('Chip con punto', () => {
    const { container } = render(<Chip tone="good" dot>Listo</Chip>)
    expect(container.querySelector('.chip-dot')).not.toBeNull()
  })
  it('EvidenceLink apunta a Datos del estudio filtrado dentro del proyecto', () => {
    render(<MemoryRouter initialEntries={['/proyectos/p_1/diagnostico']}><EvidenceLink ids={['EJ-1', 'EJ-2']} /></MemoryRouter>)
    expect(screen.getByRole('link', { name: 'Ver evidencia' })).toHaveAttribute('href', '/proyectos/p_1/datos?ids=EJ-1%2CEJ-2')
  })
})

describe('formato es-ES', () => {
  it('cifras', () => {
    expect(formatPct(39.4)).toBe('39,4 %')
    expect(formatEur(24300)).toBe('24.300 €')
    expect(formatNum(1234.5, 1)).toBe('1234,5')
    expect(formatNum(12345)).toBe('12.345')
    expect(formatDate('2026-10-21T15:30:12Z')).toMatch(/2026/)
  })
})

describe('applyEvent (SSE)', () => {
  const base: Progress = {
    estado: 'en_ejecucion', paso_actual: null, llamadas: 0, coste_eur: 0, coste_real: false, transcurrido_s: 0, contador: null,
    pasos: [{ id: 'judge', nombre: 'Juez', estado: 'pendiente' } as Progress['pasos'][number]],
  }
  it('aplica step, counter, cost y done sin tocar otros pasos', () => {
    let p = applyEvent(base, 'step', { paso: 'judge', estado: 'en_curso' })!
    expect(p.pasos[0]!.estado).toBe('en_curso')
    expect(p.paso_actual).toBe('judge')
    p = applyEvent(p, 'counter', { paso: 'judge', hechos: 214, total: 624 })!
    expect(p.contador).toEqual({ paso: 'judge', hechos: 214, total: 624 })
    p = applyEvent(p, 'cost', { llamadas: 214, coste_eur: 0.4, coste_real: true })!
    expect(p.coste_real).toBe(true)
    p = applyEvent(p, 'done', { estado: 'completado' })!
    expect(p.estado).toBe('completado')
    expect(p.contador).toBeNull()
  })
  it('el snapshot sustituye todo', () => {
    expect(applyEvent(undefined, 'snapshot', { ...base, llamadas: 5 })!.llamadas).toBe(5)
  })
})
