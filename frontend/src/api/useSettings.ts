import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface TaskConfig {
  backend: 'anthropic' | 'localai' | 'ollama'
  anthropic_model: string
  localai_model: string
  ollama_model: string
  temperature: number
}

export interface SettingsData {
  localai_base_url: string
  ollama_base_url: string
  tagger: TaskConfig
  linker: TaskConfig
  anthropic_require_approval: boolean
  anthropic_fallback_enabled: boolean
  vision_enabled: boolean
  query_escalation_enabled: boolean
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

function useTestEndpoint(endpoint: string) {
  return useMutation({
    mutationFn: (base_url: string) =>
      apiFetch<{ ok: boolean; models: string[]; error?: string }>(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_url }),
      }),
  })
}

export function useTestLocalAI() {
  return useTestEndpoint('/settings/test-localai')
}

export function useTestOllama() {
  return useTestEndpoint('/settings/test-ollama')
}
