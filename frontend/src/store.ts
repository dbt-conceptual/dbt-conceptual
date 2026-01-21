import { create } from 'zustand';
import type { ProjectState, Concept, Relationship, Message, MessageSeverity } from './types';

interface MessageFilters {
  error: boolean;
  warning: boolean;
  info: boolean;
}

interface AppState extends ProjectState {
  // Loading state
  isLoading: boolean;
  isSyncing: boolean;
  error: string | null;
  hasIntegrityErrors: boolean;
  demoMode: boolean;

  // Selection state
  selectedConceptId: string | null;
  selectedRelationshipId: string | null;

  // Unsaved changes dialog state
  hasUnsavedChanges: boolean;
  showUnsavedChangesDialog: boolean;
  pendingAction: (() => void) | null;

  // Messages panel state
  messages: Message[];
  messageFilters: MessageFilters;
  messagesPanelExpanded: boolean;
  messageCounts: {
    error: number;
    warning: number;
    info: number;
  };

  // Actions
  fetchMode: () => Promise<void>;
  fetchState: () => Promise<void>;
  sync: () => Promise<void>;
  updateConcept: (id: string, updates: Partial<Concept>) => void;
  updateRelationship: (id: string, updates: Partial<Relationship>) => void;
  updatePositions: (positions: Record<string, { x: number; y: number }>) => void;
  saveState: () => Promise<void>;
  saveLayout: () => Promise<void>;
  selectConcept: (id: string | null) => void;
  selectRelationship: (id: string | null) => void;
  clearSelection: () => void;
  deleteGhostConcept: (id: string) => void;

  // Unsaved changes actions
  setHasUnsavedChanges: (hasChanges: boolean) => void;
  requestClearSelection: () => void;
  confirmDiscardChanges: () => void;
  cancelDiscardChanges: () => void;
  forceClearSelection: () => void;

  // Messages panel actions
  toggleMessageFilter: (severity: MessageSeverity) => void;
  toggleMessagesPanel: () => void;
  clearMessages: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  // Initial state
  domains: {},
  concepts: {},
  relationships: {},
  positions: {},
  isLoading: false,
  isSyncing: false,
  error: null,
  demoMode: false,
  hasIntegrityErrors: false,
  selectedConceptId: null,
  selectedRelationshipId: null,

  // Unsaved changes dialog state
  hasUnsavedChanges: false,
  showUnsavedChangesDialog: false,
  pendingAction: null,

  // Messages panel initial state
  messages: [],
  messageFilters: {
    error: true,
    warning: true,
    info: true,
  },
  messagesPanelExpanded: false,
  messageCounts: {
    error: 0,
    warning: 0,
    info: 0,
  },

  // Fetch mode (demo or normal)
  fetchMode: async () => {
    try {
      const response = await fetch('/api/mode');
      if (response.ok) {
        const data = await response.json();
        set({ demoMode: data.demoMode || false });
      }
    } catch {
      // Silently ignore - default to normal mode
    }
  },

  // Fetch state from API (no validation on initial load)
  fetchState: async () => {
    set({ isLoading: true, error: null, hasIntegrityErrors: false });
    try {
      const response = await fetch('/api/state');
      if (!response.ok) {
        throw new Error(`Failed to fetch state: ${response.statusText}`);
      }
      const data = await response.json();
      const hasIntegrityErrors = data.hasIntegrityErrors || false;

      set({
        domains: data.domains || {},
        concepts: data.concepts || {},
        relationships: data.relationships || {},
        positions: data.positions || {},
        hasIntegrityErrors,
        isLoading: false,
        // If integrity errors, show message in panel
        messages: hasIntegrityErrors
          ? [{ id: 'integrity-error', severity: 'error' as const, text: 'Conceptual model has integrity issues. Sync to resolve.' }]
          : [],
        messageCounts: hasIntegrityErrors
          ? { error: 1, warning: 0, info: 0 }
          : { error: 0, warning: 0, info: 0 },
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false,
      });
    }
  },

  // Sync with dbt project and run validation
  sync: async () => {
    set({ isSyncing: true, error: null });
    try {
      const response = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        throw new Error(`Failed to sync: ${response.statusText}`);
      }
      const data = await response.json();

      if (data.success && data.state) {
        set({
          domains: data.state.domains || {},
          concepts: data.state.concepts || {},
          relationships: data.state.relationships || {},
          positions: data.state.positions || {},
          hasIntegrityErrors: false, // Sync resolves integrity issues
          messages: data.messages || [],
          messageCounts: data.counts || { error: 0, warning: 0, info: 0 },
          isSyncing: false,
        });
      } else {
        throw new Error(data.error || 'Sync failed');
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isSyncing: false,
      });
    }
  },

  // Update a concept
  updateConcept: (id: string, updates: Partial<Concept>) => {
    set((state) => ({
      concepts: {
        ...state.concepts,
        [id]: { ...state.concepts[id], ...updates },
      },
    }));
  },

  // Update a relationship
  updateRelationship: (id: string, updates: Partial<Relationship>) => {
    set((state) => ({
      relationships: {
        ...state.relationships,
        [id]: { ...state.relationships[id], ...updates },
      },
    }));
  },

  // Update node positions
  updatePositions: (positions: Record<string, { x: number; y: number }>) => {
    set((state) => ({
      positions: { ...state.positions, ...positions },
    }));
  },

  // Save state to API
  saveState: async () => {
    const { domains, concepts, relationships } = get();
    try {
      const response = await fetch('/api/state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domains, concepts, relationships }),
      });
      if (!response.ok) {
        throw new Error(`Failed to save state: ${response.statusText}`);
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  },

  // Save layout positions to API
  saveLayout: async () => {
    const { positions } = get();
    try {
      const response = await fetch('/api/layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ positions }),
      });
      if (!response.ok) {
        throw new Error(`Failed to save layout: ${response.statusText}`);
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  },

  // Selection actions
  selectConcept: (id: string | null) => {
    set({ selectedConceptId: id, selectedRelationshipId: null });
  },

  selectRelationship: (id: string | null) => {
    set({ selectedRelationshipId: id, selectedConceptId: null });
  },

  clearSelection: () => {
    set({ selectedConceptId: null, selectedRelationshipId: null });
  },

  // Delete a ghost concept from canvas (not persisted, reappears on next sync)
  deleteGhostConcept: (id: string) => {
    set((state) => {
      const concept = state.concepts[id];
      if (!concept?.isGhost) return state;

      const { [id]: removed, ...remainingConcepts } = state.concepts;
      return {
        concepts: remainingConcepts,
        selectedConceptId: state.selectedConceptId === id ? null : state.selectedConceptId,
      };
    });
  },

  // Unsaved changes actions
  setHasUnsavedChanges: (hasChanges: boolean) => {
    set({ hasUnsavedChanges: hasChanges });
  },

  requestClearSelection: () => {
    const { hasUnsavedChanges } = get();
    if (hasUnsavedChanges) {
      set({ showUnsavedChangesDialog: true });
    } else {
      set({ selectedConceptId: null, selectedRelationshipId: null });
    }
  },

  confirmDiscardChanges: () => {
    set({
      showUnsavedChangesDialog: false,
      hasUnsavedChanges: false,
      selectedConceptId: null,
      selectedRelationshipId: null,
    });
  },

  cancelDiscardChanges: () => {
    set({ showUnsavedChangesDialog: false });
  },

  forceClearSelection: () => {
    set({
      selectedConceptId: null,
      selectedRelationshipId: null,
      hasUnsavedChanges: false,
      showUnsavedChangesDialog: false,
    });
  },

  // Messages panel actions
  toggleMessageFilter: (severity: MessageSeverity) => {
    set((state) => ({
      messageFilters: {
        ...state.messageFilters,
        [severity]: !state.messageFilters[severity],
      },
    }));
  },

  toggleMessagesPanel: () => {
    set((state) => ({
      messagesPanelExpanded: !state.messagesPanelExpanded,
    }));
  },

  clearMessages: () => {
    set({
      messages: [],
      messageCounts: { error: 0, warning: 0, info: 0 },
    });
  },
}));
