import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessagesPanel } from '../components/MessagesPanel';
import { useStore } from '../store';
import type { Message } from '../types';

function makeMessages(): Message[] {
  return [
    { id: 'm1', severity: 'error', text: "Concept 'Unknown' not found", elementType: 'concept', elementId: 'c1' },
    { id: 'm2', severity: 'warning', text: 'Missing definition for Customer', elementType: 'concept', elementId: 'c2' },
    { id: 'm3', severity: 'info', text: 'Sync completed successfully' },
  ];
}

function seedExpandedPanel() {
  useStore.setState({
    messages: makeMessages(),
    messageFilters: { error: true, warning: true, info: true },
    messagesPanelExpanded: true,
    messageCounts: { error: 1, warning: 1, info: 1 },
    isSyncing: false,
    selectedConceptId: null,
    selectedRelationshipId: null,
  });
}

beforeEach(() => {
  useStore.setState({
    messages: [],
    messageFilters: { error: true, warning: true, info: true },
    messagesPanelExpanded: false,
    messageCounts: { error: 0, warning: 0, info: 0 },
    isSyncing: false,
    selectedConceptId: null,
    selectedRelationshipId: null,
  });
  vi.restoreAllMocks();
});

describe('MessagesPanel', () => {
  describe('collapsed bar', () => {
    it('renders collapsed bar by default', () => {
      render(<MessagesPanel />);
      // The collapsed bar has a specific aria-label pattern: "Messages panel: X messages"
      expect(screen.getByRole('button', { name: /messages panel:.*messages/i })).toBeInTheDocument();
    });

    it('shows message count when messages exist', () => {
      useStore.setState({
        messages: makeMessages(),
        messageCounts: { error: 1, warning: 1, info: 1 },
      });

      render(<MessagesPanel />);
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('shows error badge when errors exist', () => {
      useStore.setState({
        messages: [{ id: 'm1', severity: 'error', text: 'Bad' }],
        messageCounts: { error: 1, warning: 0, info: 0 },
      });

      render(<MessagesPanel />);
      const badge = document.querySelector('.messages-bar-badge.error');
      expect(badge).not.toBeNull();
    });

    it('expands panel when clicked', async () => {
      const user = userEvent.setup();
      useStore.setState({
        messages: makeMessages(),
        messageCounts: { error: 1, warning: 1, info: 1 },
      });

      render(<MessagesPanel />);

      // Click the collapsed bar itself (the outer container with role="button")
      // The bar has aria-label "Messages panel: 3 messages. Click to expand."
      const bar = screen.getByRole('button', { name: /messages panel:.*click to expand/i });
      await user.click(bar);

      expect(useStore.getState().messagesPanelExpanded).toBe(true);
    });

    it('has a sync button that triggers sync', async () => {
      const user = userEvent.setup();
      const syncData = {
        success: true,
        state: { domains: {}, concepts: {}, relationships: {}, positions: {} },
        messages: [],
        counts: { error: 0, warning: 0, info: 0 },
      };
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
        new Response(JSON.stringify(syncData), { status: 200, headers: { 'Content-Type': 'application/json' } }),
      );

      render(<MessagesPanel />);

      const syncBtn = screen.getByRole('button', { name: /sync with dbt project/i });
      await user.click(syncBtn);

      expect(globalThis.fetch).toHaveBeenCalledWith('/api/sync', expect.anything());
    });
  });

  describe('expanded panel', () => {
    it('renders messages header and filters', () => {
      seedExpandedPanel();
      render(<MessagesPanel />);

      expect(screen.getByText('Messages')).toBeInTheDocument();
      expect(screen.getByRole('group', { name: /message filters/i })).toBeInTheDocument();
    });

    it('shows all messages when all filters are active', () => {
      seedExpandedPanel();
      render(<MessagesPanel />);

      const items = document.querySelectorAll('.message-item');
      expect(items.length).toBe(3);
    });

    it('filters messages when toggling error filter off', async () => {
      const user = userEvent.setup();
      seedExpandedPanel();
      render(<MessagesPanel />);

      // Toggle error filter off
      const errorToggle = screen.getByRole('button', { name: /hide errors/i });
      await user.click(errorToggle);

      // Error filter should be toggled
      expect(useStore.getState().messageFilters.error).toBe(false);
    });

    it('filters messages when toggling warning filter off', async () => {
      const user = userEvent.setup();
      seedExpandedPanel();
      render(<MessagesPanel />);

      const warnToggle = screen.getByRole('button', { name: /hide warnings/i });
      await user.click(warnToggle);

      expect(useStore.getState().messageFilters.warning).toBe(false);
    });

    it('shows empty state when no messages exist', () => {
      useStore.setState({ messagesPanelExpanded: true, messages: [] });
      render(<MessagesPanel />);

      expect(screen.getByText('Click sync to validate')).toBeInTheDocument();
    });

    it('shows filter empty state when all filtered out', () => {
      useStore.setState({
        messagesPanelExpanded: true,
        messages: [{ id: 'm1', severity: 'error', text: 'Error' }],
        messageFilters: { error: false, warning: false, info: false },
        messageCounts: { error: 1, warning: 0, info: 0 },
      });

      render(<MessagesPanel />);

      expect(screen.getByText('No messages match filters')).toBeInTheDocument();
    });

    it('navigates to concept when clicking a message with elementId', async () => {
      const user = userEvent.setup();
      seedExpandedPanel();
      render(<MessagesPanel />);

      // Click the error message (has elementType: concept, elementId: c1)
      const errorMsg = screen.getByRole('button', { name: /not found.*click to navigate/i });
      await user.click(errorMsg);

      expect(useStore.getState().selectedConceptId).toBe('c1');
    });

    it('collapses panel when collapse button is clicked', async () => {
      const user = userEvent.setup();
      seedExpandedPanel();
      render(<MessagesPanel />);

      const collapseBtn = screen.getByRole('button', { name: /collapse messages panel/i });
      await user.click(collapseBtn);

      expect(useStore.getState().messagesPanelExpanded).toBe(false);
    });

    it('highlights quoted terms in message text', () => {
      useStore.setState({
        messagesPanelExpanded: true,
        messages: [{ id: 'm1', severity: 'error', text: "Concept 'Customer' is invalid" }],
        messageCounts: { error: 1, warning: 0, info: 0 },
      });

      render(<MessagesPanel />);

      const highlight = document.querySelector('.highlight');
      expect(highlight).not.toBeNull();
      expect(highlight?.textContent).toBe('Customer');
    });

    it('shows filter counts', () => {
      seedExpandedPanel();
      render(<MessagesPanel />);

      // Should show the count for each severity
      const filterGroup = screen.getByRole('group', { name: /message filters/i });
      expect(filterGroup).toBeInTheDocument();

      // Each filter toggle shows a count
      const counts = document.querySelectorAll('.filter-toggle-count');
      expect(counts.length).toBe(3);
    });
  });
});
