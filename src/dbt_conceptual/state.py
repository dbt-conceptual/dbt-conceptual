"""State models for dbt-conceptual.

Simplified v1.0 state model:
- Single flat `models` list (no bronze/silver/gold separation)
- No `realized_by` on relationships
- No `deprecated` status
- No lineage inference
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

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
    - 'stub': No domain (needs enrichment)
    - 'draft': Has domain but no models
    - 'complete': Has domain AND has models
    """

    name: str
    domain: Optional[str] = None
    owner: Optional[str] = None
    definition: Optional[str] = None  # Markdown definition
    color: Optional[str] = None  # Override domain color

    # Models tagged with this concept (flat list, no layer separation)
    models: list[str] = field(default_factory=list)

    # Validation fields (populated during sync)
    is_ghost: bool = False  # True if referenced but not defined in YAML
    validation_status: ValidationStatus = "valid"
    validation_messages: list[str] = field(default_factory=list)

    @property
    def status(self) -> Literal["stub", "draft", "complete"]:
        """Derive status from domain and model associations.

        Returns:
            - 'stub' if no domain
            - 'draft' if has domain but no models
            - 'complete' if has domain and at least one model
        """
        if not self.domain:
            return "stub"
        if not self.models:
            return "draft"
        return "complete"


@dataclass
class RelationshipState:
    """Represents the state of a relationship between concepts.

    Status is derived at runtime:
    - 'stub': Either endpoint is a ghost or stub concept
    - 'complete': Both endpoints are draft or complete concepts
    """

    verb: str
    from_concept: str
    to_concept: str
    cardinality: str = "1:N"  # Only '1:1' or '1:N' supported
    definition: Optional[str] = None  # Markdown definition
    owner: Optional[str] = None

    # Validation fields (populated during sync)
    validation_status: ValidationStatus = "valid"
    validation_messages: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Get the display name for this relationship.

        Returns:
            Derived format: {from}:{verb}:{to}
        """
        return f"{self.from_concept}:{self.verb}:{self.to_concept}"

    def get_status(
        self, concepts: dict[str, "ConceptState"]
    ) -> Literal["stub", "complete"]:
        """Derive status based on endpoint concept states.

        Args:
            concepts: Dict of concept states for status lookup

        Returns:
            - 'stub' if either endpoint is ghost or stub
            - 'complete' otherwise
        """
        from_concept = concepts.get(self.from_concept)
        to_concept = concepts.get(self.to_concept)

        # Check if endpoints exist and are not stubs/ghosts
        if not from_concept or from_concept.is_ghost or from_concept.status == "stub":
            return "stub"
        if not to_concept or to_concept.is_ghost or to_concept.status == "stub":
            return "stub"

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
    """Represents metadata about a dbt model."""

    name: str
    concept: Optional[str] = None  # From meta.concept
    domain_tags: list[str] = field(default_factory=list)  # From tags
    owner_tag: Optional[str] = None  # From tags
    path: Optional[str] = None


@dataclass
class OrphanModel:
    """Represents a dbt model not yet linked to a concept."""

    name: str
    description: Optional[str] = None
    domain: Optional[str] = None  # From meta.domain
    path: Optional[str] = None


@dataclass
class CoverageStats:
    """Coverage statistics calculated from project state."""

    # Concept counts
    total_concepts: int = 0
    complete_concepts: int = 0
    draft_concepts: int = 0
    stub_concepts: int = 0

    # Model coverage
    concepts_with_models: int = 0

    # Relationship counts
    total_relationships: int = 0
    complete_relationships: int = 0

    # Orphans
    orphan_count: int = 0

    @property
    def completion_percent(self) -> int:
        """Percentage of concepts that are complete."""
        if self.total_concepts == 0:
            return 0
        return int((self.complete_concepts / self.total_concepts) * 100)

    @property
    def model_coverage_percent(self) -> int:
        """Percentage of concepts with at least one model."""
        if self.total_concepts == 0:
            return 0
        return int((self.concepts_with_models / self.total_concepts) * 100)

    @property
    def relationship_percent(self) -> int:
        """Percentage of relationships that are complete."""
        if self.total_relationships == 0:
            return 0
        return int((self.complete_relationships / self.total_relationships) * 100)

    def to_dict(self) -> dict[str, Any]:
        """Convert to nested dict for JSON serialization."""
        return {
            "concepts": {
                "total": self.total_concepts,
                "complete": self.complete_concepts,
                "draft": self.draft_concepts,
                "stub": self.stub_concepts,
                "completion_percent": self.completion_percent,
            },
            "coverage": {
                "models": {
                    "count": self.concepts_with_models,
                    "percent": self.model_coverage_percent,
                },
            },
            "relationships": {
                "total": self.total_relationships,
                "complete": self.complete_relationships,
                "percent": self.relationship_percent,
            },
            "orphans": self.orphan_count,
        }


@dataclass
class ProjectState:
    """Represents the complete state of the conceptual model and its dbt implementation."""

    concepts: dict[str, ConceptState] = field(default_factory=dict)
    relationships: dict[str, RelationshipState] = field(default_factory=dict)
    domains: dict[str, DomainState] = field(default_factory=dict)
    orphan_models: list[OrphanModel] = field(default_factory=list)
    models: dict[str, ModelInfo] = field(
        default_factory=dict
    )  # Model info for validation
    metadata: dict[str, str] = field(default_factory=dict)

    def concepts_by_domain(self) -> dict[str, list[tuple[str, ConceptState]]]:
        """Group concepts by their domain.

        Returns:
            Dict mapping domain name to list of (concept_id, concept) tuples.
            Concepts without a domain are grouped under 'uncategorized'.
        """
        groups: dict[str, list[tuple[str, ConceptState]]] = {}
        for concept_id, concept in self.concepts.items():
            domain = concept.domain or "uncategorized"
            if domain not in groups:
                groups[domain] = []
            groups[domain].append((concept_id, concept))
        return groups

    def calculate_coverage_stats(self) -> CoverageStats:
        """Calculate coverage statistics for this project state.

        Returns:
            CoverageStats with all metrics populated.
        """
        return CoverageStats(
            total_concepts=len(self.concepts),
            complete_concepts=sum(
                1 for c in self.concepts.values() if c.status == "complete"
            ),
            draft_concepts=sum(
                1 for c in self.concepts.values() if c.status == "draft"
            ),
            stub_concepts=sum(1 for c in self.concepts.values() if c.status == "stub"),
            concepts_with_models=sum(1 for c in self.concepts.values() if c.models),
            total_relationships=len(self.relationships),
            complete_relationships=sum(
                1
                for r in self.relationships.values()
                if r.get_status(self.concepts) == "complete"
            ),
            orphan_count=len(self.orphan_models),
        )
