import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SearchPage } from '../../routes/index'

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

describe('SearchPage', () => {
  it('renders search input', () => {
    render(<SearchPage />, { wrapper })
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('shows answer after submitting query', async () => {
    render(<SearchPage />, { wrapper })
    await userEvent.type(
      screen.getByRole('textbox'),
      'What is quantum computing?',
    )
    await userEvent.click(screen.getByRole('button', { name: /ask/i }))
    await waitFor(() => {
      expect(
        screen.getByText('Test answer from the brain.'),
      ).toBeInTheDocument()
    })
  })

  it('shows source links after answer', async () => {
    render(<SearchPage />, { wrapper })
    await userEvent.type(screen.getByRole('textbox'), 'test query')
    await userEvent.click(screen.getByRole('button', { name: /ask/i }))
    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'test_doc' })).toBeInTheDocument()
    })
  })
})
