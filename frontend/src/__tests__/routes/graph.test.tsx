import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GraphPage } from '../../routes/graph'

vi.mock('../../components/CytoscapeGraph', () => ({
  CytoscapeGraph: ({
    elements,
  }: {
    elements: unknown[]
    onNodeClick?: (slug: string) => void
  }) => (
    <div data-testid="cytoscape-graph" data-count={elements.length} />
  ),
}))

vi.mock('@tanstack/react-router', () => ({
  createFileRoute: () => (opts: unknown) => opts,
  useNavigate: () => vi.fn(),
}))

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

describe('GraphPage', () => {
  it('shows loading state initially', () => {
    render(<GraphPage />, { wrapper })
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders graph after data loads', async () => {
    render(<GraphPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByTestId('cytoscape-graph')).toBeInTheDocument()
    })
  })
})
