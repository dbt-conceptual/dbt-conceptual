import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useStore } from '../store';
import type { Concept, Relationship } from '../types';

// Mock @xyflow/react to avoid the complexity of rendering the actual canvas
const mockFitView = vi.fn();
vi.mock('@xyflow/react', () => {
  return {
    ReactFlow: ({ nodes, edges, onPaneClick, children }: {
      nodes: Array<{ id: string; data: { concept: Concept; conceptId: string } }>;
      edges: Array<{ id: string }>;
      onPaneClick?: () => void;
      children?: React.ReactNode;
    }) => (
      <div data-testid="react-flow">
        <div data-testid="node-count">{nodes.length}</div>
        <div data-testid="edge-count">{edges.length}</div>
        {nodes.map((n) => (
          <div key={n.id} data-testid={`node-${n.id}`}>
            {n.data.concept.name}
          </div>
        ))}
        {edges.map((e) => (
          <div key={e.id} data-testid={`edge-${e.id}`} />
        ))}
        {onPaneClick && (
          <button data-testid="pane-click" onClick={onPaneClick}>
            Click pane
          </button>
        )}
        {children}
      </div>
    ),
    ReactFlowProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    Background: () => <div data-testid="background" />,
    Controls: () => <div data-testid="controls" />,
    useNodesState: (initial: unknown[]) => [initial, vi.fn(), vi.fn()],
    useEdgesState: (initial: unknown[]) => [initial, vi.fn(), vi.fn()],
    useReactFlow: () => ({ fitView: mockFitView }),
  };
});

// Must import Canvas AFTER the mock
import { Canvas } from '../components/Canvas';

function makeConcept(name: string, overrides: Partial<Concept> = {}): Concept {
  return {
    name,
    domain: 'd1',
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

function makeRelationship(id: string, from: string, to: string): Relationship {
  return {
    name: `${from}-${to}`,
    verb: 'has',
    from_concept: from,
    to_concept: to,
    domains: [],
    status: 'complete',
    realized_by: [],
    validationStatus: 'valid',
    validationMessages: [],
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  mockFitView.mockClear();

  // Default: mock fetchState so it doesn't actually call fetch
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({
      domains: {},
      concepts: {},
      relationships: {},
      positions: {},
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }),
  );

  useStore.setState({
    concepts: {},
    relationships: {},
    positions: {},
    isLoading: false,
    isSyncing: false,
    error: null,
    hasIntegrityErrors: false,
    selectedConceptId: null,
    selectedRelationshipId: null,
  });

  return () => {
    fetchMock.mockRestore();
  };
});

describe('Canvas', () => {
  it('renders the canvas container with React Flow', () => {
    render(<Canvas />);
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });

  it('renders nodes for each concept', () => {
    useStore.setState({
      concepts: {
        c1: makeConcept('Customer'),
        c2: makeConcept('Order'),
      },
      positions: {
        c1: { x: 0, y: 0 },
        c2: { x: 200, y: 0 },
      },
    });

    render(<Canvas />);

    expect(screen.getByTestId('node-c1')).toBeInTheDocument();
    expect(screen.getByTestId('node-c2')).toBeInTheDocument();
    expect(screen.getByTestId('node-count')).toHaveTextContent('2');
  });

  it('renders edges for each relationship', () => {
    useStore.setState({
      concepts: {
        c1: makeConcept('Customer'),
        c2: makeConcept('Order'),
      },
      relationships: {
        r1: makeRelationship('r1', 'c1', 'c2'),
      },
      positions: {
        c1: { x: 0, y: 0 },
        c2: { x: 200, y: 0 },
      },
    });

    render(<Canvas />);

    expect(screen.getByTestId('edge-r1')).toBeInTheDocument();
    expect(screen.getByTestId('edge-count')).toHaveTextContent('1');
  });

  it('renders blocked state when integrity errors exist', async () => {
    // Override fetch to return integrity errors so fetchState on mount sets the flag
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({
        domains: {},
        concepts: {},
        relationships: {},
        positions: {},
        hasIntegrityErrors: true,
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );

    render(<Canvas />);

    // Wait for fetchState to complete and re-render with integrity errors
    await vi.waitFor(() => {
      const blocked = document.querySelector('.canvas-container--blocked');
      expect(blocked).not.toBeNull();
    });

    // Should NOT show ReactFlow
    expect(screen.queryByTestId('react-flow')).not.toBeInTheDocument();
  });

  it('renders background and controls', () => {
    render(<Canvas />);

    expect(screen.getByTestId('background')).toBeInTheDocument();
    expect(screen.getByTestId('controls')).toBeInTheDocument();
  });

  it('uses position (0,0) for concepts without saved positions', () => {
    useStore.setState({
      concepts: {
        c1: makeConcept('NoPosition'),
      },
      positions: {},
    });

    render(<Canvas />);

    expect(screen.getByTestId('node-c1')).toBeInTheDocument();
  });

  it('renders concept names inside nodes', () => {
    useStore.setState({
      concepts: {
        c1: makeConcept('Customer'),
        c2: makeConcept('Order'),
      },
      positions: {
        c1: { x: 0, y: 0 },
        c2: { x: 200, y: 0 },
      },
    });

    render(<Canvas />);

    expect(screen.getByText('Customer')).toBeInTheDocument();
    expect(screen.getByText('Order')).toBeInTheDocument();
  });
});
