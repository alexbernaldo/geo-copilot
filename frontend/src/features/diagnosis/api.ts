import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { unwrap } from '@/features/data/common'

export type Ambito = 'espontanea' | 'asistida'

/** Filas de las tablas T1-T12 tal como las devuelve la API (fracciones para las tasas, puntos para los componentes del score). */
export interface FilaT1 {
  marca: string; ambito: string; n: number; n_apariciones: number
  tasa_aparicion: number; pos_media: number | null; fuerza_media: number
  '%recomendacion_activa': number; '%negativo': number; '%desconocimiento': number
  aparicion: number; posicion: number; fuerza: number; fuente: number; score: number
  evidencia_ids?: string[]
}
export interface FilaT2 extends FilaT1 { motor: string }
export interface FilaT3 extends FilaT1 { intencion: string }
export interface FilaT4 extends FilaT1 { ciudad: string }
export interface FilaT5 extends FilaT1 { familia: string }
export interface FilaT6 { marca: string; tipo_fuente: string; n: number; n_apariciones_marca: number; pct_apariciones: number; calidad_media_tipo: number; calidad_media_marca: number; evidencia_ids?: string[] }
export interface FilaT7 { marca: string; rol_comparado: string; dominio: string; n: number; n_ejecuciones_marca: number; tasa_citacion_en_apariciones: number; evidencia_ids?: string[] }
export interface FilaT8 { par: string; marca_a: string; marca_b: string; motor: string; n: number; victorias_a: number; victorias_b: number; empates: number; ganador: string; evidencia_ids?: string[] }
export interface FilaT9 { marca: string; n: number; n_apariciones: number; tasa_aparicion: number; fuerza_media: number; '%recomendacion_activa': number; '%negativo': number; '%desconocimiento': number; objeciones_recurrentes?: string | null; evidencia_ids?: string[] }
export interface FilaT10 { marca: string; n: number; n_consolidada: number; n_azar: number; n_ausente: number; '%consolidada': number; '%azar': number; '%ausente': number; evidencia_ids?: string[] }
export interface FilaT11 { intencion: string; n: number; marca_brief: string; lider: string; tasa_aparicion_marca: number; tasa_aparicion_lider: number; tasa_aparicion_media_competidores: number; brecha_aparicion_vs_lider_pp: number; score_marca: number; score_lider: number; score_media_competidores: number; fuerza_media_marca: number; evidencia_ids?: string[] }
export interface FilaT12 { motor: string; n: number; n_sin_busqueda: number; n_con_busqueda: number; '%sin_busqueda': number; evidencia_ids?: string[] }

export interface Graficos {
  T1?: FilaT1[]; T2?: FilaT2[]; T3?: FilaT3[]; T4?: FilaT4[]; T5?: FilaT5[]; T6?: FilaT6[]
  T7?: FilaT7[]; T8?: FilaT8[]; T9?: FilaT9[]; T10?: FilaT10[]; T11?: FilaT11[]; T12?: FilaT12[]
}

export interface Indicadores {
  puesto_espontaneo?: number
  total_marcas?: number
  score_espontaneo?: number
  tasa_aparicion_espontanea?: number
  pct_recomendacion_activa_espontanea?: number
  score_asistido?: number
  tasa_aparicion_asistida?: number
  fuerza_media_asistida?: number
  pct_negativo_asistida?: number
  pct_desconocimiento_asistida?: number
  pct_azar_espontanea?: number
  pct_consolidada_espontanea?: number
}

export function useDiagnosis(id: string, ambito: Ambito) {
  return useQuery({
    queryKey: ['project', id, 'diagnosis', ambito],
    queryFn: async () => {
      const d = await unwrap(api.GET('/projects/{id}/diagnosis', { params: { path: { id }, query: { ambito } } }))
      return {
        ambito: d.ambito,
        marcaProyecto: d.marca_proyecto,
        lider: d.lider ?? null,
        indicadores: d.indicadores as Indicadores,
        graficos: d.graficos as Graficos,
        noAplica: d.no_aplica ?? {},
      }
    },
  })
}

export type Diagnosis = NonNullable<ReturnType<typeof useDiagnosis>['data']>
