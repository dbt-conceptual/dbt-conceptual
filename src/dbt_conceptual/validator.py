"""Validation logic for conceptual models and their dbt implementations.

v1.0 Validation Rules:
- E002: Relationship references undefined concept (always error, creates ghost)
- W101: Orphan model not linked to any concept (configurable)
- W102: Unimplemented concept - no models tagged (configurable)
- W104: Missing definition on concept/relationship (configurable)
- I001: Stub concept needs domain (info)
- I002: Stub relationship needs verb (info)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dbt_conceptual.config import Config, RuleSeverity
from dbt_conceptual.state import ProjectState


class Severity(Enum):
    """Validation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


def _rule_to_severity(rule: RuleSeverity) -> Optional[Severity]:
    """Convert RuleSeverity to Severity (returns None for IGNORE)."""
    if rule == RuleSeverity.ERROR:
        return Severity.ERROR
    elif rule == RuleSeverity.WARN:
        return Severity.WARNING
    return None


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    severity: Severity
    code: str
    message: str
    context: Optional[dict] = None


class Validator:
    """Validates conceptual model and dbt implementation correspondence."""

    def __init__(self, config: Config, state: ProjectState, no_drafts: bool = False):
        """Initialize the validator.

        Args:
            config: Configuration object
            state: Project state to validate
            no_drafts: If True, treat stub/draft concepts as errors
        """
        self.config = config
        self.state = state
        self.no_drafts = no_drafts
        self.issues: list[ValidationIssue] = []

    def validate(self) -> list[ValidationIssue]:
        """Run all validation checks.

        Returns:
            List of validation issues found
        """
        self.issues = []

        # Hardcoded as errors - unknown refs are always errors
        self._validate_relationship_endpoints()

        # Configurable rules
        self._validate_orphan_models()
        self._validate_unimplemented_concepts()
        self._validate_missing_definitions()

        # Always run - domain references
        self._validate_domain_references()

        # Info/stub checks
        self._check_stub_concepts()

        return self.issues

    def _validate_relationship_endpoints(self) -> None:
        """Validate that relationship endpoints reference existing concepts.

        E002: Always an error - creates ghost concepts.
        """
        for rel_id, rel in self.state.relationships.items():
            if rel.from_concept not in self.state.concepts:
                self.issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="E002",
                        message=f"Relationship '{rel_id}' references non-existent concept '{rel.from_concept}'",
                        context={
                            "relationship": rel_id,
                            "missing_concept": rel.from_concept,
                        },
                    )
                )

            if rel.to_concept not in self.state.concepts:
                self.issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="E002",
                        message=f"Relationship '{rel_id}' references non-existent concept '{rel.to_concept}'",
                        context={
                            "relationship": rel_id,
                            "missing_concept": rel.to_concept,
                        },
                    )
                )

    def _validate_orphan_models(self) -> None:
        """Check for models not linked to any concept.

        W101: Configurable severity.
        """
        severity = _rule_to_severity(
            self.config.validation.get_severity("orphan_models", "gold")
        )
        if severity is None:
            return

        if self.state.orphan_models:
            for orphan in self.state.orphan_models:
                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code="W101",
                        message=f"Model '{orphan.name}' is not linked to any concept",
                        context={"model": orphan.name, "path": orphan.path},
                    )
                )

    def _validate_unimplemented_concepts(self) -> None:
        """Check for concepts with no implementing models.

        W102: Configurable severity.
        """
        severity = _rule_to_severity(
            self.config.validation.get_severity("unimplemented_concepts", "gold")
        )
        if severity is None:
            return

        for concept_id, concept in self.state.concepts.items():
            if concept.is_ghost:
                continue  # Ghosts are already errors

            if not concept.models:
                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code="W102",
                        message=f"Concept '{concept_id}' has no implementing models",
                        context={"concept": concept_id, "status": concept.status},
                    )
                )

    def _validate_missing_definitions(self) -> None:
        """Check for non-stub concepts/relationships missing definitions.

        W104: Configurable severity.
        """
        severity = _rule_to_severity(
            self.config.validation.get_severity("missing_definitions", "gold")
        )
        if severity is None:
            return

        # Check concepts
        for concept_id, concept in self.state.concepts.items():
            if concept.status == "stub" or concept.is_ghost:
                continue
            if not concept.definition:
                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code="W104",
                        message=f"Concept '{concept_id}' is missing a definition",
                        context={"concept": concept_id, "status": concept.status},
                    )
                )

        # Check relationships
        for rel_id, rel in self.state.relationships.items():
            if not rel.definition:
                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code="W104",
                        message=f"Relationship '{rel_id}' is missing a definition",
                        context={"relationship": rel_id},
                    )
                )

    def _validate_domain_references(self) -> None:
        """Validate that concept domain references exist.

        W001: Warning when domain not found.
        """
        for concept_id, concept in self.state.concepts.items():
            if concept.domain and concept.domain not in self.state.domains:
                self.issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        code="W001",
                        message=f"Concept '{concept_id}' references unknown domain '{concept.domain}'",
                        context={"concept": concept_id, "domain": concept.domain},
                    )
                )

    def _check_stub_concepts(self) -> None:
        """Info messages for stub concepts/relationships (or errors if --no-drafts).

        I001: Stub concept needs enrichment
        I002: Stub relationship needs enrichment
        """
        # Check concepts
        for concept_id, concept in self.state.concepts.items():
            if concept.is_ghost:
                continue  # Ghosts have their own errors

            if concept.status in ("stub", "draft"):
                missing = []
                if not concept.domain:
                    missing.append("domain")
                if not concept.owner:
                    missing.append("owner")
                if not concept.definition:
                    missing.append("definition")

                if missing:
                    severity = Severity.ERROR if self.no_drafts else Severity.INFO
                    code = "E201" if self.no_drafts else "I001"
                    status_label = concept.status.capitalize()

                    self.issues.append(
                        ValidationIssue(
                            severity=severity,
                            code=code,
                            message=f"{status_label} concept '{concept_id}' needs enrichment: missing {', '.join(missing)}",
                            context={
                                "concept": concept_id,
                                "missing": missing,
                                "status": concept.status,
                            },
                        )
                    )

        # Check relationships
        for _, rel in self.state.relationships.items():
            status = rel.get_status(self.state.concepts)
            if status == "stub":
                missing = []
                if not rel.definition:
                    missing.append("definition")

                severity = Severity.ERROR if self.no_drafts else Severity.INFO
                code = "E202" if self.no_drafts else "I002"

                if missing:
                    msg = f"Stub relationship '{rel.name}' needs enrichment: missing {', '.join(missing)}"
                else:
                    msg = f"Stub relationship '{rel.name}' has stub/ghost endpoint concepts"

                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code=code,
                        message=msg,
                        context={
                            "relationship": rel.name,
                            "missing": missing,
                            "status": status,
                        },
                    )
                )

    def has_errors(self) -> bool:
        """Check if there are any error-level issues.

        Returns:
            True if there are errors, False otherwise
        """
        return any(issue.severity == Severity.ERROR for issue in self.issues)

    def get_summary(self) -> dict[str, int]:
        """Get summary counts by severity.

        Returns:
            Dictionary mapping severity to count
        """
        summary = {
            "errors": 0,
            "warnings": 0,
            "info": 0,
        }

        for issue in self.issues:
            if issue.severity == Severity.ERROR:
                summary["errors"] += 1
            elif issue.severity == Severity.WARNING:
                summary["warnings"] += 1
            elif issue.severity == Severity.INFO:
                summary["info"] += 1

        return summary
