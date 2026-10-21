import { CostConfirm, ErrorState } from '@/components'
import { useInvalidation, type Cambio } from './checkpoints'

const NOMBRE_PASO: Record<string, string> = {
  intake: 'Ficha', detect: 'Detección', judge: 'Juez', metrics: 'Métricas', market: 'Mercado', findings: 'Hallazgos',
  plan: 'Plan', write: 'Redacción', review: 'Revisión', export: 'Exportación',
}

/** Aviso previo a editar algo ya aprobado: qué pasos se recalculan y su coste, con confirmación explícita. */
export function RecalcConfirm({ id, cambio, onConfirm, onCancel }: {
  id: string
  cambio: Cambio
  onConfirm: (desdePaso: string, costeEur: number) => void
  onCancel: () => void
}) {
  const q = useInvalidation(id, cambio, true)
  if (q.isPending) return <p role="status">Calculando qué hay que recalcular…</p>
  if (q.isError) return <ErrorState error={q.error} onRetry={() => void q.refetch()} />
  const { pasos, estimacion } = q.data
  const primero = pasos[0] ?? ''
  return (
    <section aria-label="Recalcular pasos posteriores">
      <h3>Este cambio recalcula los pasos posteriores</h3>
      <p>{pasos.length ? `Se recalcularán: ${pasos.map((p) => NOMBRE_PASO[p] ?? p).join(', ')}.` : 'No hay pasos posteriores que recalcular.'}</p>
      <CostConfirm estimate={estimacion} onConfirm={() => onConfirm(primero, estimacion.total_eur)} onCancel={onCancel} />
    </section>
  )
}
