import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useProgress } from '@/api/hooks'
import type { Progress } from '@/api/types'
import { formatEur } from '@/lib/format'

/** Progreso en vivo: SSE con caída a sondeo cada 2 s (contracts/events.md). */
export function ProgressPanel({ projectId }: { projectId: string }) {
  const qc = useQueryClient()
  const { data } = useProgress(projectId)

  useEffect(() => {
    let poll: number | undefined
    const es = new EventSource(`/api/projects/${projectId}/events`)
    es.addEventListener('snapshot', (e) => qc.setQueryData(['progress', projectId], JSON.parse((e as MessageEvent<string>).data) as Progress))
    for (const ev of ['step', 'counter', 'cost', 'checkpoint', 'done']) {
      es.addEventListener(ev, () => void qc.invalidateQueries({ queryKey: ['progress', projectId] }))
    }
    es.onerror = () => {
      es.close()
      poll = window.setInterval(() => void qc.invalidateQueries({ queryKey: ['progress', projectId] }), 2000)
    }
    return () => { es.close(); if (poll) window.clearInterval(poll) }
  }, [projectId, qc])

  if (!data) return null
  return (
    <section aria-label="Progreso">
      <p>{`Estado: ${data.estado} · ${data.llamadas} llamadas · ${formatEur(data.coste_eur, 2)}`}</p>
      {data.contador && <progress value={data.contador.hechos} max={data.contador.total} aria-label={`${data.contador.hechos} de ${data.contador.total}`} />}
      <ol>{data.pasos.map((p) => <li key={p.id}>{`${p.nombre}: ${p.estado}`}</li>)}</ol>
    </section>
  )
}
