import { useQuery } from '@tanstack/react-query'
import { apiFetch } from './client'

interface DocData {
  slug: string
  title: string
  tags: string[]
  content_html: string
}

export function useDoc(slug: string) {
  return useQuery({
    queryKey: ['doc', slug],
    queryFn: () =>
      apiFetch<DocData>(`/doc/${slug}`, {
        headers: { Accept: 'application/json' },
      }),
  })
}
