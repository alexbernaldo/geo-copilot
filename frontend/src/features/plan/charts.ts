import type { EChartsOption } from 'echarts'
import type { PlanAccion, PlanResponse } from './api'
import type { ChartColors } from './theme'

const OPACIDAD_FASE = [0.3, 0.5, 0.75, 1] as const

type Carga = NonNullable<PlanResponse['carga_semanal']>

/** Cronograma por semanas: una barra por acción, coloreada según la fase del plan. */
export function ganttOption(acciones: PlanAccion[], c: ChartColors): EChartsOption {
  const ids = acciones.map((a) => a.id)
  return {
    animation: false,
    grid: { left: 48, right: 16, top: 36, bottom: 28 },
    legend: { top: 0, textStyle: { color: c.fg }, data: [0, 1, 2, 3].map((n) => `Fase ${n}`) },
    tooltip: {
      trigger: 'item',
      formatter: (p: unknown) => {
        const { dataIndex } = p as { dataIndex: number }
        const a = acciones[dataIndex]
        return a ? `${a.id} · ${a.titulo}<br/>Inicio en la semana ${a.semana_inicio} · ${a.plazo_semanas} semanas` : ''
      },
    },
    xAxis: { type: 'value', name: 'Semana', nameTextStyle: { color: c.fg }, axisLabel: { color: c.fg }, splitLine: { lineStyle: { color: c.line, opacity: 0.25 } } },
    yAxis: { type: 'category', inverse: true, data: ids, axisLabel: { color: c.fg } },
    series: [
      { name: 'Inicio', type: 'bar', stack: 'g', silent: true, itemStyle: { color: 'transparent' }, data: acciones.map((a) => a.semana_inicio), tooltip: { show: false } },
      ...OPACIDAD_FASE.map((op, n) => ({
        name: `Fase ${n}`,
        type: 'bar' as const,
        stack: 'g',
        barMaxWidth: 16,
        itemStyle: { color: c.project, opacity: op },
        data: acciones.map((a) => (a.fase_plan === n ? a.plazo_semanas : null)),
      })),
    ],
  }
}

/** Horas semanales del equipo del cliente frente a su capacidad (cifras del backend). */
export function cargaOption(carga: Carga, c: ChartColors): EChartsOption {
  return {
    animation: false,
    grid: { left: 48, right: 16, top: 36, bottom: 28 },
    legend: { top: 0, textStyle: { color: c.fg } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', name: 'Semana', nameTextStyle: { color: c.fg }, data: carga.map((s) => s.semana), axisLabel: { color: c.fg } },
    yAxis: { type: 'value', name: 'Horas', nameTextStyle: { color: c.fg }, axisLabel: { color: c.fg }, splitLine: { lineStyle: { color: c.line, opacity: 0.25 } } },
    series: [
      { name: 'Carga', type: 'bar', itemStyle: { color: c.project }, data: carga.map((s) => s.horas) },
      { name: 'Capacidad', type: 'line', symbol: 'none', lineStyle: { color: c.leader, width: 2 }, itemStyle: { color: c.leader }, data: carga.map((s) => s.capacidad) },
    ],
  }
}
