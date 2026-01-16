"""State models for dbt-conceptual."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConceptState:
    """Represents the state of a concept."""

    name: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    definition: Optional[str] = None  # Markdown definition
    status: str = "stub"  # complete, draft, stub, deprecated
    color: Optional[str] = None  # Optional color override (defaults to domain color)
    bronze_models: list[str] = field(default_factory=list)  # Source dependencies
    silver_models: list[str] = field(default_factory=list)
    gold_models: list[str] = field(default_factory=list)
    replaced_by: Optional[str] = None
    discovered_from: Optional[str] = None


@dataclass
class RelationshipState:
    """Represents the state of a relationship between concepts."""

    name: str
    from_concept: str
    to_concept: str
    cardinality: Optional[str] = None
    definition: Optional[str] = None  # Markdown definition
    status: str = "complete"
    realized_by: list[str] = field(default_factory=list)


@dataclass
class DomainState:
    """Represents a domain grouping."""

    name: str
    display_name: str
    color: Optional[str] = None


@dataclass
class OrphanModel:
    """Represents a dbt model not yet linked to a concept."""

    name: str
    description: Optional[str] = None
    domain: Optional[str] = None  # From meta.domain
    layer: Optional[str] = None  # silver or gold
    path: Optional[str] = None


@dataclass
class ProjectState:
    """Represents the complete state of the conceptual model and its dbt implementation."""

    concepts: dict[str, ConceptState] = field(default_factory=dict)
    relationships: dict[str, RelationshipState] = field(default_factory=dict)
    groups: dict[str, list[str]] = field(default_factory=dict)
    domains: dict[str, DomainState] = field(default_factory=dict)
    orphan_models: list[OrphanModel] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
