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
      splitLine: { lineStyle: { color: border, type: [4, 4] } },
    },
    bar: { itemStyle: { borderRadius: 4 }, label: { color: fg, fontFamily: mono, fontSize: 11, textBorderWidth: 0 }, emphasis: { focus: 'series' } },
    heatmap: { itemStyle: { borderColor: surface, borderWidth: 2, borderRadius: 4 }, label: { fontFamily: mono, fontSize: 11, textBorderWidth: 0 } },
    legend: { textStyle: { color: muted, fontFamily: font }, icon: 'circle', itemWidth: 9, itemHeight: 9, itemGap: 16 },
    tooltip: {
      backgroundColor: surface,
      borderColor: border,
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: fg, fontFamily: font, fontSize: 12 },
      extraCssText: 'box-shadow: var(--shadow-pop); border-radius: 10px;',
    },
    visualMap: { textStyle: { color: muted, fontFamily: mono } },
  } as EChartsOption
}

/** Rampa secuencial de una sola tonalidad para mapas de calor (de superficie a color de marca). */
export function heatRamp(): string[] {
  return [cssVar('--surface-2'), cssVar('--brand-project')]
}
