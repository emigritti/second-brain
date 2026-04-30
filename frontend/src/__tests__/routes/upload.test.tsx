import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UploadPage } from '../../routes/upload'

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      {children}
    </QueryClientProvider>
  )
}

describe('UploadPage', () => {
  it('renders the drop zone', () => {
    render(<UploadPage />, { wrapper })
    expect(screen.getByText(/drag/i)).toBeInTheDocument()
  })

  it('shows success message after upload', async () => {
    render(<UploadPage />, { wrapper })
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    const input = screen.getByLabelText(/choose file/i)
    await userEvent.upload(input, file)
    await waitFor(() => {
      expect(screen.getByText(/ingestion started/i)).toBeInTheDocument()
    })
  })
})
