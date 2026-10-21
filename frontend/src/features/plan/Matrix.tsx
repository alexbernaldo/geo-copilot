import type { PlanAccion } from './api'
import { TALLA, TALLAS } from './labels'

/** Matriz esfuerzo/impacto: tabla 3 × 3 con las acciones colocadas según su talla (equivalente accesible incluido). */
export function EffortImpactMatrix({ acciones }: { acciones: PlanAccion[] }) {
  const filas = [...TALLAS].reverse()
  return (
    <table className="w-full table-fixed border-collapse text-sm" aria-label="Matriz esfuerzo e impacto de las acciones">
      <caption className="sr-only">Acciones del plan por esfuerzo (columnas) e impacto (filas)</caption>
      <thead>
        <tr>
          <th scope="col" className="w-24 p-1 text-left font-normal text-[var(--brand-neutral)]">Impacto \ Esfuerzo</th>
          {TALLAS.map((e) => <th key={e} scope="col" className="p-1 text-left font-medium">{TALLA[e]}</th>)}
        </tr>
      </thead>
      <tbody>
        {filas.map((imp) => (
          <tr key={imp}>
            <th scope="row" className="p-1 text-left font-medium">{TALLA[imp]}</th>
            {TALLAS.map((esf) => {
              const items = acciones.filter((a) => a.impacto === imp && a.esfuerzo === esf)
              return (
                <td key={esf} className="h-20 border border-[var(--brand-neutral)]/30 p-1.5 align-top">
                  <ul className="flex flex-wrap gap-1">
                    {items.map((a) => <li key={a.id} title={a.titulo} className="rounded bg-[var(--brand-project)]/15 px-1.5 py-0.5 text-xs tabular-nums">{a.id}</li>)}
                  </ul>
                </td>
              )
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
