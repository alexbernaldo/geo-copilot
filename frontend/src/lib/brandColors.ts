import { useCallback } from 'react'

/** Color de marca del proyecto y del líder; el resto, neutro. D define los tokens finales. */
export function useBrandColors(marcaProyecto: string, lider: string | null): (marca: string) => string {
  return useCallback(
    (marca: string) => (marca === marcaProyecto ? 'var(--brand-project)' : marca === lider ? 'var(--brand-leader)' : 'var(--brand-neutral)'),
    [marcaProyecto, lider],
  )
}
