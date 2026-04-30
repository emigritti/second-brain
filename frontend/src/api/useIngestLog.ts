import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'

interface LogEvent {
  ts: string
  slug: string
  warnings: { msg: string }[]
}

export function useIngestLog() {
  return useQuery({
    queryKey: ['ingest-log'],
    queryFn: () => apiFetch<LogEvent[]>('/ingest/log'),
    refetchInterval: 5_000,
  })
}
