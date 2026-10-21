import { Chip, Panel } from '@/components'
import { formatNum } from '@/lib/format'
import type { ReviewSeal } from './api'

/** Sello del revisor. Las cifras vienen del backend; no se suman ni se comparan en el cliente. */
export function Seal({ seal }: { seal: ReviewSeal }) {
  const incidencias = seal.incidencias ?? []
  return (
    <Panel title="Sello del revisor">
      <ul className="flex flex-wrap gap-2" aria-label="Resultado de la revisión">
        <li><Chip tone={seal.cifras_no_trazables === 0 ? 'good' : 'bad'} dot>{`${formatNum(seal.cifras_verificadas)} cifras trazables · ${formatNum(seal.cifras_no_trazables)} sin traza`}</Chip></li>
        <li><Chip tone={seal.incidencias_normativas === 0 ? 'good' : 'bad'} dot>{`${formatNum(seal.incidencias_normativas)} ${seal.incidencias_normativas === 1 ? 'incidencia normativa' : 'incidencias normativas'}`}</Chip></li>
        <li><Chip tone={seal.entidades_fuera_catalogo === 0 ? 'good' : 'bad'} dot>{`${formatNum(seal.entidades_fuera_catalogo)} ${seal.entidades_fuera_catalogo === 1 ? 'entidad fuera del catálogo' : 'entidades fuera del catálogo'}`}</Chip></li>
      </ul>
      {incidencias.length > 0 && (
        <ul className="mt-4 grid gap-3" aria-label="Incidencias detectadas">
          {incidencias.map((i) => (
            <li key={`${i.tipo}-${i.texto}`} className={`rounded border p-3 text-sm ${i.bloqueante ? 'border-red-600' : 'border-[var(--brand-neutral)]/40'}`}>
              <div className="mb-1 flex items-center gap-2"><Chip tone={i.bloqueante ? 'bad' : 'warn'}>{i.bloqueante ? 'Bloquea' : 'Aviso'}</Chip><span className="text-[var(--brand-neutral)]">{i.tipo}</span></div>
              <p>{i.texto}</p>
              {i.sugerencia && <p className="mt-1"><span className="text-[var(--brand-neutral)]">Sugerencia: </span>{i.sugerencia}</p>}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  )
}
