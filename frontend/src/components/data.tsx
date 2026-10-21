import { useEffect, useRef, useState } from 'react'
import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type ColumnDef, type SortingState } from '@tanstack/react-table'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ReactNode } from 'react'
import { ArrowDown, ArrowUp } from 'lucide-react'
import { usePrefersReducedMotion, useResolvedTheme } from '@/lib/theme'
import { buildChartTheme } from './chartTheme'
import { Button, Input } from './primitives'

declare module '@tanstack/react-table' {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData, TValue> {
    /** Alinea a la derecha con cifras tabulares. */
    numeric?: boolean
    /** Con `editable` en la tabla, esta columna se edita en línea. */
    editable?: boolean
  }
}

export interface DataTableProps<T> {
  columns: ColumnDef<T, unknown>[]
  data: T[]
  filters?: ReactNode
  onRowClick?: (row: T) => void
  /** Activa la edición en línea de las columnas con `meta.editable`. */
  editable?: boolean
  onCellEdit?: (row: T, columnId: string, value: string) => void
  /** Filas visibles de una vez; el resto se carga con «Mostrar más». */
  pageSize?: number
  emptyText?: string
  caption?: string
}

export function DataTable<T>({ columns, data, filters, onRowClick, editable, onCellEdit, pageSize = 100, emptyText = 'Sin resultados.', caption }: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [shown, setShown] = useState(pageSize)
  const table = useReactTable({ columns, data, state: { sorting }, onSortingChange: setSorting, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel() })
  const rows = table.getRowModel().rows
  const visible = rows.slice(0, shown)
  return (
    <div>
      {filters && <div className="table-filters">{filters}</div>}
      <div className="table-wrap">
        <table className="table">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead>
            {table.getHeaderGroups().map((g) => (
              <tr key={g.id}>
                {g.headers.map((h) => {
                  const sorted = h.column.getIsSorted()
                  const can = h.column.getCanSort()
                  return (
                    <th key={h.id} scope="col" data-num={h.column.columnDef.meta?.numeric || undefined} aria-sort={sorted === 'asc' ? 'ascending' : sorted === 'desc' ? 'descending' : undefined}>
                      {h.isPlaceholder ? null : can ? (
                        <button type="button" className="btn" data-variant="ghost" data-size="sm" style={{ height: 22, padding: 0, font: 'inherit', textTransform: 'inherit', letterSpacing: 'inherit', color: 'inherit' }} onClick={h.column.getToggleSortingHandler()}>
                          {flexRender(h.column.columnDef.header, h.getContext())}
                          {sorted === 'asc' && <ArrowUp size={12} strokeWidth={1.5} aria-hidden />}
                          {sorted === 'desc' && <ArrowDown size={12} strokeWidth={1.5} aria-hidden />}
                        </button>
                      ) : flexRender(h.column.columnDef.header, h.getContext())}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {visible.map((r) => (
              <tr
                key={r.id}
                data-clickable={onRowClick ? 'true' : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                onClick={() => onRowClick?.(r.original)}
                onKeyDown={(e) => { if (onRowClick && e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onRowClick(r.original) } }}
              >
                {r.getVisibleCells().map((c) => {
                  const meta = c.column.columnDef.meta
                  const raw = c.getValue()
                  return (
                    <td key={c.id} data-num={meta?.numeric || undefined}>
                      {editable && meta?.editable && (typeof raw === 'string' || typeof raw === 'number' || raw == null) ? (
                        <Input className="cell-edit" aria-label={String(c.column.columnDef.header ?? c.column.id)} defaultValue={raw == null ? '' : String(raw)} onClick={(e) => e.stopPropagation()} onBlur={(e) => { if (e.target.value !== String(raw ?? '')) onCellEdit?.(r.original, c.column.id, e.target.value) }} />
                      ) : flexRender(c.column.columnDef.cell, c.getContext())}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <div className="table-empty" role="status">{emptyText}</div>}
      </div>
      {rows.length > shown && (
        <div className="table-foot">
          <span className="num">{`${shown} de ${rows.length} filas. `}</span>
          <Button size="sm" variant="ghost" onClick={() => setShown((s) => s + pageSize)}>{`Mostrar ${Math.min(pageSize, rows.length - shown)} más`}</Button>
        </div>
      )}
    </div>
  )
}

export function Chart({ option, height = 320, ariaLabel, tableFallback }: { option: EChartsOption; height?: number; ariaLabel: string; tableFallback?: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)
  const theme = useResolvedTheme()
  const reduced = usePrefersReducedMotion()
  const optionRef = useRef(option)
  optionRef.current = option

  // Instancia y tema: se recrea al cambiar de tema porque ECharts resuelve los colores al crear.
  useEffect(() => {
    if (!ref.current) return
    echarts.registerTheme('geo', buildChartTheme() as object)
    const chart = echarts.init(ref.current, 'geo')
    chartRef.current = chart
    chart.setOption({ animation: !reduced, ...optionRef.current })
    const ro = new ResizeObserver(() => chart.resize())
    ro.observe(ref.current)
    return () => { ro.disconnect(); chart.dispose(); chartRef.current = null }
  }, [theme, reduced])

  useEffect(() => {
    chartRef.current?.setOption({ animation: !reduced, ...option }, true)
  }, [option, reduced])

  return (
    <figure className="chart">
      <div className="chart-canvas" ref={ref} role="img" aria-label={ariaLabel} style={{ height }} />
      {tableFallback && <details><summary>Ver como tabla</summary>{tableFallback}</details>}
    </figure>
  )
}

export function Markdown({ source }: { source: string }) {
  return <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]}>{source}</ReactMarkdown></div>
}
