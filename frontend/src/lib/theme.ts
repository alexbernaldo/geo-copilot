import { useEffect, useState, useSyncExternalStore } from 'react'

export type ThemeChoice = 'system' | 'light' | 'dark'
const KEY = 'geo-theme'

function safeGet(): ThemeChoice {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'light' || v === 'dark' ? v : 'system'
  } catch {
    return 'system'
  }
}

export function applyTheme(choice: ThemeChoice): void {
  const root = document.documentElement
  if (choice === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', choice)
  try {
    if (choice === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, choice)
  } catch {
    /* sin almacenamiento: el tema solo dura la sesión */
  }
}

export function initTheme(): void {
  applyTheme(safeGet())
}

/** Tema efectivo ('light' | 'dark') y elección del usuario. */
export function useTheme(): { choice: ThemeChoice; resolved: 'light' | 'dark'; setChoice: (c: ThemeChoice) => void } {
  const [choice, setChoiceState] = useState<ThemeChoice>(() => safeGet())
  const resolved = useResolvedTheme()
  return {
    choice,
    resolved,
    setChoice: (c) => {
      applyTheme(c)
      setChoiceState(c)
    },
  }
}

function subscribe(cb: () => void): () => void {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return () => {}
  }
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const mo = new MutationObserver(cb)
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  mq.addEventListener('change', cb)
  return () => {
    mo.disconnect()
    mq.removeEventListener('change', cb)
  }
}

function snapshot(): 'light' | 'dark' {
  if (typeof document !== 'undefined') {
    const forced = document.documentElement.getAttribute('data-theme')
    if (forced === 'light' || forced === 'dark') return forced
  }
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

/** Tema resuelto y reactivo: lo usan los gráficos para recrear su tema. */
export function useResolvedTheme(): 'light' | 'dark' {
  return useSyncExternalStore(subscribe, snapshot, () => 'light')
}

/** Lee una variable CSS ya resuelta a color. */
export function cssVar(name: string): string {
  return typeof document !== 'undefined' ? getComputedStyle(document.documentElement).getPropertyValue(name).trim() : ''
}

export function usePrefersReducedMotion(): boolean {
  const [r, setR] = useState(() => (typeof window !== 'undefined' && typeof window.matchMedia === 'function' ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false))
  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const f = () => setR(mq.matches)
    mq.addEventListener('change', f)
    return () => mq.removeEventListener('change', f)
  }, [])
  return r
}
