import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { Concept, Domain } from '../types';
import { useStore } from '../store';

export type ConceptNodeData = {
  concept: Concept;
  conceptId: string;
};

interface ConceptNodeProps {
  data: ConceptNodeData;
}

export const ConceptNode = memo(({ data }: ConceptNodeProps) => {
  const concept: Concept = data.concept;
  const domains = useStore((state) => state.domains);

  // Get domain color if concept has a domain
  const domain: Domain | undefined = concept.domain ? domains[concept.domain] : undefined;
  // Use concept's own color if set, otherwise inherit from domain, otherwise default
  const domainColor = concept.color || domain?.color || 'var(--color-neutral-300)';

  // Validation status
  const isGhost = concept.isGhost;
  const validationStatus = concept.validationStatus || 'valid';
  const isStub = concept.status === 'stub';
  const isDraft = concept.status === 'draft';
  // Show badge for validation issues OR for stub concepts (stubs get warning badge)
  const hasValidationBadge = validationStatus === 'error' || validationStatus === 'warning' || isStub;

  // Calculate total model count
  const totalModels = concept.bronze_models.length + concept.silver_models.length + concept.gold_models.length;

  // Build class names
  const classNames = ['concept-node'];
  if (isGhost) classNames.push('ghost');
  if (isDraft) classNames.push('draft');
  if (isStub) classNames.push('stub');
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

      {/* Header with name only - status shown via border style */}
      <div className="concept-node-header">
        <div className="concept-node-name">
          {isGhost && <span className="ghost-icon">?</span>}
          {concept.name}
        </div>
      </div>

      {/* Model count badge + Domain on same row */}
      <div className="concept-node-footer">
        {!isGhost && (
          <div className="concept-node-model-count">
            {totalModels}
          </div>
        )}
        {isGhost ? (
          <div className="concept-node-domain">UNDEFINED</div>
        ) : concept.domain ? (
          <div className="concept-node-domain">{concept.domain}</div>
        ) : (
          <div className="concept-node-domain no-domain">NO DOMAIN</div>
        )}
      </div>

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
