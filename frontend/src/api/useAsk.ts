import { useMutation } from '@tanstack/react-query'
import { apiFetch } from './client'

interface AskResponse {
  // normal case
  answer?: string
  sources?: string[]
  // escalation case
  needs_escalation?: boolean
  local_answer?: string
  confidence?: number
}

export function useAsk() {
  return useMutation({
    mutationFn: ({ query, allowEscalation = false }: { query: string; allowEscalation?: boolean }) =>
      apiFetch<AskResponse>('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, allow_escalation: allowEscalation }),
      }),
  })
}
