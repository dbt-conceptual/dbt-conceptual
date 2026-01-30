"""Tests for configuration loading from conceptual.yml."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from dbt_conceptual.config import Config, RuleSeverity, ValidationConfig


def test_config_defaults() -> None:
    """Test that config loads with defaults."""
    with TemporaryDirectory() as tmpdir:
        config = Config.load(project_dir=Path(tmpdir))

        assert config.project_dir == Path(tmpdir)
        assert config.gold_paths == ["models/marts/**/*.yml"]
        # Check default validation config
        assert config.validation.orphan_models == RuleSeverity.WARN
        assert config.validation.unimplemented_concepts == RuleSeverity.WARN
        assert config.validation.missing_definitions == RuleSeverity.IGNORE


def test_config_from_conceptual_yml() -> None:
    """Test that config loads from conceptual.yml."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create conceptual.yml with custom config
        conceptual_data = {
            "config": {
                "scan": {"gold": ["models/marts/**/*.yml", "models/semantic/**/*.yml"]},
                "validation": {
                    "defaults": {
                        "orphan_models": "error",
                        "unimplemented_concepts": "ignore",
                    }
                },
            },
            "domains": {"sales": {"display_name": "Sales"}},
            "concepts": {},
            "relationships": [],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)

        assert config.gold_paths == [
            "models/marts/**/*.yml",
            "models/semantic/**/*.yml",
        ]
        assert config.validation.orphan_models == RuleSeverity.ERROR
        assert config.validation.unimplemented_concepts == RuleSeverity.IGNORE


def test_config_cli_overrides() -> None:
    """Test that CLI arguments override conceptual.yml."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create conceptual.yml
        conceptual_data = {
            "config": {
                "scan": {"gold": ["models/marts/**/*.yml"]},
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # CLI overrides
        config = Config.load(
            project_dir=tmppath,
            gold_paths=["models/gold/**/*.yml"],
        )

        assert config.gold_paths == ["models/gold/**/*.yml"]


def test_get_layer() -> None:
    """Test layer detection from path."""
    config = Config(
        project_dir=Path("/tmp"),
        gold_paths=["models/marts/**/*.yml", "models/gold/**/*.yml"],
    )

    assert config.get_layer("models/marts/schema.yml") == "gold"
    assert config.get_layer("models/gold/fact_orders.yml") == "gold"
    assert config.get_layer("models/staging/stg_orders.yml") is None


def test_validation_config_from_conceptual_yml() -> None:
    """Test that validation config loads from conceptual.yml."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create conceptual.yml with validation config
        conceptual_data = {
            "config": {
                "validation": {
                    "defaults": {
                        "orphan_models": "error",
                        "unimplemented_concepts": "ignore",
                        "missing_definitions": "warn",
                    },
                    "gold": {
                        "orphan_models": "error",
                        "missing_definitions": "error",
                    },
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)

        # Check defaults
        assert config.validation.orphan_models == RuleSeverity.ERROR
        assert config.validation.unimplemented_concepts == RuleSeverity.IGNORE
        assert config.validation.missing_definitions == RuleSeverity.WARN

        # Check layer overrides
        assert config.validation.gold.orphan_models == RuleSeverity.ERROR
        assert config.validation.gold.missing_definitions == RuleSeverity.ERROR


def test_validation_config_get_severity() -> None:
    """Test ValidationConfig.get_severity with layer overrides."""
    from dbt_conceptual.config import LayerValidationConfig

    config = ValidationConfig(
        orphan_models=RuleSeverity.WARN,
        missing_definitions=RuleSeverity.IGNORE,
        gold=LayerValidationConfig(
            orphan_models=RuleSeverity.ERROR,
            missing_definitions=RuleSeverity.WARN,
        ),
    )

    # Without layer - should return defaults
    assert config.get_severity("orphan_models") == RuleSeverity.WARN
    assert config.get_severity("missing_definitions") == RuleSeverity.IGNORE

    # With gold layer - should return layer override
    assert config.get_severity("orphan_models", "gold") == RuleSeverity.ERROR
    assert config.get_severity("missing_definitions", "gold") == RuleSeverity.WARN

    # Rule without gold override - should return default
    assert config.get_severity("unimplemented_concepts", "gold") == RuleSeverity.WARN


def test_validation_config_defaults() -> None:
    """Test ValidationConfig dataclass defaults."""
    config = ValidationConfig()

    assert config.orphan_models == RuleSeverity.WARN
    assert config.unimplemented_concepts == RuleSeverity.WARN
    assert config.missing_definitions == RuleSeverity.IGNORE
