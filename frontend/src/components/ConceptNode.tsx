import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { Concept, ConceptStatus } from '../types';

export type ConceptNodeData = {
  concept: Concept;
  conceptId: string;
};

export const ConceptNode = memo((props: any) => {
  const concept: Concept = props.data.concept;

  // Status badge color
  const statusColorMap: Record<ConceptStatus, string> = {
    complete: 'var(--status-complete)',
    draft: 'var(--status-draft)',
    stub: 'var(--status-stub)',
    deprecated: 'var(--status-deprecated)',
  };
  const statusColor = statusColorMap[concept.status];

  // Domain color (or default)
  const domainColor = concept.color || 'var(--color-neutral-300)';

  return (
    <div className="concept-node" style={{ borderLeftColor: domainColor }}>
      {/* Handles for connecting edges */}
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: 'var(--color-neutral-400)' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: 'var(--color-neutral-400)' }}
      />

      {/* Header with name and status */}
      <div className="concept-node-header">
        <div className="concept-node-name">{concept.name}</div>
        <div
          className="concept-node-status"
          style={{ backgroundColor: statusColor }}
        >
          {concept.status}
        </div>
      </div>

      {/* Domain badge */}
      {concept.domain && (
        <div className="concept-node-domain" style={{ color: domainColor }}>
          {concept.domain}
        </div>
      )}

      {/* Model counts */}
      <div className="concept-node-models">
        {concept.bronze_models.length > 0 && (
          <div className="model-count model-count-bronze">
            <span className="model-count-icon">⬡</span>
            {concept.bronze_models.length}
          </div>
        )}
        {concept.silver_models.length > 0 && (
          <div className="model-count model-count-silver">
            <span className="model-count-icon">◇</span>
            {concept.silver_models.length}
          </div>
        )}
        {concept.gold_models.length > 0 && (
          <div className="model-count model-count-gold">
            <span className="model-count-icon">◆</span>
            {concept.gold_models.length}
          </div>
        )}
      </div>

      {/* Owner (if set) */}
      {concept.owner && (
        <div className="concept-node-owner">@{concept.owner}</div>
      )}

      {/* Deprecation notice */}
      {concept.replaced_by && (
        <div className="concept-node-deprecation">
          → {concept.replaced_by}
        </div>
      )}
    </div>
  );
});

ConceptNode.displayName = 'ConceptNode';
