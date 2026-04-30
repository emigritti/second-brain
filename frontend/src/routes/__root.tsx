import { createRootRoute, Outlet } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { TopNav } from '../components/TopNav'
import { CommandPalette } from '../components/CommandPalette'

function RootLayout() {
  const [paletteOpen, setPaletteOpen] = useState(false)

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setPaletteOpen((v) => !v)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div className="min-h-screen bg-slate-50">
      <TopNav onOpenPalette={() => setPaletteOpen(true)} />
      <main className="mx-auto max-w-7xl px-4 py-8">
        <AnimatePresence mode="wait">
          <Outlet />
        </AnimatePresence>
      </main>
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
      />
    </div>
  )
}

export const Route = createRootRoute({ component: RootLayout })
