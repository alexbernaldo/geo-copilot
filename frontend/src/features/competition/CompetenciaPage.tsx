import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import type { ColumnDef } from '@tanstack/react-table'
import { useProject } from '@/api/hooks'
import type { ContrasteMercado } from '@/api/types'
import { Button, Checkbox, Chip, CheckpointBar, DataTable, EmptyState, ErrorState, PageHeader, Panel, PendingState, Select } from '@/components'
import { useApproveCheckpoint, useRecompute } from '@/features/data/checkpoints'
import { isNotReady, pct, ROLES_MARCA } from '@/features/data/common'
import { RecalcConfirm } from '@/features/data/RecalcConfirm'
import { useMarket, useSaveMarket } from './api'

type Marca = ContrasteMercado['marcas'][number]
type Rol = Marca['rol']

const OPCIONES_ROL = (Object.keys(ROLES_MARCA) as Rol[]).map((r) => ({ value: r, label: ROLES_MARCA[r] }))

function Editor({ id, inicial, aprobado }: { id: string; inicial: ContrasteMercado; aprobado: boolean }) {
  const [borrador, setBorrador] = useState<ContrasteMercado>(inicial)
  const [confirmando, setConfirmando] = useState(false)
  const guardar = useSaveMarket(id)
  const aprobar = useApproveCheckpoint(id)
  const recalcular = useRecompute(id)
  const sucio = useMemo(() => JSON.stringify(borrador) !== JSON.stringify(inicial), [borrador, inicial])

  const cambiar = (nombre: string, parche: Partial<Marca>) =>
    setBorrador((b) => ({ ...b, marcas: b.marcas.map((m) => (m.nombre === nombre ? { ...m, ...parche } : m)) }))

  const anadirCandidata = (nombre: string) =>
    setBorrador((b) => ({
      ...b,
      marcas: [...b.marcas, { nombre, rol: 'contexto', declarada_en_brief: false, detectada_en_datos: false, tasa_aparicion_espontanea: 0, nota: 'Añadida al estudio; se calculará al recalcular.' }],
      candidatas_no_catalogadas: (b.candidatas_no_catalogadas ?? []).filter((c) => c !== nombre),
    }))

  const columnas: ColumnDef<Marca, unknown>[] = [
    { header: 'Marca', accessorKey: 'nombre' },
    {
      header: 'Rol',
      cell: ({ row }) => (
        <Select ariaLabel={`Rol de ${row.original.nombre}`} value={row.original.rol} onValueChange={(v) => cambiar(row.original.nombre, { rol: v as Rol })} options={OPCIONES_ROL} />
      ),
    },
    { header: 'En el brief', cell: ({ row }) => <Chip tone={row.original.declarada_en_brief ? 'good' : 'neutral'}>{row.original.declarada_en_brief ? 'Declarada' : 'No declarada'}</Chip> },
    { header: 'En los datos', cell: ({ row }) => <Chip tone={row.original.detectada_en_datos ? 'good' : 'warn'}>{row.original.detectada_en_datos ? 'Aparece' : 'Sin datos aún'}</Chip> },
    { header: 'Aparición espontánea', accessorFn: (m) => (m.detectada_en_datos ? pct(m.tasa_aparicion_espontanea) : '—') },
    {
      header: 'Excluir del análisis',
      cell: ({ row }) => <Checkbox label={`Excluir ${row.original.nombre}`} checked={row.original.excluida ?? false} onCheckedChange={(c) => cambiar(row.original.nombre, { excluida: c })} />,
    },
    { header: 'Nota', accessorFn: (m) => m.nota ?? '' },
  ]

  const guardarYRecalcular = async (desdePaso: string, costeEur: number) => {
    await guardar.mutateAsync(borrador)
    if (desdePaso) await recalcular.mutateAsync({ desde_paso: desdePaso, confirmo_coste: costeEur > 0 })
    setConfirmando(false)
  }

  return (
    <>
      {inicial.discrepancias_brief.length > 0 && (
        <Panel title="Discrepancias entre el brief y los datos">
          <ul>
            {inicial.discrepancias_brief.map((d) => <li key={d}>{d}</li>)}
          </ul>
        </Panel>
      )}
      <Panel
        title="Marcas del estudio"
        actions={
          <Button
            disabled={!sucio || guardar.isPending}
            onClick={() => (aprobado ? setConfirmando(true) : guardar.mutate(borrador))}
          >
            Guardar cambios
          </Button>
        }
      >
        {confirmando && <RecalcConfirm id={id} cambio="market" onConfirm={(p, c) => void guardarYRecalcular(p, c)} onCancel={() => setConfirmando(false)} />}
        {borrador.marcas.length === 0 ? (
          <EmptyState title="Sin marcas" description="El estudio no contiene ninguna marca." />
        ) : (
          <DataTable columns={columnas} data={borrador.marcas} />
        )}
        {guardar.isError && <ErrorState error={guardar.error} />}
      </Panel>
      <Panel title="Marcas candidatas no catalogadas">
        {(borrador.candidatas_no_catalogadas ?? []).length === 0 ? (
          <p>No se han detectado marcas nuevas en las respuestas.</p>
        ) : (
          <ul>
            {(borrador.candidatas_no_catalogadas ?? []).map((c) => (
              <li key={c}>
                {c} <Button aria-label={`Añadir ${c} al estudio`} onClick={() => anadirCandidata(c)}>Añadir al estudio</Button>
              </li>
            ))}
          </ul>
        )}
        <p><small>Añadir una marca recalcula la detección, el juez y todo lo posterior.</small></p>
      </Panel>
      <CheckpointBar
        n={1}
        approved={aprobado}
        onApprove={() => { if (!sucio) aprobar.mutate({ n: 1 }) }}
        summary={sucio ? 'Hay cambios sin guardar: guárdalos antes de aprobar la competencia.' : aprobado ? 'La competencia está aprobada.' : 'Revisa los roles y aprueba la competencia para generar los hallazgos.'}
      />
      {aprobar.isError && <ErrorState error={aprobar.error} />}
    </>
  )
}

/** Punto de control 1. */
export default function CompetenciaPage() {
  const { id = '' } = useParams()
  const project = useProject(id)
  const market = useMarket(id)

  if (market.isPending) return <p role="status">Cargando la competencia…</p>
  if (market.isError) {
    return isNotReady(market.error) ? (
      <>
        <PageHeader title="Competencia" />
        <PendingState step="Mercado" />
      </>
    ) : (
      <ErrorState error={market.error} onRetry={() => void market.refetch()} />
    )
  }
  const aprobado = project.data?.checkpoints.competencia ?? market.data.aprobado_por_humano
  return (
    <>
      <PageHeader title="Competencia" description="Define quién cuenta como competidor. Los avisos comparan lo que dice el brief con lo que aparece en los datos." checkpoint={{ n: 1, approved: aprobado }} />
      <Editor key={market.dataUpdatedAt} id={id} inicial={market.data} aprobado={aprobado} />
    </>
  )
}
