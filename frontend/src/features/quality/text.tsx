import type { ReactNode } from 'react'

/** Resalta cada aparición de `term` en `text`. El texto es un dato no fiable: se pinta siempre como texto, nunca como HTML. */
export function highlight(text: string, term: string | null | undefined): ReactNode {
  if (!term) return text
  const lower = text.toLowerCase()
  const needle = term.toLowerCase()
  const out: ReactNode[] = []
  let from = 0
  let at = lower.indexOf(needle, from)
  while (at !== -1) {
    if (at > from) out.push(text.slice(from, at))
    out.push(<mark key={at}>{text.slice(at, at + needle.length)}</mark>)
    from = at + needle.length
    at = lower.indexOf(needle, from)
  }
  out.push(text.slice(from))
  return out
}

/** Valor de un campo del juez como texto legible. */
export function showValue(v: unknown): string {
  if (v === null || v === undefined || v === '') return '—'
  if (typeof v === 'boolean') return v ? 'Sí' : 'No'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
