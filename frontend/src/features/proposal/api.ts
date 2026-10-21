import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { components } from '@/api/schema'
import { unwrap } from '@/features/plan/http'

export type Proposal = components['schemas']['Proposal']
export type ProposalSection = components['schemas']['ProposalSection']
export type ReviewSeal = components['schemas']['ReviewSeal']

const key = (id: string) => ['proposal', id] as const

export function useProposal(id: string) {
  return useQuery({
    queryKey: key(id),
    queryFn: () => unwrap(api.GET('/projects/{id}/proposal', { params: { path: { id } } })),
    retry: false,
  })
}

/** Estimación de coste de volver a redactar y revisar. Solo se pide al abrir la confirmación. */
export function useRegenerateEstimate(id: string, enabled: boolean) {
  return useQuery({
    queryKey: ['estimates', 'analysis', id],
    queryFn: () => unwrap(api.GET('/estimates/analysis', { params: { query: { project_id: id } } })),
    enabled,
    retry: false,
  })
}

export function useRegenerate(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => unwrap(api.POST('/projects/{id}/proposal/regenerate', { params: { path: { id } }, body: { confirmo_coste: true } })),
    onSuccess: (progress) => {
      qc.setQueryData(['progress', id], progress)
      void qc.invalidateQueries({ queryKey: key(id) })
    },
  })
}

export const exportUrl = (id: string, fmt: 'docx' | 'md'): string => `/api/projects/${encodeURIComponent(id)}/exports/${fmt}`
