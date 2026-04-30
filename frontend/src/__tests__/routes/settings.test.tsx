import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SettingsPage } from '../../routes/settings'

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

describe('SettingsPage', () => {
  it('loads and displays current config', async () => {
    render(<SettingsPage />, { wrapper })
    await waitFor(() => {
      expect(
        screen.getByDisplayValue('http://localai:8080'),
      ).toBeInTheDocument()
    })
  })

  it('shows local model field when localai backend selected', async () => {
    render(<SettingsPage />, { wrapper })
    await waitFor(() => screen.getAllByRole('radio'))
    const localaiRadios = screen.getAllByRole('radio', { name: /localai/i })
    await userEvent.click(localaiRadios[0])
    await waitFor(() => {
      expect(
        screen.getByLabelText(/tagger local model/i),
      ).toBeVisible()
    })
  })

  it('saves configuration on submit', async () => {
    render(<SettingsPage />, { wrapper })
    await waitFor(() => screen.getByRole('button', { name: /save configuration/i }))
    await userEvent.click(
      screen.getByRole('button', { name: /save configuration/i }),
    )
    await waitFor(() => {
      expect(screen.getByText(/saved/i)).toBeInTheDocument()
    })
  })
})
