/**
 * Auto-layout utilities using Dagre for hierarchical graph layout.
 */
import Dagre from '@dagrejs/dagre';
import type { Concept, Relationship, Position } from './types';

// Node dimensions for layout calculation
const NODE_WIDTH = 200;
const NODE_HEIGHT = 100;

interface LayoutOptions {
  direction?: 'TB' | 'BT' | 'LR' | 'RL'; // Top-Bottom, Bottom-Top, Left-Right, Right-Left
  nodeSep?: number; // Horizontal separation between nodes
  rankSep?: number; // Vertical separation between ranks
}

/**
 * Apply Dagre auto-layout to concepts based on their relationships.
 * Returns a map of concept IDs to positions.
 */
export function applyAutoLayout(
  concepts: Record<string, Concept>,
  relationships: Record<string, Relationship>,
  options: LayoutOptions = {}
): Record<string, Position> {
  const { direction = 'LR', nodeSep = 80, rankSep = 150 } = options;

  // Create a new Dagre graph
  const g = new Dagre.graphlib.Graph();
  g.setGraph({
    rankdir: direction,
    nodesep: nodeSep,
    ranksep: rankSep,
  });
  g.setDefaultEdgeLabel(() => ({}));

  // Add all concepts as nodes
  const conceptIds = Object.keys(concepts);
  for (const id of conceptIds) {
    g.setNode(id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }

  // Add relationships as edges
  for (const rel of Object.values(relationships)) {
    // Only add edge if both nodes exist
    if (concepts[rel.from_concept] && concepts[rel.to_concept]) {
      g.setEdge(rel.from_concept, rel.to_concept);
    }
  }

  // Run the layout algorithm
  Dagre.layout(g);

  // Extract positions from the layout
  const positions: Record<string, Position> = {};
  for (const id of conceptIds) {
    const node = g.node(id);
    if (node) {
      // Dagre gives center positions, React Flow uses top-left
      positions[id] = {
        x: node.x - NODE_WIDTH / 2,
        y: node.y - NODE_HEIGHT / 2,
      };
    }
  }

  return positions;
}

/**
 * Check if positions need to be computed (no positions or missing concepts).
 */
export function needsAutoLayout(
  concepts: Record<string, Concept>,
  positions: Record<string, Position>
): boolean {
  const conceptIds = Object.keys(concepts);

  // No concepts = nothing to layout
  if (conceptIds.length === 0) {
    return false;
  }

  // No positions at all = need layout
  if (Object.keys(positions).length === 0) {
    return true;
  }

  // Check if any concept is missing a position
  for (const id of conceptIds) {
    if (!positions[id]) {
      return true;
    }
  }

  return false;
}

/**
 * Get positions for new concepts that don't have positions yet.
 * Applies layout only to new concepts, preserving existing positions.
 */
export function layoutNewConcepts(
  concepts: Record<string, Concept>,
  relationships: Record<string, Relationship>,
  existingPositions: Record<string, Position>
): Record<string, Position> {
  const newConceptIds = Object.keys(concepts).filter(id => !existingPositions[id]);

  if (newConceptIds.length === 0) {
    return existingPositions;
  }

  // Get full layout
  const fullLayout = applyAutoLayout(concepts, relationships);

  // Merge: keep existing positions, add new ones from layout
  return {
    ...fullLayout,
    ...existingPositions,
  };
}
