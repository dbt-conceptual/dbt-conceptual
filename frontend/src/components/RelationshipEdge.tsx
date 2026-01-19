import { memo } from 'react';
import { getBezierPath } from '@xyflow/react';
import type { Relationship, RelationshipStatus } from '../types';

export type RelationshipEdgeData = {
  relationship: Relationship;
  relationshipId: string;
};

export const RelationshipEdge = memo((props: any) => {
  const relationship: Relationship | undefined = props.data?.relationship;

  if (!relationship) return null;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    sourcePosition: props.sourcePosition,
    targetX: props.targetX,
    targetY: props.targetY,
    targetPosition: props.targetPosition,
  });

  // Status color
  const statusColorMap: Record<RelationshipStatus, string> = {
    complete: 'var(--status-complete)',
    draft: 'var(--status-draft)',
    stub: 'var(--status-stub)',
  };
  const statusColor = statusColorMap[relationship.status];

  // Edge stroke style based on status
  const strokeDasharray = relationship.status === 'stub' ? '5,5' : undefined;

  return (
    <>
      {/* Edge path */}
      <path
        id={props.id}
        className="react-flow__edge-path"
        d={edgePath}
        stroke={statusColor}
        strokeWidth={2}
        strokeDasharray={strokeDasharray}
        fill="none"
        markerEnd={props.markerEnd}
      />

      {/* Label */}
      <g transform={`translate(${labelX}, ${labelY})`}>
        <foreignObject
          width={200}
          height={60}
          x={-100}
          y={-30}
          className="edge-label-wrapper"
        >
          <div className="relationship-edge-label">
            {/* Verb */}
            <div className="relationship-edge-verb">{relationship.verb}</div>

            {/* Cardinality */}
            {relationship.cardinality && (
              <div className="relationship-edge-cardinality">
                {relationship.cardinality}
              </div>
            )}

            {/* Model count badge */}
            {relationship.realized_by.length > 0 && (
              <div
                className="relationship-edge-models"
                style={{ backgroundColor: statusColor }}
              >
                {relationship.realized_by.length}
              </div>
            )}
          </div>
        </foreignObject>
      </g>
    </>
  );
});

RelationshipEdge.displayName = 'RelationshipEdge';
