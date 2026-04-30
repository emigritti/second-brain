import { useEffect, useRef } from 'react'
import cytoscape, { type ElementDefinition } from 'cytoscape'

const EDGE_COLORS: Record<string, string> = {
  wikilink: '#6366f1',
  tag: '#f59e0b',
  semantic: '#06b6d4',
}

interface Props {
  elements: ElementDefinition[]
  onNodeClick?: (slug: string) => void
}

export function CytoscapeGraph({ elements, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const onNodeClickRef = useRef(onNodeClick)

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

    return () => cyRef.current?.destroy()
  }, [elements])

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
}
