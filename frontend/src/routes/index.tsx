import { createFileRoute } from '@tanstack/react-router'
import { motion } from 'framer-motion'
import { useState } from 'react'
import { useAsk } from '../api/useAsk'
import { useIngestLog } from '../api/useIngestLog'
import { AnswerCard } from '../components/AnswerCard'
import { pageVariants } from '../lib/motion'

function EmptyState() {
  const { data: log } = useIngestLog()
  if (!log || log.length === 0) return null
  return (
    <div className="mt-8">
      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-slate-400">
        Recent ingestions
      </p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {log.slice(0, 6).map((ev) => (
          <a
            key={ev.slug}
            href={`/doc/${ev.slug}`}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 transition-colors hover:border-indigo-300 hover:text-indigo-700"
          >
            {ev.slug.replace(/_/g, ' ')}
          </a>
        ))}
      </div>
    </div>
  )
}

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [lastQuery, setLastQuery] = useState('')
  const [acceptedAnswer, setAcceptedAnswer] = useState<{ answer: string; sources: string[] } | null>(null)
  const ask = useAsk()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (query.trim()) {
      setLastQuery(query.trim())
      setAcceptedAnswer(null)
      ask.mutate({ query: query.trim() })
    }
  }

  const showEscalationCard = ask.data?.needs_escalation === true && acceptedAnswer === null
  const displayAnswer = acceptedAnswer ?? (ask.data?.needs_escalation ? null : ask.data)

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

        {showEscalationCard && (
          <div className="mb-4 bg-amber-950/30 border border-amber-700/50 rounded-lg px-4 py-3">
            <p className="mb-2 text-sm font-medium text-amber-200">
              Risposta locale (confidenza: {Math.round((ask.data!.confidence ?? 0) * 100)}%)
            </p>
            <p className="mb-4 text-sm text-slate-300">
              {(ask.data!.local_answer ?? '').length > 200
                ? (ask.data!.local_answer ?? '').slice(0, 200) + '…'
                : (ask.data!.local_answer ?? '')}
            </p>
            <div className="flex gap-4">
              <button
                onClick={() =>
                  setAcceptedAnswer({
                    answer: ask.data!.local_answer ?? '',
                    sources: ask.data!.sources ?? [],
                  })
                }
                className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
              >
                Usa questa risposta
              </button>
              <button
                onClick={() => {
                  setAcceptedAnswer(null)
                  ask.mutate({ query: lastQuery, allowEscalation: true })
                }}
                className="text-sm font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                Escalare a Claude API →
              </button>
            </div>
          </div>
        )}

        {displayAnswer && (
          <AnswerCard answer={displayAnswer.answer ?? ''} sources={displayAnswer.sources ?? []} />
        )}

        {!ask.data && !acceptedAnswer && !ask.isPending && (
          <EmptyState />
        )}
      </div>
    </motion.div>
  )
}

export const Route = createFileRoute('/')({ component: SearchPage })
