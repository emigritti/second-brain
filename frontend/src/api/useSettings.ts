import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface TaskConfig {
  backend: 'anthropic' | 'localai'
  anthropic_model: string
  local_model: string
  temperature: number
}

export interface SettingsData {
  localai_base_url: string
  tagger: TaskConfig
  linker: TaskConfig
}

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => apiFetch<SettingsData>('/settings'),
  })
}

export function useSaveSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: FormData) =>
      apiFetch<{ status: string }>('/settings', { method: 'POST', body: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings'] }),
  })
}

export function useTestLocalAI() {
  return useMutation({
    mutationFn: (base_url: string) =>
      apiFetch<{ ok: boolean; models: string[]; error?: string }>(
        '/settings/test-localai',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ base_url }),
        },
      ),
  })
}
