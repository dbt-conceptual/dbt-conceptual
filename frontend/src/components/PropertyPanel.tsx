import { useState, useRef, useEffect, useCallback } from 'react';
import { useStore } from '../store';
import { PropertiesTab } from './PropertiesTab';
import type { PropertiesTabHandle } from './PropertiesTab';
import { ModelsTab } from './ModelsTab';
import { RelationshipModelsTab } from './RelationshipModelsTab';
import { ConfirmDialog } from './ConfirmDialog';

export function PropertyPanel() {
  const {
    selectedConceptId,
    selectedRelationshipId,
    concepts,
    relationships,
    showUnsavedChangesDialog,
    requestClearSelection,
    confirmDiscardChanges,
    cancelDiscardChanges,
    setHasUnsavedChanges,
    forceClearSelection,
    fetchState,
  } = useStore();
  const [activeTab, setActiveTab] = useState<'properties' | 'models'>('properties');
  const propertiesRef = useRef<PropertiesTabHandle>(null);

  const selectedConcept = selectedConceptId ? concepts[selectedConceptId] : null;
  const selectedRelationship = selectedRelationshipId ? relationships[selectedRelationshipId] : null;
  const hasSelection = selectedConcept || selectedRelationship;

  // Determine if we're showing a ghost concept
  const isGhostConcept = selectedConcept?.isGhost;

  // Handle save via keyboard
  const handleSave = useCallback(async () => {
    if (propertiesRef.current) {
      await propertiesRef.current.save();
    }
  }, []);

  // Keyboard shortcuts: Cmd+S to save, Escape to close panel
  useEffect(() => {
    if (!hasSelection) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+S or Ctrl+S to save
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
      // Escape to close panel (only if not in a text input or dialog)
      if (e.key === 'Escape' && !showUnsavedChangesDialog) {
        const target = e.target as HTMLElement;
        const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT';
        if (!isInInput) {
          requestClearSelection();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [hasSelection, handleSave, showUnsavedChangesDialog, requestClearSelection]);

  // Hide panel completely when nothing is selected
  if (!hasSelection) {
    return null;
  }

  // Determine the title to show
  let panelTitle = '';
  if (selectedConcept) {
    panelTitle = isGhostConcept ? 'Ghost Concept' : selectedConcept.name;
  } else if (selectedRelationship) {
    panelTitle = 'Relationship';
  }

  const handleClose = () => {
    requestClearSelection();
  };

  const handleSaveAndClose = async () => {
    if (propertiesRef.current) {
      await propertiesRef.current.save();
    }
    forceClearSelection();
  };

  const handleDiscardAndClose = () => {
    // Reload state from server to discard local changes
    fetchState();
    confirmDiscardChanges();
  };

  return (
    <>
      <div className="property-panel">
        {/* Header */}
        <div className="property-panel-header">
          <div className="property-panel-title">{panelTitle}</div>
          <button className="property-panel-close" onClick={handleClose} title="Close panel" aria-label="Close panel">
            {'\u00D7'}
          </button>
        </div>

        {/* Tabs (for non-ghost concepts and relationships) */}
        {((selectedConcept && !isGhostConcept) || selectedRelationship) && (
          <div className="property-panel-tabs">
            <button
              className={`property-panel-tab ${activeTab === 'properties' ? 'active' : ''}`}
              onClick={() => setActiveTab('properties')}
            >
              Properties
            </button>
            <button
              className={`property-panel-tab ${activeTab === 'models' ? 'active' : ''}`}
              onClick={() => setActiveTab('models')}
            >
              Models
            </button>
          </div>
        )}

        {/* Content */}
        <div className="property-panel-content">
          {selectedConcept && activeTab === 'properties' && (
            <PropertiesTab
              ref={propertiesRef}
              conceptId={selectedConceptId!}
              onDirtyChange={setHasUnsavedChanges}
            />
          )}
          {selectedConcept && !isGhostConcept && activeTab === 'models' && (
            <ModelsTab conceptId={selectedConceptId!} />
          )}
          {selectedRelationship && activeTab === 'properties' && (
            <PropertiesTab
              ref={propertiesRef}
              relationshipId={selectedRelationshipId!}
              onDirtyChange={setHasUnsavedChanges}
            />
          )}
          {selectedRelationship && activeTab === 'models' && (
            <RelationshipModelsTab relationshipId={selectedRelationshipId!} />
          )}
        </div>
      </div>

      {/* Unsaved changes dialog */}
      {showUnsavedChangesDialog && (
        <ConfirmDialog
          title="Unsaved Changes"
          message="You have unsaved changes that will be lost if you close this panel."
          confirmLabel="Save & Close"
          cancelLabel="Discard Changes"
          stayLabel="Cancel"
          onConfirm={handleSaveAndClose}
          onCancel={handleDiscardAndClose}
          onStay={cancelDiscardChanges}
        />
      )}
    </>
  );
}
