import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { overlayVariants, paletteVariants } from '../lib/motion'

const NAV_ACTIONS = [
  { label: 'Search', description: 'Ask your brain a question', to: '/' },
  { label: 'Graph', description: 'View knowledge graph', to: '/graph' },
  { label: 'Upload', description: 'Ingest a new document', to: '/upload' },
  { label: 'Settings', description: 'Configure LLM backend', to: '/settings' },
]

interface Props {
  open: boolean
  onClose: () => void
}

export function CommandPalette({ open, onClose }: Props) {
  const [query, setQuery] = useState('')
  const [selectedIdx, setSelectedIdx] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const filtered = NAV_ACTIONS.filter(
    (a) =>
      a.label.toLowerCase().includes(query.toLowerCase()) ||
      a.description.toLowerCase().includes(query.toLowerCase()),
  )

  useEffect(() => {
    if (!open) return
    setQuery('')
    setSelectedIdx(0)
    const id = setTimeout(() => inputRef.current?.focus(), 50)
    return () => clearTimeout(id)
  }, [open])

  useEffect(() => {
    setSelectedIdx(0)
  }, [query])

  useEffect(() => {
    if (!open) return
    function onDocKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', onDocKey)
    return () => document.removeEventListener('keydown', onDocKey)
  }, [open, onClose])

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIdx((i) => Math.min(i + 1, filtered.length - 1))
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIdx((i) => Math.max(i - 1, 0))
    }
    if (e.key === 'Enter' && filtered[selectedIdx]) {
      navigate({ to: filtered[selectedIdx].to })
      onClose()
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
          variants={overlayVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          role="dialog"
          aria-modal
          aria-label="Command palette"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-slate-900/30 backdrop-blur-sm" />

          <motion.div
            className="relative w-full max-w-lg overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl"
            variants={paletteVariants}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={handleKeyDown}
          >
            <div className="flex items-center border-b border-slate-100 px-4">
              <svg
                className="mr-3 h-4 w-4 shrink-0 text-slate-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
                />
              </svg>
              <input
                ref={inputRef}
                className="h-12 flex-1 bg-transparent text-sm text-slate-900 placeholder-slate-400 outline-none"
                placeholder="Search or jump to..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                role="textbox"
              />
            </div>

            <ul className="max-h-64 overflow-y-auto py-2">
              {filtered.map((action, i) => (
                <li key={action.to}>
                  <button
                    className={`flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                      i === selectedIdx ? 'bg-slate-50' : 'hover:bg-slate-50'
                    }`}
                    onClick={() => {
                      navigate({ to: action.to })
                      onClose()
                    }}
                    onMouseEnter={() => setSelectedIdx(i)}
                  >
                    <span className="text-sm font-medium text-slate-900">
                      {action.label}
                    </span>
                    <span className="text-xs text-slate-400">
                      {action.description}
                    </span>
                  </button>
                </li>
              ))}
              {filtered.length === 0 && (
                <li className="px-4 py-6 text-center text-sm text-slate-400">
                  No results
                </li>
              )}
            </ul>

            <div className="border-t border-slate-100 px-4 py-2 text-xs text-slate-400">
              <span className="mr-3">↑↓ navigate</span>
              <span className="mr-3">↵ select</span>
              <span>esc close</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
