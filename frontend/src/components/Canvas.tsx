import { useCallback, useEffect, useMemo, useRef } from 'react';
import type { MouseEvent as ReactMouseEvent } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow,
  type NodeChange,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useStore } from '../store';
import type { Concept, Relationship } from '../types';
import { ConceptNode } from './ConceptNode';
import { RelationshipEdge } from './RelationshipEdge';
import { applyAutoLayout, needsAutoLayout } from '../layout';

// Typed React Flow node/edge for the concept canvas
type ConceptNodeData = { concept: Concept; conceptId: string };
type ConceptFlowNode = Node<ConceptNodeData, string>;
type RelationshipEdgeData = { relationship: Relationship; relationshipId: string };
type RelationshipFlowEdge = Edge<RelationshipEdgeData, string>;

const nodeTypes = {
  concept: ConceptNode,
};

const edgeTypes = {
  relationship: RelationshipEdge,
};

// Inner component that has access to React Flow instance
function CanvasInner() {
  const {
    concepts,
    relationships,
    positions,
    hasIntegrityErrors,
    fetchState,
    updatePositions,
    saveLayout,
    addMessage,
    selectConcept,
    selectRelationship,
    requestClearSelection,
    selectedConceptId,
    selectedRelationshipId,
  } = useStore();

  const { fitView } = useReactFlow();

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
      saveLayout().catch(() => {
        addMessage('error', 'Failed to save layout');
      });
    }
  }, [concepts, relationships, positions, updatePositions, saveLayout, addMessage]);

  // Track previous selection to detect changes from search
  const prevSelectedConceptId = useRef<string | null>(null);
  const prevSelectedRelationshipId = useRef<string | null>(null);

  // Center on selected node when selection changes (from search)
  useEffect(() => {
    // Only trigger if selection changed
    if (
      selectedConceptId !== prevSelectedConceptId.current ||
      selectedRelationshipId !== prevSelectedRelationshipId.current
    ) {
      prevSelectedConceptId.current = selectedConceptId;
      prevSelectedRelationshipId.current = selectedRelationshipId;

      // If a concept is selected, center on it
      if (selectedConceptId && positions[selectedConceptId]) {
        // Small delay to ensure nodes are rendered
        setTimeout(() => {
          fitView({
            nodes: [{ id: selectedConceptId }],
            duration: 300,
            padding: 0.5,
          });
        }, 50);
      }
      // If a relationship is selected, center on both connected nodes
      else if (selectedRelationshipId) {
        const relationship = relationships[selectedRelationshipId];
        if (relationship) {
          const nodeIds = [relationship.from_concept, relationship.to_concept].filter(
            (id) => positions[id]
          );
          if (nodeIds.length > 0) {
            setTimeout(() => {
              fitView({
                nodes: nodeIds.map((id) => ({ id })),
                duration: 300,
                padding: 0.3,
              });
            }, 50);
          }
        }
      }
    }
  }, [selectedConceptId, selectedRelationshipId, positions, relationships, fitView]);

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
    (changes: NodeChange<ConceptFlowNode>[]) => {
      onNodesChange(changes);

      // Extract position changes to keep store in sync
      const positionChanges = changes.filter(
        (change): change is NodeChange<ConceptFlowNode> & { type: 'position'; id: string; position: { x: number; y: number } } =>
          change.type === 'position' && 'position' in change && change.position != null
      );

      if (positionChanges.length > 0) {
        const newPositions: Record<string, { x: number; y: number }> = {};
        positionChanges.forEach((change) => {
          newPositions[change.id] = change.position;
        });
        updatePositions(newPositions);
      }
    },
    [onNodesChange, updatePositions]
  );

  // Save layout when drag ends
  const handleNodeDragStop = useCallback(() => {
    saveLayout().catch(() => {
      addMessage('error', 'Failed to save layout');
    });
  }, [saveLayout, addMessage]);

  // Handle node selection
  const handleNodeClick = useCallback(
    (_event: ReactMouseEvent, node: ConceptFlowNode) => {
      selectConcept(node.id);
    },
    [selectConcept]
  );

  // Handle edge selection
  const handleEdgeClick = useCallback(
    (_event: ReactMouseEvent, edge: RelationshipFlowEdge) => {
      selectRelationship(edge.id);
    },
    [selectRelationship]
  );

  // Handle canvas click (clear selection)
  const handlePaneClick = useCallback(() => {
    requestClearSelection();
  }, [requestClearSelection]);

  // Show blocked state when integrity errors exist
  if (hasIntegrityErrors) {
    return (
      <div className="canvas-container--blocked">
        <div className="canvas-blocked-overlay">
          <div className="canvas-blocked-x">✕</div>
        </div>
      </div>
    );
  }

  return (
    <div className="canvas-container">
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
      </ReactFlow>
    </div>
  );
}

// Wrapper component that provides React Flow context
export function Canvas() {
  return (
    <ReactFlowProvider>
      <CanvasInner />
    </ReactFlowProvider>
  );
}
