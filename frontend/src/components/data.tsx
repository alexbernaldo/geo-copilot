import { useEffect, useRef } from 'react'
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from '@tanstack/react-table'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ReactNode } from 'react'

export interface DataTableProps<T> {
  columns: ColumnDef<T, unknown>[]
  data: T[]
  filters?: ReactNode
  onRowClick?: (row: T) => void
  editable?: boolean
}

export function DataTable<T>({ columns, data, filters, onRowClick }: DataTableProps<T>) {
  const table = useReactTable({ columns, data, getCoreRowModel: getCoreRowModel() })
  return (
    <div>
      {filters}
      <table>
        <thead>
          {table.getHeaderGroups().map((g) => (
            <tr key={g.id}>{g.headers.map((h) => <th key={h.id} scope="col">{flexRender(h.column.columnDef.header, h.getContext())}</th>)}</tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((r) => (
            <tr key={r.id} tabIndex={onRowClick ? 0 : undefined} onClick={() => onRowClick?.(r.original)} onKeyDown={(e) => e.key === 'Enter' && onRowClick?.(r.original)}>
              {r.getVisibleCells().map((c) => <td key={c.id}>{flexRender(c.column.columnDef.cell, c.getContext())}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Chart({ option, height = 320, ariaLabel, tableFallback }: { option: EChartsOption; height?: number; ariaLabel: string; tableFallback?: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const chart = echarts.init(ref.current)
    chart.setOption(option)
    const onResize = () => chart.resize()
    window.addEventListener('resize', onResize)
    return () => { window.removeEventListener('resize', onResize); chart.dispose() }
  }, [option])
  return (
    <figure>
      <div ref={ref} role="img" aria-label={ariaLabel} style={{ height }} />
      {tableFallback && <details><summary>Ver como tabla</summary>{tableFallback}</details>}
    </figure>
  )
}

export function Markdown({ source }: { source: string }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{source}</ReactMarkdown>
}
