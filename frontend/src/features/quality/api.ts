import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { components } from '@/api/schema'
import { unwrap } from '@/features/plan/http'

type S = components['schemas']
export type Quality = S['Quality']
export type Discrepancy = S['Discrepancy']
export type HumanLabel = S['HumanLabel']
export type ExecutionDetail = S['ExecutionDetail']
export type ApprovalRecord = S['ApprovalRecord']
export type TraceRow = S['TraceRow']

const key = (id: string) => ['quality', id] as const

export function useQuality(id: string) {
  return useQuery({
    queryKey: key(id),
    queryFn: () => unwrap(api.GET('/projects/{id}/quality', { params: { path: { id } } })),
    retry: false,
  })
}

export function useTraces(id: string) {
  return useQuery({
    queryKey: ['traces', id],
    queryFn: () => unwrap(api.GET('/projects/{id}/traces', { params: { path: { id } } })),
    retry: false,
  })
}

export function useExecution(id: string, eid: string | undefined) {
  return useQuery({
    queryKey: ['execution', id, eid],
    queryFn: () => unwrap(api.GET('/projects/{id}/executions/{eid}', { params: { path: { id, eid: eid ?? '' } } })),
    enabled: !!eid,
    retry: false,
  })
}

export function useSaveLabels(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (etiquetas: HumanLabel[]) => unwrap(api.POST('/projects/{id}/quality/labels', { params: { path: { id } }, body: { etiquetas } })),
    onSuccess: (data) => qc.setQueryData(key(id), data),
  })
}

export function useResolveDiscrepancy(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { eid: string; marca: string; valor: Record<string, unknown> }) =>
      unwrap(api.PATCH('/projects/{id}/quality/discrepancies/{eid}/{marca}', { params: { path: { id, eid: v.eid, marca: v.marca } }, body: { valor: v.valor } })),
    onSuccess: (data) => qc.setQueryData(key(id), data),
  })
}
