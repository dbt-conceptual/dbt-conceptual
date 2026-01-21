import { useState } from 'react';
import { useStore } from '../store';
import { PropertiesTab } from './PropertiesTab';
import { ModelsTab } from './ModelsTab';

export function PropertyPanel() {
  const { selectedConceptId, selectedRelationshipId, concepts, relationships, clearSelection } = useStore();
  const [activeTab, setActiveTab] = useState<'properties' | 'models'>('properties');

  const selectedConcept = selectedConceptId ? concepts[selectedConceptId] : null;
  const selectedRelationship = selectedRelationshipId ? relationships[selectedRelationshipId] : null;

  if (!selectedConcept && !selectedRelationship) {
    return (
      <div className="property-panel">
        <div className="property-panel-empty">
          <div className="property-panel-empty-icon">{'\u25C7'}</div>
          <div className="property-panel-empty-text">Select a concept or relationship to view details</div>
        </div>
      </div>
    );
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

  return (
    <div className="property-panel">
      {/* Header */}
      <div className="property-panel-header">
        <div className="property-panel-title">{panelTitle}</div>
        <button className="property-panel-close" onClick={clearSelection} title="Close panel">
          {'\u00D7'}
        </button>
      </div>

      {/* Tabs (only for non-ghost concepts) */}
      {selectedConcept && !isGhostConcept && (
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
          <PropertiesTab conceptId={selectedConceptId!} />
        )}
        {selectedConcept && !isGhostConcept && activeTab === 'models' && (
          <ModelsTab conceptId={selectedConceptId!} />
        )}
        {selectedRelationship && (
          <PropertiesTab relationshipId={selectedRelationshipId!} />
        )}
      </div>
    </div>
  );
}
