import { useStore } from '../store';

interface PropertiesTabProps {
  conceptId?: string;
  relationshipId?: string;
}

export function PropertiesTab({ conceptId, relationshipId }: PropertiesTabProps) {
  const { concepts, relationships, domains, updateConcept, updateRelationship, saveState } = useStore();

  if (conceptId) {
    const concept = concepts[conceptId];
    if (!concept) return null;

    const isGhost = concept.isGhost;
    const hasValidationIssues =
      concept.validationStatus === 'error' || concept.validationStatus === 'warning';

    // Count relationships referencing this ghost concept
    const referencingRelationships = isGhost
      ? Object.values(relationships).filter(
          (r) => r.from_concept === conceptId || r.to_concept === conceptId
        ).length
      : 0;

    const handleChange = (field: string, value: string) => {
      updateConcept(conceptId, { [field]: value });
    };

    const handleSave = async () => {
      try {
        // When saving a ghost concept with a domain, it becomes a real concept
        if (isGhost && concept.domain) {
          updateConcept(conceptId, { isGhost: false, validationStatus: 'valid', validationMessages: [] });
        }
        await saveState();
      } catch (error) {
        console.error('Failed to save:', error);
      }
    };

    return (
      <div className="properties-tab">
        {/* Status indicator for ghost concepts */}
        {isGhost && (
          <div className="status-indicator">
            <span>{'\u2298'}</span>
            <span>Undefined — referenced by {referencingRelationships} relationship{referencingRelationships !== 1 ? 's' : ''}</span>
          </div>
        )}

        {/* Validation messages */}
        {!isGhost && hasValidationIssues && (
          <div className={`status-indicator ${concept.validationStatus}`}>
            <span>{concept.validationStatus === 'error' ? '\u2298' : '\u26A0'}</span>
            <span>{concept.validationMessages.join(', ')}</span>
          </div>
        )}

        {/* Name */}
        <div className="property-field">
          <label className="property-label">Name</label>
          <input
            type="text"
            className={`property-input ${isGhost ? 'ghost-field' : ''}`}
            value={concept.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="Concept name"
          />
        </div>

        {/* Domain */}
        <div className="property-field">
          <label className="property-label">Domain</label>
          <select
            className="property-select"
            value={concept.domain || ''}
            onChange={(e) => handleChange('domain', e.target.value)}
          >
            <option value="">Select domain...</option>
            {Object.keys(domains).map((domainId) => (
              <option key={domainId} value={domainId}>
                {domains[domainId].display_name}
              </option>
            ))}
          </select>
        </div>

        {/* Owner */}
        <div className="property-field">
          <label className="property-label">Owner</label>
          <input
            type="text"
            className="property-input"
            value={concept.owner || ''}
            onChange={(e) => handleChange('owner', e.target.value)}
            placeholder="e.g., data_team"
          />
        </div>

        {/* Definition */}
        <div className="property-field">
          <label className="property-label">Definition</label>
          <textarea
            className="property-textarea"
            value={concept.definition || ''}
            onChange={(e) => handleChange('definition', e.target.value)}
            placeholder="Describe this concept..."
            rows={4}
          />
        </div>

        {/* Color (only for non-ghost concepts) */}
        {!isGhost && (
          <div className="property-field">
            <label className="property-label">Custom Color</label>
            <input
              type="color"
              className="property-color"
              value={concept.color || '#4a9eff'}
              onChange={(e) => handleChange('color', e.target.value)}
            />
          </div>
        )}

        {/* Replaced By (for deprecation, only for non-ghost) */}
        {!isGhost && (
          <div className="property-field">
            <label className="property-label">Replaced By</label>
            <input
              type="text"
              className="property-input"
              value={concept.replaced_by || ''}
              onChange={(e) => handleChange('replaced_by', e.target.value)}
              placeholder="New concept name"
            />
          </div>
        )}

        {/* Status (read-only, derived) - only for non-ghost */}
        {!isGhost && (
          <div className="property-field">
            <label className="property-label">Status</label>
            <div className="property-readonly">
              <span className={`status-badge status-${concept.status}`}>
                {concept.status}
              </span>
              <span className="property-help">Derived from domain and models</span>
            </div>
          </div>
        )}

        {/* Save button */}
        <button className="property-save-btn" onClick={handleSave}>
          {isGhost ? 'Save as Concept' : 'Save Changes'}
        </button>
      </div>
    );
  }

  if (relationshipId) {
    const relationship = relationships[relationshipId];
    if (!relationship) return null;

    const isInvalid = relationship.validationStatus === 'error';
    const hasValidationIssues =
      relationship.validationStatus === 'error' || relationship.validationStatus === 'warning';

    // Check if source or target is a ghost
    const fromConcept = concepts[relationship.from_concept];
    const toConcept = concepts[relationship.to_concept];
    const fromIsGhost = fromConcept?.isGhost;
    const toIsGhost = toConcept?.isGhost;

    const handleChange = (field: string, value: string | string[]) => {
      updateRelationship(relationshipId, { [field]: value });
    };

    const handleSave = async () => {
      try {
        await saveState();
      } catch (error) {
        console.error('Failed to save:', error);
      }
    };

    return (
      <div className="properties-tab">
        {/* Status indicator for invalid relationships */}
        {hasValidationIssues && (
          <div className={`status-indicator ${relationship.validationStatus}`}>
            <span>{relationship.validationStatus === 'error' ? '\u2298' : '\u26A0'}</span>
            <span>
              {isInvalid
                ? `Invalid — ${toIsGhost ? 'target' : fromIsGhost ? 'source' : ''} concept not defined`
                : relationship.validationMessages.join(', ')}
            </span>
          </div>
        )}

        {/* Verb */}
        <div className="property-field">
          <label className="property-label">Verb</label>
          <input
            type="text"
            className="property-input"
            value={relationship.verb}
            onChange={(e) => handleChange('verb', e.target.value)}
            placeholder="contains, references, etc."
          />
        </div>

        {/* Custom Name */}
        <div className="property-field">
          <label className="property-label">Custom Name</label>
          <input
            type="text"
            className="property-input"
            value={relationship.custom_name || ''}
            onChange={(e) => handleChange('custom_name', e.target.value)}
            placeholder="Optional custom name"
          />
        </div>

        {/* From */}
        <div className="property-field">
          <label className="property-label">From</label>
          <input
            type="text"
            className={`property-input ${fromIsGhost ? 'error' : ''}`}
            value={relationship.from_concept}
            readOnly
          />
        </div>

        {/* To */}
        <div className="property-field">
          <label className="property-label">To</label>
          <input
            type="text"
            className={`property-input ${toIsGhost ? 'error' : ''}`}
            value={relationship.to_concept}
            readOnly
          />
        </div>

        {/* Cardinality */}
        <div className="property-field">
          <label className="property-label">Cardinality</label>
          <select
            className="property-select"
            value={relationship.cardinality || ''}
            onChange={(e) => handleChange('cardinality', e.target.value)}
          >
            <option value="">None</option>
            <option value="1:1">1:1 (One-to-One)</option>
            <option value="1:N">1:N (One-to-Many)</option>
            <option value="N:1">N:1 (Many-to-One)</option>
            <option value="N:M">N:M (Many-to-Many)</option>
          </select>
        </div>

        {/* Domains (multi-select) */}
        <div className="property-field">
          <label className="property-label">Domains</label>
          <div className="property-help">Select all domains this relationship crosses</div>
          {Object.keys(domains).map((domainId) => (
            <label key={domainId} className="property-checkbox">
              <input
                type="checkbox"
                checked={relationship.domains.includes(domainId)}
                onChange={(e) => {
                  const newDomains = e.target.checked
                    ? [...relationship.domains, domainId]
                    : relationship.domains.filter((d) => d !== domainId);
                  handleChange('domains', newDomains);
                }}
              />
              {domains[domainId].display_name}
            </label>
          ))}
        </div>

        {/* Owner */}
        <div className="property-field">
          <label className="property-label">Owner</label>
          <input
            type="text"
            className="property-input"
            value={relationship.owner || ''}
            onChange={(e) => handleChange('owner', e.target.value)}
            placeholder="@username"
          />
        </div>

        {/* Definition */}
        <div className="property-field">
          <label className="property-label">Definition</label>
          <textarea
            className="property-textarea"
            value={relationship.definition || ''}
            onChange={(e) => handleChange('definition', e.target.value)}
            placeholder="Describe this relationship..."
            rows={4}
          />
        </div>

        {/* Status (read-only, derived) */}
        <div className="property-field">
          <label className="property-label">Status</label>
          <div className="property-readonly">
            <span className={`status-badge status-${relationship.status}`}>
              {relationship.status}
            </span>
            <span className="property-help">Derived from realized models</span>
          </div>
        </div>

        {/* Save button */}
        <button className="property-save-btn" onClick={handleSave}>
          Save Changes
        </button>
      </div>
    );
  }

  return null;
}
