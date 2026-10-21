import { z } from 'zod'
import type { FichaMarca } from '@/api/types'

/** Valores del formulario: todo texto. Las listas son una línea por elemento; el resto se convierte al guardar. */
export interface FichaFormValues {
  marca: string
  web: string
  sector: string
  subsector: string
  servicios: string
  servicios_prioritarios: string
  diferenciales: string
  publicos: string
  ciudades: string
  ciudad_principal: string
  ciudad_crecimiento: string
  competidores_declarados: string
  situacion_digital: Record<string, string>
  hipotesis_cliente: string
  objetivo_principal: string
  kpis_negocio: string
  horizonte_meses: string
  presupuesto_min_eur: string
  presupuesto_max_eur: string
  equipo: string
  restricciones_normativas: string
  tono: string
  audiencia: string
  formato: string
}

export type CampoLista = 'servicios' | 'servicios_prioritarios' | 'diferenciales' | 'publicos' | 'ciudades' | 'competidores_declarados' | 'hipotesis_cliente' | 'kpis_negocio' | 'restricciones_normativas'
export const CAMPOS_LISTA: CampoLista[] = ['servicios', 'servicios_prioritarios', 'diferenciales', 'publicos', 'ciudades', 'competidores_declarados', 'hipotesis_cliente', 'kpis_negocio', 'restricciones_normativas']

const lineas = (v: string): string[] => v.split('\n').map((s) => s.trim()).filter(Boolean)
const unirLineas = (v: string[] | undefined): string => (v ?? []).join('\n')
const aNumero = (v: string): number | null => {
  const limpio = v.trim().replace(/\./g, '').replace(',', '.')
  if (limpio === '') return null
  const n = Number(limpio)
  return Number.isFinite(n) ? n : Number.NaN
}

const numeroOpcional = (mensaje: string) =>
  z.string().refine((v) => v.trim() === '' || !Number.isNaN(aNumero(v)), mensaje)

export const fichaSchema = z
  .object({
    marca: z.string().trim().min(1, 'Indica la marca.'),
    web: z.string().refine((v) => v.trim() === '' || /^https?:\/\/\S+$/.test(v.trim()), 'La web debe empezar por http:// o https://.'),
    sector: z.string().trim().min(1, 'Indica el sector.'),
    subsector: z.string(),
    servicios: z.string(),
    servicios_prioritarios: z.string(),
    diferenciales: z.string(),
    publicos: z.string(),
    ciudades: z.string(),
    ciudad_principal: z.string(),
    ciudad_crecimiento: z.string(),
    competidores_declarados: z.string(),
    situacion_digital: z.record(z.string(), z.string()),
    hipotesis_cliente: z.string(),
    objetivo_principal: z.string().trim().min(1, 'Indica el objetivo principal.'),
    kpis_negocio: z.string(),
    horizonte_meses: numeroOpcional('El horizonte debe ser un número de meses.').refine((v) => v.trim() === '' || Number.isInteger(aNumero(v)) && (aNumero(v) ?? 0) > 0, 'El horizonte debe ser un número entero de meses mayor que 0.'),
    presupuesto_min_eur: numeroOpcional('El presupuesto mínimo debe ser un número.'),
    presupuesto_max_eur: numeroOpcional('El presupuesto máximo debe ser un número.'),
    equipo: z.string(),
    restricciones_normativas: z.string(),
    tono: z.string(),
    audiencia: z.string(),
    formato: z.string(),
  })
  .superRefine((v, ctx) => {
    const min = aNumero(v.presupuesto_min_eur)
    const max = aNumero(v.presupuesto_max_eur)
    if (min !== null && max !== null && !Number.isNaN(min) && !Number.isNaN(max) && min > max) {
      ctx.addIssue({ code: 'custom', path: ['presupuesto_max_eur'], message: 'El máximo no puede ser menor que el mínimo.' })
    }
  })

export function fichaToForm(f: FichaMarca): FichaFormValues {
  const num = (v: number | null | undefined): string => (v === null || v === undefined ? '' : String(v).replace('.', ','))
  return {
    marca: f.marca,
    web: f.web ?? '',
    sector: f.sector,
    subsector: f.subsector ?? '',
    servicios: unirLineas(f.servicios),
    servicios_prioritarios: unirLineas(f.servicios_prioritarios),
    diferenciales: unirLineas(f.diferenciales),
    publicos: unirLineas(f.publicos),
    ciudades: unirLineas(f.ciudades),
    ciudad_principal: f.ciudad_principal ?? '',
    ciudad_crecimiento: f.ciudad_crecimiento ?? '',
    competidores_declarados: unirLineas(f.competidores_declarados),
    situacion_digital: { ...(f.situacion_digital ?? {}) },
    hipotesis_cliente: unirLineas(f.hipotesis_cliente),
    objetivo_principal: f.objetivo_principal,
    kpis_negocio: unirLineas(f.kpis_negocio),
    horizonte_meses: num(f.horizonte_meses),
    presupuesto_min_eur: num(f.presupuesto_min_eur),
    presupuesto_max_eur: num(f.presupuesto_max_eur),
    equipo: f.equipo ?? '',
    restricciones_normativas: unirLineas(f.restricciones_normativas),
    tono: f.tono ?? '',
    audiencia: f.audiencia ?? '',
    formato: f.formato ?? '',
  }
}

export function formToFicha(v: FichaFormValues): FichaMarca {
  const vacioANull = (s: string): string | null => (s.trim() === '' ? null : s.trim())
  const horizonte = aNumero(v.horizonte_meses)
  return {
    marca: v.marca.trim(),
    web: vacioANull(v.web),
    sector: v.sector.trim(),
    subsector: vacioANull(v.subsector),
    servicios: lineas(v.servicios),
    servicios_prioritarios: lineas(v.servicios_prioritarios),
    diferenciales: lineas(v.diferenciales),
    publicos: lineas(v.publicos),
    ciudades: lineas(v.ciudades),
    ciudad_principal: vacioANull(v.ciudad_principal),
    ciudad_crecimiento: vacioANull(v.ciudad_crecimiento),
    competidores_declarados: lineas(v.competidores_declarados),
    situacion_digital: v.situacion_digital,
    hipotesis_cliente: lineas(v.hipotesis_cliente),
    objetivo_principal: v.objetivo_principal.trim(),
    kpis_negocio: lineas(v.kpis_negocio),
    ...(horizonte !== null ? { horizonte_meses: horizonte } : {}),
    presupuesto_min_eur: aNumero(v.presupuesto_min_eur),
    presupuesto_max_eur: aNumero(v.presupuesto_max_eur),
    equipo: v.equipo.trim(),
    restricciones_normativas: lineas(v.restricciones_normativas),
    tono: v.tono.trim(),
    audiencia: v.audiencia.trim(),
    formato: v.formato.trim(),
  }
}

export const ETIQUETAS_SITUACION: Record<string, string> = {
  web_y_contenidos: 'Web y contenidos',
  reputacion: 'Reputación',
  medios_y_terceros: 'Medios y terceros',
  tecnico: 'Técnico',
  herramientas: 'Herramientas',
  fundacion_y_tamano: 'Fundación y tamaño',
  sedes: 'Sedes',
}
