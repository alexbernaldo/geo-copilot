import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { unwrap } from '@/features/data/common'

/** Plan (solo lectura, para el coste frente al presupuesto). La edición del plan es de la feature `plan`. */
export function usePlanResumen(id: string) {
  return useQuery({
    queryKey: ['project', id, 'overview', 'plan'],
    queryFn: () => unwrap(api.GET('/projects/{id}/plan', { params: { path: { id } } })),
  })
}

/** Propuesta (solo lectura, para el sello del revisor). */
export function useSelloRevisor(id: string) {
  return useQuery({
    queryKey: ['project', id, 'overview', 'sello'],
    queryFn: async () => (await unwrap(api.GET('/projects/{id}/proposal', { params: { path: { id } } }))).sello,
  })
}
