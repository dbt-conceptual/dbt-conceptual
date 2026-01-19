import { create } from 'zustand';
import type { ProjectState, Concept, Relationship } from './types';

interface AppState extends ProjectState {
  // Loading state
  isLoading: boolean;
  error: string | null;

  // Selection state
  selectedConceptId: string | null;
  selectedRelationshipId: string | null;

  // Actions
  fetchState: () => Promise<void>;
  updateConcept: (id: string, updates: Partial<Concept>) => void;
  updateRelationship: (id: string, updates: Partial<Relationship>) => void;
  updatePositions: (positions: Record<string, { x: number; y: number }>) => void;
  saveState: () => Promise<void>;
  saveLayout: () => Promise<void>;
  selectConcept: (id: string | null) => void;
  selectRelationship: (id: string | null) => void;
  clearSelection: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  // Initial state
  domains: {},
  concepts: {},
  relationships: {},
  positions: {},
  isLoading: false,
  error: null,
  selectedConceptId: null,
  selectedRelationshipId: null,

  // Fetch state from API
  fetchState: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch('/api/state');
      if (!response.ok) {
        throw new Error(`Failed to fetch state: ${response.statusText}`);
      }
      const data = await response.json();
      set({
        domains: data.domains || {},
        concepts: data.concepts || {},
        relationships: data.relationships || {},
        positions: data.positions || {},
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false,
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
}));
