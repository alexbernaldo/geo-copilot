import { Link, useParams } from 'react-router-dom'
import { ArrowRight, FileCheck2 } from 'lucide-react'
import { useProject } from '@/api/hooks'
import type { Project } from '@/api/types'
import { Chip, ErrorState, KpiStrip, PageHeader, Panel, ProgressPanel, SourceNote, type KpiItem } from '@/components'
import { CHECKPOINTS, pct } from '@/features/data/common'
import { useDiagnosis } from '@/features/diagnosis/api'
import { useFicha } from '@/features/ficha/api'
import { useFindings } from '@/features/findings/api'
import { formatDate, formatEur, formatNum } from '@/lib/format'
import { usePlanResumen, useSelloRevisor } from './api'

const ESTADO: Record<Project['estado'], { texto: string; tono: 'neutral' | 'info' | 'warn' | 'good' | 'bad' }> = {
  borrador: { texto: 'Borrador', tono: 'neutral' },
  listo_para_lanzar: { texto: 'Listo para lanzar', tono: 'info' },
  en_ejecucion: { texto: 'En ejecución', tono: 'info' },
  esperando_revision: { texto: 'Esperando revisión', tono: 'warn' },
  completado: { texto: 'Completado', tono: 'good' },
  error: { texto: 'Con error', tono: 'bad' },
  interrumpido: { texto: 'Interrumpido', tono: 'warn' },
}

const ACCION_PUNTO: Record<number, string> = {
  0: 'Revisa la ficha',
  1: 'Revisa la competencia',
  2: 'Revisa los hallazgos',
  3: 'Revisa el plan',
}

function siguienteAccion(p: Project): { texto: string; ruta: string } | null {
  if (p.punto_control_pendiente !== null && p.punto_control_pendiente !== undefined) {
    const cp = CHECKPOINTS[p.punto_control_pendiente]
    return { texto: ACCION_PUNTO[p.punto_control_pendiente] ?? 'Revisa el punto de control', ruta: cp.ruta }
  }
  if (p.estado === 'completado') return { texto: 'Abre la propuesta', ruta: 'propuesta' }
  if (p.estado === 'error' || p.estado === 'interrumpido') return { texto: 'Reanuda el análisis desde el progreso', ruta: '' }
  return null
}

export default function ResumenPage() {
  const { id = '' } = useParams()
  const project = useProject(id)
  const diag = useDiagnosis(id, 'espontanea')
  const findings = useFindings(id)
  const plan = usePlanResumen(id)
  const sello = useSelloRevisor(id)
  const ficha = useFicha(id)

  if (project.isPending) return <p role="status">Cargando el proyecto…</p>
  if (project.isError) return <ErrorState error={project.error} onRetry={() => void project.refetch()} />

  const p = project.data
  const estado = ESTADO[p.estado]
  const accion = siguienteAccion(p)
  const enCurso = p.estado !== 'completado' && p.estado !== 'borrador'

  const kpis: KpiItem[] = []
  if (diag.data) {
    const i = diag.data.indicadores
    const fila = diag.data.graficos.T1?.find((f) => f.marca === diag.data.marcaProyecto)
    const fuente = fila ? <SourceNote tabla="T1" n={fila.n} /> : undefined
    if (i.score_espontaneo !== undefined) {
      kpis.push({ label: 'Score espontáneo', value: formatNum(i.score_espontaneo, 1), note: i.puesto_espontaneo !== undefined ? `Puesto ${formatNum(i.puesto_espontaneo)} de ${formatNum(i.total_marcas ?? 0)}` : undefined, source: fuente, highlight: true })
    }
    if (i.tasa_aparicion_espontanea !== undefined) kpis.push({ label: 'Aparición espontánea', value: pct(i.tasa_aparicion_espontanea), source: fuente })
    if (i.pct_recomendacion_activa_espontanea !== undefined) kpis.push({ label: 'Recomendación activa', value: pct(i.pct_recomendacion_activa_espontanea), source: fuente })
  }
  if (findings.data) kpis.push({ label: 'Hallazgos', value: formatNum(findings.data.length) })
  if (plan.data) {
    const f = ficha.data?.ficha
    const rango = f?.presupuesto_min_eur != null && f.presupuesto_max_eur != null ? `Presupuesto del brief: ${formatEur(f.presupuesto_min_eur)} – ${formatEur(f.presupuesto_max_eur)}` : undefined
    kpis.push({ label: 'Coste del plan', value: formatEur(plan.data.plan.coste_total_eur), note: rango })
  }
  if (sello.data) {
    kpis.push({
      label: 'Cifras trazables',
      value: formatNum(sello.data.cifras_verificadas),
      note: `${formatNum(sello.data.cifras_no_trazables)} sin trazar · ${formatNum(sello.data.incidencias_normativas)} incidencias normativas`,
    })
  }

  return (
    <>
      <PageHeader
        title={p.marca ?? p.nombre}
        description={[p.tipo === 'cliente' ? 'Cliente' : 'Prospecto', p.sector, p.origen_datos === 'vivo' ? 'Estudio en vivo' : p.origen_datos === 'csv' ? 'Datos subidos (CSV)' : null].filter(Boolean).join(' · ')}
        actions={<Chip tone={estado.tono} dot>{estado.texto}</Chip>}
      />
      <div className="meta-line">
        <Chip tone="neutral">{`Actualizado: ${formatDate(p.actualizado)}`}</Chip>
        <Chip tone="neutral">{`Coste total: ${formatEur(p.coste_eur, 2)}`}</Chip>
      </div>

      {accion && (
        <div className="callout" role="region" aria-label="Siguiente paso">
          <div>
            <div className="callout-eyebrow">Siguiente paso</div>
            <div className="callout-text">{accion.texto}</div>
          </div>
          {accion.ruta && <Link className="btn" data-variant="primary" to={accion.ruta}>Ir ahora <ArrowRight size={15} strokeWidth={1.75} aria-hidden /></Link>}
        </div>
      )}

      <Panel title="Puntos de control">
        <ol className="cp-steps" aria-label="Puntos de control">
          {CHECKPOINTS.map((c) => {
            const aprobado = p.checkpoints[c.clave]
            const toca = p.punto_control_pendiente === c.n
            return (
              <li key={c.n} className="cp-step" data-estado={aprobado ? 'aprobado' : toca ? 'toca' : 'pendiente'} aria-current={toca ? 'step' : undefined}>
                <Link to={c.ruta}>{c.nombre}</Link>
                <span><Chip tone={aprobado ? 'good' : toca ? 'warn' : 'neutral'} dot>{aprobado ? 'Aprobado' : toca ? 'Toca revisar' : 'Pendiente'}</Chip></span>
              </li>
            )
          })}
        </ol>
      </Panel>

      {enCurso && (
        <Panel title="Progreso">
          <ProgressPanel projectId={id} />
        </Panel>
      )}

      {kpis.length > 0 ? (
        <Panel title="Indicadores clave">
          <KpiStrip items={kpis} />
        </Panel>
      ) : (
        <Panel title="Indicadores clave">
          <p>Los indicadores aparecen según terminan los pasos del análisis.</p>
        </Panel>
      )}

      {p.estado === 'completado' && (
        <div className="callout" role="region" aria-label="Entregable">
          <div>
            <div className="callout-eyebrow">Entregable</div>
            <div className="callout-text">La propuesta está lista para revisar y descargar</div>
          </div>
          <Link className="btn" to="propuesta"><FileCheck2 size={15} strokeWidth={1.75} aria-hidden /> Ver la propuesta</Link>
        </div>
      )}
    </>
  )
}
