import { useState } from 'react'
import { Button, EmptyState, ErrorState, Panel } from '@/components'
import { formatNum } from '@/lib/format'
import { type Discrepancy, useResolveDiscrepancy } from './api'
import { highlight, showValue } from './text'

const btn = 'rounded border border-[var(--brand-neutral)]/40 px-3 py-1.5 text-sm disabled:opacity-50'

function Item({ d, projectId }: { d: Discrepancy; projectId: string }) {
  const resolve = useResolveDiscrepancy(projectId)
  const [choice, setChoice] = useState<'reglas' | 'llm' | null>(null)
  const campos = [...new Set([...Object.keys(d.reglas), ...Object.keys(d.llm)])]
  const group = `disc-${d.ejecucion_id}-${d.marca}`
  return (
    <li className="grid gap-3 rounded border border-[var(--brand-neutral)]/30 p-4">
      <p className="text-sm"><strong>{d.marca}</strong><span className="text-[var(--brand-neutral)]">{` · ${d.ejecucion_id}`}</span></p>
      {d.respuesta && <blockquote className="max-h-40 max-w-[72ch] overflow-y-auto whitespace-pre-wrap text-sm">{highlight(d.respuesta, d.marca)}</blockquote>}
      {d.fragmento && <p className="text-sm"><span className="text-[var(--brand-neutral)]">Fragmento: </span>{highlight(d.fragmento, d.marca)}</p>}
      <table className="text-sm">
        <thead><tr className="text-left"><th scope="col">Campo</th><th scope="col">Reglas</th><th scope="col">LLM</th></tr></thead>
        <tbody>{campos.map((c) => <tr key={c} className="border-t border-[var(--brand-neutral)]/30"><th scope="row" className="py-1 pr-4 text-left font-normal">{c}</th><td className="pr-4">{showValue(d.reglas[c])}</td><td>{showValue(d.llm[c])}</td></tr>)}</tbody>
      </table>
      <fieldset className="flex flex-wrap items-center gap-4 text-sm">
        <legend className="sr-only">Valor correcto</legend>
        <label className="flex items-center gap-1.5"><input type="radio" name={group} checked={choice === 'reglas'} onChange={() => setChoice('reglas')} />Es correcto el de las reglas</label>
        <label className="flex items-center gap-1.5"><input type="radio" name={group} checked={choice === 'llm'} onChange={() => setChoice('llm')} />Es correcto el del LLM</label>
        <Button className={btn} disabled={!choice || resolve.isPending} onClick={() => choice && resolve.mutate({ eid: d.ejecucion_id, marca: d.marca, valor: choice === 'reglas' ? d.reglas : d.llm })}>
          {resolve.isPending ? 'Guardando…' : 'Aplicar y recalcular'}
        </Button>
      </fieldset>
      {resolve.isError && <ErrorState error={resolve.error} />}
    </li>
  )
}

export function DiscrepancyQueue({ projectId, items }: { projectId: string; items: Discrepancy[] }) {
  return (
    <Panel title="Cola de discrepancias" source={<span className="text-xs text-[var(--brand-neutral)]">{`${formatNum(items.length)} pendientes`}</span>}>
      {items.length === 0
        ? <EmptyState title="Sin discrepancias" description="Reglas y LLM coinciden en todas las evaluaciones, o el juez no ha usado LLM en este proyecto." />
        : <ul className="grid gap-3">{items.map((d) => <Item key={`${d.ejecucion_id}-${d.marca}`} d={d} projectId={projectId} />)}</ul>}
    </Panel>
  )
}
