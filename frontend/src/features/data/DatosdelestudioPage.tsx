import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import type { ColumnDef } from '@tanstack/react-table'
import type { components } from '@/api/schema'
import { useProject } from '@/api/hooks'
import { Button, Chip, DataTable, EmptyState, ErrorState, Input, PageHeader, Panel, Select } from '@/components'
import { formatNum } from '@/lib/format'
import { useExecutions, useStudySummary } from './api'
import { ExecutionDrawer } from './ExecutionDrawer'
import { isNotReady } from './common'

type Fila = components['schemas']['ExecutionRow']

const TAMANO = 50
const TODOS = 'todos'
const MOTORES = ['ChatGPT', 'Gemini', 'Perplexity', 'Claude']
const INTENCIONES = ['Descubrimiento', 'Comparación', 'Validación', 'Decisión']
const FAMILIAS = [
  'Descubrimiento genérico', 'Descubrimiento por perfil', 'Localización', 'Comparación de opciones', 'Comparación de marcas',
  'Validación reputacional', 'Fuentes y citación', 'Decisión final', 'Precio y valor',
]
const AMBITOS = [{ value: TODOS, label: 'Todos los ámbitos' }, { value: 'espontanea', label: 'Espontánea' }, { value: 'asistida', label: 'Asistida' }]

const opciones = (todos: string, valores: string[]) => [{ value: TODOS, label: todos }, ...valores.map((v) => ({ value: v, label: v }))]

const COLUMNAS: ColumnDef<Fila, unknown>[] = [
  { header: 'ID', accessorKey: 'ejecucion_id' },
  { header: 'Ámbito', cell: ({ row }) => <Chip tone={row.original.ambito === 'asistida' ? 'assist' : 'spont'}>{row.original.ambito === 'asistida' ? 'Asistida' : 'Espontánea'}</Chip> },
  { header: 'Motor', accessorKey: 'motor' },
  { header: 'Familia', accessorFn: (r) => r.familia ?? '—' },
  { header: 'Intención', accessorFn: (r) => r.intencion ?? '—' },
  { header: 'Rep.', accessorFn: (r) => r.repeticion ?? '—' },
  { header: 'Ciudad', accessorFn: (r) => r.ciudad ?? '—' },
  { header: 'Prompt', accessorKey: 'prompt' },
]

/** Explorador de ejecuciones. Destino de todos los enlaces «Ver evidencia» (`?ids=EJ-0001,EJ-0002`). */
export default function DatosdelestudioPage() {
  const { id = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const project = useProject(id)
  const resumen = useStudySummary(id)

  const motor = params.get('motor') ?? TODOS
  const familia = params.get('familia') ?? TODOS
  const intencion = params.get('intencion') ?? TODOS
  const ambito = params.get('ambito') ?? TODOS
  const ciudad = params.get('ciudad') ?? TODOS
  const ids = params.get('ids') ?? ''
  const q = params.get('q') ?? ''
  const pagina = Number(params.get('pagina') ?? '1') || 1
  const [busqueda, setBusqueda] = useState(q)
  const [abierta, setAbierta] = useState<string | null>(null)

  const setParam = (cambios: Record<string, string | null>, resetPagina = true) =>
    setParams((prev) => {
      const next = new URLSearchParams(prev)
      for (const [k, v] of Object.entries(cambios)) {
        if (v === null || v === TODOS || v === '') next.delete(k)
        else next.set(k, v)
      }
      if (resetPagina) next.delete('pagina')
      return next
    }, { replace: true })

  useEffect(() => {
    const t = setTimeout(() => { if (busqueda !== q) setParam({ q: busqueda }) }, 300)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busqueda])

  const lista = useExecutions(id, {
    motor: motor === TODOS ? undefined : motor,
    familia: familia === TODOS ? undefined : familia,
    intencion: intencion === TODOS ? undefined : intencion,
    ambito: ambito === TODOS ? undefined : ambito,
    ciudad: ciudad === TODOS ? undefined : ciudad,
    ids: ids || undefined,
    q: q || undefined,
    pagina,
    tamano: TAMANO,
  })

  const ciudades = resumen.data?.ciudades ?? []
  const idsFiltrados = ids ? ids.split(',').filter(Boolean) : []
  const hayFiltros = [motor, familia, intencion, ambito, ciudad].some((v) => v !== TODOS) || q !== '' || ids !== ''
  const totalPaginas = lista.data ? Math.max(1, Math.ceil(lista.data.total / lista.data.tamano)) : 1

  const filtros = (
    <div role="search" aria-label="Filtros de ejecuciones">
      <Input type="search" aria-label="Buscar en prompt y respuesta" placeholder="Buscar texto" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
      <Select ariaLabel="Motor" value={motor} onValueChange={(v) => setParam({ motor: v })} options={opciones('Todos los motores', MOTORES)} />
      <Select ariaLabel="Familia" value={familia} onValueChange={(v) => setParam({ familia: v })} options={opciones('Todas las familias', FAMILIAS)} />
      <Select ariaLabel="Intención" value={intencion} onValueChange={(v) => setParam({ intencion: v })} options={opciones('Todas las intenciones', INTENCIONES)} />
      <Select ariaLabel="Ámbito" value={ambito} onValueChange={(v) => setParam({ ambito: v })} options={AMBITOS} />
      {ciudades.length > 0 && <Select ariaLabel="Ciudad" value={ciudad} onValueChange={(v) => setParam({ ciudad: v })} options={opciones('Todas las ciudades', ciudades)} />}
      {hayFiltros && <Button onClick={() => { setBusqueda(''); setParams({}, { replace: true }) }}>Quitar filtros</Button>}
    </div>
  )

  return (
    <>
      <PageHeader title="Datos del estudio" description="Explora cada respuesta de los asistentes, con las marcas resaltadas y la evaluación del juez." />
      {resumen.data && (
        <p>
          {formatNum(resumen.data.ejecuciones)} ejecuciones · {resumen.data.motores.join(', ')} · {formatNum(resumen.data.repeticiones)} repeticiones ·{' '}
          {formatNum(resumen.data.prompts)} prompts · {formatNum(resumen.data.marcas)} marcas · {formatNum(resumen.data.espontaneas)} espontáneas y {formatNum(resumen.data.asistidas)} asistidas
        </p>
      )}
      {idsFiltrados.length > 0 && (
        <p role="status">
          Mostrando solo la evidencia seleccionada ({formatNum(idsFiltrados.length)} ejecuciones).{' '}
          <Button onClick={() => setParam({ ids: null })}>Ver todas</Button>
        </p>
      )}
      <Panel title="Ejecuciones">
        {lista.isError ? (
          isNotReady(lista.error) ? (
            <EmptyState title="Todavía no hay ejecuciones" description="Sube los datos del estudio o genera el estudio en vivo desde el asistente del proyecto." />
          ) : (
            <ErrorState error={lista.error} onRetry={() => void lista.refetch()} />
          )
        ) : lista.isPending ? (
          <p role="status">Cargando ejecuciones…</p>
        ) : (
          <>
            <DataTable columns={COLUMNAS} data={lista.data.filas} filters={filtros} onRowClick={(r) => setAbierta(r.ejecucion_id)} />
            {lista.data.filas.length === 0 && <EmptyState title="Sin resultados" description="Ninguna ejecución cumple los filtros actuales." action={<Button onClick={() => { setBusqueda(''); setParams({}, { replace: true }) }}>Quitar filtros</Button>} />}
            <nav aria-label="Paginación">
              <Button disabled={pagina <= 1} onClick={() => setParam({ pagina: String(pagina - 1) }, false)}>Anterior</Button>
              <span role="status"> Página {formatNum(lista.data.pagina)} de {formatNum(totalPaginas)} · {formatNum(lista.data.total)} ejecuciones </span>
              <Button disabled={pagina >= totalPaginas} onClick={() => setParam({ pagina: String(pagina + 1) }, false)}>Siguiente</Button>
            </nav>
          </>
        )}
      </Panel>
      <ExecutionDrawer projectId={id} marcaProyecto={project.data?.marca ?? ''} ejecucionId={abierta} onClose={() => setAbierta(null)} />
    </>
  )
}
