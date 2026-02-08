import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { useStore } from '../store';

// Reset store before each test
beforeEach(() => {
  useStore.setState({
    domains: {},
    concepts: {},
    relationships: {},
    positions: {},
    isLoading: false,
    isSyncing: false,
    error: null,
    hasIntegrityErrors: false,
    selectedConceptId: null,
    selectedRelationshipId: null,
    hasUnsavedChanges: false,
    showUnsavedChangesDialog: false,
    pendingAction: null,
    messages: [],
    messageFilters: { error: true, warning: true, info: true },
    messagesPanelExpanded: false,
    messageCounts: { error: 0, warning: 0, info: 0 },
  });
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------- fetchState ----------

describe('fetchState', () => {
  it('sets isLoading while fetching', async () => {
    const data = { domains: {}, concepts: {}, relationships: {}, positions: {} };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );

    const promise = useStore.getState().fetchState();
    // After call starts, isLoading should be true
    expect(useStore.getState().isLoading).toBe(true);

    await promise;
    expect(useStore.getState().isLoading).toBe(false);
  });

  it('populates state from API response', async () => {
    const data = {
      domains: { d1: { name: 'd1', display_name: 'Domain One' } },
      concepts: {
        c1: {
          name: 'Customer',
          domain: 'd1',
          status: 'draft',
          isGhost: false,
          validationStatus: 'valid',
          validationMessages: [],
          bronze_models: [],
          silver_models: [],
          gold_models: [],
          inferred_models: [],
        },
      },
      relationships: {},
      positions: { c1: { x: 100, y: 200 } },
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );

    await useStore.getState().fetchState();

    const state = useStore.getState();
    expect(state.domains).toEqual(data.domains);
    expect(state.concepts).toEqual(data.concepts);
    expect(state.positions).toEqual(data.positions);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('handles integrity errors in response', async () => {
    const data = {
      domains: {},
      concepts: {},
      relationships: {},
      positions: {},
      hasIntegrityErrors: true,
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );

    await useStore.getState().fetchState();

    const state = useStore.getState();
    expect(state.hasIntegrityErrors).toBe(true);
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].severity).toBe('error');
    expect(state.messageCounts.error).toBe(1);
  });

  it('sets error on fetch failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('', { status: 500, statusText: 'Internal Server Error' }),
    );

    await useStore.getState().fetchState();

    const state = useStore.getState();
    expect(state.error).toContain('Failed to fetch state');
    expect(state.isLoading).toBe(false);
  });

  it('sets error on network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'));

    await useStore.getState().fetchState();

    const state = useStore.getState();
    expect(state.error).toBe('Network error');
    expect(state.isLoading).toBe(false);
  });
});

// ---------- sync ----------

describe('sync', () => {
  it('sets isSyncing while syncing', async () => {
    const data = {
      success: true,
      state: { domains: {}, concepts: {}, relationships: {}, positions: {} },
      messages: [],
      counts: { error: 0, warning: 0, info: 0 },
    };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );

    const promise = useStore.getState().sync();
    expect(useStore.getState().isSyncing).toBe(true);

    await promise;
    expect(useStore.getState().isSyncing).toBe(false);
  });

  it('populates state and messages after successful sync', async () => {
    const messages = [
      { id: 'm1', severity: 'warning', text: 'Missing definition' },
    ];
    const data = {
      success: true,
      state: {
        domains: { d1: { name: 'd1', display_name: 'Sales' } },
        concepts: {},
        relationships: {},
        positions: {},
      },
      messages,
      counts: { error: 0, warning: 1, info: 0 },
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );

    await useStore.getState().sync();

    const state = useStore.getState();
    expect(state.domains).toEqual(data.state.domains);
    expect(state.messages).toEqual(messages);
    expect(state.messageCounts.warning).toBe(1);
    expect(state.hasIntegrityErrors).toBe(false);
  });

  it('sets error when sync returns success=false', async () => {
    const data = { success: false, error: 'Parse error' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );

    await useStore.getState().sync();

    expect(useStore.getState().error).toBe('Parse error');
    expect(useStore.getState().isSyncing).toBe(false);
  });

  it('sets error on HTTP failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('', { status: 500, statusText: 'Server Error' }),
    );

    await useStore.getState().sync();

    expect(useStore.getState().error).toContain('Failed to sync');
    expect(useStore.getState().isSyncing).toBe(false);
  });
});

// ---------- updateConcept ----------

describe('updateConcept', () => {
  it('updates a concept by id', () => {
    useStore.setState({
      concepts: {
        c1: {
          name: 'Customer',
          domain: 'd1',
          status: 'draft',
          isGhost: false,
          validationStatus: 'valid',
          validationMessages: [],
          bronze_models: [],
          silver_models: [],
          gold_models: [],
          inferred_models: [],
        },
      },
    });

    useStore.getState().updateConcept('c1', { name: 'Client', owner: 'team_a' });

    const concept = useStore.getState().concepts.c1;
    expect(concept.name).toBe('Client');
    expect(concept.owner).toBe('team_a');
    expect(concept.domain).toBe('d1'); // unchanged field preserved
  });
});

// ---------- updateRelationship ----------

describe('updateRelationship', () => {
  it('updates a relationship by id', () => {
    useStore.setState({
      relationships: {
        r1: {
          name: 'has',
          verb: 'has',
          from_concept: 'c1',
          to_concept: 'c2',
          domains: [],
          status: 'stub',
          realized_by: [],
          validationStatus: 'valid',
          validationMessages: [],
        },
      },
    });

    useStore.getState().updateRelationship('r1', { verb: 'contains', cardinality: '1:N' });

    const rel = useStore.getState().relationships.r1;
    expect(rel.verb).toBe('contains');
    expect(rel.cardinality).toBe('1:N');
    expect(rel.from_concept).toBe('c1'); // unchanged
  });
});

// ---------- updatePositions ----------

describe('updatePositions', () => {
  it('merges new positions with existing', () => {
    useStore.setState({ positions: { c1: { x: 0, y: 0 } } });

    useStore.getState().updatePositions({ c2: { x: 100, y: 200 } });

    const positions = useStore.getState().positions;
    expect(positions.c1).toEqual({ x: 0, y: 0 });
    expect(positions.c2).toEqual({ x: 100, y: 200 });
  });
});

// ---------- saveState ----------

describe('saveState', () => {
  it('posts current state to API', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('{}', { status: 200 }),
    );

    useStore.setState({
      domains: { d1: { name: 'd1', display_name: 'Sales' } },
      concepts: {},
      relationships: {},
    });

    await useStore.getState().saveState();

    expect(fetchMock).toHaveBeenCalledWith('/api/state', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }));

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    expect(body.domains).toEqual({ d1: { name: 'd1', display_name: 'Sales' } });
  });

  it('sets error on failure and re-throws', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('', { status: 500, statusText: 'Server Error' }),
    );

    await expect(useStore.getState().saveState()).rejects.toThrow();
    expect(useStore.getState().error).toContain('Failed to save state');
  });
});

// ---------- saveLayout ----------

describe('saveLayout', () => {
  it('posts positions to API', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('{}', { status: 200 }),
    );

    useStore.setState({ positions: { c1: { x: 50, y: 75 } } });

    await useStore.getState().saveLayout();

    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    expect(body.positions).toEqual({ c1: { x: 50, y: 75 } });
  });
});

// ---------- Selection ----------

describe('selection', () => {
  it('selectConcept sets concept id and clears relationship', () => {
    useStore.setState({ selectedRelationshipId: 'r1' });

    useStore.getState().selectConcept('c1');

    expect(useStore.getState().selectedConceptId).toBe('c1');
    expect(useStore.getState().selectedRelationshipId).toBeNull();
  });

  it('selectRelationship sets relationship id and clears concept', () => {
    useStore.setState({ selectedConceptId: 'c1' });

    useStore.getState().selectRelationship('r1');

    expect(useStore.getState().selectedRelationshipId).toBe('r1');
    expect(useStore.getState().selectedConceptId).toBeNull();
  });

  it('clearSelection clears both selections', () => {
    useStore.setState({ selectedConceptId: 'c1', selectedRelationshipId: 'r1' });

    useStore.getState().clearSelection();

    expect(useStore.getState().selectedConceptId).toBeNull();
    expect(useStore.getState().selectedRelationshipId).toBeNull();
  });
});

// ---------- deleteGhostConcept ----------

describe('deleteGhostConcept', () => {
  it('removes a ghost concept', () => {
    useStore.setState({
      concepts: {
        c1: {
          name: 'Ghost',
          isGhost: true,
          status: 'stub',
          validationStatus: 'error',
          validationMessages: [],
          bronze_models: [],
          silver_models: [],
          gold_models: [],
          inferred_models: [],
        },
      },
    });

    useStore.getState().deleteGhostConcept('c1');

    expect(useStore.getState().concepts.c1).toBeUndefined();
  });

  it('does not remove non-ghost concepts', () => {
    useStore.setState({
      concepts: {
        c1: {
          name: 'Real',
          isGhost: false,
          status: 'draft',
          validationStatus: 'valid',
          validationMessages: [],
          bronze_models: [],
          silver_models: [],
          gold_models: [],
          inferred_models: [],
        },
      },
    });

    useStore.getState().deleteGhostConcept('c1');

    expect(useStore.getState().concepts.c1).toBeDefined();
  });

  it('clears selection if deleted ghost was selected', () => {
    useStore.setState({
      selectedConceptId: 'c1',
      concepts: {
        c1: {
          name: 'Ghost',
          isGhost: true,
          status: 'stub',
          validationStatus: 'error',
          validationMessages: [],
          bronze_models: [],
          silver_models: [],
          gold_models: [],
          inferred_models: [],
        },
      },
    });

    useStore.getState().deleteGhostConcept('c1');

    expect(useStore.getState().selectedConceptId).toBeNull();
  });
});

// ---------- Unsaved changes ----------

describe('unsaved changes flow', () => {
  it('requestClearSelection shows dialog when unsaved changes exist', () => {
    useStore.setState({ hasUnsavedChanges: true, selectedConceptId: 'c1' });

    useStore.getState().requestClearSelection();

    expect(useStore.getState().showUnsavedChangesDialog).toBe(true);
    expect(useStore.getState().selectedConceptId).toBe('c1'); // selection preserved
  });

  it('requestClearSelection clears immediately when no unsaved changes', () => {
    useStore.setState({ hasUnsavedChanges: false, selectedConceptId: 'c1' });

    useStore.getState().requestClearSelection();

    expect(useStore.getState().selectedConceptId).toBeNull();
    expect(useStore.getState().showUnsavedChangesDialog).toBe(false);
  });

  it('confirmDiscardChanges clears selection and resets state', () => {
    useStore.setState({
      hasUnsavedChanges: true,
      showUnsavedChangesDialog: true,
      selectedConceptId: 'c1',
    });

    useStore.getState().confirmDiscardChanges();

    expect(useStore.getState().selectedConceptId).toBeNull();
    expect(useStore.getState().hasUnsavedChanges).toBe(false);
    expect(useStore.getState().showUnsavedChangesDialog).toBe(false);
  });

  it('cancelDiscardChanges closes dialog without clearing selection', () => {
    useStore.setState({
      hasUnsavedChanges: true,
      showUnsavedChangesDialog: true,
      selectedConceptId: 'c1',
    });

    useStore.getState().cancelDiscardChanges();

    expect(useStore.getState().showUnsavedChangesDialog).toBe(false);
    expect(useStore.getState().selectedConceptId).toBe('c1');
    expect(useStore.getState().hasUnsavedChanges).toBe(true);
  });

  it('forceClearSelection clears everything', () => {
    useStore.setState({
      hasUnsavedChanges: true,
      showUnsavedChangesDialog: true,
      selectedConceptId: 'c1',
      selectedRelationshipId: 'r1',
    });

    useStore.getState().forceClearSelection();

    expect(useStore.getState().selectedConceptId).toBeNull();
    expect(useStore.getState().selectedRelationshipId).toBeNull();
    expect(useStore.getState().hasUnsavedChanges).toBe(false);
    expect(useStore.getState().showUnsavedChangesDialog).toBe(false);
  });
});

// ---------- Messages panel ----------

describe('messages panel', () => {
  it('addMessage appends a message and increments count', () => {
    useStore.getState().addMessage('warning', 'Missing definition');

    const state = useStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].severity).toBe('warning');
    expect(state.messages[0].text).toBe('Missing definition');
    expect(state.messageCounts.warning).toBe(1);
  });

  it('addMessage accumulates messages', () => {
    useStore.getState().addMessage('error', 'Error 1');
    useStore.getState().addMessage('error', 'Error 2');
    useStore.getState().addMessage('info', 'Info 1');

    const state = useStore.getState();
    expect(state.messages).toHaveLength(3);
    expect(state.messageCounts.error).toBe(2);
    expect(state.messageCounts.info).toBe(1);
  });

  it('toggleMessageFilter toggles filter state', () => {
    expect(useStore.getState().messageFilters.error).toBe(true);

    useStore.getState().toggleMessageFilter('error');
    expect(useStore.getState().messageFilters.error).toBe(false);

    useStore.getState().toggleMessageFilter('error');
    expect(useStore.getState().messageFilters.error).toBe(true);
  });

  it('toggleMessagesPanel toggles expanded state', () => {
    expect(useStore.getState().messagesPanelExpanded).toBe(false);

    useStore.getState().toggleMessagesPanel();
    expect(useStore.getState().messagesPanelExpanded).toBe(true);

    useStore.getState().toggleMessagesPanel();
    expect(useStore.getState().messagesPanelExpanded).toBe(false);
  });

  it('clearMessages resets messages and counts', () => {
    useStore.getState().addMessage('error', 'Error 1');
    useStore.getState().addMessage('warning', 'Warn 1');

    useStore.getState().clearMessages();

    const state = useStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.messageCounts).toEqual({ error: 0, warning: 0, info: 0 });
  });
});
