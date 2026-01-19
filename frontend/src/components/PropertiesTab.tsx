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

    const handleChange = (field: string, value: string) => {
      updateConcept(conceptId, { [field]: value });
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
        {/* Name */}
        <div className="property-field">
          <label className="property-label">Name</label>
          <input
            type="text"
            className="property-input"
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
            <option value="">None</option>
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
            placeholder="@username"
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

        {/* Color */}
        <div className="property-field">
          <label className="property-label">Custom Color</label>
          <input
            type="color"
            className="property-color"
            value={concept.color || '#4a9eff'}
            onChange={(e) => handleChange('color', e.target.value)}
          />
        </div>

        {/* Replaced By (for deprecation) */}
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

        {/* Status (read-only, derived) */}
        <div className="property-field">
          <label className="property-label">Status</label>
          <div className="property-readonly">
            <span className={`status-badge status-${concept.status}`}>
              {concept.status}
            </span>
            <span className="property-help">Derived from domain and models</span>
          </div>
        </div>

        {/* Save button */}
        <button className="property-save-btn" onClick={handleSave}>
          Save Changes
        </button>
      </div>
    );
  }

  if (relationshipId) {
    const relationship = relationships[relationshipId];
    if (!relationship) return null;

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

        {/* From/To (read-only) */}
        <div className="property-field">
          <label className="property-label">From → To</label>
          <div className="property-readonly">
            {relationship.from_concept} → {relationship.to_concept}
          </div>
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
