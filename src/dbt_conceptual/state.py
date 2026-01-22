"""State models for dbt-conceptual."""

from dataclasses import dataclass, field
from typing import Literal, Optional

# Validation types
ValidationStatus = Literal["valid", "warning", "error"]
MessageSeverity = Literal["error", "warning", "info"]


@dataclass
class Message:
    """Represents a validation message."""

    id: str
    severity: MessageSeverity
    text: str
    element_type: Optional[Literal["concept", "relationship", "domain"]] = None
    element_id: Optional[str] = None


@dataclass
class ValidationState:
    """Represents the validation state after sync."""

    messages: list[Message] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0


@dataclass
class ConceptState:
    """Represents the state of a concept.

    Status is derived at runtime based on domain and model associations:
    - 'stub': No domain (created from sync, needs enrichment)
    - 'draft': Has domain but no models
    - 'complete': Has domain AND has models
    """

    name: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    definition: Optional[str] = None  # Markdown definition

    # Optional extensions (not in spec but useful)
    color: Optional[str] = None  # Override domain color
    replaced_by: Optional[str] = None  # Deprecation tracking

    # Derived fields (populated at runtime, not stored in YAML)
    bronze_models: list[str] = field(
        default_factory=list
    )  # Inferred from manifest.json
    silver_models: list[str] = field(
        default_factory=list
    )  # From meta.concept in silver paths
    gold_models: list[str] = field(
        default_factory=list
    )  # From meta.concept in gold paths

    # Validation fields (populated during sync)
    is_ghost: bool = False  # True if referenced but not defined in YAML
    validation_status: ValidationStatus = "valid"
    validation_messages: list[str] = field(default_factory=list)

    @property
    def status(self) -> Literal["stub", "draft", "complete", "deprecated"]:
        """Derive status from domain and model associations.

        Returns:
            - 'deprecated' if replaced_by is set
            - 'stub' if no domain
            - 'draft' if has domain but no models
            - 'complete' if has domain and at least one model
        """
        if self.replaced_by:
            return "deprecated"
        if not self.domain:
            return "stub"
        if not (self.silver_models or self.gold_models):
            return "draft"
        return "complete"


@dataclass
class RelationshipState:
    """Represents the state of a relationship between concepts.

    Status is derived at runtime based on domains and realizations:
    - 'stub': Missing verb (created from sync, needs enrichment)
    - 'draft': Missing domain OR (N:M without realization)
    - 'complete': Has domain(s) AND (not N:M OR has realization)
    """

    verb: str  # NEW: explicit verb field (e.g., "places", "contains")
    from_concept: str
    to_concept: str
    cardinality: Optional[str] = None  # 1:1, 1:N, N:M (informational)
    definition: Optional[str] = None  # Markdown definition
    domains: list[str] = field(default_factory=list)  # NEW: array of domains
    owner: Optional[str] = None
    custom_name: Optional[str] = None  # NEW: optional override for display name

    # Derived fields (populated at runtime, not stored in YAML)
    realized_by: list[str] = field(default_factory=list)  # From meta.realizes tags

    # Validation fields (populated during sync)
    validation_status: ValidationStatus = "valid"
    validation_messages: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Get the display name for this relationship.

        Returns:
            custom_name if set, otherwise derived format: {from}:{verb}:{to}
        """
        if self.custom_name:
            return self.custom_name
        return f"{self.from_concept}:{self.verb}:{self.to_concept}"

    @property
    def status(self) -> Literal["stub", "draft", "complete"]:
        """Derive status from domains and realizations.

        Returns:
            - 'stub' if missing verb (shouldn't happen, verb is required)
            - 'draft' if no domains OR (N:M cardinality without realization)
            - 'complete' otherwise
        """
        if not self.verb:
            return "stub"
        if not self.domains:
            return "draft"
        if self.cardinality == "N:M" and not self.realized_by:
            return "draft"
        return "complete"


@dataclass
class DomainState:
    """Represents a domain grouping."""

    name: str
    display_name: str
    color: Optional[str] = None
    owner: Optional[str] = None


@dataclass
class ModelInfo:
    """Represents metadata about a dbt model for tag validation."""

    name: str
    concept: Optional[str] = None  # From meta.concept
    realizes: list[str] = field(default_factory=list)  # From meta.realizes
    domain_tags: list[str] = field(
        default_factory=list
    )  # domain:X tags or databricks domain
    owner_tag: Optional[str] = None  # owner:X tag or databricks owner
    layer: Optional[str] = None  # silver or gold
    path: Optional[str] = None


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
    groups: dict[str, list[str]] = field(
        default_factory=dict
    )  # Extension: relationship groups
    domains: dict[str, DomainState] = field(default_factory=dict)
    orphan_models: list[OrphanModel] = field(default_factory=list)
    models: dict[str, ModelInfo] = field(
        default_factory=dict
    )  # Model tag info for validation
    metadata: dict[str, str] = field(default_factory=dict)
