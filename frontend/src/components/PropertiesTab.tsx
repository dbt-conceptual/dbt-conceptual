import { forwardRef } from 'react';
import { ConceptProperties } from './ConceptProperties';
import { RelationshipProperties } from './RelationshipProperties';

// Handle for parent to check dirty state and trigger save
export interface PropertiesTabHandle {
  isDirty: () => boolean;
  save: () => Promise<void>;
  discard: () => void;
}

interface PropertiesTabProps {
  conceptId?: string;
  relationshipId?: string;
  onDirtyChange?: (isDirty: boolean) => void;
}

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
