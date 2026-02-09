import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render } from '@testing-library/react';
import { RelationshipEdge } from '../components/RelationshipEdge';
import type { RelationshipEdgeData } from '../components/RelationshipEdge';
import type { Relationship } from '../types';

// Mock @xyflow/react's getBezierPath
vi.mock('@xyflow/react', () => ({
  getBezierPath: () => ['M 0 0 L 100 100', 50, 50], // [path, labelX, labelY]
  Position: {
    Left: 'left',
    Right: 'right',
  },
}));

function makeRelationship(overrides: Partial<Relationship> = {}): Relationship {
  return {
    name: 'Customer has Order',
    verb: 'has',
    from_concept: 'customer',
    to_concept: 'order',
    cardinality: undefined,
    domains: ['sales'],
    owner: undefined,
    definition: undefined,
    status: 'complete',
    realized_by: [],
    validationStatus: 'valid',
    validationMessages: [],
    ...overrides,
  };
}

function makeEdgeData(relationship: Relationship, relationshipId: string = 'test-id'): RelationshipEdgeData {
  return {
    relationship,
    relationshipId,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('RelationshipEdge', () => {
  describe('basic rendering', () => {
    it('renders relationship verb', () => {
      const relationship = makeRelationship({ verb: 'owns' });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      expect(container).toHaveTextContent('owns');
    });

    it('renders cardinality when present', () => {
      const relationship = makeRelationship({
        verb: 'has',
        cardinality: '1:N',
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      expect(container).toHaveTextContent('1:N');
    });

    it('does not render cardinality when not set', () => {
      const relationship = makeRelationship({
        verb: 'has',
        cardinality: undefined,
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      expect(container.querySelector('.relationship-edge-cardinality')).not.toBeInTheDocument();
    });

    it('returns null when data is undefined', () => {
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      expect(container.querySelector('.relationship-edge-label')).not.toBeInTheDocument();
    });
  });

  describe('model count badge', () => {
    it('shows model count badge when relationship has realized models', () => {
      const relationship = makeRelationship({
        realized_by: ['fct_orders', 'stg_orders'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const badge = container.querySelector('.relationship-edge-models');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('2');
    });

    it('does not show model count badge when no realized models', () => {
      const relationship = makeRelationship({
        realized_by: [],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      expect(container.querySelector('.relationship-edge-models')).not.toBeInTheDocument();
    });

    it('hides model count badge when relationship has validation issues', () => {
      const relationship = makeRelationship({
        realized_by: ['fct_orders'],
        validationStatus: 'error',
        validationMessages: ['Invalid relationship'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      expect(container.querySelector('.relationship-edge-models')).not.toBeInTheDocument();
    });
  });

  describe('validation states', () => {
    it('applies invalid class to path for error validation', () => {
      const relationship = makeRelationship({
        validationStatus: 'error',
        validationMessages: ['Missing definition'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const path = container.querySelector('.react-flow__edge-path');
      expect(path).toHaveClass('invalid');
    });

    it('applies warning class to path for warning validation', () => {
      const relationship = makeRelationship({
        validationStatus: 'warning',
        validationMessages: ['Missing owner'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const path = container.querySelector('.react-flow__edge-path');
      expect(path).toHaveClass('warning');
    });

    it('applies invalid class to label for error validation', () => {
      const relationship = makeRelationship({
        validationStatus: 'error',
        validationMessages: ['Missing definition'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveClass('invalid');
    });

    it('applies warning class to label for warning validation', () => {
      const relationship = makeRelationship({
        validationStatus: 'warning',
        validationMessages: ['Missing owner'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveClass('warning');
    });
  });

  describe('status styles', () => {
    it('applies dashed stroke for stub status', () => {
      const relationship = makeRelationship({ status: 'stub' });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const path = container.querySelector('.react-flow__edge-path');
      expect(path).toHaveAttribute('stroke-dasharray', '5,5');
    });

    it('applies dashed stroke for validation errors', () => {
      const relationship = makeRelationship({
        validationStatus: 'error',
        status: 'complete',
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const path = container.querySelector('.react-flow__edge-path');
      expect(path).toHaveAttribute('stroke-dasharray', '5,5');
    });

    it('does not apply dashed stroke for complete status without errors', () => {
      const relationship = makeRelationship({ status: 'complete' });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const path = container.querySelector('.react-flow__edge-path');
      expect(path).not.toHaveAttribute('stroke-dasharray');
    });
  });

  describe('aria labels', () => {
    it('includes relationship verb in aria-label', () => {
      const relationship = makeRelationship({ verb: 'owns' });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveAttribute('aria-label', expect.stringContaining('Relationship: owns'));
    });

    it('includes cardinality in aria-label when present', () => {
      const relationship = makeRelationship({
        verb: 'has',
        cardinality: '1:N',
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveAttribute('aria-label', expect.stringContaining('cardinality: 1:N'));
    });

    it('includes status in aria-label', () => {
      const relationship = makeRelationship({ status: 'draft' });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveAttribute('aria-label', expect.stringContaining('status: draft'));
    });

    it('includes validation status in aria-label when invalid', () => {
      const relationship = makeRelationship({
        validationStatus: 'error',
        validationMessages: ['Missing definition'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveAttribute('aria-label', expect.stringContaining('validation: error'));
    });

    it('includes model count in aria-label', () => {
      const relationship = makeRelationship({
        realized_by: ['fct_orders', 'stg_orders'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveAttribute('aria-label', expect.stringContaining('2 models'));
    });

    it('uses singular model in aria-label for single model', () => {
      const relationship = makeRelationship({
        realized_by: ['fct_orders'],
      });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
          />
        </svg>
      );

      const label = container.querySelector('.relationship-edge-label');
      expect(label).toHaveAttribute('aria-label', expect.stringContaining('1 model'));
      expect(label?.getAttribute('aria-label')).not.toContain('1 models');
    });
  });

  describe('edge path', () => {
    it('renders edge path with correct attributes', () => {
      const relationship = makeRelationship({ status: 'complete' });
      const { container } = render(
        <svg>
          <RelationshipEdge
            id="test-edge"
            data={makeEdgeData(relationship)}
            sourceX={0}
            sourceY={0}
            sourcePosition="right"
            targetX={100}
            targetY={100}
            targetPosition="left"
            markerEnd="url(#arrow)"
          />
        </svg>
      );

      const path = container.querySelector('.react-flow__edge-path');
      expect(path).toHaveAttribute('d', 'M 0 0 L 100 100');
      expect(path).toHaveAttribute('stroke-width', '2');
      expect(path).toHaveAttribute('fill', 'none');
      expect(path).toHaveAttribute('marker-end', 'url(#arrow)');
    });
  });
});
