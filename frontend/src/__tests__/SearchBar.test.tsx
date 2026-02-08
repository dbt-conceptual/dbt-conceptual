import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchBar } from '../components/SearchBar';
import { useStore } from '../store';
import type { Concept, Relationship } from '../types';

function makeConcept(overrides: Partial<Concept> & { name: string }): Concept {
  return {
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

// Seed the store with concepts and relationships for search tests
function seedStore() {
  useStore.setState({
    concepts: {
      customer: makeConcept({ name: 'Customer', domain: 'sales', status: 'complete' }),
      order: makeConcept({ name: 'Order', domain: 'sales' }),
      product: makeConcept({ name: 'Product', domain: 'inventory', status: 'stub' }),
    },
    relationships: {
      'customer-has-order': {
        name: 'Customer has Order',
        verb: 'has',
        from_concept: 'customer',
        to_concept: 'order',
        domains: ['sales'],
        status: 'complete',
        realized_by: [],
        validationStatus: 'valid',
        validationMessages: [],
      } satisfies Relationship,
    },
    selectedConceptId: null,
    selectedRelationshipId: null,
  });
}

beforeEach(() => {
  seedStore();
  vi.restoreAllMocks();
});

describe('SearchBar', () => {
  it('renders a search input', () => {
    render(<SearchBar />);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search concepts/i)).toBeInTheDocument();
  });

  it('shows results when typing a matching query', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'cust');

    // Should show the dropdown
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    // Should have at least one option
    const options = screen.getAllByRole('option');
    expect(options.length).toBeGreaterThanOrEqual(1);
    // One option should contain "Customer" in its text content (may be split by highlight spans)
    const hasCustomerOption = options.some(
      (opt) => opt.textContent?.includes('Customer'),
    );
    expect(hasCustomerOption).toBe(true);
  });

  it('shows "No results found" when query matches nothing', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'zzzznotfound');

    expect(screen.getByText('No results found')).toBeInTheDocument();
  });

  it('filters by domain name', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'inventory');

    const options = screen.getAllByRole('option');
    expect(options.length).toBe(1);
    expect(within(options[0]).getByText('Product')).toBeInTheDocument();
  });

  it('finds relationships by verb', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'has');

    const options = screen.getAllByRole('option');
    // At least one option should be the relationship
    const relOption = options.find(
      (opt) => opt.textContent?.includes('\u2192'),
    );
    expect(relOption).toBeDefined();
  });

  it('navigates with arrow keys and selects with enter', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'or');

    const options = screen.getAllByRole('option');
    expect(options.length).toBeGreaterThanOrEqual(1);

    // First option should be selected by default
    expect(options[0]).toHaveAttribute('aria-selected', 'true');

    // Arrow down to navigate
    if (options.length > 1) {
      await user.keyboard('{ArrowDown}');
      expect(options[1]).toHaveAttribute('aria-selected', 'true');
    }

    // Press Enter to select the currently highlighted option
    await user.keyboard('{Enter}');

    // Input should be cleared after selection
    expect(input).toHaveValue('');
  });

  it('closes dropdown on Escape', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'cust');

    expect(screen.getByRole('listbox')).toBeInTheDocument();

    await user.keyboard('{Escape}');

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    expect(input).toHaveValue('');
  });

  it('selects a concept via click and updates store', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    // Use a query unique enough to only match the concept "Product"
    await user.type(input, 'Product');

    const options = screen.getAllByRole('option');
    expect(options.length).toBe(1);

    await user.click(options[0]);

    expect(useStore.getState().selectedConceptId).toBe('product');
    expect(input).toHaveValue('');
  });

  it('selects a relationship result and updates store', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'has');

    const options = screen.getAllByRole('option');
    // Find the relationship option (contains arrow character)
    const relOption = options.find(
      (opt) => opt.textContent?.includes('\u2192'),
    );
    expect(relOption).toBeDefined();

    await user.click(relOption!);
    expect(useStore.getState().selectedRelationshipId).toBe('customer-has-order');
  });

  it('limits results to 10', async () => {
    // Add many concepts
    const manyConcepts: Record<string, Concept> = {};
    for (let i = 0; i < 15; i++) {
      manyConcepts[`concept_${i}`] = makeConcept({ name: `TestConcept${i}` });
    }
    useStore.setState({ concepts: manyConcepts });

    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'TestConcept');

    const options = screen.getAllByRole('option');
    expect(options.length).toBeLessThanOrEqual(10);
  });

  it('highlights matching text in results', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('combobox');
    await user.type(input, 'Cust');

    // The highlight span should exist
    const highlight = document.querySelector('.search-highlight');
    expect(highlight).not.toBeNull();
    expect(highlight?.textContent).toBe('Cust');
  });
});
