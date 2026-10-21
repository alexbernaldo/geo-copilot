/** Utilidades de red compartidas por plan, propuesta y calidad (F). */

export class ApiFailure extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

interface Result<T> {
  data?: T
  error?: unknown
  response: Response
}

function messageOf(error: unknown): string {
  if (typeof error === 'object' && error && 'error' in error) {
    const m = (error as { error?: { message?: string } }).error?.message
    if (m) return m
  }
  return 'Ha ocurrido un error.'
}

/** Devuelve `data` o lanza `ApiFailure` con el estado HTTP y el mensaje del contrato de errores. */
export async function unwrap<T>(request: Promise<Result<T>>): Promise<T> {
  const { data, error, response } = await request
  if (error !== undefined || !response.ok) throw new ApiFailure(response.status, messageOf(error))
  return data as T
}

/** 409: el paso anterior todavía no ha terminado. */
export const isPending = (e: unknown): boolean => e instanceof ApiFailure && e.status === 409
