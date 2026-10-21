import { formatPct } from '@/lib/format'

/** Error de la API con el estado HTTP, para distinguir «aún no existe» (404/409) de un fallo real. */
export class ApiFailure extends Error {
  status: number
  code: string | undefined
  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = 'ApiFailure'
    this.status = status
    this.code = code
  }
}

interface FetchResult<T> {
  data?: T
  error?: unknown
  response: Response
}

/** Desenvuelve una respuesta de openapi-fetch: devuelve `data` o lanza un `ApiFailure` con el mensaje en español de la API. */
export async function unwrap<T>(promise: Promise<FetchResult<T>>): Promise<T> {
  const { data, error, response } = await promise
  if (error !== undefined && error !== null) {
    const e = (error as { error?: { message?: string; code?: string } }).error
    throw new ApiFailure(e?.message ?? 'No se ha podido completar la operación.', response.status, e?.code)
  }
  return data as T
}

/** El resultado todavía no existe porque el paso que lo produce no ha terminado. */
export function isNotReady(error: unknown): boolean {
  return error instanceof ApiFailure && (error.status === 404 || error.status === 409)
}

/** Las tasas llegan como fracción (0,3875); esto solo cambia la unidad de presentación, no calcula nada. */
export const pct = (ratio: number, decimals = 1): string => formatPct(ratio * 100, decimals)

const valorFmt = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 })
/** Valor de una evidencia tal como lo da la API, con formato es-ES. */
export const formatValor = (v: number): string => valorFmt.format(v)

export const ROLES_MARCA = {
  marca_brief: 'Marca del proyecto',
  lider: 'Líder',
  competidor_directo: 'Competidor directo',
  referencia: 'Referencia',
  contexto: 'Contexto',
} as const

export const CHECKPOINTS = [
  { n: 0, clave: 'ficha', nombre: 'Ficha', ruta: 'ficha' },
  { n: 1, clave: 'competencia', nombre: 'Competencia', ruta: 'competencia' },
  { n: 2, clave: 'hallazgos', nombre: 'Hallazgos', ruta: 'hallazgos' },
  { n: 3, clave: 'plan', nombre: 'Plan', ruta: 'plan' },
] as const
