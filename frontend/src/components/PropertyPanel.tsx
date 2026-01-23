import { useState, useRef } from 'react';
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
    setHasUnsavedChanges,
    forceClearSelection,
    fetchState,
  } = useStore();
  const [activeTab, setActiveTab] = useState<'properties' | 'models'>('properties');
  const propertiesRef = useRef<PropertiesTabHandle>(null);

  const selectedConcept = selectedConceptId ? concepts[selectedConceptId] : null;
  const selectedRelationship = selectedRelationshipId ? relationships[selectedRelationshipId] : null;

  // Hide panel completely when nothing is selected
  if (!selectedConcept && !selectedRelationship) {
    return null;
  }

  // Determine if we're showing a ghost concept
  const isGhostConcept = selectedConcept?.isGhost;

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
          onConfirm={handleSaveAndClose}
          onCancel={handleDiscardAndClose}
        />
      )}
    </>
  );
}
