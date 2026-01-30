"""Diff functionality for conceptual models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .state import ConceptState, DomainState, ProjectState, RelationshipState


@dataclass
class ConceptChange:
    """Represents a change to a concept."""

    key: str
    change_type: str  # "added", "removed", "modified"
    old_value: ConceptState | None = None
    new_value: ConceptState | None = None
    modified_fields: dict[str, tuple[Any, Any]] = field(
        default_factory=dict
    )  # field -> (old, new)


@dataclass
class RelationshipChange:
    """Represents a change to a relationship."""

    key: str
    change_type: str  # "added", "removed", "modified"
    old_value: RelationshipState | None = None
    new_value: RelationshipState | None = None
    modified_fields: dict[str, tuple[Any, Any]] = field(
        default_factory=dict
    )  # field -> (old, new)


@dataclass
class DomainChange:
    """Represents a change to a domain."""

    key: str
    change_type: str  # "added", "removed", "modified"
    old_value: DomainState | None = None
    new_value: DomainState | None = None
    modified_fields: dict[str, tuple[Any, Any]] = field(
        default_factory=dict
    )  # field -> (old, new)


@dataclass
class ConceptualDiff:
    """Represents all changes between two conceptual models."""

    concept_changes: list[ConceptChange] = field(default_factory=list)
    relationship_changes: list[RelationshipChange] = field(default_factory=list)
    domain_changes: list[DomainChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(
            self.concept_changes or self.relationship_changes or self.domain_changes
        )


def _compare_concepts(
    old: ConceptState | None, new: ConceptState | None, key: str
) -> ConceptChange | None:
    """Compare two concept states and return changes if any.

    Args:
        old: Old concept state (None if concept was added)
        new: New concept state (None if concept was removed)
        key: Concept key

    Returns:
        ConceptChange if there are differences, None otherwise
    """
    if old is None and new is not None:
        return ConceptChange(key=key, change_type="added", new_value=new)
    if old is not None and new is None:
        return ConceptChange(key=key, change_type="removed", old_value=old)

    if old is None or new is None:
        return None

    # Compare fields that matter for conceptual model (exclude derived runtime fields)
    # v1.0: removed replaced_by
    modified_fields = {}
    for attr in ["name", "domain", "owner", "definition", "color"]:
        old_val = getattr(old, attr)
        new_val = getattr(new, attr)
        if old_val != new_val:
            modified_fields[attr] = (old_val, new_val)

    if modified_fields:
        return ConceptChange(
            key=key,
            change_type="modified",
            old_value=old,
            new_value=new,
            modified_fields=modified_fields,
        )

    return None


def _compare_relationships(
    old: RelationshipState | None, new: RelationshipState | None, key: str
) -> RelationshipChange | None:
    """Compare two relationship states and return changes if any.

    Args:
        old: Old relationship state (None if relationship was added)
        new: New relationship state (None if relationship was removed)
        key: Relationship key

    Returns:
        RelationshipChange if there are differences, None otherwise
    """
    if old is None and new is not None:
        return RelationshipChange(key=key, change_type="added", new_value=new)
    if old is not None and new is None:
        return RelationshipChange(key=key, change_type="removed", old_value=old)

    if old is None or new is None:
        return None

    # Compare fields (exclude derived runtime fields)
    # v1.0: removed custom_name and domains
    modified_fields = {}
    for attr in [
        "verb",
        "from_concept",
        "to_concept",
        "cardinality",
        "definition",
        "owner",
    ]:
        old_val = getattr(old, attr)
        new_val = getattr(new, attr)
        if old_val != new_val:
            modified_fields[attr] = (old_val, new_val)

    if modified_fields:
        return RelationshipChange(
            key=key,
            change_type="modified",
            old_value=old,
            new_value=new,
            modified_fields=modified_fields,
        )

    return None


def _compare_domains(
    old: DomainState | None, new: DomainState | None, key: str
) -> DomainChange | None:
    """Compare two domain states and return changes if any.

    Args:
        old: Old domain state (None if domain was added)
        new: New domain state (None if domain was removed)
        key: Domain key

    Returns:
        DomainChange if there are differences, None otherwise
    """
    if old is None and new is not None:
        return DomainChange(key=key, change_type="added", new_value=new)
    if old is not None and new is None:
        return DomainChange(key=key, change_type="removed", old_value=old)

    if old is None or new is None:
        return None

    # Compare fields
    modified_fields = {}
    for attr in ["name", "display_name", "color"]:
        old_val = getattr(old, attr)
        new_val = getattr(new, attr)
        if old_val != new_val:
            modified_fields[attr] = (old_val, new_val)

    if modified_fields:
        return DomainChange(
            key=key,
            change_type="modified",
            old_value=old,
            new_value=new,
            modified_fields=modified_fields,
        )

    return None


def compute_diff(base: ProjectState, current: ProjectState) -> ConceptualDiff:
    """Compute the diff between two project states.

    Args:
        base: Base project state (e.g., from main branch)
        current: Current project state (e.g., from feature branch)

    Returns:
        ConceptualDiff containing all changes
    """
    diff = ConceptualDiff()

    # Compare concepts
    all_concept_keys = set(base.concepts.keys()) | set(current.concepts.keys())
    for key in sorted(all_concept_keys):
        old_concept = base.concepts.get(key)
        new_concept = current.concepts.get(key)
        concept_change = _compare_concepts(old_concept, new_concept, key)
        if concept_change:
            diff.concept_changes.append(concept_change)

    # Compare relationships
    all_rel_keys = set(base.relationships.keys()) | set(current.relationships.keys())
    for key in sorted(all_rel_keys):
        old_rel = base.relationships.get(key)
        new_rel = current.relationships.get(key)
        rel_change = _compare_relationships(old_rel, new_rel, key)
        if rel_change:
            diff.relationship_changes.append(rel_change)

    # Compare domains
    all_domain_keys = set(base.domains.keys()) | set(current.domains.keys())
    for key in sorted(all_domain_keys):
        old_domain = base.domains.get(key)
        new_domain = current.domains.get(key)
        domain_change = _compare_domains(old_domain, new_domain, key)
        if domain_change:
            diff.domain_changes.append(domain_change)

    return diff
