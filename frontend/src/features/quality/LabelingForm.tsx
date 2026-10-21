import { useEffect, useState } from 'react'
import { Button, Chip, ErrorState, Panel } from '@/components'
import { formatNum } from '@/lib/format'
import { type HumanLabel, useExecution, useSaveLabels } from './api'
import { highlight } from './text'

const MENCION = ['Recomendación activa', 'Comparación neutra', 'Pasiva']
const SENTIMIENTO = ['positivo', 'neutro', 'negativo']
const FUENTE = ['Ranking / institución', 'Medio', 'Web propia', 'Directorio / comparador', 'Plataforma de reseñas', 'Red social / foro', 'Sin fuente']

const field = 'rounded border border-[var(--brand-neutral)]/40 bg-transparent px-1.5 py-1 text-sm'
const btn = 'rounded border border-[var(--brand-neutral)]/40 px-3 py-1.5 text-sm disabled:opacity-50'

const keyOf = (eid: string, marca: string) => `${eid}\u0000${marca}`
const vacia = (eid: string, marca: string): HumanLabel => ({ ejecucion_id: eid, marca, aparece: false, posicion: null, tipo_mencion: null, fuerza: 0, sentimiento: null, tipo_fuente: null })

/** Motivo por el que una etiqueta no se puede guardar, o null si está completa. */
export function labelProblem(l: HumanLabel): string | null {
  if (!l.aparece) return null
  if (!l.tipo_mencion) return 'falta el tipo de mención'
  if (!l.sentimiento) return 'falta el sentimiento'
  if (!l.tipo_fuente) return 'falta el tipo de fuente'
  if (l.posicion == null || l.posicion < 1) return 'falta la posición'
  return null
}

function Choice({ label, value, options, onChange }: { label: string; value: string | null | undefined; options: string[]; onChange: (v: string | null) => void }) {
  return (
    <label className="grid gap-1 text-xs">
      {label}
      <select className={field} value={value ?? ''} onChange={(e) => onChange(e.target.value || null)}>
        <option value="">Sin indicar</option>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  )
}

export function LabelingForm({ projectId, muestra }: { projectId: string; muestra: string[] }) {
  const [index, setIndex] = useState(0)
  const [labels, setLabels] = useState<Record<string, HumanLabel>>({})
  const [problemas, setProblemas] = useState<string[]>([])
  const save = useSaveLabels(projectId)
  const eid = muestra[index]
  const det = useExecution(projectId, eid)
  const [marcasPor, setMarcasPor] = useState<Record<string, string[]>>({})
  const detData = det.data
  useEffect(() => {
    if (!eid || !detData) return
    const lista = detData.fila.marcas_a_evaluar ?? detData.evaluaciones.map((e) => e.marca)
    setMarcasPor((p) => (p[eid] ? p : { ...p, [eid]: lista }))
  }, [eid, detData])

  if (!eid) return <Panel title="Evaluar a mano"><p className="text-sm">No hay ejecuciones para etiquetar.</p></Panel>

  const marcas = det.data?.fila.marcas_a_evaluar ?? det.data?.evaluaciones.map((e) => e.marca) ?? []
  const get = (marca: string) => labels[keyOf(eid, marca)] ?? vacia(eid, marca)
  const set = (marca: string, patch: Partial<HumanLabel>) => setLabels((p) => ({ ...p, [keyOf(eid, marca)]: { ...get(marca), ...patch } }))

  const submit = () => {
    // Una ejecución cuenta como revisada cuando se ha abierto; las marcas sin tocar se guardan como «no aparece».
    const todas = muestra.flatMap((e) => (marcasPor[e] ?? []).map((m) => labels[keyOf(e, m)] ?? vacia(e, m)))
    const errores = todas.flatMap((l) => { const p = labelProblem(l); return p ? [`${l.ejecucion_id} · ${l.marca}: ${p}`] : [] })
    const sinTocar = muestra.filter((e) => !marcasPor[e])
    if (sinTocar.length) errores.push(`Faltan por revisar: ${sinTocar.join(', ')}`)
    setProblemas(errores)
    if (errores.length === 0) save.mutate(todas)
  }

  return (
    <Panel
      title="Evaluar a mano"
      source={<span className="text-xs text-[var(--brand-neutral)]">{`Ejecución ${index + 1} de ${formatNum(muestra.length)} · ${eid}`}</span>}
    >
      <p className="mb-3 max-w-[72ch] text-sm">Marca para cada marca si aparece en la respuesta y cómo. Tus etiquetas se guardan como muestra evaluada del proyecto y permiten calcular la exactitud del juez.</p>
      {det.isPending ? <p role="status">Cargando la ejecución…</p> : det.isError ? <ErrorState error={det.error} onRetry={() => void det.refetch()} /> : (
        <div className="grid gap-4">
          <div className="grid gap-1 text-sm">
            <p className="text-[var(--brand-neutral)]">{`${det.data.fila.motor}${det.data.fila.ciudad ? ` · ${det.data.fila.ciudad}` : ''}`}</p>
            <p><strong>Prompt: </strong>{det.data.fila.prompt}</p>
            <blockquote className="max-h-72 max-w-[72ch] overflow-y-auto whitespace-pre-wrap rounded border border-[var(--brand-neutral)]/30 p-3">{det.data.respuesta}</blockquote>
          </div>
          <ul className="grid gap-3">
            {marcas.map((marca) => {
              const l = get(marca)
              return (
                <li key={marca} className="grid gap-2 rounded border border-[var(--brand-neutral)]/30 p-3">
                  <label className="flex items-center gap-2 text-sm font-medium">
                    <input type="checkbox" checked={l.aparece} onChange={(e) => set(marca, { aparece: e.target.checked })} />
                    <span>{highlight(marca, marca)}</span>
                    <span className="font-normal text-[var(--brand-neutral)]">aparece en la respuesta</span>
                  </label>
                  {l.aparece && (
                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                      <label className="grid gap-1 text-xs">Posición<input className={field} type="number" min={1} value={l.posicion ?? ''} onChange={(e) => set(marca, { posicion: e.target.value === '' ? null : Number(e.target.value) })} /></label>
                      <Choice label="Tipo de mención" value={l.tipo_mencion} options={MENCION} onChange={(v) => set(marca, { tipo_mencion: v })} />
                      <label className="grid gap-1 text-xs">Fuerza
                        <select className={field} value={l.fuerza} onChange={(e) => set(marca, { fuerza: Number(e.target.value) })}>{[0, 1, 2, 3].map((n) => <option key={n} value={n}>{n}</option>)}</select>
                      </label>
                      <Choice label="Sentimiento" value={l.sentimiento} options={SENTIMIENTO} onChange={(v) => set(marca, { sentimiento: v })} />
                      <Choice label="Tipo de fuente" value={l.tipo_fuente} options={FUENTE} onChange={(v) => set(marca, { tipo_fuente: v })} />
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button className={btn} disabled={index === 0} onClick={() => setIndex(index - 1)}>Anterior</Button>
        <Button className={btn} disabled={index === muestra.length - 1} onClick={() => setIndex(index + 1)}>Siguiente</Button>
        <Button className={`${btn} border-[var(--brand-project)]`} disabled={save.isPending} onClick={submit}>{save.isPending ? 'Guardando…' : 'Guardar etiquetas'}</Button>
        {save.isSuccess && <Chip tone="good">Etiquetas guardadas</Chip>}
      </div>
      {problemas.length > 0 && (
        <ul role="alert" className="mt-3 grid gap-1 text-sm">{problemas.map((p) => <li key={p}>{p}</li>)}</ul>
      )}
      {save.isError && <ErrorState error={save.error} />}
    </Panel>
  )
}
