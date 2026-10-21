import type { Hallazgo } from '@/api/types'

export function estadoHallazgo(h: Hallazgo): 'aprobado' | 'descartado' | 'pendiente' {
  if (h.aprobado) return 'aprobado'
  return h.descartado_motivo ? 'descartado' : 'pendiente'
}

