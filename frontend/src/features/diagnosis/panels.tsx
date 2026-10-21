import { useMemo, type ReactNode } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Chart, DataTable, EvidenceLink, Panel, SourceNote } from '@/components'
import { describir } from './charts'
import type { PaletaGrafico } from './colors'
import { evidenciaDe, nDe, type Col, type Especificacion, type Fila } from './especificaciones'

const vacio = (v: unknown): string => (v === null || v === undefined || v === '' ? '—' : String(v))

function TablaEquivalente({ columnas, filas }: { columnas: Col[]; filas: Fila[] }) {
  const defs = useMemo<ColumnDef<Fila, unknown>[]>(
    () => columnas.map((c) => ({ header: c.header, accessorFn: (r: Fila) => (c.formato ?? vacio)(r[c.clave]) })),
    [columnas],
  )
  return <DataTable columns={defs} data={filas} />
}

export function PanelGrafico({ spec, filas, paleta, marcaProyecto, accion }: {
  spec: Especificacion
  filas: Fila[]
  paleta: PaletaGrafico
  marcaProyecto: string
  accion?: ReactNode
}) {
  const option = useMemo(() => (spec.construir ? spec.construir(filas as never[], paleta) : null), [spec, filas, paleta])
  const ids = useMemo(() => evidenciaDe(filas, marcaProyecto), [filas, marcaProyecto])
  const tabla = <TablaEquivalente columnas={spec.columnas} filas={filas} />
  return (
    <Panel
      title={spec.titulo}
      source={<SourceNote tabla={spec.tabla} n={nDe(filas, marcaProyecto)} />}
      actions={<>{ids.length > 0 && <EvidenceLink ids={ids} />}{accion}</>}
    >
      {option ? (
        <Chart option={option} height={spec.altura?.(filas.length) ?? 320} ariaLabel={describir(spec.titulo, spec.descripcion(filas as never[]))} tableFallback={tabla} />
      ) : (
        tabla
      )}
    </Panel>
  )
}
