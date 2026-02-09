"""Diff functionality for conceptual models."""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

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


# TypeVar for the state types (ConceptState, RelationshipState, DomainState)
_S = TypeVar("_S")
# TypeVar for the change types (ConceptChange, RelationshipChange, DomainChange)
_C = TypeVar("_C")


def _compare_entities(
    old: _S | None,
    new: _S | None,
    key: str,
    compare_fields: Sequence[str],
    change_cls: type[_C],
) -> _C | None:
    """Compare two entity states and return a change if any differences exist.

    This is a generic compare function that works for concepts, relationships,
    and domains by accepting the list of fields to compare and the change
    dataclass to construct.

    Args:
        old: Old entity state (None if entity was added).
        new: New entity state (None if entity was removed).
        key: Entity key identifier.
        compare_fields: Attribute names to compare for modification detection.
        change_cls: The Change dataclass to instantiate (e.g. ConceptChange).

    Returns:
        A change instance if there are differences, None otherwise.
    """
    if old is None and new is not None:
        return change_cls(key=key, change_type="added", new_value=new)  # type: ignore[call-arg]
    if old is not None and new is None:
        return change_cls(key=key, change_type="removed", old_value=old)  # type: ignore[call-arg]

    if old is None or new is None:
        return None

    modified_fields: dict[str, tuple[Any, Any]] = {}
    for attr in compare_fields:
        old_val = getattr(old, attr)
        new_val = getattr(new, attr)
        if old_val != new_val:
            modified_fields[attr] = (old_val, new_val)

    if modified_fields:
        return change_cls(  # type: ignore[call-arg]
            key=key,
            change_type="modified",
            old_value=old,
            new_value=new,
            modified_fields=modified_fields,
        )

    return None


def _get_comparable_fields(state_class: type) -> Sequence[str]:
    """Extract field names from a dataclass, excluding runtime/derived fields.

    Args:
        state_class: The dataclass type to inspect.

    Returns:
        Tuple of field names suitable for comparison.
    """
    # Get all dataclass fields
    all_fields = [f.name for f in dataclasses.fields(state_class)]

    # Define runtime/derived fields to exclude
    runtime_fields = {
        # ConceptState runtime fields
        "models",
        "is_ghost",
        "validation_status",
        "validation_messages",
        # RelationshipState runtime fields (validation only, not 'name' which is property)
        # DomainState has no runtime fields to exclude
    }

    # Filter out runtime fields
    return tuple(f for f in all_fields if f not in runtime_fields)


# Field lists for each entity type -- derived from dataclass fields
_CONCEPT_COMPARE_FIELDS: Sequence[str] = _get_comparable_fields(ConceptState)
_RELATIONSHIP_COMPARE_FIELDS: Sequence[str] = _get_comparable_fields(RelationshipState)
_DOMAIN_COMPARE_FIELDS: Sequence[str] = _get_comparable_fields(DomainState)


def compute_diff(base: ProjectState, current: ProjectState) -> ConceptualDiff:
    """Compute the diff between two project states.

    Args:
        base: Base project state (e.g., from main branch).
        current: Current project state (e.g., from feature branch).

    Returns:
        ConceptualDiff containing all changes.
    """
    diff = ConceptualDiff()

    # Compare concepts
    all_concept_keys = set(base.concepts.keys()) | set(current.concepts.keys())
    for key in sorted(all_concept_keys):
        concept_change = _compare_entities(
            base.concepts.get(key),
            current.concepts.get(key),
            key,
            _CONCEPT_COMPARE_FIELDS,
            ConceptChange,
        )
        if concept_change:
            diff.concept_changes.append(concept_change)

    # Compare relationships
    all_rel_keys = set(base.relationships.keys()) | set(current.relationships.keys())
    for key in sorted(all_rel_keys):
        rel_change = _compare_entities(
            base.relationships.get(key),
            current.relationships.get(key),
            key,
            _RELATIONSHIP_COMPARE_FIELDS,
            RelationshipChange,
        )
        if rel_change:
            diff.relationship_changes.append(rel_change)

    # Compare domains
    all_domain_keys = set(base.domains.keys()) | set(current.domains.keys())
    for key in sorted(all_domain_keys):
        domain_change = _compare_entities(
            base.domains.get(key),
            current.domains.get(key),
            key,
            _DOMAIN_COMPARE_FIELDS,
            DomainChange,
        )
        if domain_change:
            diff.domain_changes.append(domain_change)

    return diff
