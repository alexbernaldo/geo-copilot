import { useQuery } from '@tanstack/react-query'
import { api } from './client'

/** Hooks comunes (D). Cada feature tiene sus hooks en features/<x>/api.ts. */
export function useProject(id: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      const { data, error } = await api.GET('/projects/{id}', { params: { path: { id } } })
      if (error) throw error
      return data
    },
  })
}

export function useProgress(id: string) {
  return useQuery({
    queryKey: ['progress', id],
    queryFn: async () => {
      const { data, error } = await api.GET('/projects/{id}/progress', { params: { path: { id } } })
      if (error) throw error
      return data
    },
  })
}

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const { data, error } = await api.GET('/settings')
      if (error) throw error
      return data
    },
  })
}
