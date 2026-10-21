import type { ColumnDef } from '@tanstack/react-table'
import { Chip, DataTable, EmptyState, ErrorState, Panel } from '@/components'
import { formatDate, formatEur, formatNum } from '@/lib/format'
import { type ApprovalRecord, type TraceRow, useTraces } from './api'

const str = (v: unknown): string => (typeof v === 'string' ? v : v == null ? '—' : String(v))
const n = (v: unknown, d = 0): string => (typeof v === 'number' ? formatNum(v, d) : '—')

const columns: ColumnDef<TraceRow, unknown>[] = [
  { header: 'Paso', cell: ({ row }) => <span className="font-medium">{str(row.original.step)}</span> },
  { header: 'Modelo', cell: ({ row }) => str(row.original.model) },
  { header: 'Versión del prompt', cell: ({ row }) => str(row.original.prompt_version) },
  { header: 'Duración (s)', cell: ({ row }) => <span className="tabular-nums">{n(row.original.duration_s, 2)}</span> },
  { header: 'Llamadas', cell: ({ row }) => <span className="tabular-nums">{n(row.original.llm_calls)}</span> },
  { header: 'Aciertos de caché', cell: ({ row }) => <span className="tabular-nums">{n(row.original.cache_hits)}</span> },
  { header: 'Tokens (ent. / sal.)', cell: ({ row }) => <span className="tabular-nums">{`${n(row.original.tokens_in)} / ${n(row.original.tokens_out)}`}</span> },
  { header: 'Coste', cell: ({ row }) => <span className="tabular-nums">{typeof row.original.estimated_cost_eur === 'number' ? formatEur(row.original.estimated_cost_eur, 4) : '—'}</span> },
  { header: 'Degradación', cell: ({ row }) => (row.original.degradado ? <Chip tone="warn">Degradado</Chip> : <span className="text-[var(--brand-neutral)]">No</span>) },
  { header: 'Error', cell: ({ row }) => (row.original.error ? <Chip tone="bad">{str(row.original.error)}</Chip> : <span className="text-[var(--brand-neutral)]">—</span>) },
]

export function TracePanel({ projectId }: { projectId: string }) {
  const q = useTraces(projectId)
  return (
    <Panel title="Traza de ejecución" source={<span className="text-xs text-[var(--brand-neutral)]">Un registro por paso</span>}>
      {q.isPending ? <p role="status">Cargando la traza…</p> : q.isError ? <ErrorState error={q.error} onRetry={() => void q.refetch()} /> : q.data.length === 0
        ? <EmptyState title="Sin traza" description="Todavía no se ha ejecutado ningún paso." />
        : <div className="overflow-x-auto"><DataTable columns={columns} data={q.data} /></div>}
    </Panel>
  )
}

export function ApprovalsPanel({ items }: { items: ApprovalRecord[] }) {
  return (
    <Panel title="Registro de aprobaciones">
      {items.length === 0 ? <EmptyState title="Sin aprobaciones" description="Todavía no se ha aprobado ningún punto de control." /> : (
        <table className="w-full text-sm">
          <thead><tr className="text-left"><th scope="col">Punto de control</th><th scope="col">Fecha</th><th scope="col">Origen</th><th scope="col">Nota</th></tr></thead>
          <tbody>
            {items.map((a) => (
              <tr key={`${a.punto_control}-${a.fecha}`} className="border-t border-[var(--brand-neutral)]/30 align-top">
                <td className="py-1.5">{`${a.punto_control} · ${a.nombre}`}</td>
                <td className="tabular-nums">{formatDate(a.fecha)}</td>
                <td>{a.automatica ? <Chip tone="neutral">Automática</Chip> : <Chip tone="good">Consultor</Chip>}</td>
                <td>{a.nota ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
