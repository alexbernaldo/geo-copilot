import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { components } from '@/api/schema'
import { unwrap } from './http'

type S = components['schemas']
export type PlanData = S['Plan']
export type PlanAccion = S['Accion']
export type PlanObjetivo = S['Objetivo']
export type PlanResponse = S['PlanResponse']
export type PlanAviso = S['PlanAviso']
export type SimulateResult = S['SimulateResult']
export type TableData = S['TableData']

const planKey = (id: string) => ['plan', id] as const

export function usePlan(id: string) {
  return useQuery({
    queryKey: planKey(id),
    queryFn: () => unwrap(api.GET('/projects/{id}/plan', { params: { path: { id } } })),
    retry: false,
  })
}

/** Guarda y devuelve el plan revalidado por el backend (avisos incluidos). */
export function useSavePlan(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (plan: PlanData) => unwrap(api.PUT('/projects/{id}/plan', { params: { path: { id } }, body: plan })),
    onSuccess: (data) => qc.setQueryData(planKey(id), data),
  })
}

export function useSimulate(id: string) {
  return useMutation({
    mutationFn: (cambios: Record<string, unknown>) => unwrap(api.POST('/projects/{id}/plan/simulate', { params: { path: { id } }, body: { cambios } })),
  })
}

/** Tabla T1-T12 (solo lectura): de ella salen las líneas base del simulador. */
export function useTable(id: string, tid: string) {
  return useQuery({
    queryKey: ['table', id, tid],
    queryFn: () => unwrap(api.GET('/projects/{id}/tables/{tid}', { params: { path: { id, tid } } })),
    retry: false,
  })
}

export function useApprovePlan(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => unwrap(api.POST('/projects/{id}/checkpoints/{n}/approve', { params: { path: { id, n: 3 } }, body: {} })),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: planKey(id) })
      void qc.invalidateQueries({ queryKey: ['project', id] })
    },
  })
}
