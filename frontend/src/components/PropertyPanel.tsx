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
          <div className="property-panel-empty-icon">◇</div>
          <div className="property-panel-empty-text">Select a concept or relationship to view details</div>
        </div>
      </div>
    );
  }

  return (
    <div className="property-panel">
      {/* Header */}
      <div className="property-panel-header">
        <div className="property-panel-title">
          {selectedConcept ? selectedConcept.name : selectedRelationship?.name}
        </div>
        <button className="property-panel-close" onClick={clearSelection} title="Close panel">
          ×
        </button>
      </div>

      {/* Tabs (only for concepts) */}
      {selectedConcept && (
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
        {selectedConcept && activeTab === 'models' && (
          <ModelsTab conceptId={selectedConceptId!} />
        )}
        {selectedRelationship && (
          <PropertiesTab relationshipId={selectedRelationshipId!} />
        )}
      </div>
    </div>
  );
}
