import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useProgress } from '@/api/hooks'
import type { Progress } from '@/api/types'
import { formatEur, formatNum } from '@/lib/format'
import { Chip, Skeleton, type Tone } from './display'
import { Button } from './primitives'

const ESTADO: Record<string, { tone: Tone; texto: string }> = {
  en_ejecucion: { tone: 'info', texto: 'En ejecución' },
  esperando_revision: { tone: 'warn', texto: 'Esperando tu revisión' },
  completado: { tone: 'good', texto: 'Completado' },
  error: { tone: 'bad', texto: 'Con error' },
  interrumpido: { tone: 'warn', texto: 'Interrumpido' },
}
const PASO_ESTADO: Record<string, string> = {
  pendiente: 'Pendiente', en_curso: 'En curso', hecho: 'Hecho', hecho_automatico: 'Hecho en modo automático', error: 'Error', esperando_revision: 'Esperando revisión',
}

export function formatDuration(s: number): string {
  const t = Math.max(0, Math.round(s))
  const m = Math.floor(t / 60)
  return m > 0 ? `${m} min ${String(t % 60).padStart(2, '0')} s` : `${t} s`
}

type Ev = Record<string, unknown>

/** Aplica un evento SSE al estado de progreso (contracts/events.md). */
export function applyEvent(prev: Progress | undefined, name: string, d: Ev): Progress | undefined {
  if (name === 'snapshot') return d as unknown as Progress
  if (!prev) return prev
  switch (name) {
    case 'step': {
      const paso = d.paso as string
      return { ...prev, paso_actual: d.estado === 'en_curso' ? paso : prev.paso_actual, pasos: prev.pasos.map((p) => (p.id === paso ? { ...p, ...(d as object), id: p.id, estado: d.estado as never } : p)) }
    }
    case 'counter':
      return { ...prev, contador: { paso: d.paso as string, hechos: d.hechos as number, total: d.total as number } }
    case 'cost':
      return { ...prev, llamadas: d.llamadas as number, coste_eur: d.coste_eur as number, coste_real: d.coste_real as boolean }
    case 'checkpoint':
      return { ...prev, estado: 'esperando_revision' }
    case 'done':
      return { ...prev, estado: d.estado as Progress['estado'], contador: null }
    default:
      return prev
  }
}

/** Consultas cuyo contenido depende de los pasos del análisis; se piden de nuevo cuando un paso termina. */
const RESULT_KEYS = ['project', 'plan', 'table', 'proposal', 'quality', 'traces', 'execution'] as const

/** Huella del avance: cambia cuando un paso cambia de estado o el trabajo se para, no con cada contador o coste. */
export function progressSignature(p: Progress | undefined): string {
  return p ? `${p.estado}|${p.pasos.map((s) => s.estado).join(',')}` : ''
}

/** Progreso en vivo del proyecto: SSE con caída a sondeo cada 2 s (contracts/events.md).
 *  Lo monta el shell una sola vez por proyecto y, cuando cambia el estado de algún paso, pide de nuevo los resultados:
 *  así una pantalla que se abrió antes de que su paso terminara (409) se actualiza sola. */
export function useLiveProgress(projectId: string): void {
  const qc = useQueryClient()

  useEffect(() => {
    let poll: number | undefined
    const key = ['progress', projectId]
    let firma = progressSignature(qc.getQueryData<Progress>(key))
    const unsubscribe = qc.getQueryCache().subscribe((ev) => {
      if (ev.type !== 'updated' || ev.query.queryHash !== JSON.stringify(key)) return
      const nueva = progressSignature(ev.query.state.data as Progress | undefined)
      if (firma && nueva && nueva !== firma) {
        for (const k of RESULT_KEYS) void qc.invalidateQueries({ queryKey: [k, projectId] })
      }
      if (nueva) firma = nueva
    })
    const startPolling = () => {
      if (poll) return
      poll = window.setInterval(() => void qc.invalidateQueries({ queryKey: key }), 2000)
    }
    const stop = () => { unsubscribe(); if (poll) window.clearInterval(poll) }
    if (typeof EventSource === 'undefined') { startPolling(); return stop }
    const es = new EventSource(`/api/projects/${projectId}/events`)
    for (const name of ['snapshot', 'step', 'counter', 'cost', 'checkpoint', 'done']) {
      es.addEventListener(name, (e) => {
        let d: Ev = {}
        try { d = JSON.parse((e as MessageEvent<string>).data) as Ev } catch { return }
        qc.setQueryData<Progress | undefined>(key, (prev) => applyEvent(prev, name, d))
      })
    }
    es.onerror = () => { es.close(); startPolling() }
    return () => { es.close(); stop() }
  }, [projectId, qc])
}

/** Panel de progreso; los datos en vivo los mantiene `useLiveProgress` desde el shell. */
export function ProgressPanel({ projectId, onResume, onRetryStep }: { projectId: string; onResume?: () => void; onRetryStep?: (paso: string) => void }) {
  const { data, isLoading } = useProgress(projectId)

  if (isLoading) return <div className="prog" aria-busy><Skeleton height={20} width="60%" /><Skeleton height={6} /><Skeleton height={120} /></div>
  if (!data) return null
  const estado = ESTADO[data.estado] ?? { tone: 'neutral' as Tone, texto: data.estado }
  const c = data.contador
  const pct = c && c.total > 0 ? c.hechos / c.total : 0
  return (
    <section className="prog" aria-label="Progreso del análisis">
      <div className="prog-summary" aria-live="polite">
        <Chip tone={estado.tone} dot>{estado.texto}</Chip>
        <span>Tiempo <b>{formatDuration(data.transcurrido_s)}</b></span>
        <span>Llamadas a IA <b>{formatNum(data.llamadas)}</b></span>
        <span>{data.coste_real ? 'Coste real' : 'Coste'} <b>{formatEur(data.coste_eur, 2)}</b></span>
        {data.estado === 'interrumpido' && onResume && <Button size="sm" variant="primary" onClick={onResume}>Reanudar</Button>}
      </div>
      {c && (
        <div>
          <div className="bar-label"><span>{data.pasos.find((p) => p.id === c.paso)?.nombre ?? c.paso}</span><span>{`${formatNum(c.hechos)} de ${formatNum(c.total)}`}</span></div>
          <div className="bar" role="progressbar" aria-valuemin={0} aria-valuemax={c.total} aria-valuenow={c.hechos} aria-label={`${c.hechos} de ${c.total}`}><i style={{ transform: `scaleX(${pct})` }} /></div>
        </div>
      )}
      <ol className="steps">
        {data.pasos.map((p) => (
          <li className="step" key={p.id} data-estado={p.estado} aria-current={p.estado === 'en_curso' ? 'step' : undefined}>
            <span className="step-icon" aria-hidden />
            <div>
              <div className="step-name">{p.nombre}</div>
              <div className="step-sub">
                {PASO_ESTADO[p.estado] ?? p.estado}
                {p.estado === 'hecho_automatico' && p.error ? `: ${p.error}` : ''}
                {p.estado === 'error' && p.error ? `: ${p.error}` : ''}
              </div>
              {p.estado === 'hecho_automatico' && onRetryStep && <div style={{ marginTop: 4 }}><Button size="sm" onClick={() => onRetryStep(p.id)}>Reintentar este paso</Button></div>}
            </div>
            <div className="step-end">{p.duracion_s != null && p.estado !== 'pendiente' ? `${p.duracion_s < 10 ? p.duracion_s.toFixed(1).replace('.', ',') : Math.round(p.duracion_s)} s` : ''}</div>
          </li>
        ))}
      </ol>
    </section>
  )
}
