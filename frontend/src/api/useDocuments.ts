import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'

export interface DocumentMeta {
  slug: string
  title: string
  tags: string[]
  semantic_links: string[]
  edges: { wikilink: number; tag: number; semantic: number }
}

export interface DocumentsResponse {
  documents: DocumentMeta[]
}

export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: () => apiFetch<DocumentsResponse>('/documents'),
  })
}
