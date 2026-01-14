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

  useEffect(() => {
    if (!svgRef.current) return

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Create graph data
    const nodes: GraphNode[] = Object.entries(state.concepts).map(([id, concept]) => ({
      id,
      label: concept.name,
      concept,
      domain: concept.domain,
      color: concept.domain && state.domains[concept.domain]?.color
        ? state.domains[concept.domain].color
        : '#E3F2FD',
    }))

    const links: GraphLink[] = Object.entries(state.relationships).map(([id, rel]) => ({
      id,
      source: rel.from_concept,
      target: rel.to_concept,
      relationship: rel,
    }))

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links)
        .id(d => d.id)
        .distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(60))

    // Create container for zoom
    const g = svg.append('g')

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Draw links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)')
      .on('click', (_event, d) => {
        setSelectedLink(d.id)
        setSelectedNode(null)
      })

    // Draw link labels
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(links)
      .join('text')
      .attr('class', 'link-label')
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#666')
      .text(d => d.relationship.name)

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
          d.fx = null
          d.fy = null
        }))

    // Add circles to nodes
    node.append('circle')
      .attr('r', 40)
      .attr('fill', d => d.color)
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .on('click', (_event, d) => {
        setSelectedNode(d.id)
        setSelectedLink(null)
      })

    // Add text to nodes
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.3em')
      .attr('font-size', '14px')
      .attr('font-weight', 'bold')
      .attr('pointer-events', 'none')
      .text(d => d.label)

    // Add status indicator
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.5em')
      .attr('font-size', '10px')
      .attr('pointer-events', 'none')
      .attr('fill', '#666')
      .text(d => d.concept.status || 'draft')

    // Add arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 50)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#999')

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as GraphNode).x!)
        .attr('y1', d => (d.source as GraphNode).y!)
        .attr('x2', d => (d.target as GraphNode).x!)
        .attr('y2', d => (d.target as GraphNode).y!)

      linkLabel
        .attr('x', d => ((d.source as GraphNode).x! + (d.target as GraphNode).x!) / 2)
        .attr('y', d => ((d.source as GraphNode).y! + (d.target as GraphNode).y!) / 2)

      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [state])

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
          />
        )}
        {selectedLink && (
          <RelationshipPanel
            relationshipId={selectedLink}
            relationship={state.relationships[selectedLink]}
            state={state}
            setState={setState}
            onClose={() => setSelectedLink(null)}
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
}

function ConceptPanel({ conceptId, concept, state, setState, onClose }: ConceptPanelProps) {
  const [editedConcept, setEditedConcept] = useState(concept)

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
        <h3>Edit Concept</h3>
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
          Definition:
          <textarea
            value={editedConcept.definition || ''}
            onChange={(e) => setEditedConcept({ ...editedConcept, definition: e.target.value })}
          />
        </label>
        <label>
          Domain:
          <select
            value={editedConcept.domain || ''}
            onChange={(e) => setEditedConcept({ ...editedConcept, domain: e.target.value })}
          >
            <option value="">None</option>
            {Object.keys(state.domains).map((domainId) => (
              <option key={domainId} value={domainId}>
                {state.domains[domainId].name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Owner:
          <input
            type="text"
            value={editedConcept.owner || ''}
            onChange={(e) => setEditedConcept({ ...editedConcept, owner: e.target.value })}
          />
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
        <button onClick={handleSave} className="save-panel-btn">Save Changes</button>
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
}

function RelationshipPanel({ relationshipId, relationship, state, setState, onClose }: RelationshipPanelProps) {
  const [editedRel, setEditedRel] = useState(relationship)

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
          Cardinality:
          <input
            type="text"
            value={editedRel.cardinality || ''}
            placeholder="e.g., 1:N, 1:1, N:M"
            onChange={(e) => setEditedRel({ ...editedRel, cardinality: e.target.value })}
          />
        </label>
        <button onClick={handleSave} className="save-panel-btn">Save Changes</button>
      </div>
    </div>
  )
}
