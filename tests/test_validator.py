"""Tests for validation logic.

v1.0 Validation Rules:
- E002: Relationship references undefined concept (always error)
- W101: Orphan model not linked to any concept (configurable)
- W102: Unimplemented concept - no models tagged (configurable)
- W104: Missing definition on concept/relationship (configurable)
- I001: Stub concept needs domain (info)
- I002: Stub relationship needs enrichment (info)
"""

from pathlib import Path

from dbt_conceptual.config import Config, ValidationConfig
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    OrphanModel,
    ProjectState,
    RelationshipState,
)
from dbt_conceptual.validator import Severity, Validator


def test_validate_relationship_endpoints() -> None:
    """Test validation of relationship endpoints (E002)."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a relationship with non-existent concepts
    state.relationships["customer:places:order"] = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have errors for missing concepts (E002)
    errors = [i for i in issues if i.severity == Severity.ERROR and i.code == "E002"]
    assert len(errors) >= 2  # One for each missing concept


def test_validate_orphan_models() -> None:
    """Test validation of orphan models (W101)."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add an orphan model
    state.orphan_models.append(
        OrphanModel(name="orphan_model", path="models/marts/orphan.yml")
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have warning for orphan model
    orphan_issues = [i for i in issues if i.code == "W101"]
    assert len(orphan_issues) == 1
    assert "orphan_model" in orphan_issues[0].message


def test_validate_unimplemented_concepts() -> None:
    """Test validation of unimplemented concepts (W102)."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a concept with no models
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        models=[],  # No models
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have warning for unimplemented concept
    unimplemented = [i for i in issues if i.code == "W102"]
    assert len(unimplemented) == 1


def test_validate_missing_definitions() -> None:
    """Test validation of missing definitions (W104)."""
    from dbt_conceptual.config import LayerValidationConfig, RuleSeverity

    # Enable missing_definitions validation
    validation_config = ValidationConfig(
        missing_definitions=RuleSeverity.WARN,
        gold=LayerValidationConfig(missing_definitions=RuleSeverity.WARN),
    )
    config = Config(project_dir=Path("/tmp"), validation=validation_config)
    state = ProjectState()

    # Add a concept without definition
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        models=["dim_customer"],
        definition=None,  # Missing
    )

    # Add a relationship without definition
    state.concepts["order"] = ConceptState(
        name="Order", domain="party", models=["fct_orders"]
    )
    state.relationships["customer:places:order"] = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
        definition=None,  # Missing
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have warnings for missing definitions
    missing_def = [i for i in issues if i.code == "W104"]
    assert len(missing_def) >= 1


def test_validator_summary() -> None:
    """Test validator summary counts."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a stub concept (no domain) - generates info message
    state.concepts["stub"] = ConceptState(name="Stub")

    validator = Validator(config, state)
    validator.validate()

    summary = validator.get_summary()
    assert "errors" in summary
    assert "warnings" in summary
    assert "info" in summary


def test_validator_has_errors() -> None:
    """Test has_errors method."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a relationship with missing endpoints (generates E002 errors)
    state.relationships["missing:relates:nonexistent"] = RelationshipState(
        verb="relates",
        from_concept="missing",
        to_concept="nonexistent",
    )

    validator = Validator(config, state)
    validator.validate()

    assert validator.has_errors() is True


def test_validator_no_errors() -> None:
    """Test has_errors returns False when no errors."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a valid stub concept (only info, no errors)
    state.concepts["valid_stub"] = ConceptState(name="Valid Stub")

    validator = Validator(config, state)
    validator.validate()

    assert validator.has_errors() is False


def test_validate_unknown_domain() -> None:
    """Test validation warns about unknown domain references (W001)."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add concept with unknown domain
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="unknown_domain",
        models=["dim_customer"],
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have warning about unknown domain
    warnings = [i for i in issues if i.code == "W001"]
    assert len(warnings) == 1
    assert "unknown domain" in warnings[0].message.lower()


def test_stub_concept_info() -> None:
    """Test that stub concepts generate info messages (I001)."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a stub concept
    state.concepts["stub"] = ConceptState(name="Stub")  # No domain

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have info message
    info_issues = [i for i in issues if i.code == "I001"]
    assert len(info_issues) == 1
    assert "missing" in info_issues[0].message.lower()


def test_stub_concept_error_with_no_drafts() -> None:
    """Test that --no-drafts treats stub concepts as errors."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a stub concept
    state.concepts["stub"] = ConceptState(name="Stub")

    validator = Validator(config, state, no_drafts=True)
    issues = validator.validate()

    # Should have error (E201) instead of info
    stub_issues = [i for i in issues if "stub" in i.message.lower()]
    assert any(i.severity == Severity.ERROR for i in stub_issues)


def test_complete_concept_no_warnings() -> None:
    """Test that a complete concept generates no validation warnings."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a complete concept with all fields
    state.domains["party"] = DomainState(name="party", display_name="Party")
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        owner="data_team",
        definition="A customer who purchases products",
        models=["dim_customer"],
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have no warnings or errors related to this concept
    concept_issues = [
        i for i in issues if i.context and i.context.get("concept") == "customer"
    ]
    warnings_and_errors = [
        i for i in concept_issues if i.severity in (Severity.WARNING, Severity.ERROR)
    ]
    assert len(warnings_and_errors) == 0
