import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { unwrap } from './common'

export type Cambio = 'ficha' | 'market' | 'findings' | 'plan'

/** Qué se recalcula si se edita `cambio` y cuánto cuesta (GET sin coste). */
export function useInvalidation(id: string, cambio: Cambio, enabled: boolean) {
  return useQuery({
    queryKey: ['project', id, 'invalidation', cambio],
    enabled,
    queryFn: () => unwrap(api.GET('/projects/{id}/invalidation', { params: { path: { id }, query: { cambio } } })),
  })
}

export function useApproveCheckpoint(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ n, nota }: { n: number; nota?: string }) =>
      unwrap(api.POST('/projects/{id}/checkpoints/{n}/approve', { params: { path: { id, n } }, body: nota ? { nota } : {} })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', id] }),
  })
}

export function useRecompute(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ desde_paso, confirmo_coste }: { desde_paso: string; confirmo_coste: boolean }) =>
      unwrap(api.POST('/projects/{id}/recompute', { params: { path: { id } }, body: { desde_paso, confirmo_coste } })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['project', id] })
      void qc.invalidateQueries({ queryKey: ['progress', id] })
    },
  })
}
