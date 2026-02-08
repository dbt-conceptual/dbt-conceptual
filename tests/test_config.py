"""Tests for configuration loading and schema validation."""

import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from dbt_conceptual.config import (
    Config,
    ConfigError,
    LayerValidationConfig,
    RuleSeverity,
    ValidationConfig,
    _validate_config_schema,
)

# ──────────────────────────────────────────────────────────────────────────────
# Defaults (no files at all)
# ──────────────────────────────────────────────────────────────────────────────


class TestDefaults:
    """Test default configuration values."""

    def test_config_defaults_no_files(self) -> None:
        """Config loads with defaults when no files exist."""
        with TemporaryDirectory() as tmpdir:
            config = Config.load(project_dir=Path(tmpdir))

            assert config.project_dir == Path(tmpdir)
            assert config.gold_paths == ["models/marts/**/*.yml"]
            assert config.validation.orphan_models == RuleSeverity.WARN
            assert config.validation.unimplemented_concepts == RuleSeverity.WARN
            assert config.validation.missing_definitions == RuleSeverity.IGNORE

    def test_config_defaults_empty_dbt_project(self) -> None:
        """Config loads with defaults when dbt_project.yml has no vars."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "dbt_project.yml").write_text(yaml.dump({"name": "test"}))
            config = Config.load(project_dir=tmppath)

            assert config.gold_paths == ["models/marts/**/*.yml"]
            assert config.validation.orphan_models == RuleSeverity.WARN

    def test_config_defaults_empty_vars(self) -> None:
        """Config loads with defaults when vars exists but no dbt_conceptual."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "dbt_project.yml").write_text(
                yaml.dump({"name": "test", "vars": {"other_tool": True}})
            )
            config = Config.load(project_dir=tmppath)

            assert config.gold_paths == ["models/marts/**/*.yml"]

    def test_validation_config_dataclass_defaults(self) -> None:
        """ValidationConfig defaults are correct."""
        config = ValidationConfig()

        assert config.orphan_models == RuleSeverity.WARN
        assert config.unimplemented_concepts == RuleSeverity.WARN
        assert config.missing_definitions == RuleSeverity.IGNORE

    def test_dbt_project_file_property(self) -> None:
        """Config.dbt_project_file property returns correct path."""
        config = Config(project_dir=Path("/tmp/test"))
        assert config.dbt_project_file == Path("/tmp/test/dbt_project.yml")


# ──────────────────────────────────────────────────────────────────────────────
# Loading from dbt_project.yml vars
# ──────────────────────────────────────────────────────────────────────────────


class TestLoadFromDbtProject:
    """Test loading config from dbt_project.yml vars.dbt_conceptual."""

    def test_load_scan_gold_list(self) -> None:
        """Load scan.gold as list from dbt_project.yml."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {
                    "dbt_conceptual": {
                        "scan": {
                            "gold": [
                                "models/marts/**/*.yml",
                                "models/semantic/**/*.yml",
                            ]
                        }
                    }
                },
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))
            config = Config.load(project_dir=tmppath)

            assert config.gold_paths == [
                "models/marts/**/*.yml",
                "models/semantic/**/*.yml",
            ]

    def test_load_scan_gold_string(self) -> None:
        """Load scan.gold as single string from dbt_project.yml."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {"dbt_conceptual": {"scan": {"gold": "models/gold/**/*.yml"}}},
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))
            config = Config.load(project_dir=tmppath)

            assert config.gold_paths == ["models/gold/**/*.yml"]

    def test_load_validation_rules(self) -> None:
        """Load flat validation rules from dbt_project.yml."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {
                    "dbt_conceptual": {
                        "validation": {
                            "orphan_models": "error",
                            "unimplemented_concepts": "ignore",
                            "missing_definitions": "warn",
                        }
                    }
                },
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))
            config = Config.load(project_dir=tmppath)

            assert config.validation.orphan_models == RuleSeverity.ERROR
            assert config.validation.unimplemented_concepts == RuleSeverity.IGNORE
            assert config.validation.missing_definitions == RuleSeverity.WARN

    def test_load_validation_overrides(self) -> None:
        """Load validation_overrides from dbt_project.yml."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {
                    "dbt_conceptual": {
                        "validation": {"orphan_models": "warn"},
                        "validation_overrides": {
                            "gold": {
                                "orphan_models": "error",
                                "missing_definitions": "warn",
                            }
                        },
                    }
                },
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))
            config = Config.load(project_dir=tmppath)

            assert config.validation.orphan_models == RuleSeverity.WARN
            assert config.validation.gold.orphan_models == RuleSeverity.ERROR
            assert config.validation.gold.missing_definitions == RuleSeverity.WARN

    def test_load_empty_dbt_conceptual_block(self) -> None:
        """Empty dbt_conceptual block uses defaults."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {"dbt_conceptual": {}},
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))
            config = Config.load(project_dir=tmppath)

            assert config.gold_paths == ["models/marts/**/*.yml"]
            assert config.validation.orphan_models == RuleSeverity.WARN


# ──────────────────────────────────────────────────────────────────────────────
# Precedence: dbt_project.yml wins over legacy
# ──────────────────────────────────────────────────────────────────────────────


class TestPrecedence:
    """Test config precedence rules."""

    def test_dbt_project_wins_over_legacy(self) -> None:
        """dbt_project.yml vars take precedence over conceptual.yml config."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Legacy conceptual.yml with config section
            conceptual_data = {
                "config": {
                    "scan": {"gold": ["models/legacy/**/*.yml"]},
                    "validation": {"defaults": {"orphan_models": "ignore"}},
                },
            }
            (tmppath / "conceptual.yml").write_text(yaml.dump(conceptual_data))

            # dbt_project.yml with vars.dbt_conceptual
            dbt_data = {
                "name": "test",
                "vars": {
                    "dbt_conceptual": {
                        "scan": {"gold": ["models/new/**/*.yml"]},
                        "validation": {"orphan_models": "error"},
                    }
                },
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))

            config = Config.load(project_dir=tmppath)

            # dbt_project.yml should win
            assert config.gold_paths == ["models/new/**/*.yml"]
            assert config.validation.orphan_models == RuleSeverity.ERROR

    def test_cli_overrides_dbt_project(self) -> None:
        """CLI flags override dbt_project.yml."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {
                    "dbt_conceptual": {
                        "scan": {"gold": ["models/file/**/*.yml"]},
                    }
                },
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))

            config = Config.load(
                project_dir=tmppath,
                gold_paths=["models/cli/**/*.yml"],
            )

            assert config.gold_paths == ["models/cli/**/*.yml"]


# ──────────────────────────────────────────────────────────────────────────────
# Legacy fallback with DeprecationWarning
# ──────────────────────────────────────────────────────────────────────────────


class TestLegacyFallback:
    """Test legacy config loading from conceptual.yml."""

    def test_legacy_config_emits_deprecation_warning(self) -> None:
        """Loading config from conceptual.yml emits DeprecationWarning."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conceptual_data = {
                "config": {
                    "scan": {"gold": ["models/marts/**/*.yml"]},
                    "validation": {
                        "defaults": {"orphan_models": "error"},
                    },
                },
            }
            (tmppath / "conceptual.yml").write_text(yaml.dump(conceptual_data))

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = Config.load(project_dir=tmppath)

            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 1
            assert "deprecated" in str(deprecation_warnings[0].message).lower()

            # Config should still load correctly
            assert config.gold_paths == ["models/marts/**/*.yml"]
            assert config.validation.orphan_models == RuleSeverity.ERROR

    def test_legacy_without_config_section_no_warning(self) -> None:
        """conceptual.yml without config section does not emit warning."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conceptual_data = {
                "domains": {"sales": {"display_name": "Sales"}},
                "concepts": {},
            }
            (tmppath / "conceptual.yml").write_text(yaml.dump(conceptual_data))

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                Config.load(project_dir=tmppath)

            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0

    def test_legacy_validation_with_gold_overrides(self) -> None:
        """Legacy format with defaults and gold layer overrides."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conceptual_data = {
                "config": {
                    "validation": {
                        "defaults": {
                            "orphan_models": "warn",
                            "missing_definitions": "ignore",
                        },
                        "gold": {
                            "orphan_models": "error",
                            "missing_definitions": "error",
                        },
                    }
                },
            }
            (tmppath / "conceptual.yml").write_text(yaml.dump(conceptual_data))

            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                config = Config.load(project_dir=tmppath)

            assert config.validation.orphan_models == RuleSeverity.WARN
            assert config.validation.gold.orphan_models == RuleSeverity.ERROR
            assert config.validation.gold.missing_definitions == RuleSeverity.ERROR

    def test_legacy_scan_gold_string(self) -> None:
        """Legacy format with scan.gold as string."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conceptual_data = {
                "config": {
                    "scan": {"gold": "models/gold/**/*.yml"},
                },
            }
            (tmppath / "conceptual.yml").write_text(yaml.dump(conceptual_data))

            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                config = Config.load(project_dir=tmppath)

            assert config.gold_paths == ["models/gold/**/*.yml"]


# ──────────────────────────────────────────────────────────────────────────────
# CLI overrides
# ──────────────────────────────────────────────────────────────────────────────


class TestCLIOverrides:
    """Test CLI parameter overrides."""

    def test_cli_gold_paths_override(self) -> None:
        """CLI gold_paths override file config."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conceptual_data = {
                "config": {
                    "scan": {"gold": ["models/marts/**/*.yml"]},
                },
            }
            (tmppath / "conceptual.yml").write_text(yaml.dump(conceptual_data))

            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                config = Config.load(
                    project_dir=tmppath,
                    gold_paths=["models/gold/**/*.yml"],
                )

            assert config.gold_paths == ["models/gold/**/*.yml"]

    def test_cli_gold_paths_override_defaults(self) -> None:
        """CLI gold_paths override defaults when no file config."""
        with TemporaryDirectory() as tmpdir:
            config = Config.load(
                project_dir=Path(tmpdir),
                gold_paths=["custom/**/*.yml"],
            )
            assert config.gold_paths == ["custom/**/*.yml"]


# ──────────────────────────────────────────────────────────────────────────────
# Schema validation
# ──────────────────────────────────────────────────────────────────────────────


class TestSchemaValidation:
    """Test config schema validation."""

    def test_unknown_top_level_key_warns(self) -> None:
        """Unknown top-level key returns warning."""
        result = _validate_config_schema({"future_feature": True})
        assert len(result) == 1
        assert "Unknown config key 'future_feature'" in result[0]

    def test_unknown_scan_key_warns(self) -> None:
        """Unknown scan key returns warning."""
        result = _validate_config_schema({"scan": {"silver": ["x"]}})
        assert len(result) == 1
        assert "Unknown scan key 'silver'" in result[0]

    def test_valid_config_no_warnings(self) -> None:
        """Valid config returns no warnings."""
        result = _validate_config_schema(
            {
                "scan": {"gold": ["models/**/*.yml"]},
                "validation": {"orphan_models": "warn"},
                "validation_overrides": {"gold": {"orphan_models": "error"}},
            }
        )
        assert result == []

    def test_invalid_scan_gold_type_errors(self) -> None:
        """Non-string, non-list scan.gold raises ConfigError."""
        with pytest.raises(ConfigError, match="scan.gold must be a string or list"):
            _validate_config_schema({"scan": {"gold": 42}})

    def test_invalid_scan_gold_list_item_errors(self) -> None:
        """Non-string item in scan.gold list raises ConfigError."""
        with pytest.raises(ConfigError, match="scan.gold\\[0\\] must be a string"):
            _validate_config_schema({"scan": {"gold": [123]}})

    def test_unknown_validation_rule_errors(self) -> None:
        """Unknown validation rule raises ConfigError."""
        with pytest.raises(ConfigError, match="Unknown validation rule 'bogus'"):
            _validate_config_schema({"validation": {"bogus": "warn"}})

    def test_invalid_severity_value_errors(self) -> None:
        """Invalid severity value raises ConfigError."""
        with pytest.raises(ConfigError, match="Invalid severity 'critical'"):
            _validate_config_schema({"validation": {"orphan_models": "critical"}})

    def test_invalid_layer_name_errors(self) -> None:
        """Invalid layer name in validation_overrides raises ConfigError."""
        with pytest.raises(ConfigError, match="Invalid layer name 'silver'"):
            _validate_config_schema(
                {"validation_overrides": {"silver": {"orphan_models": "error"}}}
            )

    def test_unknown_rule_in_overrides_errors(self) -> None:
        """Unknown rule in validation_overrides raises ConfigError."""
        with pytest.raises(ConfigError, match="Unknown validation rule 'bogus'"):
            _validate_config_schema(
                {"validation_overrides": {"gold": {"bogus": "error"}}}
            )

    def test_invalid_severity_in_overrides_errors(self) -> None:
        """Invalid severity in validation_overrides raises ConfigError."""
        with pytest.raises(ConfigError, match="Invalid severity 'fatal'"):
            _validate_config_schema(
                {"validation_overrides": {"gold": {"orphan_models": "fatal"}}}
            )

    def test_unknown_key_warns_on_load(self) -> None:
        """Unknown key emits UserWarning during Config.load()."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {
                    "dbt_conceptual": {
                        "future_feature": True,
                    }
                },
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                Config.load(project_dir=tmppath)

            user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
            assert len(user_warnings) == 1
            assert "Unknown config key" in str(user_warnings[0].message)

    def test_config_error_on_load_with_invalid_rule(self) -> None:
        """ConfigError propagates through Config.load()."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            dbt_data = {
                "name": "test",
                "vars": {
                    "dbt_conceptual": {
                        "validation": {"bogus_rule": "warn"},
                    }
                },
            }
            (tmppath / "dbt_project.yml").write_text(yaml.dump(dbt_data))

            with pytest.raises(ConfigError, match="Unknown validation rule"):
                Config.load(project_dir=tmppath)


# ──────────────────────────────────────────────────────────────────────────────
# get_severity with and without layer overrides
# ──────────────────────────────────────────────────────────────────────────────


class TestGetSeverity:
    """Test ValidationConfig.get_severity()."""

    def test_default_severity_no_layer(self) -> None:
        """get_severity returns default when no layer specified."""
        config = ValidationConfig(
            orphan_models=RuleSeverity.WARN,
            missing_definitions=RuleSeverity.IGNORE,
        )
        assert config.get_severity("orphan_models") == RuleSeverity.WARN
        assert config.get_severity("missing_definitions") == RuleSeverity.IGNORE

    def test_gold_layer_override(self) -> None:
        """get_severity returns gold override when layer='gold'."""
        config = ValidationConfig(
            orphan_models=RuleSeverity.WARN,
            gold=LayerValidationConfig(orphan_models=RuleSeverity.ERROR),
        )
        assert config.get_severity("orphan_models", "gold") == RuleSeverity.ERROR

    def test_gold_layer_no_override_falls_back(self) -> None:
        """get_severity falls back to default when gold has no override."""
        config = ValidationConfig(
            orphan_models=RuleSeverity.WARN,
            gold=LayerValidationConfig(),
        )
        assert config.get_severity("orphan_models", "gold") == RuleSeverity.WARN

    def test_unknown_layer_returns_default(self) -> None:
        """get_severity returns default for unknown layer."""
        config = ValidationConfig(orphan_models=RuleSeverity.WARN)
        assert config.get_severity("orphan_models", "silver") == RuleSeverity.WARN


# ──────────────────────────────────────────────────────────────────────────────
# get_layer path matching
# ──────────────────────────────────────────────────────────────────────────────


class TestGetLayer:
    """Test Config.get_layer() path matching."""

    def test_gold_path_match(self) -> None:
        """Paths matching gold patterns return 'gold'."""
        config = Config(
            project_dir=Path("/tmp"),
            gold_paths=["models/marts/**/*.yml", "models/gold/**/*.yml"],
        )
        assert config.get_layer("models/marts/schema.yml") == "gold"
        assert config.get_layer("models/gold/fact_orders.yml") == "gold"

    def test_non_gold_path(self) -> None:
        """Paths not matching gold patterns return None."""
        config = Config(
            project_dir=Path("/tmp"),
            gold_paths=["models/marts/**/*.yml"],
        )
        assert config.get_layer("models/staging/stg_orders.yml") is None

    def test_base_pattern_prefix_match(self) -> None:
        """Paths starting with base pattern prefix are matched."""
        config = Config(
            project_dir=Path("/tmp"),
            gold_paths=["models/marts/**/*.yml"],
        )
        # Should match via prefix (before the *)
        assert config.get_layer("models/marts/deep/nested/file.yml") == "gold"
