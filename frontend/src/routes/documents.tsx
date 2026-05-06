import { createFileRoute, Link } from '@tanstack/react-router'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useDocuments } from '../api/useDocuments'
import { pageVariants } from '../lib/motion'

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center shadow-sm">
      <div className="text-2xl font-bold text-slate-900">{value}</div>
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
        <h1 className="mb-6 text-2xl font-bold tracking-tight text-slate-900">Documents</h1>

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
                  ? 'bg-indigo-500 text-white shadow-sm'
                  : 'border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-900'
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
                    ? 'bg-indigo-500 text-white shadow-sm'
                    : 'border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-900'
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
              <div key={i} className="h-14 animate-pulse rounded-xl bg-slate-200" />
            ))}
          </div>
        )}

        {isError && (
          <p className="text-sm text-red-600">Failed to load documents.</p>
        )}

        {!isPending && !isError && filtered.length === 0 && (
          <div className="rounded-xl border border-slate-200 bg-white px-6 py-10 text-center shadow-sm">
            <p className="text-slate-500">
              {docs.length === 0
                ? 'No documents yet. '
                : 'No documents match this tag. '}
              {docs.length === 0 && (
                <Link to="/upload" className="font-medium text-indigo-600 hover:text-indigo-500">
                  Upload your first document →
                </Link>
              )}
            </p>
          </div>
        )}

        {!isPending && filtered.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm divide-y divide-slate-100">
            {filtered.map(doc => (
              <div key={doc.slug} className="flex items-start justify-between gap-4 px-4 py-3 transition-colors hover:bg-slate-50">
                <div className="min-w-0">
                  <Link
                    to="/doc/$slug"
                    params={{ slug: doc.slug }}
                    className="block truncate text-sm font-medium text-slate-900 hover:text-indigo-600"
                  >
                    {doc.title}
                  </Link>
                  {doc.tags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {doc.tags.map(tag => (
                        <span key={tag} className="rounded border border-slate-200 bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-600">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="shrink-0 text-right text-xs text-slate-500">
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
