import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button, Chart, Chip, CheckpointBar, EmptyState, ErrorState, PageHeader, Panel, PendingState } from '@/components'
import { useProject } from '@/api/hooks'
import { formatEur, formatNum } from '@/lib/format'
import { ActionsTable } from './ActionsTable'
import { type PlanAccion, type PlanData, type SimulateResult, useApprovePlan, usePlan, useSavePlan, useSimulate, useTable } from './api'
import { buildBaseline } from './baseline'
import { cargaOption, ganttOption } from './charts'
import { isPending } from './http'
import { EffortImpactMatrix } from './Matrix'
import { Simulator } from './Simulator'
import { useChartColors } from './theme'

const NIVEL_TONO = { error: 'bad', aviso: 'warn', info: 'info' } as const

export default function PlanPage() {
  const { id = '' } = useParams()
  const project = useProject(id)
  const planQ = usePlan(id)
  const save = useSavePlan(id)
  const approve = useApprovePlan(id)
  const simulate = useSimulate(id)
  const colors = useChartColors()
  const [draft, setDraft] = useState<PlanData | null>(null)

  const server = planQ.data
  useEffect(() => { if (server) setDraft(server.plan) }, [server])

  const marca = project.data?.marca ?? ''
  const t1 = useTable(id, 'T1')
  const t2 = useTable(id, 'T2')
  const t4 = useTable(id, 'T4')
  // Una simulación sin cambios devuelve la línea base completa en `detalle` (parametros_base).
  const baseSim = useSimulate(id)
  const loadBase = baseSim.mutate
  useEffect(() => { if (server) loadBase({}) }, [server, loadBase])
  const baseline = useMemo(
    () => buildBaseline(marca, t1.data, t2.data, t4.data, baseSim.data?.detalle),
    [marca, t1.data, t2.data, t4.data, baseSim.data],
  )

  const edit = useCallback((accionId: string, patch: Partial<PlanAccion>) => {
    setDraft((d) => (d ? { ...d, acciones: d.acciones.map((a) => (a.id === accionId ? { ...a, ...patch } : a)) } : d))
  }, [])

  if (planQ.isPending) return <><PageHeader title="Plan" /><p role="status">Cargando el plan…</p></>
  if (planQ.isError) {
    return (
      <>
        <PageHeader title="Plan" />
        {isPending(planQ.error) ? <PendingState step="Estrategia" /> : <ErrorState error={planQ.error} onRetry={() => void planQ.refetch()} />}
      </>
    )
  }
  if (!draft || !server) return null

  const dirty = JSON.stringify(draft) !== JSON.stringify(server.plan)
  const hayErrores = server.avisos.some((a) => a.nivel === 'error')
  const bloqueado = dirty || hayErrores
  const useAsObjective = (r: SimulateResult) => {
    setDraft((d) => d && {
      ...d,
      objetivos: [
        ...d.objetivos.filter((o) => !o.kpi.startsWith('Escenario simulado')),
        { kpi: 'Escenario simulado · Score de Citación espontáneo', valor_actual: r.score_actual, valor_objetivo_min: r.score_simulado, valor_objetivo_max: r.score_simulado, plazo_meses: 12, hallazgos: [] },
      ],
    })
  }

  const acciones = draft.acciones
  const presupuesto = server.presupuesto_max_eur ?? null

  return (
    <div className="grid min-w-0 gap-6 [&>*]:min-w-0">
      <PageHeader
        title="Plan"
        description="Objetivos, acciones y cronograma. Al guardar, el backend revalida presupuesto, capacidad y dependencias."
        checkpoint={{ n: 3, approved: server.aprobado }}
        actions={
          <div className="flex items-center gap-3">
            {dirty && <Chip tone="warn">Cambios sin guardar</Chip>}
            <Button className="rounded border border-[var(--brand-project)] px-3 py-1.5 text-sm disabled:opacity-50" disabled={!dirty || save.isPending} onClick={() => save.mutate(draft)}>
              {save.isPending ? 'Guardando…' : 'Guardar cambios'}
            </Button>
            {dirty && <Button className="rounded border border-[var(--brand-neutral)]/40 px-3 py-1.5 text-sm" onClick={() => setDraft(server.plan)}>Descartar cambios</Button>}
          </div>
        }
      />
      {save.isError && <ErrorState error={save.error} />}

      {server.avisos.length > 0 && (
        <Panel title="Avisos de revalidación">
          <ul className="grid gap-2" aria-label="Avisos del backend">
            {server.avisos.map((a) => (
              <li key={`${a.accion_id ?? 'plan'}-${a.texto}`} className="flex items-start gap-2 text-sm">
                <Chip tone={NIVEL_TONO[a.nivel]}>{a.nivel === 'error' ? 'Error' : a.nivel === 'aviso' ? 'Aviso' : 'Info'}</Chip>
                <span>{a.accion_id ? <strong>{a.accion_id}: </strong> : null}{a.texto}</span>
              </li>
            ))}
          </ul>
        </Panel>
      )}

      <Panel title="Objetivos" source={<span className="text-xs text-[var(--brand-neutral)]">Valores calculados por el backend</span>}>
        {draft.objetivos.length === 0 ? <EmptyState title="Sin objetivos" description="El plan no tiene objetivos definidos." /> : (
          <table className="w-full text-sm">
            <thead><tr className="text-left"><th scope="col">KPI</th><th scope="col" className="text-right">Actual</th><th scope="col" className="text-right">Objetivo</th><th scope="col" className="text-right">Plazo</th><th scope="col" className="pl-3">Hallazgos</th></tr></thead>
            <tbody>
              {draft.objetivos.map((o) => (
                <tr key={o.kpi} className="border-t border-[var(--brand-neutral)]/30 align-top">
                  <td className="py-1.5 pr-3">{o.kpi}</td>
                  <td className="text-right tabular-nums">{formatNum(o.valor_actual, 1)}</td>
                  <td className="text-right tabular-nums">{o.valor_objetivo_min === o.valor_objetivo_max ? formatNum(o.valor_objetivo_min, 1) : `${formatNum(o.valor_objetivo_min, 1)} – ${formatNum(o.valor_objetivo_max, 1)}`}</td>
                  <td className="text-right tabular-nums">{`${o.plazo_meses} meses`}</td>
                  <td className="pl-3">{o.hallazgos.length ? o.hallazgos.join(', ') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      <Panel title="Presupuesto" source={<span className="text-xs text-[var(--brand-neutral)]">Plan guardado</span>}>
        <div className="grid gap-1">
          {presupuesto !== null
            ? <meter className="h-3 w-full" min={0} max={presupuesto} value={server.plan.coste_total_eur} aria-label="Presupuesto usado frente al máximo del brief" />
            : null}
          <p className="text-sm tabular-nums">
            {formatEur(server.plan.coste_total_eur)} en el plan
            {presupuesto !== null && server.presupuesto_min_eur != null ? ` · horquilla del brief: ${formatEur(server.presupuesto_min_eur)} – ${formatEur(presupuesto)}` : ' · el brief no indica horquilla'}
          </p>
          {dirty && <p className="text-xs text-[var(--brand-neutral)]">Los costes editados se recalculan al guardar.</p>}
        </div>
      </Panel>

      <Panel title="Acciones" source={<span className="text-xs text-[var(--brand-neutral)]">{`${formatNum(acciones.length)} acciones`}</span>}>
        {acciones.length === 0 ? <EmptyState title="Sin acciones" description="El plan no tiene acciones." /> : <ActionsTable acciones={acciones} avisos={server.avisos} onEdit={edit} />}
      </Panel>

      {acciones.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Panel title="Matriz esfuerzo / impacto"><EffortImpactMatrix acciones={acciones} /></Panel>
          <Panel title="Carga semanal del equipo del cliente">
            {server.carga_semanal && server.carga_semanal.length > 0 ? (
              <Chart
                option={cargaOption(server.carga_semanal, colors)}
                height={280}
                ariaLabel="Horas semanales del equipo del cliente frente a su capacidad"
                tableFallback={
                  <table className="text-sm"><thead><tr><th scope="col">Semana</th><th scope="col">Horas</th><th scope="col">Capacidad</th></tr></thead>
                    <tbody>{server.carga_semanal.map((s) => <tr key={s.semana}><td>{s.semana}</td><td>{formatNum(s.horas, 1)}</td><td>{formatNum(s.capacidad, 1)}</td></tr>)}</tbody>
                  </table>
                }
              />
            ) : <EmptyState title="Sin carga semanal" description="El backend no ha devuelto la carga del equipo del cliente para este plan." />}
          </Panel>
        </div>
      )}

      {acciones.length > 0 && (
        <Panel title="Cronograma por semanas">
          <Chart
            option={ganttOption(acciones, colors)}
            height={96 + 24 * acciones.length}
            ariaLabel="Cronograma de las acciones por semana, coloreado por fase del plan"
            tableFallback={
              <table className="text-sm"><thead><tr><th scope="col">Acción</th><th scope="col">Fase</th><th scope="col">Inicio (sem.)</th><th scope="col">Duración (sem.)</th></tr></thead>
                <tbody>{acciones.map((a) => <tr key={a.id}><td>{`${a.id} · ${a.titulo}`}</td><td>{a.fase_plan}</td><td>{a.semana_inicio}</td><td>{a.plazo_semanas}</td></tr>)}</tbody>
              </table>
            }
          />
          <ol className="mt-3 grid gap-1 text-sm">
            {draft.fases.map((f) => <li key={f.numero}><strong>{f.nombre}</strong>{` · semanas ${f.semanas.join(' a ')} · ${f.objetivo}`}</li>)}
          </ol>
        </Panel>
      )}

      <Simulator
        baseline={baseline}
        result={simulate.data}
        pending={simulate.isPending}
        error={simulate.isError ? simulate.error : null}
        onSimulate={simulate.mutate}
        onUse={useAsObjective}
      />

      {bloqueado ? (
        <p role="status" className="rounded border border-[var(--brand-neutral)]/40 p-3 text-sm">
          {dirty ? 'Guarda los cambios para poder aprobar el plan.' : 'Resuelve los errores de revalidación para poder aprobar el plan.'}
        </p>
      ) : (
        <CheckpointBar n={3} approved={server.aprobado} onApprove={() => approve.mutate()} summary={`${formatNum(acciones.length)} acciones · ${formatEur(server.plan.coste_total_eur)}`} />
      )}
      {approve.isError && <ErrorState error={approve.error} />}
    </div>
  )
}
