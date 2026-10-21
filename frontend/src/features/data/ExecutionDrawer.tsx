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
        <div className="exec">
          <p className="exec-meta">
            <Chip tone={q.data.fila.ambito === 'asistida' ? 'assist' : 'spont'} dot>{q.data.fila.ambito === 'asistida' ? 'Asistida' : 'Espontánea'}</Chip>
            <Chip tone="neutral">{q.data.fila.motor}</Chip>
            <Chip tone="neutral">{`Repetición ${q.data.fila.repeticion ?? '—'}`}</Chip>
            {q.data.fila.ciudad && <Chip tone="neutral">{q.data.fila.ciudad}</Chip>}
          </p>
          <h3>Prompt</h3>
          <blockquote className="exec-prompt">{q.data.fila.prompt}</blockquote>
          <h3>Respuesta</h3>
          <div className="exec-answer">
            {trocear(q.data.respuesta, q.data.resaltados).map((t, i) => {
              // Los ** de Markdown se quitan al pintar cada trozo: las posiciones del resaltado ya están calculadas
              const texto = t.texto.replace(/\*\*/g, '')
              return t.marca ? (
                <mark key={i} data-marca={t.marca} title={t.marca} style={{ background: `color-mix(in srgb, ${color(t.marca)} 14%, transparent)`, color: 'inherit', borderBottom: `2px solid ${color(t.marca)}` }}>{texto}</mark>
              ) : (
                <span key={i}>{texto}</span>
              )
            })}
          </div>
          <h3>Fuentes citadas</h3>
          {q.data.fuentes.length === 0 ? (
            <p className="exec-empty">Esta respuesta no cita fuentes.</p>
          ) : (
            <ul className="exec-sources">
              {q.data.fuentes.map((f, i) => (
                <li key={i}><Chip tone="neutral">{`${f.dominio}${f.tipo ? ` · ${f.tipo}` : ''}${f.calidad != null ? ` · calidad ${f.calidad}` : ''}`}</Chip></li>
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
