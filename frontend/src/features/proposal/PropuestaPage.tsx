import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Button, Chip, CostConfirm, EmptyState, ErrorState, Markdown, OriginTag, PageHeader, Panel, PendingState, ProgressPanel, Tabs } from '@/components'
import { useProgress } from '@/api/hooks'
import { isPending } from '@/features/plan/http'
import { formatNum } from '@/lib/format'
import { exportUrl, type Proposal, useProposal, useRegenerate, useRegenerateEstimate } from './api'
import { Seal } from './Seal'

const link = 'rounded border border-[var(--brand-neutral)]/40 px-3 py-1.5 text-sm'

function Document({ proposal }: { proposal: Proposal }) {
  if (proposal.secciones.length === 0) return <EmptyState title="Sin secciones" description="La propuesta todavía no tiene secciones redactadas." />
  return (
    <div className="grid gap-8 lg:grid-cols-[13rem_minmax(0,1fr)]">
      <nav aria-label="Índice de la propuesta" className="lg:sticky lg:top-4 lg:self-start">
        <ol className="grid gap-1 text-sm">
          {proposal.secciones.map((s) => <li key={s.id}><a className="underline-offset-2 hover:underline focus-visible:underline" href={`#seccion-${s.id}`}>{s.titulo}</a></li>)}
        </ol>
      </nav>
      <div className="grid gap-8">
        {proposal.secciones.map((s) => (
          <article key={s.id} id={`seccion-${s.id}`} className="scroll-mt-4 grid gap-2">
            <header className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold">{s.titulo}</h2>
              <OriginTag origen={s.origen.origen} modelo={s.origen.modelo} />
            </header>
            <div className="min-w-0 max-w-full overflow-x-auto [&_p]:my-2 [&_p]:max-w-[72ch] [&_table]:my-3 [&_table]:text-sm [&_td]:border [&_td]:border-[var(--brand-neutral)]/30 [&_td]:p-1.5 [&_th]:border [&_th]:border-[var(--brand-neutral)]/30 [&_th]:p-1.5 [&_th]:text-left [&_ul]:list-disc [&_ul]:pl-5">
              <Markdown source={s.markdown} />
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

function Email({ correo }: { correo: NonNullable<Proposal['correo']> }) {
  const [copied, setCopied] = useState<'ok' | 'error' | null>(null)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`Asunto: ${correo.asunto}\n\n${correo.cuerpo}`)
      setCopied('ok')
    } catch {
      setCopied('error')
    }
  }
  return (
    <Panel title="Correo comercial" actions={<Button className={link} onClick={() => void copy()}>Copiar correo</Button>}>
      <p className="text-sm"><span className="text-[var(--brand-neutral)]">Asunto: </span><strong>{correo.asunto}</strong></p>
      <pre className="mt-3 max-w-[72ch] whitespace-pre-wrap font-[inherit] text-sm">{correo.cuerpo}</pre>
      <p role="status" className="mt-2 text-sm">{copied === 'ok' ? 'Correo copiado al portapapeles.' : copied === 'error' ? 'No se ha podido copiar; selecciona el texto a mano.' : ''}</p>
    </Panel>
  )
}

export default function PropuestaPage() {
  const { id = '' } = useParams()
  const q = useProposal(id)
  const [confirming, setConfirming] = useState(false)
  const estimate = useRegenerateEstimate(id, confirming)
  const regenerate = useRegenerate(id)
  const progress = useProgress(id)
  const qc = useQueryClient()
  const running = progress.data?.estado === 'en_ejecucion'

  useEffect(() => {
    if (progress.data?.estado === 'completado') void qc.invalidateQueries({ queryKey: ['proposal', id] })
  }, [progress.data?.estado, qc, id])

  if (q.isPending) return <><PageHeader title="Propuesta" /><p role="status">Cargando la propuesta…</p></>
  if (q.isError) {
    return (
      <>
        <PageHeader title="Propuesta" />
        {isPending(q.error) ? <PendingState step="Redacción" /> : <ErrorState error={q.error} onRetry={() => void q.refetch()} />}
      </>
    )
  }

  const p = q.data
  const items = [{ value: 'documento', label: p.modo === 'prospecto' ? 'Propuesta al prospecto' : 'Documento del cliente', content: <Document proposal={p} /> }]
  if (p.correo) items.push({ value: 'correo', label: 'Correo comercial', content: <Email correo={p.correo} /> })

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Propuesta"
        description={`${p.marca} · ${p.modo === 'prospecto' ? 'modo prospecto' : 'modo cliente'} · ${formatNum(p.secciones.length)} secciones`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button className={`${link} disabled:opacity-50`} disabled={running || regenerate.isPending} onClick={() => setConfirming(true)}>Regenerar redacción</Button>
            {(p.exportaciones ?? []).includes('docx') && <a className={link} href={exportUrl(id, 'docx')} download>Descargar .docx</a>}
            {(p.exportaciones ?? []).includes('md') && <a className={link} href={exportUrl(id, 'md')} download>Descargar .md</a>}
          </div>
        }
      />

      {confirming && (
        <Panel title="Regenerar redacción">
          {estimate.isPending ? <p role="status">Calculando el coste previsto…</p> : estimate.isError ? <ErrorState error={estimate.error} onRetry={() => void estimate.refetch()} /> : (
            <CostConfirm
              estimate={estimate.data}
              onCancel={() => setConfirming(false)}
              onConfirm={() => { regenerate.mutate(undefined, { onSettled: () => setConfirming(false) }) }}
            />
          )}
        </Panel>
      )}
      {regenerate.isError && <ErrorState error={regenerate.error} />}
      {running && <ProgressPanel projectId={id} />}

      <Seal seal={p.sello} />
      {p.sello.aprobado === false && <Chip tone="bad">El revisor no ha aprobado esta propuesta</Chip>}

      <Tabs items={items} />
    </div>
  )
}
