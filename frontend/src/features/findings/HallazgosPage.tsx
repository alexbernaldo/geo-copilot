import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useProject } from '@/api/hooks'
import { CheckpointBar, EmptyState, ErrorState, PageHeader, PendingState } from '@/components'
import { formatNum } from '@/lib/format'
import { useApproveCheckpoint, useRecompute } from '@/features/data/checkpoints'
import { isNotReady } from '@/features/data/common'
import { RecalcConfirm } from '@/features/data/RecalcConfirm'
import { useFindings, usePatchFinding, type FindingPatch } from './api'
import { HallazgoCard } from './HallazgoCard'

/** Punto de control 2. */
export default function HallazgosPage() {
  const { id = '' } = useParams()
  const project = useProject(id)
  const findings = useFindings(id)
  const patch = usePatchFinding(id)
  const aprobar = useApproveCheckpoint(id)
  const recalcular = useRecompute(id)
  const [pendiente, setPendiente] = useState<{ hid: string; cambio: FindingPatch } | null>(null)

  if (findings.isPending) return <p role="status">Cargando hallazgos…</p>
  if (findings.isError) {
    return isNotReady(findings.error) ? (
      <>
        <PageHeader title="Hallazgos" />
        <PendingState step="Hallazgos" />
      </>
    ) : (
      <ErrorState error={findings.error} onRetry={() => void findings.refetch()} />
    )
  }

  const aprobado = project.data?.checkpoints.hallazgos ?? false
  const lista = [...findings.data].sort((a, b) => a.prioridad - b.prioridad)

  const pedir = (hid: string, cambio: FindingPatch) => {
    if (aprobado) setPendiente({ hid, cambio })
    else patch.mutate({ hid, cambio })
  }

  const confirmar = async (desdePaso: string, costeEur: number) => {
    if (!pendiente) return
    await patch.mutateAsync(pendiente)
    if (desdePaso) await recalcular.mutateAsync({ desde_paso: desdePaso, confirmo_coste: costeEur > 0 })
    setPendiente(null)
  }

  return (
    <>
      <PageHeader title="Hallazgos" description="Ordenados por prioridad. Cada cifra lleva su tabla de origen y las ejecuciones que la respaldan." checkpoint={{ n: 2, approved: aprobado }} />
      {patch.isError && <ErrorState error={patch.error} />}
      {pendiente && <RecalcConfirm id={id} cambio="findings" onConfirm={(p, c) => void confirmar(p, c)} onCancel={() => setPendiente(null)} />}
      {lista.length === 0 ? (
        <EmptyState title="Sin hallazgos" description="Los datos del estudio no han producido ningún hallazgo con evidencia suficiente." />
      ) : (
        <ol aria-label="Hallazgos por prioridad">
          {lista.map((h) => (
            <li key={h.id}>
              <HallazgoCard hallazgo={h} ocupado={patch.isPending} onPatch={(c) => pedir(h.id, c)} />
            </li>
          ))}
        </ol>
      )}
      <CheckpointBar
        n={2}
        approved={aprobado}
        onApprove={() => aprobar.mutate({ n: 2 })}
        summary={aprobado ? 'Los hallazgos están aprobados.' : `${formatNum(lista.length)} hallazgos por revisar. Al aprobarlos se desbloquea el plan.`}
      />
      {aprobar.isError && <ErrorState error={aprobar.error} />}
    </>
  )
}
