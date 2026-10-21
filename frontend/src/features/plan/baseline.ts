import type { TableData } from './api'

export interface Baseline {
  ciudades: { nombre: string; tasa: number }[]
  motores: { nombre: string; tasa: number }[]
  fuerza: number | null
  pctCalidad: number | null
}

type Row = Record<string, unknown>

/** Filas de una tabla del backend para la marca y el ámbito espontáneo; sin cálculo alguno. */
function filas(t: TableData | undefined, marca: string): Row[] {
  return (t?.filas ?? []).filter((r) => r.marca === marca && (r.ambito === undefined || r.ambito === 'espontanea'))
}

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

function porClave(t: TableData | undefined, marca: string, clave: 'ciudad' | 'motor'): { nombre: string; tasa: number }[] {
  const out: { nombre: string; tasa: number }[] = []
  for (const r of filas(t, marca)) {
    const nombre = r[clave]
    const tasa = num(r.tasa_aparicion)
    if (typeof nombre === 'string' && tasa !== null) out.push({ nombre, tasa })
  }
  return out
}

/** Convierte los valores del formulario (porcentaje 0-100) en el cuerpo que espera `geo/simulate.py` (fracciones 0-1). */
export function buildCambios(ciudades: Record<string, number>, motores: Record<string, number>, fuerza: number | null, pctCalidad: number | null): Record<string, unknown> {
  const frac = (o: Record<string, number>) => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v / 100]))
  const out: Record<string, unknown> = {}
  if (Object.keys(ciudades).length) out.aparicion_por_ciudad = frac(ciudades)
  if (Object.keys(motores).length) out.aparicion_por_motor = frac(motores)
  if (fuerza !== null) out.fuerza_media_objetivo = fuerza
  if (pctCalidad !== null) out.pct_fuentes_calidad = pctCalidad / 100
  return out
}

/** Líneas base del simulador: todas salen de T1, T2 y T4 y del detalle de una simulación sin cambios. */
export function buildBaseline(marca: string, t1?: TableData, t2?: TableData, t4?: TableData, detalle?: Record<string, unknown>): Baseline {
  const base = (detalle?.parametros_base ?? {}) as Record<string, unknown>
  return {
    ciudades: porClave(t4, marca, 'ciudad'),
    motores: porClave(t2, marca, 'motor'),
    fuerza: num(filas(t1, marca)[0]?.fuerza_media_apariciones) ?? num(base.fuerza_presentes),
    pctCalidad: num(base.pct_fuentes_calidad),
  }
}
