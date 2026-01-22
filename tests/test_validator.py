"""Tests for validation logic."""

from pathlib import Path

from dbt_conceptual.config import Config, TagValidationConfig, ValidationConfig
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    ModelInfo,
    ProjectState,
    RelationshipState,
)
from dbt_conceptual.validator import Severity, Validator


def test_validate_concept_required_fields() -> None:
    """Test validation of concept required fields."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a complete concept missing fields - status will be draft since no models
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",  # Has domain
        owner=None,  # Missing
        definition=None,  # Missing
        gold_models=["dim_customer"],  # Has models, so status = complete
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have a warning for missing owner/definition
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    assert len(warnings) > 0


def test_validate_relationship_endpoints() -> None:
    """Test validation of relationship endpoints."""
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

    # Should have errors for missing concepts
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert len(errors) >= 2  # One for each missing concept


def test_validate_deprecated_references() -> None:
    """Test validation warns about deprecated concept usage."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a deprecated concept that's still being used
    state.concepts["old_customer"] = ConceptState(
        name="Old Customer",
        domain="party",
        owner="data_team",
        definition="Deprecated",
        replaced_by="customer",  # This makes status = deprecated
        gold_models=["dim_old_customer"],
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have a warning
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    assert len(warnings) > 0
    assert any("deprecated" in i.message.lower() for i in warnings)


def test_validate_gold_only_warning() -> None:
    """Test that gold-only concepts generate warnings."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add a concept with only gold models
    state.concepts["derived"] = ConceptState(
        name="Derived Metric",
        domain="analytics",
        owner="data_team",
        definition="A derived metric",
        gold_models=["fact_derived"],
        silver_models=[],
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have a warning about gold-only
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    assert any("gold models but no silver" in i.message for i in warnings)


def test_validator_summary() -> None:
    """Test validator summary counts."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add various issues
    # Stub concept (no domain) - generates info message
    state.concepts["stub"] = ConceptState(name="Stub")
    # Concept with domain but missing owner/definition - generates warnings
    state.concepts["incomplete"] = ConceptState(
        name="Incomplete",
        domain="party",
        gold_models=["dim_incomplete"],
    )

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

    # Add a relationship with missing endpoints (generates errors)
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
    """Test validation warns about unknown domain references."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add concept with unknown domain
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="unknown_domain",
        gold_models=["dim_customer"],
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have warning about unknown domain
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    assert any("unknown domain" in i.message.lower() for i in warnings)


def test_tag_validation_disabled_by_default() -> None:
    """Test that tag validation is disabled by default."""
    config = Config(project_dir=Path("/tmp"))
    state = ProjectState()

    # Add concept and model without domain tag
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        silver_models=["stg_customer"],
    )
    state.domains["party"] = DomainState(name="party", display_name="Party")
    state.models["stg_customer"] = ModelInfo(
        name="stg_customer",
        concept="customer",
        domain_tags=[],  # Missing domain tag
        layer="silver",
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should NOT have tag validation warnings (disabled by default)
    tag_issues = [i for i in issues if i.code.startswith("T")]
    assert len(tag_issues) == 0


def test_tag_validation_missing_domain_tag() -> None:
    """Test that missing domain tags are detected when enabled."""
    validation_config = ValidationConfig(
        tag_validation=TagValidationConfig(enabled=True)
    )
    config = Config(project_dir=Path("/tmp"), validation=validation_config)
    state = ProjectState()

    # Add concept and model without domain tag
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        silver_models=["stg_customer"],
    )
    state.domains["party"] = DomainState(name="party", display_name="Party")
    state.models["stg_customer"] = ModelInfo(
        name="stg_customer",
        concept="customer",
        domain_tags=[],  # Missing domain tag
        layer="silver",
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have T001 warning for missing domain tag
    tag_issues = [i for i in issues if i.code == "T001"]
    assert len(tag_issues) == 1
    assert "missing domain tag" in tag_issues[0].message.lower()


def test_tag_validation_wrong_domain_tag() -> None:
    """Test that wrong domain tags are detected."""
    validation_config = ValidationConfig(
        tag_validation=TagValidationConfig(enabled=True)
    )
    config = Config(project_dir=Path("/tmp"), validation=validation_config)
    state = ProjectState()

    # Add concept and model with wrong domain tag
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        silver_models=["stg_customer"],
    )
    state.domains["party"] = DomainState(name="party", display_name="Party")
    state.models["stg_customer"] = ModelInfo(
        name="stg_customer",
        concept="customer",
        domain_tags=["wrong_domain"],  # Wrong domain tag
        layer="silver",
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have T002 warning for wrong domain tag
    tag_issues = [i for i in issues if i.code == "T002"]
    assert len(tag_issues) == 1
    assert "wrong domain tag" in tag_issues[0].message.lower()


def test_tag_validation_correct_tags() -> None:
    """Test that correct tags don't generate warnings."""
    validation_config = ValidationConfig(
        tag_validation=TagValidationConfig(enabled=True)
    )
    config = Config(project_dir=Path("/tmp"), validation=validation_config)
    state = ProjectState()

    # Add concept and model with correct tags
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        owner="data_team",
        silver_models=["stg_customer"],
    )
    state.domains["party"] = DomainState(name="party", display_name="Party")
    state.models["stg_customer"] = ModelInfo(
        name="stg_customer",
        concept="customer",
        domain_tags=["party"],
        owner_tag="data_team",
        layer="silver",
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have no tag validation warnings
    tag_issues = [i for i in issues if i.code.startswith("T")]
    assert len(tag_issues) == 0


def test_tag_validation_missing_owner_tag() -> None:
    """Test that missing owner tags are detected."""
    validation_config = ValidationConfig(
        tag_validation=TagValidationConfig(enabled=True)
    )
    config = Config(project_dir=Path("/tmp"), validation=validation_config)
    state = ProjectState()

    # Add concept with owner and model without owner tag
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        owner="data_team",
        silver_models=["stg_customer"],
    )
    state.domains["party"] = DomainState(name="party", display_name="Party")
    state.models["stg_customer"] = ModelInfo(
        name="stg_customer",
        concept="customer",
        domain_tags=["party"],
        owner_tag=None,  # Missing owner tag
        layer="silver",
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have T004 warning for missing owner tag
    tag_issues = [i for i in issues if i.code == "T004"]
    assert len(tag_issues) == 1


def test_tag_validation_owner_from_domain() -> None:
    """Test that owner can be inherited from domain."""
    validation_config = ValidationConfig(
        tag_validation=TagValidationConfig(enabled=True)
    )
    config = Config(project_dir=Path("/tmp"), validation=validation_config)
    state = ProjectState()

    # Add concept without owner, but domain has owner
    state.concepts["customer"] = ConceptState(
        name="Customer",
        domain="party",
        owner=None,  # No concept-level owner
        silver_models=["stg_customer"],
    )
    state.domains["party"] = DomainState(
        name="party", display_name="Party", owner="party_team"
    )
    state.models["stg_customer"] = ModelInfo(
        name="stg_customer",
        concept="customer",
        domain_tags=["party"],
        owner_tag="party_team",  # Matches domain owner
        layer="silver",
    )

    validator = Validator(config, state)
    issues = validator.validate()

    # Should have no owner tag warnings
    owner_issues = [i for i in issues if i.code in ("T004", "T005")]
    assert len(owner_issues) == 0
