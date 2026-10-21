import { useEffect, useState } from 'react'

export interface ChartColors {
  fg: string
  muted: string
  line: string
  project: string
  leader: string
  neutral: string
}

function read(): ChartColors {
  const s = getComputedStyle(document.documentElement)
  const v = (name: string, fallback: string) => s.getPropertyValue(name).trim() || fallback
  return {
    fg: v('--fg', '#1a1a1a'),
    muted: v('--brand-neutral', '#8b95a1'),
    line: v('--brand-neutral', '#8b95a1'),
    project: v('--brand-project', '#1f6feb'),
    leader: v('--brand-leader', '#d9822b'),
    neutral: v('--brand-neutral', '#8b95a1'),
  }
}

/** Colores de los tokens CSS para ECharts; se vuelven a leer al cambiar entre claro y oscuro. */
export function useChartColors(): ChartColors {
  const [colors, setColors] = useState<ChartColors>(() => read())
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!mq) return
    const on = () => setColors(read())
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return colors
}
