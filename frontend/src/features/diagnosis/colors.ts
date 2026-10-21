import { useEffect, useMemo, useState } from 'react'
import { useBrandColors } from '@/components'

const FALLBACK: Record<string, string> = {
  '--brand-project': '#1f6feb',
  '--brand-leader': '#d9822b',
  '--brand-neutral': '#8b95a1',
  '--fg': '#1a1a1a',
  '--bg': '#ffffff',
}

/** ECharts pinta en canvas y no entiende `var(--x)`: se resuelve el token a su valor actual. */
export function resolveColor(valor: string): string {
  const m = /^var\((--[\w-]+)\)$/.exec(valor.trim())
  if (!m) return valor
  const nombre = m[1] as string
  if (typeof document === 'undefined') return FALLBACK[nombre] ?? '#8b95a1'
  const v = getComputedStyle(document.documentElement).getPropertyValue(nombre).trim()
  return v || FALLBACK[nombre] || '#8b95a1'
}

/** Cambia cuando cambia el tema (preferencia del sistema o atributo `data-theme`), para repintar los gráficos. */
function useTemaVersion(): number {
  const [v, setV] = useState(0)
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)')
    const bump = () => setV((x) => x + 1)
    mq?.addEventListener('change', bump)
    const obs = new MutationObserver(bump)
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class'] })
    return () => { mq?.removeEventListener('change', bump); obs.disconnect() }
  }, [])
  return v
}

export interface PaletaGrafico {
  /** Color de una marca: la del proyecto, el líder o neutro. */
  marca: (nombre: string) => string
  texto: string
  fondo: string
  neutro: string
  proyecto: string
  lider: string
}

/** Colores de marca (vía `useBrandColors`) ya resueltos para canvas. */
export function usePaletaGrafico(marcaProyecto: string, lider: string | null): PaletaGrafico {
  const brand = useBrandColors(marcaProyecto, lider)
  const version = useTemaVersion()
  return useMemo(
    () => ({
      marca: (n: string) => resolveColor(brand(n)),
      texto: resolveColor('var(--fg)'),
      fondo: resolveColor('var(--bg)'),
      neutro: resolveColor('var(--brand-neutral)'),
      proyecto: resolveColor('var(--brand-project)'),
      lider: resolveColor('var(--brand-leader)'),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [brand, version],
  )
}
