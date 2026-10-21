import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { ContrasteMercado } from '@/api/types'
import { unwrap } from '@/features/data/common'

export function useMarket(id: string) {
  return useQuery({
    queryKey: ['project', id, 'market'],
    queryFn: () => unwrap(api.GET('/projects/{id}/market', { params: { path: { id } } })),
  })
}

export function useSaveMarket(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (market: ContrasteMercado) => unwrap(api.PUT('/projects/{id}/market', { params: { path: { id } }, body: market })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', id] }),
  })
}
