import { createFileRoute, Link } from '@tanstack/react-router'
import { motion } from 'framer-motion'
import { useDoc } from '../api/useDoc'
import { TagChip } from '../components/TagChip'
import { pageVariants } from '../lib/motion'

function DocPage() {
  const { slug } = Route.useParams()
  const { data, isLoading, isError } = useDoc(slug)

  if (isLoading)
    return <p className="text-sm text-slate-400">Loading document...</p>
  if (isError || !data)
    return <p className="text-sm text-red-600">Document not found.</p>

  return (
    <motion.article
      className="mx-auto max-w-2xl"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <nav className="mb-6 flex items-center gap-2 text-xs text-slate-400">
        <Link to="/" className="hover:text-slate-700">
          Search
        </Link>
        <span>/</span>
        <Link to="/graph" className="hover:text-slate-700">
          Graph
        </Link>
        <span>/</span>
        <span className="text-slate-700">{data.title}</span>
      </nav>

      <h1 className="mb-3 text-2xl font-bold tracking-tight text-slate-900">
        {data.title}
      </h1>

      {data.tags.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {data.tags.map((tag) => (
            <TagChip key={tag} tag={tag} />
          ))}
        </div>
      )}

      <div
        className="prose prose-slate prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: data.content_html }}
      />
    </motion.article>
  )
}

export const Route = createFileRoute('/doc/$slug')({ component: DocPage })
