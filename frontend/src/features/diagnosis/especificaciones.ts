import type { EChartsOption } from 'echarts'
import { formatNum } from '@/lib/format'
import type { Ambito, Graficos } from './api'
import {
  consistenciaOption, dominiosOption, duelosOption, embudoOption, fmtPct, fmtPuntos, fuentesOption,
  heatmapCiudad, heatmapFamilia, heatmapMotor, rankingOption, sinBusquedaOption,
} from './charts'
import type { PaletaGrafico } from './colors'

export type Fila = Record<string, unknown>
export type Col = { header: string; clave: string; formato?: (v: unknown) => string }

export interface Especificacion {
  tabla: keyof Graficos
  titulo: string
  /** Si el gráfico solo existe en un ámbito. */
  soloEn?: Ambito
  altura?: (n: number) => number
  columnas: Col[]
  /** Si es `null`, el panel es una tabla sin gráfico. */
  construir: ((filas: never[], p: PaletaGrafico) => EChartsOption) | null
  descripcion: (filas: never[]) => { nombre: string; valor: string }[]
}

const cols = (...c: Col[]) => c
const texto = (v: unknown) => (v === null || v === undefined || v === '' ? '—' : String(v))
const entero = (v: unknown) => (typeof v === 'number' ? formatNum(v) : '—')

const dif = <T,>(f: (x: never[]) => T) => f

/** Define qué gráficos tiene el diagnóstico (A4.8), con su tabla equivalente. */
export const ESPECIFICACIONES: Especificacion[] = [
  {
    tabla: 'T1', titulo: 'Ranking de marcas por score', altura: (n) => 64 + n * 30,
    columnas: cols({ header: 'Marca', clave: 'marca' }, { header: 'Score', clave: 'score', formato: fmtPuntos }, { header: 'Aparición', clave: 'tasa_aparicion', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: rankingOption as never, descripcion: dif((f) => (f as { marca: string; score: number }[]).map((x) => ({ nombre: x.marca, valor: fmtPuntos(x.score) }))),
  },
  {
    tabla: 'T2', titulo: 'Marca por motor', altura: (n) => 120 + n * 7,
    columnas: cols({ header: 'Marca', clave: 'marca' }, { header: 'Motor', clave: 'motor' }, { header: 'Aparición', clave: 'tasa_aparicion', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: heatmapMotor as never, descripcion: dif((f) => (f as { marca: string; motor: string; tasa_aparicion: number }[]).map((x) => ({ nombre: `${x.marca} en ${x.motor}`, valor: fmtPct(x.tasa_aparicion) }))),
  },
  {
    tabla: 'T11', titulo: 'Embudo frente al líder y a la media de competidores', altura: () => 320,
    columnas: cols({ header: 'Intención', clave: 'intencion' }, { header: 'Marca', clave: 'tasa_aparicion_marca', formato: fmtPct }, { header: 'Líder', clave: 'tasa_aparicion_lider', formato: fmtPct }, { header: 'Media competidores', clave: 'tasa_aparicion_media_competidores', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: embudoOption as never, descripcion: dif((f) => (f as { intencion: string; tasa_aparicion_marca: number }[]).map((x) => ({ nombre: x.intencion, valor: fmtPct(x.tasa_aparicion_marca) }))),
  },
  {
    tabla: 'T4', titulo: 'Marca por ciudad', altura: (n) => 120 + n * 14,
    columnas: cols({ header: 'Marca', clave: 'marca' }, { header: 'Ciudad', clave: 'ciudad' }, { header: 'Aparición', clave: 'tasa_aparicion', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: heatmapCiudad as never, descripcion: dif((f) => (f as { marca: string; ciudad: string; tasa_aparicion: number }[]).map((x) => ({ nombre: `${x.marca} en ${x.ciudad}`, valor: fmtPct(x.tasa_aparicion) }))),
  },
  {
    tabla: 'T5', titulo: 'Marca por familia de prompt', altura: (n) => 160 + n * 5,
    columnas: cols({ header: 'Marca', clave: 'marca' }, { header: 'Familia', clave: 'familia' }, { header: 'Aparición', clave: 'tasa_aparicion', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: heatmapFamilia as never, descripcion: dif((f) => (f as { marca: string; familia: string; tasa_aparicion: number }[]).map((x) => ({ nombre: `${x.marca} en ${x.familia}`, valor: fmtPct(x.tasa_aparicion) }))),
  },
  {
    tabla: 'T6', titulo: 'Perfil de fuentes por marca', altura: () => 400,
    columnas: cols({ header: 'Marca', clave: 'marca' }, { header: 'Tipo de fuente', clave: 'tipo_fuente' }, { header: 'Peso en las apariciones', clave: 'pct_apariciones', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: fuentesOption as never, descripcion: dif((f) => (f as { marca: string; tipo_fuente: string; pct_apariciones: number }[]).map((x) => ({ nombre: `${x.marca}, ${x.tipo_fuente}`, valor: fmtPct(x.pct_apariciones) }))),
  },
  {
    tabla: 'T7', titulo: 'Dominios más citados', altura: (n) => 140 + n * 9,
    columnas: cols({ header: 'Dominio', clave: 'dominio' }, { header: 'Marca', clave: 'marca' }, { header: 'Citación en apariciones', clave: 'tasa_citacion_en_apariciones', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: dominiosOption as never, descripcion: dif((f) => (f as { dominio: string; marca: string; tasa_citacion_en_apariciones: number }[]).map((x) => ({ nombre: `${x.dominio} (${x.marca})`, valor: fmtPct(x.tasa_citacion_en_apariciones) }))),
  },
  {
    tabla: 'T8', titulo: 'Duelos 1 a 1', soloEn: 'asistida', altura: (n) => 100 + n * 26,
    columnas: cols({ header: 'Par', clave: 'par' }, { header: 'Motor', clave: 'motor' }, { header: 'Victorias A', clave: 'victorias_a', formato: entero }, { header: 'Empates', clave: 'empates', formato: entero }, { header: 'Victorias B', clave: 'victorias_b', formato: entero }, { header: 'Ganador', clave: 'ganador' }, { header: 'n', clave: 'n', formato: entero }),
    construir: duelosOption as never, descripcion: dif((f) => (f as { par: string; motor: string; ganador: string }[]).map((x) => ({ nombre: `${x.par} en ${x.motor}`, valor: `gana ${x.ganador}` }))),
  },
  {
    tabla: 'T9', titulo: 'Calidad de la mención asistida y objeciones recurrentes', soloEn: 'asistida', construir: null,
    columnas: cols({ header: 'Marca', clave: 'marca' }, { header: 'Fuerza media', clave: 'fuerza_media', formato: fmtPuntos }, { header: 'Recomendación activa', clave: '%recomendacion_activa', formato: fmtPct }, { header: 'Negativas', clave: '%negativo', formato: fmtPct }, { header: 'Objeciones recurrentes', clave: 'objeciones_recurrentes', formato: texto }, { header: 'n', clave: 'n', formato: entero }),
    descripcion: () => [],
  },
  {
    tabla: 'T10', titulo: 'Consistencia entre repeticiones', altura: (n) => 100 + n * 30,
    columnas: cols({ header: 'Marca', clave: 'marca' }, { header: 'Consolidada', clave: '%consolidada', formato: fmtPct }, { header: 'Por azar', clave: '%azar', formato: fmtPct }, { header: 'Ausente', clave: '%ausente', formato: fmtPct }, { header: 'n', clave: 'n', formato: entero }),
    construir: consistenciaOption as never, descripcion: dif((f) => (f as { marca: string; '%consolidada': number }[]).map((x) => ({ nombre: x.marca, valor: `${fmtPct(x['%consolidada'])} consolidada` }))),
  },
  {
    tabla: 'T12', titulo: 'Ejecuciones sin búsqueda por motor', altura: () => 280,
    columnas: cols({ header: 'Motor', clave: 'motor' }, { header: 'Sin búsqueda', clave: '%sin_busqueda', formato: fmtPct }, { header: 'Ejecuciones sin búsqueda', clave: 'n_sin_busqueda', formato: entero }, { header: 'n', clave: 'n', formato: entero }),
    construir: sinBusquedaOption as never, descripcion: dif((f) => (f as { motor: string; '%sin_busqueda': number }[]).map((x) => ({ nombre: x.motor, valor: fmtPct(x['%sin_busqueda']) }))),
  },
]

/** Ejecuciones que respaldan un gráfico: las de la marca del proyecto si hay filas suyas; si no, todas. Solo se agrupan identificadores. */
export function evidenciaDe(filas: Fila[], marca: string): string[] {
  const suyas = filas.filter((f) => f.marca === marca || f.marca_brief === marca || f.marca_a === marca)
  const origen = suyas.length > 0 ? suyas : filas
  const ids: string[] = []
  const vistos = new Set<string>()
  for (const f of origen) {
    for (const id of (f.evidencia_ids as string[] | undefined) ?? []) {
      if (!vistos.has(id)) { vistos.add(id); ids.push(id) }
    }
  }
  return ids
}

export function nDe(filas: Fila[], marca: string): number {
  const fila = filas.find((f) => f.marca === marca || f.marca_brief === marca) ?? filas[0]
  return typeof fila?.n === 'number' ? fila.n : 0
}

