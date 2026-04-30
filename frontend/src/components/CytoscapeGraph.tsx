import { useEffect, useRef, useState } from 'react'
import cytoscape, { type ElementDefinition } from 'cytoscape'

const EDGE_COLORS: Record<string, string> = {
  wikilink: '#6366f1',
  tag: '#f59e0b',
  semantic: '#06b6d4',
}

interface Tooltip {
  x: number
  y: number
  label: string
  tags?: string[]
}

interface Props {
  elements: ElementDefinition[]
  onNodeClick?: (slug: string) => void
}

export function CytoscapeGraph({ elements, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const onNodeClickRef = useRef(onNodeClick)
  const [tooltip, setTooltip] = useState<Tooltip | null>(null)

  // Keep the ref up to date without triggering effect re-run
  useEffect(() => {
    onNodeClickRef.current = onNodeClick
  }, [onNodeClick])

  // Init/layout effect — only when elements change
  useEffect(() => {
    if (!containerRef.current) return

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#6366f1',
            label: 'data(label)',
            'font-size': '10px',
            color: '#1e293b',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            width: 20,
            height: 20,
          },
        },
        {
          selector: 'node:hover',
          style: {
            'background-color': '#4f46e5',
            width: 26,
            height: 26,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': (ele) =>
              EDGE_COLORS[ele.data('type') as string] ?? '#94a3b8',
            'target-arrow-color': (ele) =>
              EDGE_COLORS[ele.data('type') as string] ?? '#94a3b8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
      ],
      layout: { name: 'cose', animate: false },
    })

    cyRef.current.on('tap', 'node', (evt) => {
      onNodeClickRef.current?.(evt.target.id() as string)
    })

    cyRef.current.on('mouseover', 'node', (evt) => {
      const node = evt.target
      const pos = node.renderedPosition()
      const containerRect = containerRef.current?.getBoundingClientRect()
      if (!containerRect) return

      const data = node.data()
      setTooltip({
        x: pos.x + 14,
        y: pos.y - 10,
        label: data.label ?? node.id(),
        tags: Array.isArray(data.tags) ? data.tags : undefined,
      })
    })

    cyRef.current.on('mouseout', 'node', () => {
      setTooltip(null)
    })

    // Hide tooltip when panning/zooming
    cyRef.current.on('viewport', () => {
      setTooltip(null)
    })

    return () => {
      cyRef.current?.destroy()
      setTooltip(null)
    }
  }, [elements])

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {tooltip && (
        <div
          style={{ left: tooltip.x, top: tooltip.y }}
          className="pointer-events-none absolute z-10 max-w-48 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg"
        >
          <p className="text-xs font-semibold text-slate-800">{tooltip.label}</p>
          {tooltip.tags && tooltip.tags.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {tooltip.tags.slice(0, 4).map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-indigo-50 px-1.5 py-0.5 text-[10px] text-indigo-600"
                >
                  {tag}
                </span>
              ))}
              {tooltip.tags.length > 4 && (
                <span className="text-[10px] text-slate-400">
                  +{tooltip.tags.length - 4}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
