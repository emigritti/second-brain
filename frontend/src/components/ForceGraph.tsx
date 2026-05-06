import { useRef, useMemo, useEffect, useState } from 'react'
import ForceGraph3D from 'react-force-graph-3d'

interface Props {
  elements: any[]
  onNodeClick?: (slug: string) => void
}

const EDGE_COLORS: Record<string, string> = {
  wikilink: '#6366f1',
  tag: '#f59e0b',
  semantic: '#06b6d4',
}

export function ForceGraph({ elements, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const fgRef = useRef<any>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      })
    }
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        })
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const graphData = useMemo(() => {
    const nodes = elements
      .filter((el) => !el.data.source) // cy nodes don't have source
      .map((el) => ({
        id: el.data.id,
        name: el.data.label || el.data.id,
        val: 1,
        tags: el.data.tags || [],
      }))

    const links = elements
      .filter((el) => el.data.source && el.data.target)
      .map((el) => ({
        source: el.data.source,
        target: el.data.target,
        type: el.data.type || 'unknown',
      }))

    return { nodes, links }
  }, [elements])

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
      {dimensions.width > 0 && (
        <ForceGraph3D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeLabel={(node: any) => `
            <div style="background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); color: #1e293b; font-size: 12px; font-family: ui-sans-serif, system-ui, sans-serif; border: 1px solid #e2e8f0;">
              <strong style="font-weight: 600;">${node.name}</strong>
              ${
                node.tags?.length
                  ? `<div style="margin-top: 4px; display: flex; gap: 4px; flex-wrap: wrap;">
                      ${node.tags
                        .slice(0, 3)
                        .map(
                          (t: string) =>
                            `<span style="background: #e0e7ff; color: #4f46e5; padding: 2px 6px; border-radius: 9999px; font-size: 10px;">${t}</span>`
                        )
                        .join('')}
                      ${node.tags.length > 3 ? `<span style="color: #94a3b8; font-size: 10px;">+${node.tags.length - 3}</span>` : ''}
                    </div>`
                  : ''
              }
            </div>
          `}
          nodeColor={() => '#6366f1'}
          nodeRelSize={4}
          linkWidth={1.5}
          linkColor={(link: any) => EDGE_COLORS[link.type] || '#94a3b8'}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          onNodeClick={(node: any) => {
            onNodeClick?.(node.id)
          }}
          backgroundColor="#ffffff"
        />
      )}
    </div>
  )
}
