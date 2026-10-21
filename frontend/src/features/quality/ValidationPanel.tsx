import type { ReactNode } from 'react'
import { EmptyState, Panel } from '@/components'
import { formatNum, formatPct } from '@/lib/format'
import type { Quality } from './api'

type Campo = NonNullable<Quality['validacion']['campos']>[number]

const CAMPO: Record<string, string> = { tipo_mencion: 'Tipo de mención', fuerza: 'Fuerza', sentimiento: 'Sentimiento', tipo_fuente: 'Tipo de fuente' }

/** Matriz de confusión: acepta `{labels, confusion_matrix}` y, si el formato es otro, la muestra como pares clave-valor. */
function Matriz({ matriz }: { matriz: Record<string, unknown> }) {
  const labels = Array.isArray(matriz.labels) ? (matriz.labels as unknown[]).map(String) : null
  const rows = Array.isArray(matriz.confusion_matrix) ? (matriz.confusion_matrix as unknown[]) : null
  if (!labels || !rows) {
    return <pre className="overflow-x-auto text-xs">{JSON.stringify(matriz, null, 1)}</pre>
  }
  return (
    <div className="overflow-x-auto">
      <table className="text-sm" aria-label="Matriz de confusión: filas, etiqueta humana; columnas, etiqueta del juez">
        <thead>
          <tr><th scope="col" className="p-1 text-left font-normal text-[var(--brand-neutral)]">Humano \ Juez</th>{labels.map((l) => <th key={l} scope="col" className="p-1 text-right">{l}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={labels[i] ?? i}>
              <th scope="row" className="p-1 text-left">{labels[i]}</th>
              {(Array.isArray(r) ? (r as unknown[]) : []).map((c, j) => <td key={labels[j] ?? j} className="p-1 text-right tabular-nums">{formatNum(Number(c))}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function ValidationPanel({ validacion, sin }: { validacion: Quality['validacion']; sin: ReactNode }) {
  if (!validacion.disponible) return <>{sin}</>
  const campos: Campo[] = validacion.campos ?? []
  if (campos.length === 0) return <EmptyState title="Sin campos validados" description="La muestra evaluada no contiene campos comparables." />
  return (
    <Panel title="Validación del juez" source={<span className="text-xs text-[var(--brand-neutral)]">{`Muestra evaluada por humanos · n=${formatNum(validacion.n ?? 0)}`}</span>}>
      <table className="w-full text-sm">
        <thead><tr className="text-left"><th scope="col">Campo</th><th scope="col" className="text-right">Exactitud</th><th scope="col" className="text-right">Kappa</th></tr></thead>
        <tbody>
          {campos.map((c) => (
            <tr key={c.campo} className="border-t border-[var(--brand-neutral)]/30">
              <th scope="row" className="py-1.5 text-left font-normal">{CAMPO[c.campo] ?? c.campo}</th>
              <td className="text-right tabular-nums">{formatPct(c.exactitud * 100)}</td>
              <td className="text-right tabular-nums">{formatNum(c.kappa, 3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-4 grid gap-3">
        {campos.filter((c) => c.matriz && Object.keys(c.matriz).length > 0).map((c) => (
          <details key={c.campo}>
            <summary className="cursor-pointer text-sm">{`Matriz de confusión · ${CAMPO[c.campo] ?? c.campo}`}</summary>
            <div className="mt-2"><Matriz matriz={c.matriz ?? {}} /></div>
          </details>
        ))}
      </div>
    </Panel>
  )
}
