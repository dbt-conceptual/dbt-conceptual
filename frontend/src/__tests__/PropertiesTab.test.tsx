import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PropertiesTab } from '../components/PropertiesTab';
import { useStore } from '../store';
import type { Concept, Relationship, Domain } from '../types';

// Mock react-markdown since it's an ESM-only package that can cause issues in tests
vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown-preview">{children}</div>,
}));

vi.mock('remark-gfm', () => ({
  default: () => ({}),
}));

function makeConcept(overrides: Partial<Concept> = {}): Concept {
  return {
    name: 'Customer',
    domain: 'd1',
    owner: 'team_a',
    definition: 'A customer who buys things',
    status: 'draft',
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

function makeRelationship(overrides: Partial<Relationship> = {}): Relationship {
  return {
    name: 'has',
    verb: 'has',
    from_concept: 'customer',
    to_concept: 'order',
    domains: ['d1'],
    status: 'complete',
    realized_by: ['model_a'],
    validationStatus: 'valid',
    validationMessages: [],
    ...overrides,
  };
}

function makeDomain(overrides: Partial<Domain> = {}): Domain {
  return {
    name: 'd1',
    display_name: 'Sales',
    color: '#4a9eff',
    ...overrides,
  };
}

beforeEach(() => {
  useStore.setState({
    concepts: {
      customer: makeConcept(),
    },
    relationships: {
      r1: makeRelationship(),
    },
    domains: {
      d1: makeDomain(),
    },
    positions: {},
    selectedConceptId: null,
    selectedRelationshipId: null,
  });
  vi.restoreAllMocks();
});

describe('PropertiesTab', () => {
  it('renders ConceptProperties when conceptId is provided', () => {
    render(<PropertiesTab conceptId="customer" />);

    // Should show the concept name input
    const nameInput = screen.getByDisplayValue('Customer');
    expect(nameInput).toBeInTheDocument();
  });

  it('renders RelationshipProperties when relationshipId is provided', () => {
    render(<PropertiesTab relationshipId="r1" />);

    // Should show the verb input
    const verbInput = screen.getByDisplayValue('has');
    expect(verbInput).toBeInTheDocument();
  });

  it('renders nothing when neither id is provided', () => {
    const { container } = render(<PropertiesTab />);
    expect(container.innerHTML).toBe('');
  });

  it('shows ghost concept indicator', () => {
    useStore.setState({
      concepts: {
        ghost1: makeConcept({
          name: 'Ghost',
          isGhost: true,
          status: 'stub',
          validationStatus: 'error',
        }),
      },
      relationships: {
        r1: makeRelationship({ from_concept: 'ghost1' }),
      },
    });

    render(<PropertiesTab conceptId="ghost1" />);

    expect(screen.getByText(/undefined/i)).toBeInTheDocument();
  });

  it('shows validation messages for concepts with errors', () => {
    useStore.setState({
      concepts: {
        bad: makeConcept({
          name: 'Bad',
          validationStatus: 'warning',
          validationMessages: ['Missing definition'],
        }),
      },
    });

    render(<PropertiesTab conceptId="bad" />);

    expect(screen.getByText('Missing definition')).toBeInTheDocument();
  });

  it('shows save button for concept properties', () => {
    render(<PropertiesTab conceptId="customer" />);

    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  it('shows save button for relationship properties', () => {
    render(<PropertiesTab relationshipId="r1" />);

    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  it('shows domain tag for concept with domain', () => {
    render(<PropertiesTab conceptId="customer" />);

    expect(screen.getByText('Sales')).toBeInTheDocument();
  });

  it('shows cardinality select for relationship', () => {
    render(<PropertiesTab relationshipId="r1" />);

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
  });

  it('shows status badge for concept', () => {
    render(<PropertiesTab conceptId="customer" />);

    expect(screen.getByText('draft')).toBeInTheDocument();
  });
});
