"""Tests for guidance block functionality in conceptual models."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.parser import ConceptualModelParser, StateBuilder
from dbt_conceptual.validator import Validator


def test_parse_concept_with_guidance_context_only() -> None:
    """Test parsing a concept with guidance context only (no rules)."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with guidance context only
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {
                        "context": "Customer represents an individual or organization that purchases products.",
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert "customer" in state.concepts
        concept = state.concepts["customer"]
        assert concept.guidance is not None
        assert (
            concept.guidance.context
            == "Customer represents an individual or organization that purchases products."
        )
        assert len(concept.guidance.rules) == 0


def test_parse_concept_with_guidance_rules_only() -> None:
    """Test parsing a concept with guidance rules only (no context)."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with guidance rules only
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {
                        "rules": [
                            {
                                "name": "unique_email",
                                "description": "Email addresses must be unique across all customers",
                            },
                            {
                                "name": "valid_phone",
                                "description": "Phone numbers must be in E.164 format",
                            },
                        ],
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert "customer" in state.concepts
        concept = state.concepts["customer"]
        assert concept.guidance is not None
        assert concept.guidance.context is None
        assert len(concept.guidance.rules) == 2
        assert concept.guidance.rules[0].name == "unique_email"
        assert (
            concept.guidance.rules[0].description
            == "Email addresses must be unique across all customers"
        )
        assert concept.guidance.rules[1].name == "valid_phone"
        assert (
            concept.guidance.rules[1].description
            == "Phone numbers must be in E.164 format"
        )


def test_parse_concept_with_complete_guidance() -> None:
    """Test parsing a concept with both guidance context and rules."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with complete guidance
        conceptual_data = {
            "version": 1,
            "concepts": {
                "order": {
                    "name": "Order",
                    "guidance": {
                        "context": "An order represents a customer's request to purchase products.",
                        "rules": [
                            {
                                "name": "order_total_calculation",
                                "description": "Order total must equal sum of line item totals plus tax",
                            },
                        ],
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert "order" in state.concepts
        concept = state.concepts["order"]
        assert concept.guidance is not None
        assert (
            concept.guidance.context
            == "An order represents a customer's request to purchase products."
        )
        assert len(concept.guidance.rules) == 1
        assert concept.guidance.rules[0].name == "order_total_calculation"


def test_parse_concept_without_guidance() -> None:
    """Test parsing a concept without guidance (backward compatibility)."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml without guidance
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert "customer" in state.concepts
        concept = state.concepts["customer"]
        assert concept.guidance is None


def test_parse_empty_guidance_block() -> None:
    """Test parsing a concept with empty guidance block."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with empty guidance
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {},
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert "customer" in state.concepts
        concept = state.concepts["customer"]
        assert concept.guidance is not None
        assert concept.guidance.context is None
        assert len(concept.guidance.rules) == 0


def test_validate_duplicate_rule_names() -> None:
    """Test validation detects duplicate rule names within a concept."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with duplicate rule names
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {
                        "rules": [
                            {
                                "name": "unique_email",
                                "description": "First occurrence",
                            },
                            {
                                "name": "valid_phone",
                                "description": "Different rule",
                            },
                            {
                                "name": "unique_email",
                                "description": "Duplicate occurrence",
                            },
                        ],
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validator = Validator(config, state)
        issues = validator.validate()

        # Check that duplicate error was detected
        duplicate_errors = [issue for issue in issues if issue.code == "E003"]
        assert len(duplicate_errors) == 1
        assert "unique_email" in duplicate_errors[0].message
        assert "customer" in duplicate_errors[0].message
        assert "Duplicate rule name" in duplicate_errors[0].message


def test_validate_non_snake_case_rule_names() -> None:
    """Test validation warns about non-snake_case rule names."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with non-snake_case rule names
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {
                        "rules": [
                            {
                                "name": "UniqueEmail",  # PascalCase
                                "description": "Email must be unique",
                            },
                            {
                                "name": "valid-phone",  # kebab-case
                                "description": "Phone must be valid",
                            },
                            {
                                "name": "UPPER_CASE",  # UPPER_CASE
                                "description": "Something",
                            },
                            {
                                "name": "good_snake_case",  # Valid snake_case
                                "description": "This is fine",
                            },
                        ],
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validator = Validator(config, state)
        issues = validator.validate()

        # Check that warnings were generated
        snake_case_warnings = [issue for issue in issues if issue.code == "W105"]
        assert len(snake_case_warnings) == 3  # All except good_snake_case

        warning_names = [issue.context["rule_name"] for issue in snake_case_warnings]  # type: ignore[index]
        assert "UniqueEmail" in warning_names
        assert "valid-phone" in warning_names
        assert "UPPER_CASE" in warning_names
        assert "good_snake_case" not in warning_names


def test_validate_snake_case_allows_leading_lowercase() -> None:
    """Test that snake_case validation allows names starting with lowercase."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with valid snake_case names
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {
                        "rules": [
                            {"name": "unique_email", "description": "Valid"},
                            {"name": "valid_phone_number", "description": "Valid"},
                            {"name": "max_order_count", "description": "Valid"},
                            {"name": "single", "description": "Valid"},
                            {"name": "a", "description": "Valid"},
                        ],
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validator = Validator(config, state)
        issues = validator.validate()

        # Check that no snake_case warnings were generated
        snake_case_warnings = [issue for issue in issues if issue.code == "W105"]
        assert len(snake_case_warnings) == 0


def test_validate_multiple_concepts_with_guidance() -> None:
    """Test validation works correctly with multiple concepts having guidance."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with multiple concepts
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {
                        "rules": [
                            {
                                "name": "unique_email",
                                "description": "Email must be unique",
                            },
                            {
                                "name": "unique_email",  # Duplicate in customer
                                "description": "Duplicate",
                            },
                        ],
                    },
                },
                "order": {
                    "name": "Order",
                    "guidance": {
                        "rules": [
                            {
                                "name": "unique_email",  # Same name but different concept - OK
                                "description": "Email on order",
                            },
                            {
                                "name": "BadCamelCase",  # Non-snake_case
                                "description": "Invalid",
                            },
                        ],
                    },
                },
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validator = Validator(config, state)
        issues = validator.validate()

        # Check duplicate error only in customer
        duplicate_errors = [issue for issue in issues if issue.code == "E003"]
        assert len(duplicate_errors) == 1
        assert duplicate_errors[0].context["concept"] == "customer"  # type: ignore[index]

        # Check snake_case warning only in order
        snake_case_warnings = [issue for issue in issues if issue.code == "W105"]
        assert len(snake_case_warnings) == 1
        assert snake_case_warnings[0].context["concept"] == "order"  # type: ignore[index]


def test_concepts_without_guidance_not_validated() -> None:
    """Test that concepts without guidance don't trigger validation errors."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with mixed guidance
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    # No guidance
                },
                "order": {
                    "name": "Order",
                    "guidance": {
                        "context": "Order context",
                    },
                },
                "product": {
                    "name": "Product",
                    # No guidance
                },
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validator = Validator(config, state)
        issues = validator.validate()

        # Check no guidance-related errors for concepts without guidance
        guidance_issues = [issue for issue in issues if issue.code in ("E003", "W105")]
        assert len(guidance_issues) == 0


def test_guidance_preserved_in_state_builder() -> None:
    """Test that guidance is preserved when using StateBuilder."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with guidance
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "guidance": {
                        "context": "Business context here",
                        "rules": [
                            {
                                "name": "unique_id",
                                "description": "Customer ID must be unique",
                            },
                        ],
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Verify guidance is preserved
        assert "customer" in state.concepts
        concept = state.concepts["customer"]
        assert concept.guidance is not None
        assert concept.guidance.context == "Business context here"
        assert len(concept.guidance.rules) == 1
        assert concept.guidance.rules[0].name == "unique_id"
