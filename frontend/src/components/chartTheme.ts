import type { EChartsOption } from 'echarts'
import { cssVar } from '@/lib/theme'

/** Tema ECharts derivado de los tokens de DESIGN.md (se reconstruye al cambiar de tema). */
export function buildChartTheme(): EChartsOption {
  const fg = cssVar('--fg')
  const muted = cssVar('--fg-muted')
  const border = cssVar('--border')
  const surface = cssVar('--surface')
  const font = cssVar('--font-sans')
  const mono = cssVar('--font-mono')
  return {
    color: [cssVar('--brand-project'), cssVar('--brand-leader'), cssVar('--brand-neutral'), cssVar('--spont'), cssVar('--assist')],
    backgroundColor: 'transparent',
    textStyle: { fontFamily: font, color: fg, fontSize: 12 },
    grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
    categoryAxis: {
      axisLine: { lineStyle: { color: border } },
      axisTick: { show: false },
      axisLabel: { color: muted, fontFamily: font, fontSize: 12 },
      splitLine: { show: false },
    },
    valueAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: muted, fontFamily: mono, fontSize: 11 },
      splitLine: { lineStyle: { color: border } },
    },
    legend: { textStyle: { color: muted, fontFamily: font }, icon: 'roundRect', itemWidth: 10, itemHeight: 10 },
    tooltip: {
      backgroundColor: surface,
      borderColor: border,
      borderWidth: 1,
      textStyle: { color: fg, fontFamily: font, fontSize: 12 },
      extraCssText: 'box-shadow: var(--shadow-pop); border-radius: 6px;',
    },
    visualMap: { textStyle: { color: muted, fontFamily: mono } },
  } as EChartsOption
}

/** Rampa secuencial de una sola tonalidad para mapas de calor (de superficie a color de marca). */
export function heatRamp(): string[] {
  return [cssVar('--surface-2'), cssVar('--brand-project')]
}
