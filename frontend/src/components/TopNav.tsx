import { Link, useRouterState } from '@tanstack/react-router'
import { motion } from 'framer-motion'

const NAV_LINKS = [
  { to: '/', label: 'Search' },
  { to: '/graph', label: 'Graph' },
  { to: '/upload', label: 'Upload' },
  { to: '/settings', label: 'Settings' },
]

interface Props {
  onOpenPalette: () => void
}

export function TopNav({ onOpenPalette }: Props) {
  const { location } = useRouterState()

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex h-12 max-w-7xl items-center gap-6 px-4">
        <div className="flex items-center gap-2 font-semibold text-slate-900">
          <div className="h-5 w-5 rounded bg-indigo-500" />
          <span className="text-sm">Second Brain</span>
        </div>

        <nav className="flex items-center gap-1" aria-label="Main navigation">
          {NAV_LINKS.map(({ to, label }) => {
            const isActive =
              to === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(to)
            return (
              <Link
                key={to}
                to={to}
                className={`relative rounded-full px-3 py-1 text-sm transition-colors hover:text-slate-900 ${isActive ? 'text-indigo-700' : 'text-slate-600'}`}
              >
                {isActive && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 rounded-full bg-indigo-100"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative">{label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="ml-auto">
          <button
            onClick={onOpenPalette}
            className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-500 transition-colors hover:border-slate-300 hover:text-slate-700"
            aria-label="Open command palette (⌘K)"
          >
            <span>⌘K</span>
          </button>
        </div>
      </div>
    </header>
  )
}
