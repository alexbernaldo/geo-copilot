import type { EChartsOption } from 'echarts'
import { formatNum, formatPct } from '@/lib/format'
import type { FilaT1, FilaT2, FilaT4, FilaT5, FilaT6, FilaT7, FilaT8, FilaT10, FilaT11, FilaT12 } from './api'
import type { PaletaGrafico } from './colors'

/*
 * Mapeos de las tablas T1-T12 a opciones de ECharts.
 * Regla: los valores de cada serie son los que da la API, sin transformar. Las tasas llegan como fracción (0-1) y solo se
 * formatean como porcentaje al mostrarlas. El orden de las categorías es el de aparición en los datos.
 */

type Paleta = Pick<PaletaGrafico, 'marca' | 'texto' | 'fondo' | 'neutro' | 'proyecto' | 'lider'>

export const fmtPct = (v: unknown): string => (typeof v === 'number' ? formatPct(v * 100, 1) : '—')
export const fmtPuntos = (v: unknown): string => (typeof v === 'number' ? formatNum(v, 1) : '—')

const unicos = <T,>(valores: T[]): T[] => [...new Set(valores)]

/** Dato con su origen para el tooltip («Origen: T2 · n=60»). */
interface Dato {
  value: number | null
  n: number
  tabla: string
  itemStyle?: { color: string }
}

function tooltipItem(formato: (v: unknown) => string, etiqueta?: (p: Punto) => string) {
  return {
    trigger: 'item' as const,
    formatter: (raw: unknown) => {
      const p = raw as Punto
      const d = (p.data ?? {}) as Partial<Dato>
      const valor = Array.isArray(p.value) ? (p.value[2] as unknown) : p.value
      const cabecera = etiqueta ? etiqueta(p) : `${p.name ?? ''}${p.seriesName ? ` · ${p.seriesName}` : ''}`
      const origen = d.tabla ? `<br/><small>Origen: ${d.tabla} · n=${formatNum(d.n ?? 0)}</small>` : ''
      return `${cabecera}<br/><strong>${formato(valor)}</strong>${origen}`
    },
  }
}

interface Punto {
  name?: string
  seriesName?: string
  value?: unknown
  data?: unknown
}

const base = (p: Paleta): Pick<EChartsOption, 'textStyle' | 'animation'> => ({
  textStyle: { color: p.texto },
  animation: false,
})

/** T1: ranking de marcas por score. El orden es el de la API (de mayor a menor score). */
export function rankingOption(filas: FilaT1[], p: Paleta): EChartsOption {
  return {
    ...base(p),
    grid: { left: 8, right: 24, top: 8, bottom: 24, containLabel: true },
    tooltip: tooltipItem(fmtPuntos),
    xAxis: { type: 'value', name: 'Score', nameLocation: 'middle', nameGap: 30 },
    yAxis: { type: 'category', inverse: true, data: filas.map((f) => f.marca) },
    series: [
      {
        type: 'bar',
        name: 'Score',
        label: { show: true, position: 'right', formatter: (x: unknown) => fmtPuntos((x as Punto).value) },
        data: filas.map((f): Dato => ({ value: f.score, n: f.n, tabla: 'T1', itemStyle: { color: p.marca(f.marca) } })),
      },
    ],
  }
}

interface MapaCalorEntrada<T> {
  filas: T[]
  x: (f: T) => string
  y: (f: T) => string
  valor: (f: T) => number
  n: (f: T) => number
  tabla: string
  nombreValor: string
}

/** Mapa de calor genérico (T2, T4, T5). La escala de color va de 0 a 1 porque los valores son tasas. */
export function mapaCalorOption<T>(e: MapaCalorEntrada<T>, p: Paleta): EChartsOption {
  const xs = unicos(e.filas.map(e.x))
  const ys = unicos(e.filas.map(e.y))
  return {
    ...base(p),
    grid: { left: 8, right: 8, top: 8, bottom: 56, containLabel: true },
    tooltip: tooltipItem(fmtPct, (pt) => {
      const v = (pt.value as unknown[]) ?? []
      return `${ys[v[1] as number] ?? ''} · ${xs[v[0] as number] ?? ''}`
    }),
    xAxis: { type: 'category', data: xs, splitArea: { show: true }, axisLabel: { interval: 0, width: 104, overflow: 'break', lineHeight: 14 } },
    yAxis: { type: 'category', inverse: true, data: ys, splitArea: { show: true } },
    visualMap: {
      min: 0,
      max: 1,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      formatter: (v: unknown) => fmtPct(v),
      inRange: { color: [p.fondo, p.proyecto] },
      textStyle: { color: p.texto },
    },
    series: [
      {
        type: 'heatmap',
        name: e.nombreValor,
        label: { show: true, formatter: (x: unknown) => fmtPct(((x as Punto).value as unknown[])[2]) },
        data: e.filas.map((f) => ({ value: [xs.indexOf(e.x(f)), ys.indexOf(e.y(f)), e.valor(f)], n: e.n(f), tabla: e.tabla })),
      },
    ],
  }
}

export const heatmapMotor = (filas: FilaT2[], p: Paleta) =>
  mapaCalorOption({ filas, x: (f) => f.motor, y: (f) => f.marca, valor: (f) => f.tasa_aparicion, n: (f) => f.n, tabla: 'T2', nombreValor: 'Aparición' }, p)
export const heatmapCiudad = (filas: FilaT4[], p: Paleta) =>
  mapaCalorOption({ filas, x: (f) => f.ciudad, y: (f) => f.marca, valor: (f) => f.tasa_aparicion, n: (f) => f.n, tabla: 'T4', nombreValor: 'Aparición' }, p)
export const heatmapFamilia = (filas: FilaT5[], p: Paleta) =>
  mapaCalorOption({ filas, x: (f) => f.familia, y: (f) => f.marca, valor: (f) => f.tasa_aparicion, n: (f) => f.n, tabla: 'T5', nombreValor: 'Aparición' }, p)

/** T11: embudo de la marca frente al líder y a la media de competidores, por intención. */
export function embudoOption(filas: FilaT11[], p: Paleta): EChartsOption {
  const marca = filas[0]?.marca_brief ?? 'Marca'
  const lider = filas[0]?.lider ?? 'Líder'
  const serie = (name: string, color: string, valor: (f: FilaT11) => number) => ({
    type: 'bar' as const,
    name,
    itemStyle: { color },
    data: filas.map((f): Dato => ({ value: valor(f), n: f.n, tabla: 'T11' })),
  })
  return {
    ...base(p),
    grid: { left: 8, right: 8, top: 40, bottom: 8, containLabel: true },
    legend: { top: 0, textStyle: { color: p.texto } },
    tooltip: tooltipItem(fmtPct),
    xAxis: { type: 'category', data: filas.map((f) => f.intencion) },
    yAxis: { type: 'value', min: 0, max: 1, axisLabel: { formatter: (v: number) => fmtPct(v) } },
    series: [
      serie(marca, p.proyecto, (f) => f.tasa_aparicion_marca),
      serie(lider, p.lider, (f) => f.tasa_aparicion_lider),
      serie('Media de competidores', p.neutro, (f) => f.tasa_aparicion_media_competidores),
    ],
  }
}

/** T6: perfil de fuentes por marca, barras apiladas por tipo de fuente. */
export function fuentesOption(filas: FilaT6[], p: Paleta): EChartsOption {
  const marcas = unicos(filas.map((f) => f.marca))
  const tipos = unicos(filas.map((f) => f.tipo_fuente))
  const opacidad = (i: number) => Math.max(0.25, 1 - i * 0.15)
  return {
    ...base(p),
    grid: { left: 8, right: 8, top: 56, bottom: 8, containLabel: true },
    legend: { top: 0, type: 'scroll', textStyle: { color: p.texto } },
    tooltip: tooltipItem(fmtPct),
    xAxis: { type: 'value', max: 1, axisLabel: { formatter: (v: number) => fmtPct(v) } },
    yAxis: { type: 'category', inverse: true, data: marcas },
    series: tipos.map((tipo, i) => ({
      type: 'bar' as const,
      stack: 'fuentes',
      name: tipo,
      itemStyle: { color: p.neutro, opacity: opacidad(i) },
      data: marcas.map((m): Dato => {
        const f = filas.find((x) => x.marca === m && x.tipo_fuente === tipo)
        return { value: f ? f.pct_apariciones : null, n: f?.n ?? 0, tabla: 'T6' }
      }),
    })),
  }
}

/** T7: dominios más citados, una serie por marca. */
export function dominiosOption(filas: FilaT7[], p: Paleta): EChartsOption {
  const dominios = unicos(filas.map((f) => f.dominio))
  const marcas = unicos(filas.map((f) => f.marca))
  return {
    ...base(p),
    grid: { left: 8, right: 8, top: 40, bottom: 8, containLabel: true },
    legend: { top: 0, type: 'scroll', textStyle: { color: p.texto } },
    tooltip: tooltipItem(fmtPct),
    xAxis: { type: 'value', max: 1, axisLabel: { formatter: (v: number) => fmtPct(v) } },
    yAxis: { type: 'category', inverse: true, data: dominios },
    series: marcas.map((m) => ({
      type: 'bar' as const,
      name: m,
      itemStyle: { color: p.marca(m) },
      data: dominios.map((d): Dato => {
        const f = filas.find((x) => x.marca === m && x.dominio === d)
        return { value: f ? f.tasa_citacion_en_apariciones : null, n: f?.n ?? 0, tabla: 'T7' }
      }),
    })),
  }
}

/** T8: duelos 1 a 1 por par y motor (solo asistida). */
export function duelosOption(filas: FilaT8[], p: Paleta): EChartsOption {
  const cat = filas.map((f) => `${f.par} · ${f.motor}`)
  return {
    ...base(p),
    grid: { left: 8, right: 8, top: 40, bottom: 8, containLabel: true },
    legend: { top: 0, data: ['Gana la primera marca', 'Empates', 'Gana la segunda marca'], textStyle: { color: p.texto } },
    tooltip: tooltipItem((v) => formatNum(typeof v === 'number' ? v : 0)),
    xAxis: { type: 'value', name: 'Respuestas' },
    yAxis: { type: 'category', inverse: true, data: cat, axisLabel: { width: 260, overflow: 'truncate' } },
    series: [
      { type: 'bar', stack: 'duelo', name: 'Gana la primera marca', data: filas.map((f): Dato => ({ value: f.victorias_a, n: f.n, tabla: 'T8', itemStyle: { color: p.marca(f.marca_a) } })) },
      { type: 'bar', stack: 'duelo', name: 'Empates', itemStyle: { color: p.neutro, opacity: 0.4 }, data: filas.map((f): Dato => ({ value: f.empates, n: f.n, tabla: 'T8' })) },
      { type: 'bar', stack: 'duelo', name: 'Gana la segunda marca', data: filas.map((f): Dato => ({ value: f.victorias_b, n: f.n, tabla: 'T8', itemStyle: { color: p.marca(f.marca_b) } })) },
    ],
  }
}

/** T10: consistencia entre repeticiones (consolidada / azar / ausente). */
export function consistenciaOption(filas: FilaT10[], p: Paleta): EChartsOption {
  const serie = (name: string, opacity: number, valor: (f: FilaT10) => number) => ({
    type: 'bar' as const,
    stack: 'consistencia',
    name,
    itemStyle: { color: p.neutro, opacity },
    data: filas.map((f): Dato => ({ value: valor(f), n: f.n, tabla: 'T10' })),
  })
  return {
    ...base(p),
    grid: { left: 8, right: 8, top: 40, bottom: 8, containLabel: true },
    legend: { top: 0, textStyle: { color: p.texto } },
    tooltip: tooltipItem(fmtPct),
    xAxis: { type: 'value', max: 1, axisLabel: { formatter: (v: number) => fmtPct(v) } },
    yAxis: { type: 'category', inverse: true, data: filas.map((f) => f.marca) },
    series: [serie('Consolidada', 1, (f) => f['%consolidada']), serie('Por azar', 0.6, (f) => f['%azar']), serie('Ausente', 0.25, (f) => f['%ausente'])],
  }
}

/** T12: ejecuciones sin búsqueda web por motor. */
export function sinBusquedaOption(filas: FilaT12[], p: Paleta): EChartsOption {
  return {
    ...base(p),
    grid: { left: 8, right: 8, top: 16, bottom: 8, containLabel: true },
    tooltip: tooltipItem(fmtPct),
    xAxis: { type: 'category', data: filas.map((f) => f.motor) },
    yAxis: { type: 'value', min: 0, max: 1, axisLabel: { formatter: (v: number) => fmtPct(v) } },
    series: [
      {
        type: 'bar',
        name: 'Sin búsqueda',
        itemStyle: { color: p.neutro },
        label: { show: true, position: 'top', formatter: (x: unknown) => fmtPct((x as Punto).value) },
        data: filas.map((f): Dato => ({ value: f['%sin_busqueda'], n: f.n, tabla: 'T12' })),
      },
    ],
  }
}

/** Texto alternativo del gráfico: lista las categorías en el orden de los datos con su valor. */
export function describir(titulo: string, pares: { nombre: string; valor: string }[]): string {
  return `${titulo}. ${pares.map((p) => `${p.nombre}: ${p.valor}`).join('; ')}.`
}
