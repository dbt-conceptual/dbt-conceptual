import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { State, Concept, Relationship } from '../types'
import './GraphEditor.css'

interface Props {
  state: State
  setState: (state: State) => void
}

interface GraphNode extends d3.SimulationNodeDatum {
  id: string
  label: string
  concept: Concept
  domain?: string
  color: string
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  id: string
  relationship: Relationship
}

export default function GraphEditor({ state, setState }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [selectedLink, setSelectedLink] = useState<string | null>(null)
  const [layout, setLayout] = useState<Record<string, { x: number; y: number }>>({})
  const [availableModels, setAvailableModels] = useState<{ silver: string[]; gold: string[] }>({ silver: [], gold: [] })
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; type: 'canvas' | 'node'; nodeId?: string } | null>(null)
  const [dragConnection, setDragConnection] = useState<{ fromNodeId: string; x: number; y: number } | null>(null)
  const [relationshipDialog, setRelationshipDialog] = useState<{ fromNodeId: string; toNodeId: string } | null>(null)

  // Load layout on mount
  useEffect(() => {
    fetch('/api/layout')
      .then(res => res.json())
      .then(data => {
        if (data && typeof data === 'object' && !data.error) {
          setLayout(data)
        }
      })
      .catch(err => console.error('Failed to load layout:', err))
  }, [])

  // Load available models on mount
  useEffect(() => {
    fetch('/api/models')
      .then(res => res.json())
      .then(data => {
        if (data && typeof data === 'object' && !data.error) {
          setAvailableModels(data)
        }
      })
      .catch(err => console.error('Failed to load models:', err))
  }, [])

  // Close context menu on click
  useEffect(() => {
    const handleClick = () => setContextMenu(null)
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  // Handle drag connection mouse move and end
  useEffect(() => {
    if (!dragConnection || !svgRef.current) return

    const handleMouseMove = (event: MouseEvent) => {
      const [x, y] = d3.pointer(event, svgRef.current)
      setDragConnection(prev => prev ? { ...prev, x, y } : null)
    }

    const handleMouseUp = (event: MouseEvent) => {
      // Cancel drag if not released on a node
      if (event.button === 0) {
        setDragConnection(null)
      }
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      // Cancel drag on Escape
      if (event.key === 'Escape') {
        setDragConnection(null)
      }
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [dragConnection])

  // Save layout when positions change (debounced)
  const saveLayout = (positions: Record<string, { x: number; y: number }>) => {
    fetch('/api/layout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ positions }),
    }).catch(err => console.error('Failed to save layout:', err))
  }

  // Create a new concept
  const createNewConcept = () => {
    const conceptName = prompt('Enter concept name:')
    if (!conceptName) return

    const conceptId = conceptName.toLowerCase().replace(/\s+/g, '_')
    if (state.concepts[conceptId]) {
      alert('A concept with this name already exists')
      return
    }

    setState({
      ...state,
      concepts: {
        ...state.concepts,
        [conceptId]: {
          name: conceptName,
          status: 'draft',
          bronze_models: [],
          silver_models: [],
          gold_models: [],
        },
      },
    })
    setSelectedNode(conceptId)
  }

  // Create a new relationship from a concept
  const createNewRelationship = (fromConceptId: string) => {
    const relationshipName = prompt('Enter relationship name:')
    if (!relationshipName) return

    const toConceptId = prompt('Enter target concept ID (choose from: ' + Object.keys(state.concepts).join(', ') + '):')
    if (!toConceptId || !state.concepts[toConceptId]) {
      alert('Invalid target concept')
      return
    }

    const cardinality = prompt('Enter cardinality (e.g., 1:1, 1:N, N:M):')
    if (!cardinality) return

    const relationshipId = `${fromConceptId}_${relationshipName}_${toConceptId}`.toLowerCase().replace(/\s+/g, '_')

    setState({
      ...state,
      relationships: {
        ...state.relationships,
        [relationshipId]: {
          name: relationshipName,
          from_concept: fromConceptId,
          to_concept: toConceptId,
          cardinality,
          realized_by: [],
        },
      },
    })
    setSelectedLink(relationshipId)
  }

  useEffect(() => {
    if (!svgRef.current) return

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Create graph data with saved positions
    const nodes: GraphNode[] = Object.entries(state.concepts).map(([id, concept]) => {
      const node: GraphNode = {
        id,
        label: concept.name,
        concept,
        domain: concept.domain,
        color: concept.color // Use concept color if specified
          || (concept.domain && state.domains[concept.domain]?.color) // Otherwise use domain color
          || '#E3F2FD', // Default fallback
      }

      // Apply saved position if available
      if (layout[id]) {
        node.x = layout[id].x
        node.y = layout[id].y
        node.fx = layout[id].x
        node.fy = layout[id].y
      }

      return node
    })

    const links: GraphLink[] = Object.entries(state.relationships).map(([id, rel]) => ({
      id,
      source: rel.from_concept,
      target: rel.to_concept,
      relationship: rel,
    }))

    // Create force simulation with gentler forces
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links)
        .id(d => d.id)
        .distance(200))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(80))
      .alphaDecay(0.02) // Slower decay for smoother settling

    // Create container for zoom
    const g = svg.append('g')

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Add context menu for canvas (right-click)
    svg.on('contextmenu', (event) => {
      if (event.target === svgRef.current || event.target.tagName === 'svg') {
        event.preventDefault()
        setContextMenu({
          x: event.clientX,
          y: event.clientY,
          type: 'canvas',
        })
      }
    })

    // Add crow's foot notation markers for different cardinalities
    const defs = svg.append('defs')

    // One (mandatory) - single line perpendicular to relationship line
    defs.append('marker')
      .attr('id', 'one')
      .attr('viewBox', '-5 -5 10 10')
      .attr('refX', 5)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 10)
      .attr('markerHeight', 10)
      .append('svg:line')
      .attr('x1', 0)
      .attr('y1', -4)
      .attr('x2', 0)
      .attr('y2', 4)
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2)

    // Many - crow's foot (three lines spreading out)
    const manyMarker = defs.append('marker')
      .attr('id', 'many')
      .attr('viewBox', '-5 -5 10 10')
      .attr('refX', 5)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 10)
      .attr('markerHeight', 10)
    manyMarker.append('svg:line')
      .attr('x1', 0).attr('y1', -4).attr('x2', 5).attr('y2', 0)
      .attr('stroke', '#94a3b8').attr('stroke-width', 2)
    manyMarker.append('svg:line')
      .attr('x1', 0).attr('y1', 0).attr('x2', 5).attr('y2', 0)
      .attr('stroke', '#94a3b8').attr('stroke-width', 2)
    manyMarker.append('svg:line')
      .attr('x1', 0).attr('y1', 4).attr('x2', 5).attr('y2', 0)
      .attr('stroke', '#94a3b8').attr('stroke-width', 2)

    // Optional (zero) - small circle
    defs.append('marker')
      .attr('id', 'zero')
      .attr('viewBox', '-5 -5 10 10')
      .attr('refX', 5)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 10)
      .attr('markerHeight', 10)
      .append('svg:circle')
      .attr('cx', 0)
      .attr('cy', 0)
      .attr('r', 2.5)
      .attr('fill', 'none')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2)

    // Unknown cardinality - question mark (for design-time/stubs)
    const unknownMarker = defs.append('marker')
      .attr('id', 'unknown')
      .attr('viewBox', '-5 -5 10 10')
      .attr('refX', 5)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 10)
      .attr('markerHeight', 10)
    unknownMarker.append('svg:text')
      .attr('x', -1)
      .attr('y', 2)
      .attr('font-size', '8px')
      .attr('font-weight', 'bold')
      .attr('fill', '#94a3b8')
      .text('?')

    // Helper to parse cardinality and return marker IDs
    const getCardinalityMarkers = (cardinality: string | undefined): { start: string; end: string } => {
      if (!cardinality) return { start: 'unknown', end: 'unknown' }

      // Parse cardinality like "1:1", "1:N", "0:N", "N:M", "?:?", etc.
      const parts = cardinality.split(':').map(p => p.trim().toUpperCase())
      if (parts.length !== 2) return { start: 'unknown', end: 'unknown' }

      const getMarker = (part: string): string => {
        if (part === '?' || part === 'UNKNOWN') return 'unknown'
        if (part === '1') return 'one'
        if (part === 'N' || part === 'M' || part === '*') return 'many'
        if (part === '0' || part === '0..1') return 'zero'
        if (part === '1..N' || part === '0..N') return 'many'
        return 'unknown' // default to unknown for unrecognized
      }

      return {
        start: getMarker(parts[0]),
        end: getMarker(parts[1])
      }
    }

    // Draw links with crow's foot notation
    const link = g.append('g')
      .selectAll('path')
      .data(links)
      .join('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2.5)
      .attr('marker-start', d => {
        const markers = getCardinalityMarkers(d.relationship.cardinality)
        return markers.start ? `url(#${markers.start})` : ''
      })
      .attr('marker-end', d => {
        const markers = getCardinalityMarkers(d.relationship.cardinality)
        return markers.end ? `url(#${markers.end})` : ''
      })
      .attr('opacity', 0.7)
      .style('cursor', 'pointer')
      .on('mouseenter', function() {
        d3.select(this).attr('stroke', '#475569').attr('stroke-width', 3).attr('opacity', 1)
      })
      .on('mouseleave', function() {
        d3.select(this).attr('stroke', '#94a3b8').attr('stroke-width', 2.5).attr('opacity', 0.7)
      })
      .on('click', (_event, d) => {
        setSelectedLink(d.id)
        setSelectedNode(null)
      })

    // Draw link labels with background
    const linkLabelGroup = g.append('g')
      .selectAll('g')
      .data(links)
      .join('g')
      .attr('class', 'link-label-group')

    // Add background rect for better readability
    linkLabelGroup.append('rect')
      .attr('fill', 'white')
      .attr('rx', 4)
      .attr('ry', 4)
      .attr('opacity', 0.9)

    // Add text
    const linkLabel = linkLabelGroup.append('text')
      .attr('class', 'link-label')
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('fill', '#475569')
      .text(d => d.relationship.name)

    // Size background to text
    linkLabel.each(function() {
      const bbox = (this as SVGTextElement).getBBox()
      d3.select((this as SVGTextElement).parentNode as SVGGElement)
        .select('rect')
        .attr('x', bbox.x - 4)
        .attr('y', bbox.y - 2)
        .attr('width', bbox.width + 8)
        .attr('height', bbox.height + 4)
    })

    // Draw nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          // Keep position fixed after drag
          d.fx = event.x
          d.fy = event.y

          // Save all positions to layout.yml
          const positions: Record<string, { x: number; y: number }> = {}
          nodes.forEach(node => {
            if (node.x !== undefined && node.y !== undefined) {
              positions[node.id] = { x: node.x, y: node.y }
            }
          })
          saveLayout(positions)
        }))

    // Add rounded rectangles (boxes) to nodes
    node.append('rect')
      .attr('width', 140)
      .attr('height', 70)
      .attr('x', -70)
      .attr('y', -35)
      .attr('rx', 8)
      .attr('ry', 8)
      .attr('fill', d => d.color)
      .attr('stroke', '#334155')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseenter', function(event) {
        if (event.shiftKey) {
          d3.select(this).style('cursor', 'crosshair')
        }
        d3.select(this).attr('stroke-width', 3).attr('stroke', '#1e293b')
      })
      .on('mouseleave', function() {
        d3.select(this).style('cursor', 'pointer')
        d3.select(this).attr('stroke-width', 2).attr('stroke', '#334155')
      })
      .on('mousedown', (event, d) => {
        if (event.shiftKey) {
          // Start dragging a connection
          event.preventDefault()
          event.stopPropagation()
          const [x, y] = d3.pointer(event, svgRef.current)
          setDragConnection({ fromNodeId: d.id, x, y })
        }
      })
      .on('mouseup', (event, d) => {
        if (dragConnection && dragConnection.fromNodeId !== d.id) {
          // Complete the connection
          event.preventDefault()
          event.stopPropagation()
          setRelationshipDialog({ fromNodeId: dragConnection.fromNodeId, toNodeId: d.id })
          setDragConnection(null)
        }
      })
      .on('click', (event, d) => {
        if (!event.shiftKey && !dragConnection) {
          setSelectedNode(d.id)
          setSelectedLink(null)
        }
      })
      .on('contextmenu', (event, d) => {
        event.preventDefault()
        event.stopPropagation()
        setContextMenu({
          x: event.clientX,
          y: event.clientY,
          type: 'node',
          nodeId: d.id,
        })
      })

    // Add text to nodes with wrapping
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.3em')
      .attr('font-size', '13px')
      .attr('font-weight', '600')
      .attr('fill', '#1e293b')
      .attr('pointer-events', 'none')
      .each(function(d) {
        const text = d3.select(this)
        const words = d.label.split(/\s+/)
        const maxWidth = 120

        // Simple two-line wrapping
        if (words.length > 2) {
          const mid = Math.ceil(words.length / 2)
          text.append('tspan')
            .attr('x', 0)
            .attr('dy', '-0.5em')
            .text(words.slice(0, mid).join(' '))
          text.append('tspan')
            .attr('x', 0)
            .attr('dy', '1.2em')
            .text(words.slice(mid).join(' '))
        } else if (words.length > 1) {
          text.append('tspan')
            .attr('x', 0)
            .attr('dy', '-0.3em')
            .text(words[0])
          text.append('tspan')
            .attr('x', 0)
            .attr('dy', '1.2em')
            .text(words.slice(1).join(' '))
        } else {
          text.text(d.label)
        }
      })

    // Add status indicator icon in top-right corner with Lucide icons
    const statusGroup = node.append('g')
      .attr('transform', 'translate(55, -20)')
      .attr('pointer-events', 'none')

    // Complete: green circle-check
    statusGroup.filter(d => (d.concept.status || 'draft') === 'complete')
      .each(function() {
        const g = d3.select(this)
        g.append('circle')
          .attr('cx', 0)
          .attr('cy', 0)
          .attr('r', 5)
          .attr('fill', 'none')
          .attr('stroke', '#22c55e')
          .attr('stroke-width', 1.5)
        g.append('path')
          .attr('d', 'm-2 0 1 1 2-2')
          .attr('fill', 'none')
          .attr('stroke', '#22c55e')
          .attr('stroke-width', 1.5)
          .attr('stroke-linecap', 'round')
          .attr('stroke-linejoin', 'round')
      })

    // Draft: blue pencil
    statusGroup.filter(d => (d.concept.status || 'draft') === 'draft')
      .each(function() {
        const g = d3.select(this)
        g.append('path')
          .attr('d', 'M4.4-3.4a0.5 0.5 0 0 0-2-2L-4.1 1.1a1 1 0 0 0-0.25 0.42l-0.66 2.18a0.25 0.25 0 0 0 0.31 0.31l2.18-0.66a1 1 0 0 0 0.42-0.25z')
          .attr('fill', 'none')
          .attr('stroke', '#3b82f6')
          .attr('stroke-width', 1.2)
          .attr('stroke-linecap', 'round')
          .attr('stroke-linejoin', 'round')
        g.append('path')
          .attr('d', 'm1.5-2.5 2 2')
          .attr('fill', 'none')
          .attr('stroke', '#3b82f6')
          .attr('stroke-width', 1.2)
          .attr('stroke-linecap', 'round')
          .attr('stroke-linejoin', 'round')
      })

    // Stub: gray circle
    statusGroup.filter(d => (d.concept.status || 'draft') === 'stub')
      .append('circle')
      .attr('cx', 0)
      .attr('cy', 0)
      .attr('r', 5)
      .attr('fill', 'none')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 1.5)

    // Deprecated: red circle-x
    statusGroup.filter(d => (d.concept.status || 'draft') === 'deprecated')
      .each(function() {
        const g = d3.select(this)
        g.append('circle')
          .attr('cx', 0)
          .attr('cy', 0)
          .attr('r', 5)
          .attr('fill', 'none')
          .attr('stroke', '#ef4444')
          .attr('stroke-width', 1.5)
        g.append('path')
          .attr('d', 'm2-2-4 4')
          .attr('fill', 'none')
          .attr('stroke', '#ef4444')
          .attr('stroke-width', 1.5)
          .attr('stroke-linecap', 'round')
        g.append('path')
          .attr('d', 'm-2-2 4 4')
          .attr('fill', 'none')
          .attr('stroke', '#ef4444')
          .attr('stroke-width', 1.5)
          .attr('stroke-linecap', 'round')
      })

    // Add model count badges with Databricks brick icons inside the box
    const badgeGroup = node.append('g')
      .attr('class', 'medallion-badges')
      .attr('transform', 'translate(0, 18)')

    badgeGroup.each(function(d) {
      const bronzeCount = d.concept.bronze_models?.length || 0
      const silverCount = d.concept.silver_models?.length || 0
      const goldCount = d.concept.gold_models?.length || 0

      // Always show all three medallion badges
      const badges = [
        { color: '#CD7F32', count: bronzeCount, label: 'Bronze' },
        { color: '#C0C0C0', count: silverCount, label: 'Silver' },
        { color: '#FFD700', count: goldCount, label: 'Gold' }
      ]

      const group = d3.select(this)
      const totalWidth = badges.length * 30 - 5
      const startX = -totalWidth / 2

      badges.forEach((badge, i) => {
        const badgeX = startX + i * 30

        const badgeGroup = group.append('g')
          .attr('transform', `translate(${badgeX}, 0)`)

        // Databricks logo (layered brick pattern)
        // Scale and center the icon (original is in 24x24 viewBox)
        const scale = 0.5
        const offsetX = -6
        const offsetY = -5

        badgeGroup.append('path')
          .attr('d', 'M3 17l9 5l9 -5v-3l-9 5l-9 -5v-3l9 5l9 -5v-3l-9 5l-9 -5l9 -5l5.418 3.01')
          .attr('transform', `translate(${offsetX}, ${offsetY}) scale(${scale})`)
          .attr('fill', 'none')
          .attr('stroke', badge.color)
          .attr('stroke-width', 2)
          .attr('stroke-linecap', 'round')
          .attr('stroke-linejoin', 'round')

        // Count text
        badgeGroup.append('text')
          .attr('x', 7)
          .attr('y', 1)
          .attr('text-anchor', 'start')
          .attr('font-size', '9px')
          .attr('font-weight', '600')
          .attr('fill', '#1e293b')
          .text(badge.count)
      })
    })

    // Helper function for orthogonal routing (Visio-style)
    const getOrthogonalPath = (source: GraphNode, target: GraphNode): string => {
      const sx = source.x!
      const sy = source.y!
      const tx = target.x!
      const ty = target.y!

      // Box dimensions
      const boxWidth = 140
      const boxHeight = 70
      const halfWidth = boxWidth / 2
      const halfHeight = boxHeight / 2

      // Calculate which sides to connect
      const dx = tx - sx
      const dy = ty - sy

      // Determine start and end points on box edges
      let startX = sx
      let startY = sy
      let endX = tx
      let endY = ty

      // Start point (from source box)
      if (Math.abs(dx) > Math.abs(dy)) {
        // Horizontal connection
        startX = dx > 0 ? sx + halfWidth : sx - halfWidth
        startY = sy
      } else {
        // Vertical connection
        startX = sx
        startY = dy > 0 ? sy + halfHeight : sy - halfHeight
      }

      // End point (to target box)
      if (Math.abs(dx) > Math.abs(dy)) {
        // Horizontal connection
        endX = dx > 0 ? tx - halfWidth : tx + halfWidth
        endY = ty
      } else {
        // Vertical connection
        endX = tx
        endY = dy > 0 ? ty - halfHeight : ty + halfHeight
      }

      // Create orthogonal path with one or two bends
      const midX = (startX + endX) / 2
      const midY = (startY + endY) / 2

      // Simple orthogonal: horizontal then vertical, or vice versa
      if (Math.abs(dx) > Math.abs(dy)) {
        // Go horizontal first, then vertical
        return `M ${startX},${startY} L ${midX},${startY} L ${midX},${endY} L ${endX},${endY}`
      } else {
        // Go vertical first, then horizontal
        return `M ${startX},${startY} L ${startX},${midY} L ${endX},${midY} L ${endX},${endY}`
      }
    }

    // Add visual feedback for drag connection
    if (dragConnection) {
      const sourceNode = nodes.find(n => n.id === dragConnection.fromNodeId)
      if (sourceNode && sourceNode.x !== undefined && sourceNode.y !== undefined) {
        g.append('line')
          .attr('class', 'drag-connection-line')
          .attr('x1', sourceNode.x)
          .attr('y1', sourceNode.y)
          .attr('x2', dragConnection.x)
          .attr('y2', dragConnection.y)
          .attr('stroke', '#3b82f6')
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '5,5')
          .attr('opacity', 0.6)
          .attr('pointer-events', 'none')
      }
    }

    // Update positions on tick
    simulation.on('tick', () => {
      // Update orthogonal link paths
      link.attr('d', d => {
        const source = d.source as GraphNode
        const target = d.target as GraphNode
        return getOrthogonalPath(source, target)
      })

      // Update link labels
      linkLabelGroup.attr('transform', d => {
        const source = d.source as GraphNode
        const target = d.target as GraphNode
        const x = (source.x! + target.x!) / 2
        const y = (source.y! + target.y!) / 2
        return `translate(${x},${y})`
      })

      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [state, layout, dragConnection])

  return (
    <div className="graph-editor">
      <div className="graph-canvas">
        <svg ref={svgRef} className="graph-svg" />
        {contextMenu && (
          <div
            style={{
              position: 'fixed',
              left: contextMenu.x,
              top: contextMenu.y,
              backgroundColor: 'white',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              zIndex: 1000,
              minWidth: '160px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {contextMenu.type === 'canvas' ? (
              <div
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
                onClick={() => {
                  createNewConcept()
                  setContextMenu(null)
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f1f5f9')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'white')}
              >
                Add New Concept
              </div>
            ) : (
              <div
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
                onClick={() => {
                  if (contextMenu.nodeId) {
                    createNewRelationship(contextMenu.nodeId)
                  }
                  setContextMenu(null)
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f1f5f9')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'white')}
              >
                Add New Relationship
              </div>
            )}
          </div>
        )}
        {relationshipDialog && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 2000,
            }}
            onClick={() => setRelationshipDialog(null)}
          >
            <div
              style={{
                backgroundColor: 'white',
                borderRadius: '8px',
                padding: '24px',
                maxWidth: '500px',
                width: '90%',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
                Create Relationship
              </h3>
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  const formData = new FormData(e.currentTarget)
                  const relationshipName = formData.get('name') as string
                  const cardinality = formData.get('cardinality') as string

                  if (!relationshipName) {
                    alert('Please enter a relationship name')
                    return
                  }

                  const relationshipId = `${relationshipDialog.fromNodeId}_${relationshipName}_${relationshipDialog.toNodeId}`.toLowerCase().replace(/\s+/g, '_')

                  setState({
                    ...state,
                    relationships: {
                      ...state.relationships,
                      [relationshipId]: {
                        name: relationshipName,
                        from_concept: relationshipDialog.fromNodeId,
                        to_concept: relationshipDialog.toNodeId,
                        cardinality: cardinality || undefined,
                        realized_by: [],
                      },
                    },
                  })
                  setSelectedLink(relationshipId)
                  setRelationshipDialog(null)
                }}
              >
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>
                    From:
                  </label>
                  <div style={{ padding: '8px 12px', backgroundColor: '#f1f5f9', borderRadius: '4px', fontSize: '14px' }}>
                    {state.concepts[relationshipDialog.fromNodeId]?.name || relationshipDialog.fromNodeId}
                  </div>
                </div>
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>
                    To:
                  </label>
                  <div style={{ padding: '8px 12px', backgroundColor: '#f1f5f9', borderRadius: '4px', fontSize: '14px' }}>
                    {state.concepts[relationshipDialog.toNodeId]?.name || relationshipDialog.toNodeId}
                  </div>
                </div>
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>
                    Relationship Name: *
                  </label>
                  <input
                    type="text"
                    name="name"
                    placeholder="e.g., places, contains, belongs to"
                    required
                    autoFocus
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #cbd5e1',
                      borderRadius: '4px',
                      fontSize: '14px',
                    }}
                  />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500', fontSize: '14px' }}>
                    Cardinality:
                  </label>
                  <select
                    name="cardinality"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #cbd5e1',
                      borderRadius: '4px',
                      fontSize: '14px',
                    }}
                  >
                    <option value="">Not specified</option>
                    <option value="1:1">1:1 (One to One)</option>
                    <option value="1:N">1:N (One to Many)</option>
                    <option value="N:1">N:1 (Many to One)</option>
                    <option value="N:M">N:M (Many to Many)</option>
                  </select>
                </div>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    onClick={() => setRelationshipDialog(null)}
                    style={{
                      padding: '8px 16px',
                      border: '1px solid #cbd5e1',
                      borderRadius: '4px',
                      backgroundColor: 'white',
                      cursor: 'pointer',
                      fontSize: '14px',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: '8px 16px',
                      border: 'none',
                      borderRadius: '4px',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                    }}
                  >
                    Create
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
      <div className="graph-sidebar">
        {selectedNode && (
          <ConceptPanel
            conceptId={selectedNode}
            concept={state.concepts[selectedNode]}
            state={state}
            setState={setState}
            onClose={() => setSelectedNode(null)}
            availableModels={availableModels}
          />
        )}
        {selectedLink && (
          <RelationshipPanel
            relationshipId={selectedLink}
            relationship={state.relationships[selectedLink]}
            state={state}
            setState={setState}
            onClose={() => setSelectedLink(null)}
            availableModels={availableModels}
          />
        )}
        {!selectedNode && !selectedLink && (
          <div className="sidebar-placeholder">
            <p>Click on a concept or relationship to edit</p>
            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '6px', fontSize: '13px', color: '#0c4a6e' }}>
              <div style={{ fontWeight: '600', marginBottom: '8px' }}>Quick Actions:</div>
              <div style={{ marginBottom: '4px' }}>• Right-click canvas → Add Concept</div>
              <div style={{ marginBottom: '4px' }}>• Hold <kbd style={{ padding: '2px 6px', backgroundColor: 'white', border: '1px solid #cbd5e1', borderRadius: '3px', fontSize: '12px' }}>Shift</kbd> + drag from one concept to another → Create Relationship</div>
              <div>• Right-click concept → Add Relationship</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

interface ConceptPanelProps {
  conceptId: string
  concept: Concept
  state: State
  setState: (state: State) => void
  onClose: () => void
  availableModels: { silver: string[]; gold: string[] }
}

function ConceptPanel({ conceptId, concept, state, setState, onClose, availableModels }: ConceptPanelProps) {
  const [customDomain, setCustomDomain] = useState('')
  const [customOwner, setCustomOwner] = useState('')
  const [activeTab, setActiveTab] = useState<'properties' | 'models'>('properties')
  const [modelLayerTab, setModelLayerTab] = useState<'bronze' | 'silver' | 'gold'>('bronze')

  // Get unique owners from all concepts
  const existingOwners = Array.from(new Set(
    Object.values(state.concepts)
      .map(c => c.owner)
      .filter(o => o && o.trim() !== '')
  )).sort()

  // Update concept directly in state (instant save)
  const updateConcept = (updates: Partial<Concept>) => {
    setState({
      ...state,
      concepts: {
        ...state.concepts,
        [conceptId]: { ...concept, ...updates },
      },
    })
  }

  // Sort models: selected first, then unselected alphabetically
  const getSortedModels = (allModels: string[], selectedModels: string[]) => {
    const selected = allModels.filter(m => selectedModels.includes(m)).sort()
    const unselected = allModels.filter(m => !selectedModels.includes(m)).sort()
    return [...selected, ...unselected]
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>{concept.name}</h3>
        <button onClick={onClose}>✕</button>
      </div>
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc' }}>
        <button
          onClick={() => setActiveTab('properties')}
          style={{
            flex: 1,
            padding: '12px',
            border: 'none',
            background: activeTab === 'properties' ? 'white' : 'transparent',
            borderBottom: activeTab === 'properties' ? '2px solid #3b82f6' : '2px solid transparent',
            cursor: 'pointer',
            fontWeight: activeTab === 'properties' ? '600' : '400',
            color: activeTab === 'properties' ? '#1e293b' : '#64748b'
          }}
        >
          Properties
        </button>
        <button
          onClick={() => setActiveTab('models')}
          style={{
            flex: 1,
            padding: '12px',
            border: 'none',
            background: activeTab === 'models' ? 'white' : 'transparent',
            borderBottom: activeTab === 'models' ? '2px solid #3b82f6' : '2px solid transparent',
            cursor: 'pointer',
            fontWeight: activeTab === 'models' ? '600' : '400',
            color: activeTab === 'models' ? '#1e293b' : '#64748b'
          }}
        >
          Models ({(concept.bronze_models?.length || 0) + (concept.silver_models?.length || 0) + (concept.gold_models?.length || 0)})
        </button>
      </div>
      <div className="panel-content">{activeTab === 'properties' ? (
        // Properties Tab
        <>
        <label>
          Name:
          <input
            type="text"
            value={concept.name}
            onChange={(e) => updateConcept({ name: e.target.value })}
          />
        </label>
        <label>
          Description (Markdown):
          <textarea
            value={concept.description || ''}
            onChange={(e) => updateConcept({ description: e.target.value })}
            placeholder="Supports markdown formatting..."
            rows={6}
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
        </label>
        <label>
          Domain:
          <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
            <select
              value={concept.domain || ''}
              onChange={(e) => {
                if (e.target.value === '__custom__') {
                  setCustomDomain('')
                } else {
                  updateConcept({ domain: e.target.value })
                  setCustomDomain('')
                }
              }}
              style={{ flex: 1 }}
            >
              <option value="">None</option>
              {Object.keys(state.domains).map((domainId) => (
                <option key={domainId} value={domainId}>
                  {state.domains[domainId].name}
                </option>
              ))}
              <option value="__custom__">+ Add new domain...</option>
            </select>
          </div>
          {(concept.domain === '' || customDomain !== '') && (
            <input
              type="text"
              value={customDomain}
              onChange={(e) => {
                setCustomDomain(e.target.value)
                updateConcept({ domain: e.target.value })
              }}
              placeholder="Enter new domain ID (e.g., 'sales', 'finance')"
              style={{ marginTop: '8px' }}
            />
          )}
          {concept.domain && (
            <div style={{ marginTop: '8px' }}>
              <label style={{ fontSize: '12px', color: '#64748b' }}>
                Domain Color:
                <select
                  value={concept.domain && state.domains[concept.domain]?.color || ''}
                  onChange={(e) => {
                    if (concept.domain) {
                      setState({
                        ...state,
                        domains: {
                          ...state.domains,
                          [concept.domain]: {
                            ...state.domains[concept.domain],
                            name: state.domains[concept.domain]?.name || concept.domain,
                            display_name: state.domains[concept.domain]?.display_name || concept.domain,
                            color: e.target.value,
                          }
                        }
                      })
                    }
                  }}
                  style={{ marginTop: '4px', width: '100%' }}
                >
                  <option value="">Default (Light Blue)</option>
                  <option value="#e9ecef" style={{backgroundColor: '#e9ecef'}}>⬜ Gray</option>
                  <option value="#ffc9c9" style={{backgroundColor: '#ffc9c9'}}>🟥 Red</option>
                  <option value="#ffd8a8" style={{backgroundColor: '#ffd8a8'}}>🟧 Orange</option>
                  <option value="#ffec99" style={{backgroundColor: '#ffec99'}}>🟨 Yellow</option>
                  <option value="#b2f2bb" style={{backgroundColor: '#b2f2bb'}}>🟩 Green</option>
                  <option value="#a5d8ff" style={{backgroundColor: '#a5d8ff'}}>🟦 Cyan</option>
                  <option value="#91a7ff" style={{backgroundColor: '#91a7ff'}}>🟦 Blue</option>
                  <option value="#d0bfff" style={{backgroundColor: '#d0bfff'}}>🟪 Purple</option>
                  <option value="#fcc2d7" style={{backgroundColor: '#fcc2d7'}}>🟪 Pink</option>
                </select>
              </label>
            </div>
          )}
        </label>
        <label>
          Owner:
          <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
            <select
              value={concept.owner || ''}
              onChange={(e) => {
                if (e.target.value === '__custom__') {
                  setCustomOwner('')
                } else {
                  updateConcept({ owner: e.target.value })
                  setCustomOwner('')
                }
              }}
              style={{ flex: 1 }}
            >
              <option value="">None</option>
              {existingOwners.map((owner) => (
                <option key={owner} value={owner}>
                  {owner}
                </option>
              ))}
              <option value="__custom__">+ Add new owner...</option>
            </select>
          </div>
          {(concept.owner === '' || customOwner !== '') && (
            <input
              type="text"
              value={customOwner}
              onChange={(e) => {
                setCustomOwner(e.target.value)
                updateConcept({ owner: e.target.value })
              }}
              placeholder="Enter owner name (e.g., 'data_team', 'analytics')"
              style={{ marginTop: '8px' }}
            />
          )}
        </label>
        <label>
          Status:
          <select
            value={concept.status || 'draft'}
            onChange={(e) => updateConcept({ status: e.target.value as any })}
          >
            <option value="draft">Draft</option>
            <option value="complete">Complete</option>
            <option value="stub">Stub</option>
            <option value="deprecated">Deprecated</option>
          </select>
        </label>
        <label>
          Color:
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="color"
              value={concept.color || (concept.domain && state.domains[concept.domain]?.color) || '#E3F2FD'}
              onChange={(e) => updateConcept({ color: e.target.value })}
              style={{ width: '60px', height: '36px', cursor: 'pointer' }}
            />
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              {concept.color ? 'Custom' : `From ${concept.domain || 'default'}`}
            </span>
            {concept.color && (
              <button
                type="button"
                onClick={() => updateConcept({ color: undefined })}
                style={{ padding: '4px 8px', fontSize: '12px' }}
              >
                Reset
              </button>
            )}
          </div>
        </label>
        </>
      ) : (
        // Models Tab
        <>
        <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f1f5f9', marginBottom: '12px' }}>
          <button
            onClick={() => setModelLayerTab('bronze')}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              background: modelLayerTab === 'bronze' ? 'white' : 'transparent',
              borderBottom: modelLayerTab === 'bronze' ? '2px solid #3b82f6' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: modelLayerTab === 'bronze' ? '600' : '400',
              color: modelLayerTab === 'bronze' ? '#1e293b' : '#64748b',
              fontSize: '13px'
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" style={{ display: 'inline-block', marginRight: '6px', verticalAlign: 'middle' }}>
              <path d="M3 17l9 5l9 -5v-3l-9 5l-9 -5v-3l9 5l9 -5v-3l-9 5l-9 -5l9 -5l5.418 3.01" fill="none" stroke="#CD7F32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Bronze ({concept.bronze_models?.length || 0})
          </button>
          <button
            onClick={() => setModelLayerTab('silver')}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              background: modelLayerTab === 'silver' ? 'white' : 'transparent',
              borderBottom: modelLayerTab === 'silver' ? '2px solid #3b82f6' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: modelLayerTab === 'silver' ? '600' : '400',
              color: modelLayerTab === 'silver' ? '#1e293b' : '#64748b',
              fontSize: '13px'
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" style={{ display: 'inline-block', marginRight: '6px', verticalAlign: 'middle' }}>
              <path d="M3 17l9 5l9 -5v-3l-9 5l-9 -5v-3l9 5l9 -5v-3l-9 5l-9 -5l9 -5l5.418 3.01" fill="none" stroke="#C0C0C0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Silver ({concept.silver_models?.length || 0})
          </button>
          <button
            onClick={() => setModelLayerTab('gold')}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              background: modelLayerTab === 'gold' ? 'white' : 'transparent',
              borderBottom: modelLayerTab === 'gold' ? '2px solid #3b82f6' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: modelLayerTab === 'gold' ? '600' : '400',
              color: modelLayerTab === 'gold' ? '#1e293b' : '#64748b',
              fontSize: '13px'
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" style={{ display: 'inline-block', marginRight: '6px', verticalAlign: 'middle' }}>
              <path d="M3 17l9 5l9 -5v-3l-9 5l-9 -5v-3l9 5l9 -5v-3l-9 5l-9 -5l9 -5l5.418 3.01" fill="none" stroke="#FFD700" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Gold ({concept.gold_models?.length || 0})
          </button>
        </div>

        {modelLayerTab === 'bronze' ? (
          <div>
            <div style={{ marginBottom: '12px', padding: '8px', backgroundColor: '#fef3c7', border: '1px solid #fcd34d', borderRadius: '4px', fontSize: '12px', color: '#78350f' }}>
              Bronze sources are automatically discovered from manifest.json (run dbt parse/compile first)
            </div>
            <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px', backgroundColor: '#f8fafc' }}>
              {concept.bronze_models?.length === 0 ? (
                <div style={{ padding: '8px', color: '#64748b', fontSize: '13px' }}>No bronze sources found</div>
              ) : (
                concept.bronze_models?.map(model => (
                  <div key={model} style={{ padding: '6px 4px', fontFamily: 'monospace', fontSize: '13px', color: '#1e293b' }}>
                    {model}
                  </div>
                ))
              )}
            </div>
          </div>
        ) : modelLayerTab === 'silver' ? (
          <div>
            <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px', backgroundColor: '#f8fafc' }}>
              {availableModels.silver.length === 0 ? (
                <div style={{ padding: '8px', color: '#64748b', fontSize: '13px' }}>No silver models found</div>
              ) : (
                getSortedModels(availableModels.silver, concept.silver_models || []).map(model => (
                  <label key={model} style={{ display: 'flex', alignItems: 'center', padding: '6px 4px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={concept.silver_models?.includes(model) || false}
                      onChange={(e) => {
                        if (e.target.checked) {
                          updateConcept({
                            silver_models: [...(concept.silver_models || []), model]
                          })
                        } else {
                          updateConcept({
                            silver_models: (concept.silver_models || []).filter(m => m !== model)
                          })
                        }
                      }}
                      style={{ width: '16px', height: '16px', margin: '0 8px 0 0', flexShrink: 0 }}
                    />
                    <span style={{ fontFamily: 'monospace', fontSize: '13px', flex: 1 }}>{model}</span>
                  </label>
                ))
              )}
            </div>
          </div>
        ) : (
          <div>
            <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px', backgroundColor: '#f8fafc' }}>
              {availableModels.gold.length === 0 ? (
                <div style={{ padding: '8px', color: '#64748b', fontSize: '13px' }}>No gold models found</div>
              ) : (
                getSortedModels(availableModels.gold, concept.gold_models || []).map(model => (
                  <label key={model} style={{ display: 'flex', alignItems: 'center', padding: '6px 4px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={concept.gold_models?.includes(model) || false}
                      onChange={(e) => {
                        if (e.target.checked) {
                          updateConcept({
                            gold_models: [...(concept.gold_models || []), model]
                          })
                        } else {
                          updateConcept({
                            gold_models: (concept.gold_models || []).filter(m => m !== model)
                          })
                        }
                      }}
                      style={{ width: '16px', height: '16px', margin: '0 8px 0 0', flexShrink: 0 }}
                    />
                    <span style={{ fontFamily: 'monospace', fontSize: '13px', flex: 1 }}>{model}</span>
                  </label>
                ))
              )}
            </div>
          </div>
        )}
        </>
      )}
      </div>
    </div>
  )
}

interface RelationshipPanelProps {
  relationshipId: string
  relationship: Relationship
  state: State
  setState: (state: State) => void
  onClose: () => void
  availableModels: { silver: string[]; gold: string[] }
}

function RelationshipPanel({ relationshipId, relationship, state, setState, onClose, availableModels }: RelationshipPanelProps) {
  const [activeTab, setActiveTab] = useState<'properties' | 'models'>('properties')

  // Update relationship directly in state (instant save)
  const updateRelationship = (updates: Partial<Relationship>) => {
    setState({
      ...state,
      relationships: {
        ...state.relationships,
        [relationshipId]: { ...relationship, ...updates },
      },
    })
  }

  // Sort models: selected first, then unselected alphabetically
  const getSortedModels = (allModels: string[], selectedModels: string[]) => {
    const selected = allModels.filter(m => selectedModels.includes(m)).sort()
    const unselected = allModels.filter(m => !selectedModels.includes(m)).sort()
    return [...selected, ...unselected]
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>{editedRel.name}</h3>
        <button onClick={onClose}>✕</button>
      </div>
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc' }}>
        <button
          onClick={() => setActiveTab('properties')}
          style={{
            flex: 1,
            padding: '12px',
            border: 'none',
            background: activeTab === 'properties' ? 'white' : 'transparent',
            borderBottom: activeTab === 'properties' ? '2px solid #3b82f6' : '2px solid transparent',
            cursor: 'pointer',
            fontWeight: activeTab === 'properties' ? '600' : '400',
            color: activeTab === 'properties' ? '#1e293b' : '#64748b'
          }}
        >
          Properties
        </button>
        <button
          onClick={() => setActiveTab('models')}
          style={{
            flex: 1,
            padding: '12px',
            border: 'none',
            background: activeTab === 'models' ? 'white' : 'transparent',
            borderBottom: activeTab === 'models' ? '2px solid #3b82f6' : '2px solid transparent',
            cursor: 'pointer',
            fontWeight: activeTab === 'models' ? '600' : '400',
            color: activeTab === 'models' ? '#1e293b' : '#64748b'
          }}
        >
          Models ({editedRel.realized_by?.length || 0})
        </button>
      </div>
      <div className="panel-content">{activeTab === 'properties' ? (
        <>
        <label>
          Name:
          <input
            type="text"
            value={relationship.name}
            onChange={(e) => updateRelationship({ name: e.target.value })}
          />
        </label>
        <label>
          From:
          <select
            value={relationship.from_concept}
            onChange={(e) => updateRelationship({ from_concept: e.target.value })}
          >
            {Object.entries(state.concepts).map(([id, concept]) => (
              <option key={id} value={id}>{concept.name}</option>
            ))}
          </select>
        </label>
        <label>
          To:
          <select
            value={relationship.to_concept}
            onChange={(e) => updateRelationship({ to_concept: e.target.value })}
          >
            {Object.entries(state.concepts).map(([id, concept]) => (
              <option key={id} value={id}>{concept.name}</option>
            ))}
          </select>
        </label>
        <label>
          Cardinality (informational):
          <select
            value={relationship.cardinality || ''}
            onChange={(e) => updateRelationship({ cardinality: e.target.value })}
          >
            <option value="">Not specified</option>
            <option value="1:1">1:1 (One to One)</option>
            <option value="1:N">1:N (One to Many)</option>
            <option value="N:1">N:1 (Many to One)</option>
            <option value="N:M">N:M (Many to Many)</option>
          </select>
          <small style={{ display: 'block', marginTop: '4px', color: '#64748b', fontSize: '11px' }}>
            Note: Cardinality is for documentation only and is not enforced.
          </small>
        </label>
        <label>
          Description (Markdown):
          <textarea
            value={relationship.description || ''}
            onChange={(e) => updateRelationship({ description: e.target.value })}
            placeholder="Supports markdown formatting..."
            rows={6}
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
        </label>
        </>
      ) : (
        <>
        <div style={{ marginTop: '8px' }}>
          <label>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span>Realized By Models ({relationship.realized_by?.length || 0}):</span>
            </div>
            <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px', backgroundColor: '#f8fafc' }}>
              {[...availableModels.silver, ...availableModels.gold].length === 0 ? (
                <div style={{ padding: '8px', color: '#64748b', fontSize: '13px' }}>No models found</div>
              ) : (
                getSortedModels([...availableModels.silver, ...availableModels.gold], relationship.realized_by || []).map(model => (
                  <label key={model} style={{ display: 'flex', alignItems: 'center', padding: '6px 4px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={relationship.realized_by?.includes(model) || false}
                      onChange={(e) => {
                        if (e.target.checked) {
                          updateRelationship({
                            realized_by: [...(relationship.realized_by || []), model]
                          })
                        } else {
                          updateRelationship({
                            realized_by: (relationship.realized_by || []).filter(m => m !== model)
                          })
                        }
                      }}
                      style={{ width: '16px', height: '16px', margin: '0 8px 0 0', flexShrink: 0 }}
                    />
                    <span style={{ fontFamily: 'monospace', fontSize: '13px', flex: 1 }}>{model}</span>
                  </label>
                ))
              )}
            </div>
          </label>
        </div>
        </>
      )}
      </div>
    </div>
  )
}
