import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConceptNode } from '../components/ConceptNode';
import type { ConceptNodeData } from '../components/ConceptNode';
import { useStore } from '../store';
import type { Concept, Domain } from '../types';

// Mock @xyflow/react since ConceptNode uses Handle
vi.mock('@xyflow/react', () => ({
  Handle: ({ type, position }: { type: string; position: string }) => (
    <div data-testid={`handle-${type}-${position}`} />
  ),
  Position: {
    Left: 'left',
    Right: 'right',
  },
}));

function makeConcept(name: string, overrides: Partial<Concept> = {}): Concept {
  return {
    name,
    domain: undefined,
    owner: undefined,
    definition: undefined,
    status: 'draft',
    color: undefined,
    isGhost: false,
    validationStatus: 'valid',
    validationMessages: [],
    bronze_models: [],
    silver_models: [],
    gold_models: [],
    inferred_models: [],
    ...overrides,
  };
}

function makeNodeData(concept: Concept, conceptId: string = 'test-id'): ConceptNodeData {
  return {
    concept,
    conceptId,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  useStore.setState({
    domains: {},
  });
});

describe('ConceptNode', () => {
  describe('basic rendering', () => {
    it('renders concept name', () => {
      const concept = makeConcept('Customer');
      render(<ConceptNode data={makeNodeData(concept)} />);

      expect(screen.getByText('Customer')).toBeInTheDocument();
    });

    it('renders connection handles', () => {
      const concept = makeConcept('Customer');
      render(<ConceptNode data={makeNodeData(concept)} />);

      expect(screen.getByTestId('handle-target-left')).toBeInTheDocument();
      expect(screen.getByTestId('handle-source-right')).toBeInTheDocument();
    });

    it('shows model count for non-ghost concepts', () => {
      const concept = makeConcept('Customer', {
        bronze_models: ['raw_customers'],
        silver_models: ['stg_customers'],
        gold_models: ['dim_customers'],
      });
      render(<ConceptNode data={makeNodeData(concept)} />);

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('shows domain name when concept has domain', () => {
      const concept = makeConcept('Customer', { domain: 'sales' });
      render(<ConceptNode data={makeNodeData(concept)} />);

      expect(screen.getByText('sales')).toBeInTheDocument();
    });

    it('shows NO DOMAIN when concept has no domain', () => {
      const concept = makeConcept('Customer', { domain: undefined });
      render(<ConceptNode data={makeNodeData(concept)} />);

      expect(screen.getByText('NO DOMAIN')).toBeInTheDocument();
    });
  });

  describe('ghost concepts', () => {
    it('renders ghost icon for ghost concepts', () => {
      const concept = makeConcept('UnknownConcept', { isGhost: true });
      render(<ConceptNode data={makeNodeData(concept)} />);

      expect(screen.getByText('?')).toBeInTheDocument();
    });

    it('shows UNDEFINED for ghost concepts', () => {
      const concept = makeConcept('UnknownConcept', { isGhost: true });
      render(<ConceptNode data={makeNodeData(concept)} />);

      expect(screen.getByText('UNDEFINED')).toBeInTheDocument();
    });

    it('does not show model count for ghost concepts', () => {
      const concept = makeConcept('UnknownConcept', {
        isGhost: true,
        bronze_models: ['some_model'],
      });
      render(<ConceptNode data={makeNodeData(concept)} />);

      // Model count should not be visible
      expect(screen.queryByText('1')).not.toBeInTheDocument();
    });

    it('includes undefined reference in aria-label', () => {
      const concept = makeConcept('UnknownConcept', { isGhost: true });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const node = container.querySelector('.concept-node');
      expect(node).toHaveAttribute('aria-label', expect.stringContaining('undefined reference'));
    });
  });

  describe('visual states', () => {
    it('applies draft class for draft concepts', () => {
      const concept = makeConcept('Customer', { status: 'draft' });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.concept-node.draft')).toBeInTheDocument();
    });

    it('applies stub class for stub concepts', () => {
      const concept = makeConcept('Customer', { status: 'stub' });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.concept-node.stub')).toBeInTheDocument();
    });

    it('applies error class for concepts with validation errors', () => {
      const concept = makeConcept('Customer', {
        validationStatus: 'error',
        validationMessages: ['Missing definition'],
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.concept-node.error')).toBeInTheDocument();
    });

    it('applies warning class for concepts with validation warnings', () => {
      const concept = makeConcept('Customer', {
        validationStatus: 'warning',
        validationMessages: ['Missing owner'],
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.concept-node.warning')).toBeInTheDocument();
    });

    it('applies ghost class for ghost concepts', () => {
      const concept = makeConcept('UnknownConcept', { isGhost: true });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.concept-node.ghost')).toBeInTheDocument();
    });
  });

  describe('validation badges', () => {
    it('shows error badge for concepts with validation errors', () => {
      const concept = makeConcept('Customer', {
        validationStatus: 'error',
        validationMessages: ['Missing definition'],
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const badge = container.querySelector('.validation-badge.error');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('!');
    });

    it('shows warning badge for concepts with validation warnings', () => {
      const concept = makeConcept('Customer', {
        validationStatus: 'warning',
        validationMessages: ['Missing owner'],
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const badge = container.querySelector('.validation-badge.warning');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('!');
    });

    it('shows warning badge for stub concepts even with valid status', () => {
      const concept = makeConcept('Customer', {
        status: 'stub',
        validationStatus: 'valid',
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const badge = container.querySelector('.validation-badge.warning');
      expect(badge).toBeInTheDocument();
    });

    it('does not show badge for valid non-stub concepts', () => {
      const concept = makeConcept('Customer', {
        status: 'complete',
        validationStatus: 'valid',
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.validation-badge')).not.toBeInTheDocument();
    });
  });

  describe('deprecation', () => {
    it('shows deprecation notice when concept is replaced', () => {
      const concept = makeConcept('OldCustomer', {
        status: 'deprecated',
        replaced_by: 'NewCustomer',
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const deprecationNotice = container.querySelector('.concept-node-deprecation');
      expect(deprecationNotice).toBeInTheDocument();
      expect(deprecationNotice).toHaveTextContent('→ NewCustomer');
    });

    it('does not show deprecation notice for ghost concepts', () => {
      const concept = makeConcept('GhostConcept', {
        isGhost: true,
        replaced_by: 'Something',
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.concept-node-deprecation')).not.toBeInTheDocument();
    });

    it('does not show deprecation notice when not replaced', () => {
      const concept = makeConcept('Customer', {
        status: 'complete',
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      expect(container.querySelector('.concept-node-deprecation')).not.toBeInTheDocument();
    });
  });

  describe('domain colors', () => {
    it('applies domain color from concept color if set', () => {
      const concept = makeConcept('Customer', {
        domain: 'sales',
        color: '#FF0000',
      });
      useStore.setState({
        domains: {
          sales: { name: 'sales', display_name: 'Sales', color: '#0000FF' },
        },
      });

      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);
      const node = container.querySelector('.concept-node');

      // Concept color takes precedence over domain color
      expect(node).toHaveStyle({ borderLeftColor: '#FF0000' });
    });

    it('applies domain color when concept color not set', () => {
      const concept = makeConcept('Customer', {
        domain: 'sales',
      });
      useStore.setState({
        domains: {
          sales: { name: 'sales', display_name: 'Sales', color: '#0000FF' } as Domain,
        },
      });

      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);
      const node = container.querySelector('.concept-node');

      expect(node).toHaveStyle({ borderLeftColor: '#0000FF' });
    });

    it('does not apply border color for ghost concepts', () => {
      const concept = makeConcept('UnknownConcept', { isGhost: true });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);
      const node = container.querySelector('.concept-node');

      // Ghost concepts don't have a border-left-color style applied
      expect(node?.style.borderLeftColor).toBe('');
    });
  });

  describe('aria labels', () => {
    it('includes all relevant information in aria-label for complete concept', () => {
      const concept = makeConcept('Customer', {
        domain: 'sales',
        status: 'complete',
        bronze_models: ['raw_customers'],
        silver_models: ['stg_customers'],
        gold_models: ['dim_customers'],
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const node = container.querySelector('.concept-node');
      const label = node?.getAttribute('aria-label') || '';

      expect(label).toContain('Concept: Customer');
      expect(label).toContain('domain: sales');
      expect(label).toContain('3 models');
      expect(label).toContain('status: complete');
    });

    it('includes validation status in aria-label when invalid', () => {
      const concept = makeConcept('Customer', {
        validationStatus: 'error',
        validationMessages: ['Missing definition'],
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const node = container.querySelector('.concept-node');
      expect(node).toHaveAttribute('aria-label', expect.stringContaining('validation: error'));
    });

    it('uses singular model in aria-label for single model', () => {
      const concept = makeConcept('Customer', {
        bronze_models: ['raw_customers'],
      });
      const { container } = render(<ConceptNode data={makeNodeData(concept)} />);

      const node = container.querySelector('.concept-node');
      expect(node).toHaveAttribute('aria-label', expect.stringContaining('1 model'));
      expect(node?.getAttribute('aria-label')).not.toContain('1 models');
    });
  });
});
