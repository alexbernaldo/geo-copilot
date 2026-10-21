/** Formato es-ES centralizado (39,4 %, 24.300 €). D lo completa en W1. */

const nf = (min: number, max: number) => new Intl.NumberFormat('es-ES', { minimumFractionDigits: min, maximumFractionDigits: max, useGrouping: 'min2' })

export const formatNum = (v: number, decimals = 0): string => nf(decimals, decimals).format(v)
export const formatPct = (v: number, decimals = 1): string => `${nf(decimals, decimals).format(v)} %`.replace(/ /g, ' ')
export const formatEur = (v: number, decimals = 0): string => `${nf(decimals, decimals).format(v)} €`.replace(/ /g, ' ')
export const formatDate = (iso: string): string => new Date(iso).toLocaleString('es-ES', { dateStyle: 'medium', timeStyle: 'short' })
