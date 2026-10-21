import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { FichaMarca } from '@/api/types'
import { unwrap } from '@/features/data/common'

export function useFicha(id: string) {
  return useQuery({
    queryKey: ['project', id, 'ficha'],
    queryFn: () => unwrap(api.GET('/projects/{id}/ficha', { params: { path: { id } } })),
  })
}

export function useSaveFicha(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ficha: FichaMarca) => unwrap(api.PUT('/projects/{id}/ficha', { params: { path: { id } }, body: ficha })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', id] }),
  })
}
