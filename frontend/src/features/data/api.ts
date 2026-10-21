import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { unwrap } from './common'

export interface ExecutionFilters {
  motor?: string
  familia?: string
  intencion?: string
  ambito?: string
  ciudad?: string
  ids?: string
  q?: string
  pagina: number
  tamano: number
}

export function useExecutions(id: string, filters: ExecutionFilters) {
  return useQuery({
    queryKey: ['project', id, 'executions', filters],
    placeholderData: keepPreviousData,
    queryFn: () => unwrap(api.GET('/projects/{id}/executions', { params: { path: { id }, query: filters } })),
  })
}

export function useExecution(id: string, eid: string | null) {
  return useQuery({
    queryKey: ['project', id, 'execution', eid],
    enabled: eid !== null,
    queryFn: () => unwrap(api.GET('/projects/{id}/executions/{eid}', { params: { path: { id, eid: eid ?? '' } } })),
  })
}

export function useStudySummary(id: string) {
  return useQuery({
    queryKey: ['project', id, 'study-summary'],
    queryFn: () => unwrap(api.GET('/projects/{id}/study/summary', { params: { path: { id } } })),
  })
}
