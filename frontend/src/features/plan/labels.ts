import type { PlanAccion } from './api'

export const PALANCA: Record<PlanAccion['palanca'], string> = {
  autoridad_terceros: 'Autoridad en terceros',
  entidad_datos_estructurados: 'Entidad y datos estructurados',
  contenido: 'Contenido',
  reputacion_resenas: 'Reputación y reseñas',
  comunidades: 'Comunidades',
  tecnico: 'Técnico',
  medicion: 'Medición',
}

export const RESPONSABLE: Record<PlanAccion['responsable'], string> = {
  cliente_marketing: 'Cliente · marketing',
  cliente_comunicacion: 'Cliente · comunicación',
  cliente_medico: 'Cliente · equipo médico',
  agencia: 'Agencia',
  tercero: 'Tercero',
}

export const TALLA: Record<PlanAccion['esfuerzo'], string> = { S: 'Bajo', M: 'Medio', L: 'Alto' }
export const TALLAS = ['S', 'M', 'L'] as const

export const FASES = [0, 1, 2, 3] as const

/** Convierte el texto de un campo de lista (una entrada por línea o separadas por comas) en lista. */
export function parseList(text: string, separator: RegExp = /\n/): string[] {
  return text.split(separator).map((s) => s.trim()).filter(Boolean)
}
