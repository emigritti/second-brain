import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'

export function useUpload() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return apiFetch<{ filename: string; status: string }>('/upload', {
        method: 'POST',
        body: form,
      })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ingest-log'] }),
  })
}
