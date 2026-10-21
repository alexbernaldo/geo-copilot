import { useParams } from 'react-router-dom'
import { ErrorState, PageHeader, Panel, PendingState, Tabs } from '@/components'
import { isPending } from '@/features/plan/http'
import { formatNum } from '@/lib/format'
import { useQuality } from './api'
import { DiscrepancyQueue } from './DiscrepancyQueue'
import { LabelingForm } from './LabelingForm'
import { ApprovalsPanel, TracePanel } from './TracePanel'
import { ValidationPanel } from './ValidationPanel'

export default function CalidadytrazasPage() {
  const { id = '' } = useParams()
  const q = useQuality(id)

  if (q.isPending) return <><PageHeader title="Calidad y trazas" /><p role="status">Cargando la calidad del juez…</p></>
  if (q.isError) {
    return (
      <>
        <PageHeader title="Calidad y trazas" />
        {isPending(q.error) ? <PendingState step="Juez" /> : <ErrorState error={q.error} onRetry={() => void q.refetch()} />}
      </>
    )
  }

  const d = q.data
  const muestra = d.muestra_para_etiquetar ?? []
  const sinValidacion = (
    <Panel title="Validación del juez">
      <p className="max-w-[72ch] text-sm">Todavía no hay una muestra evaluada por humanos, así que no se puede medir la exactitud del juez. Evalúa a mano {formatNum(muestra.length)} ejecuciones desde la pestaña «Evaluar a mano» y se calcularán la exactitud y el kappa por campo.</p>
    </Panel>
  )

  const items = [
    {
      value: 'validacion',
      label: 'Validación',
      content: (
        <div className="grid gap-6">
          <ValidationPanel validacion={d.validacion} sin={sinValidacion} />
          {!d.validacion.disponible && muestra.length > 0 && <LabelingForm projectId={id} muestra={muestra} />}
        </div>
      ),
    },
    { value: 'discrepancias', label: `Discrepancias (${formatNum(d.discrepancias.length)})`, content: <DiscrepancyQueue projectId={id} items={d.discrepancias} /> },
    { value: 'traza', label: 'Traza', content: <TracePanel projectId={id} /> },
    { value: 'aprobaciones', label: 'Aprobaciones', content: <ApprovalsPanel items={d.aprobaciones} /> },
  ]

  return (
    <div className="grid gap-6">
      <PageHeader title="Calidad y trazas" description="Cuánto se puede fiar del juez, qué evaluaciones están en duda y qué hizo cada paso." />
      <Tabs items={items} />
    </div>
  )
}
