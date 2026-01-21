import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { useStore } from '../store';
import { MarkdownField } from './MarkdownField';
import type { Concept, Relationship } from '../types';

// Handle for parent to check dirty state and trigger save
export interface PropertiesTabHandle {
  isDirty: () => boolean;
  save: () => Promise<void>;
  discard: () => void;
}

// Helper to determine if text should be light or dark based on background color
function getContrastTextColor(hexColor: string): string {
  // Default to white if no valid color
  if (!hexColor || !hexColor.startsWith('#')) return '#ffffff';

  // Parse hex color
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate relative luminance (simplified)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  // Return dark text for light backgrounds, white for dark
  return luminance > 0.6 ? '#1a1a2e' : '#ffffff';
}

interface PropertiesTabProps {
  conceptId?: string;
  relationshipId?: string;
  onDirtyChange?: (isDirty: boolean) => void;
}

interface ConceptPropertiesProps {
  conceptId: string;
  onDirtyChange?: (isDirty: boolean) => void;
}

interface RelationshipPropertiesProps {
  relationshipId: string;
  onDirtyChange?: (isDirty: boolean) => void;
}

// Helper to deep compare relevant concept fields
function conceptHasChanges(original: Concept | null, current: Concept | null): boolean {
  if (!original || !current) return false;
  return (
    original.name !== current.name ||
    original.domain !== current.domain ||
    original.owner !== current.owner ||
    original.definition !== current.definition ||
    original.color !== current.color
  );
}

// Helper to deep compare relevant relationship fields
function relationshipHasChanges(original: Relationship | null, current: Relationship | null): boolean {
  if (!original || !current) return false;
  return (
    original.verb !== current.verb ||
    original.custom_name !== current.custom_name ||
    original.cardinality !== current.cardinality ||
    original.owner !== current.owner ||
    original.definition !== current.definition ||
    JSON.stringify(original.domains.slice().sort()) !== JSON.stringify(current.domains.slice().sort())
  );
}

const ConceptProperties = forwardRef<PropertiesTabHandle, ConceptPropertiesProps>(
  function ConceptProperties({ conceptId, onDirtyChange }, ref) {
  const { concepts, relationships, domains, updateConcept, saveState, fetchState } = useStore();
  const concept = concepts[conceptId];

  // Store original concept state to detect changes
  const [originalConcept, setOriginalConcept] = useState<Concept | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDomainPickerOpen, setIsDomainPickerOpen] = useState(false);

  // Reset original when concept ID changes or after save
  useEffect(() => {
    if (concept) {
      setOriginalConcept({ ...concept });
    }
  }, [conceptId]); // Only reset on ID change, not on every concept update

  // Close domain picker when clicking outside
  useEffect(() => {
    if (!isDomainPickerOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.domain-field-container')) {
        setIsDomainPickerOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDomainPickerOpen]);

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

  // Check if there are unsaved changes
  const hasChanges = conceptHasChanges(originalConcept, concept);
  // Ghost concepts always show save button as enabled (to create the concept)
  const canSave = isGhost || hasChanges;

  // Notify parent of dirty state changes
  useEffect(() => {
    onDirtyChange?.(hasChanges);
  }, [hasChanges, onDirtyChange]);

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    isDirty: () => hasChanges,
    save: async () => {
      await handleSave();
    },
    discard: () => {
      // Reload state from server to discard changes
      fetchState();
    },
  }), [hasChanges]);

  const handleChange = (field: string, value: string) => {
    updateConcept(conceptId, { [field]: value });
  };

  const handleSave = async () => {
    if (!canSave || isSaving) return;

    setIsSaving(true);
    try {
      // When saving a ghost concept with a domain, it becomes a real concept
      if (isGhost && concept.domain) {
        updateConcept(conceptId, { isGhost: false, validationStatus: 'valid', validationMessages: [] });
      }
      await saveState();
      // Update original to current state after successful save
      setOriginalConcept({ ...concepts[conceptId] });
    } catch (error) {
      console.error('Failed to save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Get domain info for color picker
  const domain = concept.domain ? domains[concept.domain] : null;
  const domainColor = domain?.color || '#4a9eff';
  const hasCustomColor = !!concept.color;

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

      {/* Domain */}
      <div className="property-field">
        <label className="property-label">Domain</label>
        <div className="domain-field-container" style={{ position: 'relative' }}>
          <div className="domain-tags-container">
            {concept.domain && domains[concept.domain] ? (() => {
              const tagColor = domains[concept.domain].color || '#4a9eff';
              const textColor = getContrastTextColor(tagColor);
              return (
                <div
                  className="domain-tag"
                  style={{ backgroundColor: tagColor, color: textColor }}
                >
                  <span>{domains[concept.domain].display_name}</span>
                  <button
                    className="domain-tag-remove"
                    onClick={() => handleChange('domain', '')}
                    title="Remove domain"
                    style={{ color: textColor }}
                  >
                    {'\u00D7'}
                  </button>
                </div>
              );
            })() : (
              <button
                className="add-domain-btn-empty"
                onClick={() => setIsDomainPickerOpen(true)}
              >
                <span>+</span>
                <span>Add domain</span>
              </button>
            )}
          </div>

          {isDomainPickerOpen && (
            <div className="domain-picker">
              {Object.entries(domains).map(([domainId, domainData]) => (
                <button
                  key={domainId}
                  className="domain-picker-option"
                  onClick={() => {
                    handleChange('domain', domainId);
                    setIsDomainPickerOpen(false);
                  }}
                >
                  <span
                    className="domain-picker-color"
                    style={{ backgroundColor: domainData.color || '#4a9eff' }}
                  />
                  <span>{domainData.display_name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

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

      {/* Owner (inheritable from domain) */}
      {!isGhost && (() => {
        const domainOwner = domain?.owner;
        const hasCustomOwner = !!concept.owner;
        const displayOwner = concept.owner || domainOwner || '';
        const canInherit = !!domainOwner;

        return (
          <div className="property-field">
            <label className="property-label">Owner</label>
            <div className="inheritable-field">
              {hasCustomOwner ? (
                <div className="inheritable-field-row">
                  <input
                    type="text"
                    className="property-input"
                    value={concept.owner || ''}
                    onChange={(e) => handleChange('owner', e.target.value)}
                    placeholder="e.g., data_team"
                    style={{ flex: 1 }}
                  />
                  {canInherit && (
                    <button
                      className="inheritable-field-action"
                      onClick={() => handleChange('owner', '')}
                    >
                      Reset
                    </button>
                  )}
                </div>
              ) : canInherit ? (
                <div className="inheritable-field-row">
                  <div className="inheritable-field-inherited">
                    {displayOwner}
                  </div>
                  <span className="inheritable-field-source">from domain</span>
                  <button
                    className="inheritable-field-action"
                    onClick={() => handleChange('owner', displayOwner)}
                  >
                    Customize
                  </button>
                </div>
              ) : (
                <input
                  type="text"
                  className="property-input"
                  value={concept.owner || ''}
                  onChange={(e) => handleChange('owner', e.target.value)}
                  placeholder="e.g., data_team"
                />
              )}
            </div>
          </div>
        );
      })()}

      {/* Owner (for ghost concepts - simple input) */}
      {isGhost && (
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
      )}

      {/* Definition */}
      <MarkdownField
        label="Definition"
        value={concept.definition || ''}
        onChange={(value) => handleChange('definition', value)}
        placeholder="Describe this concept..."
      />

      {/* Color (inheritable from domain, only for non-ghost) */}
      {!isGhost && (
        <div className="property-field">
          <label className="property-label">Color</label>
          <div className="inheritable-field">
            {hasCustomColor ? (
              <div className="inheritable-field-row">
                <input
                  type="color"
                  className="property-color"
                  value={concept.color || domainColor}
                  onChange={(e) => handleChange('color', e.target.value)}
                />
                <button
                  className="inheritable-field-action"
                  onClick={() => handleChange('color', '')}
                >
                  Reset
                </button>
              </div>
            ) : (
              <div className="inheritable-field-row">
                <div
                  className="property-color-preview"
                  style={{ backgroundColor: domainColor }}
                />
                <span className="inheritable-field-source">
                  {domain ? `from ${domain.display_name}` : 'default'}
                </span>
                <button
                  className="inheritable-field-action"
                  onClick={() => handleChange('color', domainColor)}
                >
                  Customize
                </button>
              </div>
            )}
          </div>
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
      <button
        className="property-save-btn"
        onClick={handleSave}
        disabled={!canSave || isSaving}
      >
        {isSaving ? 'Saving...' : isGhost ? 'Save as Concept' : 'Save Changes'}
      </button>
    </div>
  );
});

const RelationshipProperties = forwardRef<PropertiesTabHandle, RelationshipPropertiesProps>(
  function RelationshipProperties({ relationshipId, onDirtyChange }, ref) {
  const { concepts, relationships, domains, updateRelationship, saveState, fetchState } = useStore();
  const relationship = relationships[relationshipId];

  // Store original relationship state to detect changes
  const [originalRelationship, setOriginalRelationship] = useState<Relationship | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Reset original when relationship ID changes or after save
  useEffect(() => {
    if (relationship) {
      setOriginalRelationship({ ...relationship, domains: [...relationship.domains] });
    }
  }, [relationshipId]); // Only reset on ID change

  if (!relationship) return null;

  const isInvalid = relationship.validationStatus === 'error';
  const hasValidationIssues =
    relationship.validationStatus === 'error' || relationship.validationStatus === 'warning';

  // Check if source or target is a ghost
  const fromConcept = concepts[relationship.from_concept];
  const toConcept = concepts[relationship.to_concept];
  const fromIsGhost = fromConcept?.isGhost;
  const toIsGhost = toConcept?.isGhost;

  // Check if there are unsaved changes
  const hasChanges = relationshipHasChanges(originalRelationship, relationship);

  // Notify parent of dirty state changes
  useEffect(() => {
    onDirtyChange?.(hasChanges);
  }, [hasChanges, onDirtyChange]);

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    isDirty: () => hasChanges,
    save: async () => {
      await handleSave();
    },
    discard: () => {
      // Reload state from server to discard changes
      fetchState();
    },
  }), [hasChanges]);

  const handleChange = (field: string, value: string | string[]) => {
    updateRelationship(relationshipId, { [field]: value });
  };

  const handleSave = async () => {
    if (!hasChanges || isSaving) return;

    setIsSaving(true);
    try {
      await saveState();
      // Update original to current state after successful save
      setOriginalRelationship({ ...relationships[relationshipId], domains: [...relationships[relationshipId].domains] });
    } catch (error) {
      console.error('Failed to save:', error);
    } finally {
      setIsSaving(false);
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
      <MarkdownField
        label="Definition"
        value={relationship.definition || ''}
        onChange={(value) => handleChange('definition', value)}
        placeholder="Describe this relationship..."
      />

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
      <button
        className="property-save-btn"
        onClick={handleSave}
        disabled={!hasChanges || isSaving}
      >
        {isSaving ? 'Saving...' : 'Save Changes'}
      </button>
    </div>
  );
});

export const PropertiesTab = forwardRef<PropertiesTabHandle, PropertiesTabProps>(
  function PropertiesTab({ conceptId, relationshipId, onDirtyChange }, ref) {
  if (conceptId) {
    return <ConceptProperties ref={ref} conceptId={conceptId} onDirtyChange={onDirtyChange} />;
  }

  if (relationshipId) {
    return <RelationshipProperties ref={ref} relationshipId={relationshipId} onDirtyChange={onDirtyChange} />;
  }

  return null;
});
