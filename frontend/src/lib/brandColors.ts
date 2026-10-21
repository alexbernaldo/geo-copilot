import { useCallback } from 'react'
import { cssVar, useResolvedTheme } from './theme'

/**
 * Color de la marca del proyecto y del líder; el resto, neutro (A6.4).
 * Devuelve colores ya resueltos (hexadecimal) porque ECharts pinta en canvas y no entiende `var(--x)`.
 * Cambia al cambiar el tema claro/oscuro.
 */
export function useBrandColors(marcaProyecto: string, lider: string | null): (marca: string) => string {
  const theme = useResolvedTheme()
  return useCallback(
    (marca: string) => {
      void theme
      return cssVar(marca === marcaProyecto ? '--brand-project' : marca === lider ? '--brand-leader' : '--brand-neutral')
    },
    [marcaProyecto, lider, theme],
  )
}

/** Colores de identidad de ámbito (espontánea / asistida) resueltos para el tema actual. */
export function scopeColor(scope: 'espontanea' | 'asistida'): string {
  return cssVar(scope === 'espontanea' ? '--spont' : '--assist')
}
