import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PropertyPanel } from '../components/PropertyPanel';
import { useStore } from '../store';
import type { Concept, Relationship } from '../types';

// Mock child components to simplify testing
vi.mock('../components/PropertiesTab', () => ({
  PropertiesTab: vi.fn(({ conceptId, relationshipId }: { conceptId?: string; relationshipId?: string }) => (
    <div data-testid="properties-tab">
      {conceptId && <span>Concept: {conceptId}</span>}
      {relationshipId && <span>Relationship: {relationshipId}</span>}
    </div>
  )),
}));

vi.mock('../components/ModelsTab', () => ({
  ModelsTab: vi.fn(({ conceptId }: { conceptId: string }) => (
    <div data-testid="models-tab">Models for {conceptId}</div>
  )),
}));

vi.mock('../components/RelationshipModelsTab', () => ({
  RelationshipModelsTab: vi.fn(({ relationshipId }: { relationshipId: string }) => (
    <div data-testid="relationship-models-tab">Models for {relationshipId}</div>
  )),
}));

vi.mock('../components/ConfirmDialog', () => ({
  ConfirmDialog: vi.fn(({ title, onConfirm, onCancel, onStay }: {
    title: string;
    onConfirm: () => void;
    onCancel: () => void;
    onStay: () => void;
  }) => (
    <div data-testid="confirm-dialog">
      <h3>{title}</h3>
      <button onClick={onConfirm}>Save & Close</button>
      <button onClick={onCancel}>Discard</button>
      <button onClick={onStay}>Cancel</button>
    </div>
  )),
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

function makeRelationship(): Relationship {
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
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  useStore.setState({
    concepts: {},
    relationships: {},
    selectedConceptId: null,
    selectedRelationshipId: null,
    showUnsavedChangesDialog: false,
    hasUnsavedChanges: false,
  });
});

describe('PropertyPanel', () => {
  describe('visibility', () => {
    it('is hidden when nothing is selected', () => {
      const { container } = render(<PropertyPanel />);
      expect(container.querySelector('.property-panel')).not.toBeInTheDocument();
    });

    it('shows panel when concept is selected', () => {
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
      });

      render(<PropertyPanel />);
      expect(screen.getByRole('button', { name: /close panel/i })).toBeInTheDocument();
    });

    it('shows panel when relationship is selected', () => {
      useStore.setState({
        relationships: { r1: makeRelationship() },
        selectedRelationshipId: 'r1',
      });

      render(<PropertyPanel />);
      expect(screen.getByRole('button', { name: /close panel/i })).toBeInTheDocument();
    });
  });

  describe('concept panel', () => {
    it('displays concept name in title', () => {
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
      });

      render(<PropertyPanel />);
      expect(screen.getByText('Customer')).toBeInTheDocument();
    });

    it('displays Ghost Concept title for ghost concepts', () => {
      useStore.setState({
        concepts: { unknown: makeConcept('Unknown', { isGhost: true }) },
        selectedConceptId: 'unknown',
      });

      render(<PropertyPanel />);
      expect(screen.getByText('Ghost Concept')).toBeInTheDocument();
    });

    it('shows Properties and Models tabs for non-ghost concepts', () => {
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
      });

      render(<PropertyPanel />);
      expect(screen.getByRole('button', { name: /properties/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /models/i })).toBeInTheDocument();
    });

    it('does not show tabs for ghost concepts', () => {
      useStore.setState({
        concepts: { unknown: makeConcept('Unknown', { isGhost: true }) },
        selectedConceptId: 'unknown',
      });

      render(<PropertyPanel />);
      expect(screen.queryByRole('button', { name: /models/i })).not.toBeInTheDocument();
    });

    it('shows PropertiesTab by default', () => {
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
      });

      render(<PropertyPanel />);
      expect(screen.getByTestId('properties-tab')).toBeInTheDocument();
      expect(screen.getByText('Concept: customer')).toBeInTheDocument();
    });

    it('switches to Models tab when clicked', async () => {
      const user = userEvent.setup();
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
      });

      render(<PropertyPanel />);

      const modelsTab = screen.getByRole('button', { name: /models/i });
      await user.click(modelsTab);

      expect(screen.getByTestId('models-tab')).toBeInTheDocument();
      expect(screen.getByText('Models for customer')).toBeInTheDocument();
    });

    it('does not show Models tab content for ghost concepts', () => {
      useStore.setState({
        concepts: { unknown: makeConcept('Unknown', { isGhost: true }) },
        selectedConceptId: 'unknown',
      });

      render(<PropertyPanel />);
      expect(screen.queryByTestId('models-tab')).not.toBeInTheDocument();
    });
  });

  describe('relationship panel', () => {
    it('displays Relationship in title', () => {
      useStore.setState({
        relationships: { r1: makeRelationship() },
        selectedRelationshipId: 'r1',
      });

      render(<PropertyPanel />);
      expect(screen.getByText('Relationship')).toBeInTheDocument();
    });

    it('shows Properties and Models tabs', () => {
      useStore.setState({
        relationships: { r1: makeRelationship() },
        selectedRelationshipId: 'r1',
      });

      render(<PropertyPanel />);
      expect(screen.getByRole('button', { name: /properties/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /models/i })).toBeInTheDocument();
    });

    it('shows PropertiesTab by default', () => {
      useStore.setState({
        relationships: { r1: makeRelationship() },
        selectedRelationshipId: 'r1',
      });

      render(<PropertyPanel />);
      expect(screen.getByTestId('properties-tab')).toBeInTheDocument();
      expect(screen.getByText('Relationship: r1')).toBeInTheDocument();
    });

    it('switches to RelationshipModelsTab when Models tab clicked', async () => {
      const user = userEvent.setup();
      useStore.setState({
        relationships: { r1: makeRelationship() },
        selectedRelationshipId: 'r1',
      });

      render(<PropertyPanel />);

      const modelsTab = screen.getByRole('button', { name: /models/i });
      await user.click(modelsTab);

      expect(screen.getByTestId('relationship-models-tab')).toBeInTheDocument();
      expect(screen.getByText('Models for r1')).toBeInTheDocument();
    });
  });

  describe('close button', () => {
    it('calls requestClearSelection when close button clicked', async () => {
      const user = userEvent.setup();
      const requestClearSelection = vi.fn();

      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
        requestClearSelection,
      });

      render(<PropertyPanel />);

      const closeButton = screen.getByRole('button', { name: /close panel/i });
      await user.click(closeButton);

      expect(requestClearSelection).toHaveBeenCalled();
    });
  });

  describe('unsaved changes dialog', () => {
    it('shows dialog when showUnsavedChangesDialog is true', () => {
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
        showUnsavedChangesDialog: true,
      });

      render(<PropertyPanel />);
      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
      expect(screen.getByText('Unsaved Changes')).toBeInTheDocument();
    });

    it('does not show dialog when showUnsavedChangesDialog is false', () => {
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
        showUnsavedChangesDialog: false,
      });

      render(<PropertyPanel />);
      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument();
    });

    it('calls forceClearSelection when Save & Close is clicked', async () => {
      const user = userEvent.setup();
      const forceClearSelection = vi.fn();

      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
        showUnsavedChangesDialog: true,
        forceClearSelection,
      });

      render(<PropertyPanel />);

      const saveButton = screen.getByRole('button', { name: /save & close/i });
      await user.click(saveButton);

      expect(forceClearSelection).toHaveBeenCalled();
    });

    it('calls fetchState and confirmDiscardChanges when Discard is clicked', async () => {
      const user = userEvent.setup();
      const fetchState = vi.fn();
      const confirmDiscardChanges = vi.fn();

      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
        showUnsavedChangesDialog: true,
        fetchState,
        confirmDiscardChanges,
      });

      render(<PropertyPanel />);

      const discardButton = screen.getByRole('button', { name: /discard/i });
      await user.click(discardButton);

      expect(fetchState).toHaveBeenCalled();
      expect(confirmDiscardChanges).toHaveBeenCalled();
    });

    it('calls cancelDiscardChanges when Cancel is clicked', async () => {
      const user = userEvent.setup();
      const cancelDiscardChanges = vi.fn();

      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
        showUnsavedChangesDialog: true,
        cancelDiscardChanges,
      });

      render(<PropertyPanel />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(cancelDiscardChanges).toHaveBeenCalled();
    });
  });

  describe('tab navigation', () => {
    it('marks active tab with active class', async () => {
      const user = userEvent.setup();
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
      });

      render(<PropertyPanel />);

      const propertiesTab = screen.getByRole('button', { name: /properties/i });
      const modelsTab = screen.getByRole('button', { name: /models/i });

      // Properties tab should be active by default
      expect(propertiesTab.className).toContain('active');
      expect(modelsTab.className).not.toContain('active');

      // Click Models tab
      await user.click(modelsTab);

      // Models tab should now be active
      expect(modelsTab.className).toContain('active');
      expect(propertiesTab.className).not.toContain('active');
    });

    it('switches back to Properties tab when clicked again', async () => {
      const user = userEvent.setup();
      useStore.setState({
        concepts: { customer: makeConcept('Customer') },
        selectedConceptId: 'customer',
      });

      render(<PropertyPanel />);

      const propertiesTab = screen.getByRole('button', { name: /properties/i });
      const modelsTab = screen.getByRole('button', { name: /models/i });

      // Switch to Models
      await user.click(modelsTab);
      expect(screen.getByTestId('models-tab')).toBeInTheDocument();

      // Switch back to Properties
      await user.click(propertiesTab);
      expect(screen.getByTestId('properties-tab')).toBeInTheDocument();
    });
  });
});
