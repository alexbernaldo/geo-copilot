import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { components } from '@/api/schema'
import { unwrap } from '@/features/data/common'

export type FindingPatch = components['schemas']['FindingPatch']

export function useFindings(id: string) {
  return useQuery({
    queryKey: ['project', id, 'findings'],
    queryFn: () => unwrap(api.GET('/projects/{id}/findings', { params: { path: { id } } })),
  })
}

export function usePatchFinding(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ hid, cambio }: { hid: string; cambio: FindingPatch }) =>
      unwrap(api.PATCH('/projects/{id}/findings/{hid}', { params: { path: { id, hid } }, body: cambio })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', id] }),
  })
}
