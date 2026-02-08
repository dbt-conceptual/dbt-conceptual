import { useState, useEffect, useImperativeHandle, forwardRef, useCallback } from 'react';
import { useStore } from '../store';
import { MarkdownField } from './MarkdownField';
import type { Relationship } from '../types';
import type { PropertiesTabHandle } from './PropertiesTab';

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

interface RelationshipPropertiesProps {
  relationshipId: string;
  onDirtyChange?: (isDirty: boolean) => void;
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

export const RelationshipProperties = forwardRef<PropertiesTabHandle, RelationshipPropertiesProps>(
  function RelationshipProperties({ relationshipId, onDirtyChange }, ref) {
  const { concepts, relationships, domains, updateRelationship, saveState, fetchState } = useStore();
  const relationship = relationships[relationshipId];

  // Store original relationship state to detect changes
  const [originalRelationship, setOriginalRelationship] = useState<Relationship | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDomainPickerOpen, setIsDomainPickerOpen] = useState(false);

  // Reset original when relationship ID changes or after save
  useEffect(() => {
    if (relationship) {
      setOriginalRelationship({ ...relationship, domains: [...relationship.domains] });
    }
  }, [relationshipId]); // Only reset on ID change

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

  // Check if there are unsaved changes (computed before early return so hooks can use it)
  const hasChanges = relationshipHasChanges(originalRelationship, relationship);

  // Notify parent of dirty state changes
  // All hooks must be called before any conditional returns (Rules of Hooks)
  useEffect(() => {
    onDirtyChange?.(hasChanges);
  }, [hasChanges, onDirtyChange]);

  const handleSave = useCallback(async () => {
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
  }, [hasChanges, isSaving, saveState, relationships, relationshipId]);

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    isDirty: () => hasChanges,
    save: handleSave,
    discard: fetchState,
  }), [hasChanges, handleSave, fetchState]);

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

      {/* Domains (multi-select with tags) */}
      <div className="property-field">
        <label className="property-label">Domains</label>
        <div className="domain-field-container" style={{ position: 'relative' }}>
          <div className="domain-tags-container">
            {relationship.domains.map((domainId) => {
              const domainData = domains[domainId];
              if (!domainData) return null;
              const tagColor = domainData.color || '#4a9eff';
              const textColor = getContrastTextColor(tagColor);
              return (
                <div
                  key={domainId}
                  className="domain-tag"
                  style={{ backgroundColor: tagColor, color: textColor }}
                >
                  <span>{domainData.display_name}</span>
                  <button
                    className="domain-tag-remove"
                    onClick={() => {
                      const newDomains = relationship.domains.filter((d) => d !== domainId);
                      handleChange('domains', newDomains);
                    }}
                    title="Remove domain"
                    aria-label={`Remove ${domainData.display_name} domain`}
                    style={{ color: textColor }}
                  >
                    {'\u00D7'}
                  </button>
                </div>
              );
            })}
            {/* Add domain button */}
            {Object.keys(domains).some((d) => !relationship.domains.includes(d)) && (
              <button
                className="add-domain-btn"
                onClick={() => setIsDomainPickerOpen(true)}
                title="Add domain"
              >
                +
              </button>
            )}
            {relationship.domains.length === 0 && (
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
              {Object.entries(domains)
                .filter(([domainId]) => !relationship.domains.includes(domainId))
                .map(([domainId, domainData]) => (
                  <button
                    key={domainId}
                    className="domain-picker-option"
                    onClick={() => {
                      const newDomains = [...relationship.domains, domainId];
                      handleChange('domains', newDomains);
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
