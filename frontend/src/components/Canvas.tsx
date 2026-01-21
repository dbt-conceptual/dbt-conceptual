import { useCallback, useEffect, useMemo, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useStore } from '../store';
import { ConceptNode, type ConceptNodeData } from './ConceptNode';
import { RelationshipEdge } from './RelationshipEdge';
import { applyAutoLayout, needsAutoLayout } from '../layout';

const nodeTypes = {
  concept: ConceptNode,
};

const edgeTypes = {
  relationship: RelationshipEdge,
};

export function Canvas() {
  const {
    concepts,
    relationships,
    positions,
    hasIntegrityErrors,
    fetchState,
    updatePositions,
    saveLayout,
    selectConcept,
    selectRelationship,
    clearSelection,
  } = useStore();

  // Track if we've applied auto-layout to avoid re-running
  const hasAppliedAutoLayout = useRef(false);

  // Load state on mount
  useEffect(() => {
    fetchState();
  }, [fetchState]);

  // Apply auto-layout when needed (no saved positions)
  useEffect(() => {
    if (
      !hasAppliedAutoLayout.current &&
      Object.keys(concepts).length > 0 &&
      needsAutoLayout(concepts, positions)
    ) {
      hasAppliedAutoLayout.current = true;
      const autoPositions = applyAutoLayout(concepts, relationships);
      updatePositions(autoPositions);
      // Save the auto-generated layout
      saveLayout().catch(console.error);
    }
  }, [concepts, relationships, positions, updatePositions, saveLayout]);

  // Convert concepts to React Flow nodes
  const initialNodes = useMemo(() => {
    return Object.entries(concepts).map(([conceptId, concept]) => ({
      id: conceptId,
      type: 'concept',
      position: positions[conceptId] || { x: 0, y: 0 },
      data: { concept, conceptId },
    }));
  }, [concepts, positions]);

  // Convert relationships to React Flow edges
  const initialEdges = useMemo(() => {
    return Object.entries(relationships).map(([relationshipId, relationship]) => ({
      id: relationshipId,
      type: 'relationship',
      source: relationship.from_concept,
      target: relationship.to_concept,
      data: { relationship, relationshipId },
      markerEnd: {
        type: 'arrowclosed' as const,
      },
    }));
  }, [relationships]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes/edges when state changes
  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  // Handle node position changes (updates local state during drag)
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChange(changes);

      // Extract position changes to keep store in sync
      const positionChanges = changes.filter(
        (change: any) => change.type === 'position' && change.position
      );

      if (positionChanges.length > 0) {
        const newPositions: Record<string, { x: number; y: number }> = {};
        positionChanges.forEach((change: any) => {
          if (change.position) {
            newPositions[change.id] = change.position;
          }
        });
        updatePositions(newPositions);
      }
    },
    [onNodesChange, updatePositions]
  );

  // Save layout when drag ends
  const handleNodeDragStop = useCallback(() => {
    saveLayout().catch(console.error);
  }, [saveLayout]);

  // Handle node selection
  const handleNodeClick = useCallback(
    (_event: any, node: any) => {
      selectConcept(node.id);
    },
    [selectConcept]
  );

  // Handle edge selection
  const handleEdgeClick = useCallback(
    (_event: any, edge: any) => {
      selectRelationship(edge.id);
    },
    [selectRelationship]
  );

  // Handle canvas click (clear selection)
  const handlePaneClick = useCallback(() => {
    clearSelection();
  }, [clearSelection]);

  // Show blocked state when integrity errors exist
  if (hasIntegrityErrors) {
    return (
      <div style={{ flex: 1, height: '100vh', position: 'relative' }}>
        <div className="canvas-blocked-overlay">
          <div className="canvas-blocked-x">✕</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={handleNodeDragStop}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node: any) => {
            const concept = (node.data as ConceptNodeData)?.concept;
            return concept?.color || 'var(--color-neutral-300)';
          }}
        />
      </ReactFlow>
    </div>
  );
}
