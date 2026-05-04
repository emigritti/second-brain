import { createFileRoute, Link } from '@tanstack/react-router'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useDocuments } from '../api/useDocuments'
import { pageVariants } from '../lib/motion'

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-center">
      <div className="text-2xl font-bold text-slate-100">{value}</div>
      <div className="mt-0.5 text-xs text-slate-500">{label}</div>
    </div>
  )
}

export function DocumentsPage() {
  const { data, isPending, isError } = useDocuments()
  const [activeTag, setActiveTag] = useState<string | null>(null)

  const docs = data?.documents ?? []

  // Stats
  const totalTags = new Set(docs.flatMap(d => d.tags)).size
  const totalSemantic = Math.round(docs.reduce((s, d) => s + d.edges.semantic, 0) / 2)
  const totalWikilinks = docs.reduce((s, d) => s + d.edges.wikilink, 0)

  // All unique tags sorted
  const allTags = [...new Set(docs.flatMap(d => d.tags))].sort()

  // Filtered docs
  const filtered = activeTag ? docs.filter(d => d.tags.includes(activeTag)) : docs

  return (
    <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-6 text-2xl font-bold tracking-tight text-slate-100">Documents</h1>

        {/* Stats */}
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="documents" value={docs.length} />
          <StatCard label="unique tags" value={totalTags} />
          <StatCard label="semantic links" value={totalSemantic} />
          <StatCard label="wikilinks" value={totalWikilinks} />
        </div>

        {/* Tag filter */}
        {allTags.length > 0 && (
          <div className="mb-5 flex flex-wrap gap-2">
            <button
              onClick={() => setActiveTag(null)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                activeTag === null
                  ? 'bg-indigo-500 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            {allTags.map(tag => (
              <button
                key={tag}
                onClick={() => setActiveTag(activeTag === tag ? null : tag)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  activeTag === tag
                    ? 'bg-indigo-500 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}

        {/* List */}
        {isPending && (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg bg-slate-800" />
            ))}
          </div>
        )}

        {isError && (
          <p className="text-sm text-red-400">Failed to load documents.</p>
        )}

        {!isPending && !isError && filtered.length === 0 && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 px-6 py-10 text-center">
            <p className="text-slate-400">
              {docs.length === 0
                ? 'No documents yet. '
                : 'No documents match this tag. '}
              {docs.length === 0 && (
                <Link to="/upload" className="text-indigo-400 hover:text-indigo-300">
                  Upload your first document →
                </Link>
              )}
            </p>
          </div>
        )}

        {!isPending && filtered.length > 0 && (
          <div className="divide-y divide-slate-800 rounded-lg border border-slate-800">
            {filtered.map(doc => (
              <div key={doc.slug} className="flex items-start justify-between gap-4 px-4 py-3 hover:bg-slate-900/50">
                <div className="min-w-0">
                  <Link
                    to="/doc/$slug"
                    params={{ slug: doc.slug }}
                    className="block truncate text-sm font-medium text-slate-100 hover:text-indigo-400"
                  >
                    {doc.title}
                  </Link>
                  {doc.tags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {doc.tags.map(tag => (
                        <span key={tag} className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-400">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="shrink-0 text-right text-xs text-slate-600">
                  {doc.edges.semantic > 0 && <span>{doc.edges.semantic} semantic</span>}
                  {doc.edges.semantic > 0 && doc.edges.wikilink > 0 && <span> · </span>}
                  {doc.edges.wikilink > 0 && <span>{doc.edges.wikilink} links</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export const Route = createFileRoute('/documents')({ component: DocumentsPage })
