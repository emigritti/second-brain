import { createFileRoute } from '@tanstack/react-router'
import { motion } from 'framer-motion'
import { useState } from 'react'
import { useAsk } from '../api/useAsk'
import { AnswerCard } from '../components/AnswerCard'
import { pageVariants } from '../lib/motion'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const ask = useAsk()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (query.trim()) ask.mutate(query.trim())
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-8 text-3xl font-bold tracking-tight text-slate-900">
          Second Brain
        </h1>

        <form onSubmit={handleSubmit} className="mb-6 flex gap-3">
          <input
            className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            placeholder="Ask your brain anything..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search query"
          />
          <button
            type="submit"
            disabled={ask.isPending || !query.trim()}
            className="rounded-xl bg-indigo-500 px-5 py-3 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-600 disabled:opacity-50"
            aria-label="Ask"
          >
            {ask.isPending ? '...' : 'Ask'}
          </button>
        </form>

        {ask.isError && (
          <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {ask.error.message}
          </p>
        )}

        {ask.data && (
          <AnswerCard answer={ask.data.answer} sources={ask.data.sources} />
        )}
      </div>
    </motion.div>
  )
}

export const Route = createFileRoute('/')({ component: SearchPage })
