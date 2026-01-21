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

  // Validation status
  const isGhost = concept.isGhost;
  const validationStatus = concept.validationStatus || 'valid';
  const isStub = concept.status === 'stub';
  // Show badge for validation issues OR for stub concepts (stubs get warning badge)
  const hasValidationBadge = validationStatus === 'error' || validationStatus === 'warning' || isStub;

  // Build class names
  const classNames = ['concept-node'];
  if (isGhost) classNames.push('ghost');
  if (validationStatus === 'error') classNames.push('error');
  if (validationStatus === 'warning') classNames.push('warning');

  return (
    <div
      className={classNames.join(' ')}
      style={isGhost ? undefined : { borderLeftColor: domainColor }}
    >
      {/* Validation badge (also shown for stubs as warning) */}
      {hasValidationBadge && (
        <div className={`validation-badge ${isStub && validationStatus === 'valid' ? 'warning' : validationStatus}`}>!</div>
      )}

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
        <div className="concept-node-name">
          {isGhost && <span className="ghost-icon">?</span>}
          {concept.name}
        </div>
        {!isGhost && (
          <div
            className="concept-node-status"
            style={{ backgroundColor: statusColor }}
          >
            {concept.status}
          </div>
        )}
      </div>

      {/* Domain badge */}
      {isGhost ? (
        <div className="concept-node-domain">undefined</div>
      ) : concept.domain ? (
        <div className="concept-node-domain" style={{ color: domainColor }}>
          {concept.domain}
        </div>
      ) : null}

      {/* Model counts (not shown for ghosts) */}
      {!isGhost && (
        <div className="concept-node-models">
          {concept.bronze_models.length > 0 && (
            <div className="model-count model-count-bronze">
              <span className="model-count-icon">{'\u2B21'}</span>
              {concept.bronze_models.length}
            </div>
          )}
          {concept.silver_models.length > 0 && (
            <div className="model-count model-count-silver">
              <span className="model-count-icon">{'\u25C7'}</span>
              {concept.silver_models.length}
            </div>
          )}
          {concept.gold_models.length > 0 && (
            <div className="model-count model-count-gold">
              <span className="model-count-icon">{'\u25C6'}</span>
              {concept.gold_models.length}
            </div>
          )}
        </div>
      )}

      {/* Owner (if set and not ghost) */}
      {!isGhost && concept.owner && (
        <div className="concept-node-owner">@{concept.owner}</div>
      )}

      {/* Deprecation notice */}
      {!isGhost && concept.replaced_by && (
        <div className="concept-node-deprecation">
          {'\u2192'} {concept.replaced_by}
        </div>
      )}
    </div>
  );
});

ConceptNode.displayName = 'ConceptNode';
