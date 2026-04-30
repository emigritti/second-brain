import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TopNav } from '../../components/TopNav'

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    to,
    children,
    className,
  }: {
    to: string
    children: React.ReactNode
    className?: string
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
  useRouterState: () => ({ location: { pathname: '/' } }),
}))

describe('TopNav', () => {
  it('renders all nav links', () => {
    render(<TopNav onOpenPalette={() => {}} />)
    expect(screen.getByText('Search')).toBeInTheDocument()
    expect(screen.getByText('Graph')).toBeInTheDocument()
    expect(screen.getByText('Upload')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('calls onOpenPalette when ⌘K button is clicked', async () => {
    const handler = vi.fn()
    render(<TopNav onOpenPalette={handler} />)
    await userEvent.click(screen.getByRole('button', { name: /⌘K/i }))
    expect(handler).toHaveBeenCalledOnce()
  })
})
