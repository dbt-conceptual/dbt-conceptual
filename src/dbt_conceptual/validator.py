"""Validation logic for conceptual models and their dbt implementations."""

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

    # Required fields by concept status
    REQUIRED_FIELDS = {
        "stub": ["name"],
        "draft": ["name", "domain"],
        "complete": ["name", "domain", "owner", "definition"],
        "deprecated": ["name", "domain", "owner", "definition"],
    }

    def __init__(self, config: Config, state: ProjectState):
        """Initialize the validator.

        Args:
            config: Configuration object
            state: Project state to validate
        """
        self.config = config
        self.state = state
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
        self._validate_unrealized_relationships()
        self._validate_missing_definitions()
        self._validate_domain_mismatch()

        # Other validations (always run)
        self._validate_concept_required_fields()
        self._validate_domain_references()
        self._validate_relationship_endpoint_implementation()
        self._validate_group_name_collisions()
        self._validate_deprecated_references()
        self._check_gold_only_concepts()
        self._check_stub_concepts()

        return self.issues

    def _validate_orphan_models(self) -> None:
        """Check for models not linked to any concept."""
        severity = _rule_to_severity(self.config.validation.orphan_models)
        if severity is None:
            return

        if self.state.orphan_models:
            for orphan in self.state.orphan_models:
                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code="W101",
                        message=f"Model '{orphan.name}' is not linked to any concept",
                        context={"model": orphan.name, "layer": orphan.layer},
                    )
                )

    def _validate_unimplemented_concepts(self) -> None:
        """Check for concepts with no implementing models."""
        severity = _rule_to_severity(self.config.validation.unimplemented_concepts)
        if severity is None:
            return

        for concept_id, concept in self.state.concepts.items():
            if concept.status == "deprecated":
                continue
            if not concept.silver_models and not concept.gold_models:
                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code="W102",
                        message=f"Concept '{concept_id}' has no implementing models",
                        context={"concept": concept_id, "status": concept.status},
                    )
                )

    def _validate_unrealized_relationships(self) -> None:
        """Check for relationships with no realizing models."""
        severity = _rule_to_severity(self.config.validation.unrealized_relationships)
        if severity is None:
            return

        for rel_id, rel in self.state.relationships.items():
            if not rel.realized_by:
                self.issues.append(
                    ValidationIssue(
                        severity=severity,
                        code="W103",
                        message=f"Relationship '{rel_id}' ({rel.from_concept} -> {rel.to_concept}) is not realized by any model",
                        context={
                            "relationship": rel_id,
                            "from": rel.from_concept,
                            "to": rel.to_concept,
                        },
                    )
                )

    def _validate_missing_definitions(self) -> None:
        """Check for non-stub concepts missing definitions."""
        severity = _rule_to_severity(self.config.validation.missing_definitions)
        if severity is None:
            return

        for concept_id, concept in self.state.concepts.items():
            if concept.status in ["stub", "deprecated"]:
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

    def _validate_domain_mismatch(self) -> None:
        """Check for models with meta.domain that doesn't match concept domain."""
        severity = _rule_to_severity(self.config.validation.domain_mismatch)
        if severity is None:
            return

        # This would require tracking model domains in state
        # For now, skip - would need to enhance state to track this
        pass

    def _validate_concept_required_fields(self) -> None:
        """Validate that concepts have required fields based on their status."""
        for concept_id, concept in self.state.concepts.items():
            status = concept.status
            required = self.REQUIRED_FIELDS.get(status, [])

            missing = []
            for field in required:
                value = getattr(concept, field, None)
                if value is None:
                    missing.append(field)

            if missing and status != "stub":
                self.issues.append(
                    ValidationIssue(
                        severity=(
                            Severity.ERROR if status == "complete" else Severity.WARNING
                        ),
                        code="E001",
                        message=f"Concept '{concept_id}' is missing required fields for status '{status}': {', '.join(missing)}",
                        context={
                            "concept": concept_id,
                            "status": status,
                            "missing": missing,
                        },
                    )
                )

    def _validate_domain_references(self) -> None:
        """Validate that concept domain references exist."""
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

    def _validate_relationship_endpoints(self) -> None:
        """Validate that relationship endpoints reference existing concepts."""
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

    def _validate_relationship_endpoint_implementation(self) -> None:
        """Validate that realized relationships have implemented endpoint concepts."""
        for rel_id, rel in self.state.relationships.items():
            # Only check if the relationship is realized
            if not rel.realized_by:
                continue

            # Check if both endpoint concepts have models
            from_concept = self.state.concepts.get(rel.from_concept)
            to_concept = self.state.concepts.get(rel.to_concept)

            if from_concept:
                if not from_concept.silver_models and not from_concept.gold_models:
                    self.issues.append(
                        ValidationIssue(
                            severity=Severity.ERROR,
                            code="E003",
                            message=f"Relationship '{rel_id}' is realized but '{rel.from_concept}' has no implementing models",
                            context={
                                "relationship": rel_id,
                                "concept": rel.from_concept,
                                "realized_by": rel.realized_by,
                            },
                        )
                    )

            if to_concept:
                if not to_concept.silver_models and not to_concept.gold_models:
                    self.issues.append(
                        ValidationIssue(
                            severity=Severity.ERROR,
                            code="E003",
                            message=f"Relationship '{rel_id}' is realized but '{rel.to_concept}' has no implementing models",
                            context={
                                "relationship": rel_id,
                                "concept": rel.to_concept,
                                "realized_by": rel.realized_by,
                            },
                        )
                    )

    def _validate_group_name_collisions(self) -> None:
        """Validate that group names don't collide with relationship names."""
        # Build set of relationship names
        rel_names = {rel.name for rel in self.state.relationships.values()}

        for group_name in self.state.groups:
            if group_name in rel_names:
                self.issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="E004",
                        message=f"Group name '{group_name}' collides with relationship name",
                        context={"group": group_name},
                    )
                )

    def _validate_deprecated_references(self) -> None:
        """Warn when models reference deprecated concepts."""
        for concept_id, concept in self.state.concepts.items():
            if concept.status == "deprecated":
                if concept.silver_models or concept.gold_models:
                    all_models = concept.silver_models + concept.gold_models
                    self.issues.append(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            code="W002",
                            message=f"Deprecated concept '{concept_id}' is still referenced by models: {', '.join(all_models)}",
                            context={
                                "concept": concept_id,
                                "models": all_models,
                                "replaced_by": concept.replaced_by,
                            },
                        )
                    )

    def _check_gold_only_concepts(self) -> None:
        """Warn about concepts that only have gold models (unusual pattern)."""
        for concept_id, concept in self.state.concepts.items():
            if concept.gold_models and not concept.silver_models:
                self.issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        code="W003",
                        message=f"Concept '{concept_id}' has gold models but no silver models (unusual)",
                        context={
                            "concept": concept_id,
                            "gold_models": concept.gold_models,
                        },
                    )
                )

    def _check_stub_concepts(self) -> None:
        """Info messages for stub concepts that need attention."""
        for concept_id, concept in self.state.concepts.items():
            if concept.status == "stub":
                missing = []
                for field in ["domain", "owner", "definition"]:
                    if getattr(concept, field, None) is None:
                        missing.append(field)

                if missing:
                    self.issues.append(
                        ValidationIssue(
                            severity=Severity.INFO,
                            code="I001",
                            message=f"Stub concept '{concept_id}' needs enrichment: missing {', '.join(missing)}",
                            context={
                                "concept": concept_id,
                                "missing": missing,
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
