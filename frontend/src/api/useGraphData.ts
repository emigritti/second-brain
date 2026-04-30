import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'

interface GraphData {
  nodes: { data: { id: string; label: string; title?: string; tags?: string[] } }[]
  edges: { data: { source: string; target: string; type?: string } }[]
}

export function useGraphData() {
  return useQuery({
    queryKey: ['graph'],
    queryFn: () => apiFetch<GraphData>('/graph/data'),
    staleTime: 60_000,
  })
}
