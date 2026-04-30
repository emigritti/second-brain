import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { CommandPalette } from '../../components/CommandPalette'

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => vi.fn(),
}))

describe('CommandPalette', () => {
  it('renders search input when open', () => {
    render(<CommandPalette open onClose={() => {}} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<CommandPalette open={false} onClose={() => {}} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('calls onClose when Escape is pressed', async () => {
    const onClose = vi.fn()
    render(<CommandPalette open onClose={onClose} />)
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('filters nav items by query', async () => {
    render(<CommandPalette open onClose={() => {}} />)
    await userEvent.type(screen.getByRole('textbox'), 'graph')
    expect(screen.getByText('Graph')).toBeInTheDocument()
    expect(screen.queryByText('Upload')).not.toBeInTheDocument()
  })
})
