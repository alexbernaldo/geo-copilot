import type { ColumnDef } from '@tanstack/react-table'
import type { components } from '@/api/schema'
import { Chip, DataTable, Drawer, ErrorState, useBrandColors } from '@/components'
import { formatPct } from '@/lib/format'
import { useExecution } from './api'
import { trocear } from './highlight'

type Evaluacion = components['schemas']['BrandEvaluation']

const SI_NO = (v: boolean) => (v ? 'Sí' : 'No')

const COLUMNAS: ColumnDef<Evaluacion, unknown>[] = [
  { header: 'Marca', accessorKey: 'marca' },
  { header: 'Aparece', accessorFn: (e) => SI_NO(e.aparece) },
  { header: 'Posición', accessorFn: (e) => e.posicion ?? '—' },
  { header: 'Tipo de mención', accessorFn: (e) => e.tipo_mencion ?? '—' },
  { header: 'Fuerza', accessorKey: 'fuerza' },
  { header: 'Sentimiento', accessorFn: (e) => e.sentimiento ?? '—' },
  { header: 'Fuente', accessorFn: (e) => (e.tipo_fuente ? `${e.tipo_fuente}${e.calidad_fuente != null ? ` (${e.calidad_fuente})` : ''}` : '—') },
  { header: 'Juez', accessorKey: 'juez' },
  { header: 'Confianza', accessorFn: (e) => formatPct(e.confianza * 100, 0) },
  { header: 'Discrepancia', cell: ({ row }) => (row.original.discrepancia ? <Chip tone="warn">Reglas y LLM no coinciden</Chip> : '—') },
]

/** Detalle de una ejecución: prompt, respuesta con las marcas resaltadas, fuentes y evaluación por marca. */
export function ExecutionDrawer({ projectId, marcaProyecto, ejecucionId, onClose }: {
  projectId: string
  marcaProyecto: string
  ejecucionId: string | null
  onClose: () => void
}) {
  const q = useExecution(projectId, ejecucionId)
  const color = useBrandColors(marcaProyecto, null)
  return (
    <Drawer open={ejecucionId !== null} onOpenChange={(o) => !o && onClose()} title={ejecucionId ? `Ejecución ${ejecucionId}` : 'Ejecución'}>
      {q.isPending && ejecucionId && <p role="status">Cargando ejecución…</p>}
      {q.isError && <ErrorState error={q.error} onRetry={() => void q.refetch()} />}
      {q.data && (
        <div>
          <p>
            <Chip tone={q.data.fila.ambito === 'asistida' ? 'assist' : 'spont'}>{q.data.fila.ambito === 'asistida' ? 'Asistida' : 'Espontánea'}</Chip>{' '}
            {q.data.fila.motor} · repetición {q.data.fila.repeticion ?? '—'}
            {q.data.fila.ciudad ? ` · ${q.data.fila.ciudad}` : ''}
          </p>
          <h3>Prompt</h3>
          <p>{q.data.fila.prompt}</p>
          <h3>Respuesta</h3>
          <p style={{ whiteSpace: 'pre-wrap' }}>
            {trocear(q.data.respuesta, q.data.resaltados).map((t, i) =>
              t.marca ? (
                <mark key={i} data-marca={t.marca} title={t.marca} style={{ background: 'transparent', color: 'inherit', borderBottom: `3px solid ${color(t.marca)}` }}>{t.texto}</mark>
              ) : (
                <span key={i}>{t.texto}</span>
              ),
            )}
          </p>
          <h3>Fuentes citadas</h3>
          {q.data.fuentes.length === 0 ? (
            <p>Esta respuesta no cita fuentes.</p>
          ) : (
            <ul>
              {q.data.fuentes.map((f, i) => (
                <li key={i}>{f.dominio}{f.tipo ? ` · ${f.tipo}` : ''}{f.calidad != null ? ` · calidad ${f.calidad}` : ''}</li>
              ))}
            </ul>
          )}
          <h3>Evaluación por marca</h3>
          <DataTable columns={COLUMNAS} data={q.data.evaluaciones} />
        </div>
      )}
    </Drawer>
  )
}
