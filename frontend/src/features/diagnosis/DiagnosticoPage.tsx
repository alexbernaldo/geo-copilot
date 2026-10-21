import { useParams, useSearchParams } from 'react-router-dom'
import { EmptyState, ErrorState, KpiStrip, PageHeader, Panel, PendingState, ScopeToggle, SourceNote, type KpiItem } from '@/components'
import { isNotReady, pct } from '@/features/data/common'
import { formatNum } from '@/lib/format'
import { useDiagnosis, type Ambito, type Diagnosis, type FilaT1 } from './api'
import { usePaletaGrafico } from './colors'
import { ESPECIFICACIONES } from './especificaciones'
import { PanelGrafico } from './panels'
import { fmtPuntos } from './charts'

function indicadores(d: Diagnosis, filaMarca: FilaT1 | undefined): KpiItem[] {
  const i = d.indicadores
  const fuente = filaMarca ? <SourceNote tabla="T1" n={filaMarca.n} /> : undefined
  const nT10 = d.graficos.T10?.find((f) => f.marca === d.marcaProyecto)?.n
  const num = (v: number | undefined, f: (x: number) => string): string => (v === undefined ? '—' : f(v))
  if (d.ambito === 'espontanea') {
    return [
      { label: 'Score espontáneo', value: num(i.score_espontaneo, (v) => formatNum(v, 1)), note: i.puesto_espontaneo !== undefined ? `Puesto ${formatNum(i.puesto_espontaneo)} de ${formatNum(i.total_marcas ?? 0)}` : undefined, source: fuente, highlight: true },
      { label: 'Aparición espontánea', value: num(i.tasa_aparicion_espontanea, pct), source: fuente },
      { label: 'Recomendación activa', value: num(i.pct_recomendacion_activa_espontanea, pct), source: fuente },
      { label: 'Aparición consolidada', value: num(i.pct_consolidada_espontanea, pct), note: i.pct_azar_espontanea !== undefined ? `Por azar: ${pct(i.pct_azar_espontanea)}` : undefined, source: nT10 !== undefined ? <SourceNote tabla="T10" n={nT10} /> : undefined },
    ]
  }
  return [
    { label: 'Score asistido', value: num(i.score_asistido, (v) => formatNum(v, 1)), source: fuente, highlight: true },
    { label: 'Aparición asistida', value: num(i.tasa_aparicion_asistida, pct), source: fuente },
    { label: 'Fuerza media', value: num(i.fuerza_media_asistida, (v) => formatNum(v, 2)), source: fuente },
    { label: 'Menciones negativas', value: num(i.pct_negativo_asistida, pct), source: fuente },
    { label: 'Desconocimiento', value: num(i.pct_desconocimiento_asistida, pct), source: fuente },
  ]
}

export default function DiagnosticoPage() {
  const { id = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const ambito: Ambito = params.get('ambito') === 'asistida' ? 'asistida' : 'espontanea'
  const q = useDiagnosis(id, ambito)
  const paleta = usePaletaGrafico(q.data?.marcaProyecto ?? '', q.data?.lider ?? null)

  const cambiarAmbito = (a: Ambito) => setParams((p) => { const n = new URLSearchParams(p); n.set('ambito', a); return n }, { replace: true })
  const cabecera = (
    <PageHeader
      title="Diagnóstico"
      description="Espontánea y asistida se muestran por separado: nunca se mezclan en un mismo gráfico."
      actions={<ScopeToggle value={ambito} onChange={cambiarAmbito} />}
    />
  )

  if (q.isPending) return <>{cabecera}<p role="status">Cargando diagnóstico…</p></>
  if (q.isError) {
    return (
      <>
        {cabecera}
        {isNotReady(q.error) ? <PendingState step="Métricas" /> : <ErrorState error={q.error} onRetry={() => void q.refetch()} />}
      </>
    )
  }

  const d = q.data
  const filasT1 = d.graficos.T1 ?? []
  const filaMarca = filasT1.find((f) => f.marca === d.marcaProyecto)
  const visibles = ESPECIFICACIONES.filter((s) => (!s.soloEn || s.soloEn === ambito) && (d.graficos[s.tabla]?.length ?? 0) > 0 && !(s.tabla in d.noAplica))
  const ocultos = ESPECIFICACIONES.map((s) => {
    if (s.soloEn && s.soloEn !== ambito) return { spec: s, motivo: 'Solo se calcula para la visibilidad asistida.' }
    const motivo = d.noAplica[s.tabla]
    if (motivo) return { spec: s, motivo }
    if ((d.graficos[s.tabla]?.length ?? 0) === 0) return { spec: s, motivo: 'Este estudio no tiene datos para este gráfico.' }
    return null
  }).filter((x): x is NonNullable<typeof x> => x !== null)

  return (
    <>
      {cabecera}
      <p>
        Marca del proyecto: <strong>{d.marcaProyecto}</strong>
        {d.lider ? <> · Líder: <strong>{d.lider}</strong></> : null}
      </p>
      <KpiStrip items={indicadores(d, filaMarca)} scope={ambito} />
      {filaMarca && (
        <Panel title="Componentes del score" source={<SourceNote tabla="T1" n={filaMarca.n} />}>
          <KpiStrip
            scope={ambito}
            items={[
              { label: 'Aparición', value: fmtPuntos(filaMarca.aparicion), unit: 'pts' },
              { label: 'Posición', value: fmtPuntos(filaMarca.posicion), unit: 'pts' },
              { label: 'Fuerza', value: fmtPuntos(filaMarca.fuerza), unit: 'pts' },
              { label: 'Fuente', value: fmtPuntos(filaMarca.fuente), unit: 'pts' },
            ]}
          />
        </Panel>
      )}
      {visibles.length === 0 && <EmptyState title="Sin gráficos" description="El estudio no ha producido datos para este ámbito." />}
      {visibles.map((s) => (
        <PanelGrafico key={`${ambito}-${s.tabla}`} spec={s} filas={(d.graficos[s.tabla] ?? []) as unknown as Record<string, unknown>[]} paleta={paleta} marcaProyecto={d.marcaProyecto} />
      ))}
      {ocultos.length > 0 && (
        <Panel title="Gráficos que no se muestran">
          <ul>
            {ocultos.map(({ spec, motivo }) => (
              <li key={spec.tabla}>{spec.tabla} · {spec.titulo}: {motivo}</li>
            ))}
          </ul>
        </Panel>
      )}
    </>
  )
}
