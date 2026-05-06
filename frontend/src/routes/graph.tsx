import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { motion } from 'framer-motion'
import { useCallback } from 'react'
import { useGraphData } from '../api/useGraphData'
import { ForceGraph } from '../components/ForceGraph'
import { pageVariants } from '../lib/motion'

export function GraphPage() {
  const { data, isLoading, isError } = useGraphData()
  const navigate = useNavigate()

  const handleNodeClick = useCallback(
    (slug: string) => navigate({ to: '/doc/$slug', params: { slug } }),
    [navigate],
  )

  if (isLoading)
    return <p className="text-sm text-slate-400">Loading graph...</p>
  if (isError)
    return <p className="text-sm text-red-600">Failed to load graph.</p>

  const elements = [...(data?.nodes ?? []), ...(data?.edges ?? [])]

  if (elements.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-24 text-slate-400">
        <p className="text-sm">No documents indexed yet.</p>
        <a href="/upload" className="text-sm text-indigo-500 hover:underline">
          Upload a document
        </a>
      </div>
    )
  }

  return (
    <motion.div
      className="h-[calc(100vh-8rem)] w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <ForceGraph elements={elements} onNodeClick={handleNodeClick} />
    </motion.div>
  )
}

export const Route = createFileRoute('/graph')({ component: GraphPage })
