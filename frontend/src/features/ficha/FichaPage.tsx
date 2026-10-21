import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useProject } from '@/api/hooks'
import { Chip, CheckpointBar, EmptyState, ErrorState, Markdown, PageHeader, Panel, PendingState } from '@/components'
import { useApproveCheckpoint, useRecompute } from '@/features/data/checkpoints'
import { isNotReady } from '@/features/data/common'
import { RecalcConfirm } from '@/features/data/RecalcConfirm'
import { useFicha, useSaveFicha } from './api'
import { FichaForm } from './FichaForm'
import { fichaToForm, formToFicha, type FichaFormValues } from './fichaValores'

/** Punto de control 0. */
export default function FichaPage() {
  const { id = '' } = useParams()
  const project = useProject(id)
  const ficha = useFicha(id)
  const guardar = useSaveFicha(id)
  const aprobar = useApproveCheckpoint(id)
  const recalcular = useRecompute(id)
  const [sucio, setSucio] = useState(false)
  const [pendiente, setPendiente] = useState<FichaFormValues | null>(null)
  const valores = useMemo(() => (ficha.data ? fichaToForm(ficha.data.ficha) : null), [ficha.data])

  if (ficha.isPending) return <p role="status">Cargando la ficha…</p>
  if (ficha.isError) {
    return isNotReady(ficha.error) ? (
      <>
        <PageHeader title="Ficha" />
        <PendingState step="Ficha" />
      </>
    ) : (
      <ErrorState error={ficha.error} onRetry={() => void ficha.refetch()} />
    )
  }
  if (!valores) return null

  const aprobada = project.data?.checkpoints.ficha ?? ficha.data.aprobada
  const faltantes = ficha.data.faltantes
  const brief = ficha.data.brief_texto

  const onSubmit = (v: FichaFormValues) => {
    if (aprobada) setPendiente(v)
    else guardar.mutate(formToFicha(v))
  }

  const confirmar = async (desdePaso: string, costeEur: number) => {
    if (!pendiente) return
    await guardar.mutateAsync(formToFicha(pendiente))
    if (desdePaso) await recalcular.mutateAsync({ desde_paso: desdePaso, confirmo_coste: costeEur > 0 })
    setPendiente(null)
  }

  return (
    <>
      <PageHeader title="Ficha" description="Revisa lo que se ha extraído del brief antes de seguir. Todo lo que cambies se usará en el resto del análisis." checkpoint={{ n: 0, approved: aprobada }} />
      {faltantes.length > 0 && (
        <p role="status">
          <Chip tone="warn">Faltan datos</Chip> Completa los campos marcados como «Falta» antes de aprobar la ficha.
        </p>
      )}
      {guardar.isError && <ErrorState error={guardar.error} />}
      {recalcular.isError && <ErrorState error={recalcular.error} />}
      {pendiente && <RecalcConfirm id={id} cambio="ficha" onConfirm={(p, c) => void confirmar(p, c)} onCancel={() => setPendiente(null)} />}
      <div>
        <FichaForm
          valores={valores}
          faltantes={faltantes}
          origenCampos={ficha.data.origen_campos ?? {}}
          guardando={guardar.isPending}
          onSubmit={onSubmit}
          onDirtyChange={setSucio}
        />
        <aside aria-label="Brief original">
          <Panel title="Brief original">
            {brief ? <Markdown source={brief} /> : <EmptyState title="Sin brief" description="Este proyecto no tiene un brief de cliente (por ejemplo, un prospecto)." />}
          </Panel>
        </aside>
      </div>
      <CheckpointBar
        n={0}
        approved={aprobada}
        onApprove={() => { if (!sucio) aprobar.mutate({ n: 0 }) }}
        summary={sucio ? 'Hay cambios sin guardar: guárdalos antes de aprobar la ficha.' : aprobada ? 'La ficha está aprobada.' : 'Aprueba la ficha para desbloquear la competencia.'}
      />
      {aprobar.isError && <ErrorState error={aprobar.error} />}
    </>
  )
}
