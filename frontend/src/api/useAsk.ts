import { useMutation } from '@tanstack/react-query'
import { apiFetch } from './client'

interface AskResponse {
  answer: string
  sources: string[]
}

export function useAsk() {
  return useMutation({
    mutationFn: (query: string) =>
      apiFetch<AskResponse>('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      }),
  })
}
