import { useEffect, useRef, useState } from 'react'
import { Button, Chip, ErrorState, Panel, Slider } from '@/components'
import { formatNum, formatPct } from '@/lib/format'
import type { SimulateResult } from './api'
import { buildCambios, type Baseline } from './baseline'

export const ETIQUETA_ESCENARIO = 'Escenario hipotético, no una predicción'

type Valores = Record<string, number>

interface Props {
  baseline: Baseline
  result?: SimulateResult
  pending: boolean
  error: unknown
  onSimulate: (cambios: Record<string, unknown>) => void
  onUse: (r: SimulateResult) => void
}

function SliderRow({ label, value, base, max, step, unit, onChange }: { label: string; value: number; base: number; max: number; step: number; unit: 'pct' | 'num'; onChange: (v: number) => void }) {
  const fmt = (v: number) => (unit === 'pct' ? formatPct(v, 0) : formatNum(v, 1))
  return (
    <div className="grid gap-1">
      <div className="flex items-baseline justify-between text-sm">
        <span>{label}</span>
        <span className="tabular-nums">{fmt(value)} <span className="text-[var(--brand-neutral)]">(actual {fmt(base)})</span></span>
      </div>
      <Slider ariaLabel={label} value={value} min={0} max={max} step={step} onValueChange={onChange} />
    </div>
  )
}

export function Simulator({ baseline, result, pending, error, onSimulate, onUse }: Props) {
  const inicial = (lista: { nombre: string; tasa: number }[]): Valores => Object.fromEntries(lista.map((x) => [x.nombre, x.tasa * 100]))
  const [ciudades, setCiudades] = useState<Valores>(() => inicial(baseline.ciudades))
  const [motores, setMotores] = useState<Valores>(() => inicial(baseline.motores))
  const [fuerza, setFuerza] = useState<number | null>(baseline.fuerza)
  const [calidad, setCalidad] = useState<number | null>(baseline.pctCalidad === null ? null : baseline.pctCalidad * 100)
  const tocado = useRef(false)

  useEffect(() => {
    setCiudades(inicial(baseline.ciudades))
    setMotores(inicial(baseline.motores))
    setFuerza(baseline.fuerza)
    setCalidad(baseline.pctCalidad === null ? null : baseline.pctCalidad * 100)
    tocado.current = false
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseline])

  useEffect(() => {
    if (!tocado.current) return
    const t = window.setTimeout(() => onSimulate(buildCambios(ciudades, motores, fuerza, calidad)), 350)
    return () => window.clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ciudades, motores, fuerza, calidad])

  const touch = <T,>(set: (v: T) => void) => (v: T) => { tocado.current = true; set(v) }
  const vacio = baseline.ciudades.length + baseline.motores.length === 0 && baseline.fuerza === null && baseline.pctCalidad === null

  const reset = () => {
    setCiudades(inicial(baseline.ciudades)); setMotores(inicial(baseline.motores)); setFuerza(baseline.fuerza)
    setCalidad(baseline.pctCalidad === null ? null : baseline.pctCalidad * 100)
    tocado.current = false
  }

  return (
    <Panel title="Simulador de escenarios" actions={<Chip tone="warn">{ETIQUETA_ESCENARIO}</Chip>}>
      {vacio ? (
        <p className="text-sm">El backend todavía no ha devuelto las líneas base del simulador.</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
          <div className="grid gap-5">
            {baseline.ciudades.length > 0 && (
              <fieldset className="grid gap-3"><legend className="mb-1 text-sm font-medium">Aparición espontánea por ciudad</legend>
                {baseline.ciudades.map((c) => <SliderRow key={c.nombre} label={c.nombre} unit="pct" max={100} step={1} base={c.tasa * 100} value={ciudades[c.nombre] ?? c.tasa * 100} onChange={touch((v: number) => setCiudades((p) => ({ ...p, [c.nombre]: v })))} />)}
              </fieldset>
            )}
            {baseline.motores.length > 0 && (
              <fieldset className="grid gap-3"><legend className="mb-1 text-sm font-medium">Aparición espontánea por motor</legend>
                {baseline.motores.map((m) => <SliderRow key={m.nombre} label={m.nombre} unit="pct" max={100} step={1} base={m.tasa * 100} value={motores[m.nombre] ?? m.tasa * 100} onChange={touch((v: number) => setMotores((p) => ({ ...p, [m.nombre]: v })))} />)}
              </fieldset>
            )}
            <fieldset className="grid gap-3"><legend className="mb-1 text-sm font-medium">Calidad de las menciones</legend>
              {baseline.fuerza !== null && fuerza !== null && <SliderRow label="Fuerza media en apariciones (0-3)" unit="num" max={3} step={0.1} base={baseline.fuerza} value={fuerza} onChange={touch(setFuerza)} />}
              {baseline.pctCalidad !== null && calidad !== null
                ? <SliderRow label="Fuentes de calidad (%)" unit="pct" max={100} step={1} base={baseline.pctCalidad * 100} value={calidad} onChange={touch(setCalidad)} />
                : <p className="text-sm text-[var(--brand-neutral)]">Fuentes de calidad: el backend no ha devuelto la línea base.</p>}
            </fieldset>
          </div>
          <div aria-live="polite" className="grid content-start gap-3 rounded border border-[var(--brand-neutral)]/40 p-4">
            {error ? <ErrorState error={error} /> : null}
            {result ? (
              <>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div><dt className="text-[var(--brand-neutral)]">Score actual</dt><dd className="text-xl tabular-nums">{formatNum(result.score_actual, 1)}</dd></div>
                  <div><dt className="text-[var(--brand-neutral)]">Score simulado</dt><dd className="text-xl tabular-nums">{formatNum(result.score_simulado, 1)}</dd></div>
                  <div><dt className="text-[var(--brand-neutral)]">Puesto actual</dt><dd className="text-xl tabular-nums">{result.puesto_actual}º</dd></div>
                  <div><dt className="text-[var(--brand-neutral)]">Puesto simulado</dt><dd className="text-xl tabular-nums">{result.puesto_simulado}º</dd></div>
                </dl>
                <p className="text-sm font-medium">{ETIQUETA_ESCENARIO}</p>
                <Button className="rounded border border-[var(--brand-project)] px-3 py-1.5 text-sm" onClick={() => onUse(result)}>Usar como objetivos del plan</Button>
              </>
            ) : (
              <p className="text-sm text-[var(--brand-neutral)]">{pending ? 'Calculando escenario…' : 'Mueve un control para ver el score y el puesto simulados.'}</p>
            )}
            <Button className="justify-self-start rounded border border-[var(--brand-neutral)]/40 px-3 py-1.5 text-sm" onClick={reset}>Restablecer controles</Button>
          </div>
        </div>
      )}
    </Panel>
  )
}
