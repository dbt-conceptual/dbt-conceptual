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

  // Save layout when positions change (debounced)
  const saveLayout = (positions: Record<string, { x: number; y: number }>) => {
    fetch('/api/layout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ positions }),
    }).catch(err => console.error('Failed to save layout:', err))
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
        color: concept.domain && state.domains[concept.domain]?.color
          ? state.domains[concept.domain].color
          : '#E3F2FD',
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

    // Draw links with curved paths
    const link = g.append('g')
      .selectAll('path')
      .data(links)
      .join('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2.5)
      .attr('marker-end', 'url(#arrowhead)')
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
      .on('mouseenter', function() {
        d3.select(this).attr('stroke-width', 3).attr('stroke', '#1e293b')
      })
      .on('mouseleave', function() {
        d3.select(this).attr('stroke-width', 2).attr('stroke', '#334155')
      })
      .on('click', (_event, d) => {
        setSelectedNode(d.id)
        setSelectedLink(null)
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

    // Add status badge
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.8em')
      .attr('font-size', '9px')
      .attr('font-weight', '500')
      .attr('pointer-events', 'none')
      .attr('fill', '#64748b')
      .style('text-transform', 'uppercase')
      .style('letter-spacing', '0.5px')
      .text(d => d.concept.status || 'draft')

    // Add model count badges
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.6em')
      .attr('font-size', '10px')
      .attr('font-weight', '400')
      .attr('pointer-events', 'none')
      .attr('fill', '#64748b')
      .text(d => {
        const silverCount = d.concept.silver_models?.length || 0
        const goldCount = d.concept.gold_models?.length || 0
        if (silverCount === 0 && goldCount === 0) return ''
        const parts = []
        if (silverCount > 0) parts.push(`📊 ${silverCount}`)
        if (goldCount > 0) parts.push(`💎 ${goldCount}`)
        return parts.join('  ')
      })

    // Add arrow marker with better styling
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 78) // Adjusted for box width
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 10)
      .attr('markerHeight', 10)
      .append('svg:path')
      .attr('d', 'M 0,-4 L 8,0 L 0,4 Z')
      .attr('fill', '#94a3b8')

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
  }, [state, layout])

  return (
    <div className="graph-editor">
      <div className="graph-canvas">
        <svg ref={svgRef} className="graph-svg" />
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
            <button className="add-concept-btn">+ Add Concept</button>
            <button className="add-relationship-btn">+ Add Relationship</button>
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
  const [editedConcept, setEditedConcept] = useState(concept)
  const [customDomain, setCustomDomain] = useState('')
  const [customOwner, setCustomOwner] = useState('')
  const [newSilverModel, setNewSilverModel] = useState('')
  const [newGoldModel, setNewGoldModel] = useState('')

  // Get unique owners from all concepts
  const existingOwners = Array.from(new Set(
    Object.values(state.concepts)
      .map(c => c.owner)
      .filter(o => o && o.trim() !== '')
  )).sort()

  const handleSave = () => {
    setState({
      ...state,
      concepts: {
        ...state.concepts,
        [conceptId]: editedConcept,
      },
    })
    onClose()
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Properties</h3>
        <button onClick={onClose}>✕</button>
      </div>
      <div className="panel-content">
        <label>
          Name:
          <input
            type="text"
            value={editedConcept.name}
            onChange={(e) => setEditedConcept({ ...editedConcept, name: e.target.value })}
          />
        </label>
        <label>
          Description (Markdown):
          <textarea
            value={editedConcept.description || ''}
            onChange={(e) => setEditedConcept({ ...editedConcept, description: e.target.value })}
            placeholder="Supports markdown formatting..."
            rows={6}
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
        </label>
        <label>
          Domain:
          <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
            <select
              value={editedConcept.domain || ''}
              onChange={(e) => {
                if (e.target.value === '__custom__') {
                  setCustomDomain('')
                } else {
                  setEditedConcept({ ...editedConcept, domain: e.target.value })
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
          {(editedConcept.domain === '' || customDomain !== '') && (
            <input
              type="text"
              value={customDomain}
              onChange={(e) => {
                setCustomDomain(e.target.value)
                setEditedConcept({ ...editedConcept, domain: e.target.value })
              }}
              placeholder="Enter new domain ID (e.g., 'sales', 'finance')"
              style={{ marginTop: '8px' }}
            />
          )}
          {editedConcept.domain && (
            <div style={{ marginTop: '8px' }}>
              <label style={{ fontSize: '12px', color: '#64748b' }}>
                Domain Color:
                <select
                  value={editedConcept.domain && state.domains[editedConcept.domain]?.color || ''}
                  onChange={(e) => {
                    if (editedConcept.domain) {
                      setState({
                        ...state,
                        domains: {
                          ...state.domains,
                          [editedConcept.domain]: {
                            ...state.domains[editedConcept.domain],
                            name: state.domains[editedConcept.domain]?.name || editedConcept.domain,
                            display_name: state.domains[editedConcept.domain]?.display_name || editedConcept.domain,
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
              value={editedConcept.owner || ''}
              onChange={(e) => {
                if (e.target.value === '__custom__') {
                  setCustomOwner('')
                } else {
                  setEditedConcept({ ...editedConcept, owner: e.target.value })
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
          {(editedConcept.owner === '' || customOwner !== '') && (
            <input
              type="text"
              value={customOwner}
              onChange={(e) => {
                setCustomOwner(e.target.value)
                setEditedConcept({ ...editedConcept, owner: e.target.value })
              }}
              placeholder="Enter owner name (e.g., 'data_team', 'analytics')"
              style={{ marginTop: '8px' }}
            />
          )}
        </label>
        <label>
          Status:
          <select
            value={editedConcept.status || 'draft'}
            onChange={(e) => setEditedConcept({ ...editedConcept, status: e.target.value as any })}
          >
            <option value="draft">Draft</option>
            <option value="complete">Complete</option>
            <option value="stub">Stub</option>
            <option value="deprecated">Deprecated</option>
          </select>
        </label>

        <div style={{ marginTop: '24px', borderTop: '1px solid #e2e8f0', paddingTop: '16px' }}>
          <label>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span>Silver Models ({editedConcept.silver_models?.length || 0}):</span>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <input
                type="text"
                value={newSilverModel}
                onChange={(e) => setNewSilverModel(e.target.value)}
                placeholder="Enter model name..."
                style={{ flex: 1 }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && newSilverModel.trim()) {
                    setEditedConcept({
                      ...editedConcept,
                      silver_models: [...(editedConcept.silver_models || []), newSilverModel.trim()]
                    })
                    setNewSilverModel('')
                  }
                }}
              />
              <button
                type="button"
                onClick={() => {
                  if (newSilverModel.trim()) {
                    setEditedConcept({
                      ...editedConcept,
                      silver_models: [...(editedConcept.silver_models || []), newSilverModel.trim()]
                    })
                    setNewSilverModel('')
                  }
                }}
                style={{ padding: '6px 12px', fontSize: '14px' }}
              >
                Add
              </button>
            </div>
            {editedConcept.silver_models && editedConcept.silver_models.length > 0 && (
              <div style={{ maxHeight: '120px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px' }}>
                {editedConcept.silver_models.map((model, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                    <span style={{ fontSize: '13px', fontFamily: 'monospace' }}>{model}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setEditedConcept({
                          ...editedConcept,
                          silver_models: editedConcept.silver_models.filter((_, i) => i !== idx)
                        })
                      }}
                      style={{ padding: '2px 8px', fontSize: '12px', color: '#ef4444' }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </label>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span>Gold Models ({editedConcept.gold_models?.length || 0}):</span>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <input
                type="text"
                value={newGoldModel}
                onChange={(e) => setNewGoldModel(e.target.value)}
                placeholder="Enter model name..."
                style={{ flex: 1 }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && newGoldModel.trim()) {
                    setEditedConcept({
                      ...editedConcept,
                      gold_models: [...(editedConcept.gold_models || []), newGoldModel.trim()]
                    })
                    setNewGoldModel('')
                  }
                }}
              />
              <button
                type="button"
                onClick={() => {
                  if (newGoldModel.trim()) {
                    setEditedConcept({
                      ...editedConcept,
                      gold_models: [...(editedConcept.gold_models || []), newGoldModel.trim()]
                    })
                    setNewGoldModel('')
                  }
                }}
                style={{ padding: '6px 12px', fontSize: '14px' }}
              >
                Add
              </button>
            </div>
            {editedConcept.gold_models && editedConcept.gold_models.length > 0 && (
              <div style={{ maxHeight: '120px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px' }}>
                {editedConcept.gold_models.map((model, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                    <span style={{ fontSize: '13px', fontFamily: 'monospace' }}>{model}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setEditedConcept({
                          ...editedConcept,
                          gold_models: editedConcept.gold_models.filter((_, i) => i !== idx)
                        })
                      }}
                      style={{ padding: '2px 8px', fontSize: '12px', color: '#ef4444' }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </label>
        </div>

        <button onClick={handleSave} className="save-panel-btn" style={{ marginTop: '16px' }}>Save Changes</button>
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
  const [editedRel, setEditedRel] = useState(relationship)
  const [newRealizedByModel, setNewRealizedByModel] = useState('')

  const handleSave = () => {
    setState({
      ...state,
      relationships: {
        ...state.relationships,
        [relationshipId]: editedRel,
      },
    })
    onClose()
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Edit Relationship</h3>
        <button onClick={onClose}>✕</button>
      </div>
      <div className="panel-content">
        <label>
          Name:
          <input
            type="text"
            value={editedRel.name}
            onChange={(e) => setEditedRel({ ...editedRel, name: e.target.value })}
          />
        </label>
        <label>
          From:
          <select
            value={editedRel.from_concept}
            onChange={(e) => setEditedRel({ ...editedRel, from_concept: e.target.value })}
          >
            {Object.entries(state.concepts).map(([id, concept]) => (
              <option key={id} value={id}>{concept.name}</option>
            ))}
          </select>
        </label>
        <label>
          To:
          <select
            value={editedRel.to_concept}
            onChange={(e) => setEditedRel({ ...editedRel, to_concept: e.target.value })}
          >
            {Object.entries(state.concepts).map(([id, concept]) => (
              <option key={id} value={id}>{concept.name}</option>
            ))}
          </select>
        </label>
        <label>
          Cardinality (informational):
          <select
            value={editedRel.cardinality || ''}
            onChange={(e) => setEditedRel({ ...editedRel, cardinality: e.target.value })}
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
            value={editedRel.description || ''}
            onChange={(e) => setEditedRel({ ...editedRel, description: e.target.value })}
            placeholder="Supports markdown formatting..."
            rows={6}
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
        </label>

        <div style={{ marginTop: '24px', borderTop: '1px solid #e2e8f0', paddingTop: '16px' }}>
          <label>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span>Realized By Models ({editedRel.realized_by?.length || 0}):</span>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <input
                type="text"
                value={newRealizedByModel}
                onChange={(e) => setNewRealizedByModel(e.target.value)}
                placeholder="Enter model name..."
                style={{ flex: 1 }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && newRealizedByModel.trim()) {
                    setEditedRel({
                      ...editedRel,
                      realized_by: [...(editedRel.realized_by || []), newRealizedByModel.trim()]
                    })
                    setNewRealizedByModel('')
                  }
                }}
              />
              <button
                type="button"
                onClick={() => {
                  if (newRealizedByModel.trim()) {
                    setEditedRel({
                      ...editedRel,
                      realized_by: [...(editedRel.realized_by || []), newRealizedByModel.trim()]
                    })
                    setNewRealizedByModel('')
                  }
                }}
                style={{ padding: '6px 12px', fontSize: '14px' }}
              >
                Add
              </button>
            </div>
            {editedRel.realized_by && editedRel.realized_by.length > 0 && (
              <div style={{ maxHeight: '120px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '8px' }}>
                {editedRel.realized_by.map((model, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
                    <span style={{ fontSize: '13px', fontFamily: 'monospace' }}>{model}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setEditedRel({
                          ...editedRel,
                          realized_by: editedRel.realized_by.filter((_, i) => i !== idx)
                        })
                      }}
                      style={{ padding: '2px 8px', fontSize: '12px', color: '#ef4444' }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </label>
        </div>

        <button onClick={handleSave} className="save-panel-btn" style={{ marginTop: '16px' }}>Save Changes</button>
      </div>
    </div>
  )
}
