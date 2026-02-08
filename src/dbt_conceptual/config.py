"""Configuration management for dbt-conceptual.

Configuration is loaded from dbt_project.yml vars.dbt_conceptual block,
with legacy fallback to conceptual.yml config section.
"""

from __future__ import annotations

import fnmatch
import warnings
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml

# Schema constants for validation
_VALID_CONFIG_KEYS = {"scan", "validation", "validation_overrides"}
_VALID_SCAN_KEYS = {"gold"}
_VALID_RULE_NAMES = {"orphan_models", "unimplemented_concepts", "missing_definitions"}
_VALID_SEVERITY_VALUES = {"error", "warn", "ignore"}
_VALID_LAYER_NAMES = {"gold"}


class ConfigError(Exception):
    """Raised when configuration contains invalid values."""


class RuleSeverity(Enum):
    """Configurable validation rule severity."""

    ERROR = "error"
    WARN = "warn"
    IGNORE = "ignore"


def _validate_config_schema(data: dict) -> list:
    """Validate config schema and return warnings for unknown keys.

    Args:
        data: Config dict to validate

    Returns:
        List of warning messages for unknown keys

    Raises:
        ConfigError: If values are invalid
    """
    warnings_list: list = []

    # Check top-level keys
    for key in data:
        if key not in _VALID_CONFIG_KEYS:
            warnings_list.append(
                f"Unknown config key '{key}' (valid keys: "
                f"{', '.join(sorted(_VALID_CONFIG_KEYS))})"
            )

    # Check scan keys
    scan_data = data.get("scan")
    if isinstance(scan_data, dict):
        for key in scan_data:
            if key not in _VALID_SCAN_KEYS:
                warnings_list.append(
                    f"Unknown scan key '{key}' (valid keys: "
                    f"{', '.join(sorted(_VALID_SCAN_KEYS))})"
                )
        # Validate scan.gold type
        gold_val = scan_data.get("gold")
        if gold_val is not None:
            if not isinstance(gold_val, (str, list)):
                raise ConfigError(
                    f"scan.gold must be a string or list, got {type(gold_val).__name__}"
                )
            if isinstance(gold_val, list):
                for i, item in enumerate(gold_val):
                    if not isinstance(item, str):
                        raise ConfigError(
                            f"scan.gold[{i}] must be a string, "
                            f"got {type(item).__name__}"
                        )

    # Check validation keys
    validation_data = data.get("validation")
    if isinstance(validation_data, dict):
        _validate_validation_rules(validation_data, "validation")

    # Check validation_overrides keys
    overrides_data = data.get("validation_overrides")
    if isinstance(overrides_data, dict):
        for layer_name, layer_rules in overrides_data.items():
            if layer_name not in _VALID_LAYER_NAMES:
                raise ConfigError(
                    f"Invalid layer name '{layer_name}' in validation_overrides "
                    f"(valid layers: {', '.join(sorted(_VALID_LAYER_NAMES))})"
                )
            if isinstance(layer_rules, dict):
                _validate_validation_rules(
                    layer_rules, f"validation_overrides.{layer_name}"
                )

    return warnings_list


def _validate_validation_rules(data: dict, context: str) -> None:
    """Validate validation rule names and severity values.

    Args:
        data: Validation rules dict
        context: Context string for error messages (e.g. "validation")

    Raises:
        ConfigError: If a rule name or severity value is invalid
    """
    for rule_name, severity_val in data.items():
        if rule_name not in _VALID_RULE_NAMES:
            raise ConfigError(
                f"Unknown validation rule '{rule_name}' in {context} "
                f"(valid rules: {', '.join(sorted(_VALID_RULE_NAMES))})"
            )
        severity_str = str(severity_val).lower()
        if severity_str not in _VALID_SEVERITY_VALUES:
            raise ConfigError(
                f"Invalid severity '{severity_val}' for {context}.{rule_name} "
                f"(valid values: {', '.join(sorted(_VALID_SEVERITY_VALUES))})"
            )


@dataclass
class LayerValidationConfig:
    """Layer-specific validation overrides."""

    orphan_models: RuleSeverity | None = None
    unimplemented_concepts: RuleSeverity | None = None
    missing_definitions: RuleSeverity | None = None


@dataclass
class ValidationConfig:
    """Validation rule configuration with defaults and layer overrides."""

    # Default severities
    orphan_models: RuleSeverity = RuleSeverity.WARN
    unimplemented_concepts: RuleSeverity = RuleSeverity.WARN
    missing_definitions: RuleSeverity = RuleSeverity.IGNORE

    # Layer-specific overrides
    gold: LayerValidationConfig = field(default_factory=LayerValidationConfig)

    def get_severity(self, rule: str, layer: str | None = None) -> RuleSeverity:
        """Get effective severity for a rule, considering layer overrides.

        Args:
            rule: Rule name (e.g., 'orphan_models')
            layer: Optional layer name (e.g., 'gold')

        Returns:
            Effective RuleSeverity for the rule
        """
        # Start with default
        default_severity = getattr(self, rule, RuleSeverity.WARN)

        # Check for layer override
        if layer == "gold" and self.gold:
            layer_override: RuleSeverity | None = getattr(self.gold, rule, None)
            if layer_override is not None:
                return layer_override

        return default_severity


@dataclass
class Config:
    """Configuration for dbt-conceptual.

    Configuration is loaded from dbt_project.yml vars.dbt_conceptual,
    with legacy fallback to conceptual.yml config section.
    """

    project_dir: Path
    gold_paths: list = field(default_factory=lambda: ["models/marts/**/*.yml"])
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    @property
    def conceptual_file(self) -> Path:
        """Get the path to conceptual.yml in project root."""
        return self.project_dir / "conceptual.yml"

    @property
    def dbt_project_file(self) -> Path:
        """Get the path to dbt_project.yml in project root."""
        return self.project_dir / "dbt_project.yml"

    @property
    def layout_file(self) -> Path:
        """Get the path to conceptual_layout.json."""
        return self.project_dir / "conceptual_layout.json"

    @classmethod
    def load(
        cls,
        project_dir: Path | None = None,
        gold_paths: list | None = None,
    ) -> Config:
        """Load configuration with precedence: CLI > dbt_project.yml > legacy > defaults.

        Priority:
            1. CLI flags (gold_paths parameter)
            2. dbt_project.yml vars.dbt_conceptual block
            3. Legacy: conceptual.yml config section (with deprecation warning)
            4. Built-in defaults

        Args:
            project_dir: Project directory (defaults to cwd)
            gold_paths: CLI override for gold layer paths

        Returns:
            Config instance
        """
        if project_dir is None:
            project_dir = Path.cwd()
        else:
            project_dir = Path(project_dir)

        # Start with defaults
        config_gold_paths: list = ["models/marts/**/*.yml"]
        validation_config = ValidationConfig()

        # 1. Try dbt_project.yml vars.dbt_conceptual
        dbt_project_file = project_dir / "dbt_project.yml"
        loaded_from_dbt_project = False

        if dbt_project_file.exists():
            dbt_data = yaml.safe_load(dbt_project_file.read_text())

            if dbt_data and isinstance(dbt_data.get("vars"), dict):
                dbc_vars = dbt_data["vars"].get("dbt_conceptual")
                if isinstance(dbc_vars, dict):
                    loaded_from_dbt_project = True
                    config_gold_paths, validation_config = cls._parse_config_block(
                        dbc_vars
                    )

        # 2. Legacy fallback: conceptual.yml config section
        if not loaded_from_dbt_project:
            conceptual_file = project_dir / "conceptual.yml"
            if conceptual_file.exists():
                data = yaml.safe_load(conceptual_file.read_text())

                if data and "config" in data:
                    warnings.warn(
                        "Config in conceptual.yml is deprecated. "
                        "Move to dbt_project.yml vars.dbt_conceptual.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    config_gold_paths, validation_config = cls._parse_legacy_config(
                        data["config"]
                    )

        # 3. CLI overrides (highest priority)
        if gold_paths is not None:
            config_gold_paths = gold_paths

        return cls(
            project_dir=project_dir,
            gold_paths=config_gold_paths,
            validation=validation_config,
        )

    @classmethod
    def _parse_config_block(cls, data: dict) -> tuple:
        """Parse config from dbt_project.yml vars.dbt_conceptual block.

        The new format uses flat keys:
            scan:
              gold: [...]
            validation:
              orphan_models: warn
            validation_overrides:
              gold:
                orphan_models: error

        Args:
            data: The vars.dbt_conceptual dict

        Returns:
            Tuple of (gold_paths, validation_config)
        """
        # Validate schema (warnings for unknown keys, errors for bad values)
        schema_warnings = _validate_config_schema(data)
        for msg in schema_warnings:
            warnings.warn(msg, UserWarning, stacklevel=3)

        # Parse scan paths
        gold_paths: list = ["models/marts/**/*.yml"]
        scan_data = data.get("scan")
        if isinstance(scan_data, dict):
            gold_val = scan_data.get("gold")
            if isinstance(gold_val, list):
                gold_paths = gold_val
            elif isinstance(gold_val, str):
                gold_paths = [gold_val]

        # Parse flat validation defaults
        validation_config = ValidationConfig()
        validation_data = data.get("validation")
        if isinstance(validation_data, dict):
            validation_config = cls._parse_flat_validation(validation_data)

        # Parse layer overrides
        overrides_data = data.get("validation_overrides")
        if isinstance(overrides_data, dict):
            gold_overrides = overrides_data.get("gold")
            if isinstance(gold_overrides, dict):
                validation_config.gold = cls._parse_layer_validation(gold_overrides)

        return gold_paths, validation_config

    @classmethod
    def _parse_flat_validation(cls, data: dict) -> ValidationConfig:
        """Parse flat validation rules (new format).

        New format:
            validation:
              orphan_models: warn
              unimplemented_concepts: warn

        Args:
            data: Flat validation rules dict

        Returns:
            ValidationConfig with defaults set
        """
        severity_map = {
            "error": RuleSeverity.ERROR,
            "warn": RuleSeverity.WARN,
            "ignore": RuleSeverity.IGNORE,
        }

        config = ValidationConfig()
        for rule_name in _VALID_RULE_NAMES:
            if rule_name in data:
                severity_str = str(data[rule_name]).lower()
                if severity_str in severity_map:
                    if rule_name == "orphan_models":
                        config.orphan_models = severity_map[severity_str]
                    elif rule_name == "unimplemented_concepts":
                        config.unimplemented_concepts = severity_map[severity_str]
                    elif rule_name == "missing_definitions":
                        config.missing_definitions = severity_map[severity_str]

        return config

    @classmethod
    def _parse_layer_validation(cls, data: dict) -> LayerValidationConfig:
        """Parse layer-specific validation overrides.

        Args:
            data: Layer validation rules dict

        Returns:
            LayerValidationConfig with overrides set
        """
        severity_map = {
            "error": RuleSeverity.ERROR,
            "warn": RuleSeverity.WARN,
            "ignore": RuleSeverity.IGNORE,
        }

        config = LayerValidationConfig()
        for rule_name in _VALID_RULE_NAMES:
            if rule_name in data:
                severity_str = str(data[rule_name]).lower()
                if severity_str in severity_map:
                    if rule_name == "orphan_models":
                        config.orphan_models = severity_map[severity_str]
                    elif rule_name == "unimplemented_concepts":
                        config.unimplemented_concepts = severity_map[severity_str]
                    elif rule_name == "missing_definitions":
                        config.missing_definitions = severity_map[severity_str]

        return config

    @classmethod
    def _parse_legacy_config(cls, config_section: dict) -> tuple:
        """Parse legacy config from conceptual.yml config section.

        Legacy format:
            config:
              scan:
                gold: [...]
              validation:
                defaults:
                  orphan_models: warn
                gold:
                  orphan_models: error

        Args:
            config_section: The config section from conceptual.yml

        Returns:
            Tuple of (gold_paths, validation_config)
        """
        # Parse scan paths
        gold_paths: list = ["models/marts/**/*.yml"]
        if "scan" in config_section:
            scan_config = config_section["scan"]
            if "gold" in scan_config:
                gold_val = scan_config["gold"]
                if isinstance(gold_val, list):
                    gold_paths = gold_val
                elif isinstance(gold_val, str):
                    gold_paths = [gold_val]

        # Parse validation config (legacy format with defaults/gold sections)
        validation_config = ValidationConfig()
        if "validation" in config_section:
            validation_config = cls._parse_validation_config(
                config_section["validation"]
            )

        return gold_paths, validation_config

    @classmethod
    def _parse_validation_config(cls, data: dict) -> ValidationConfig:
        """Parse validation config from YAML data (legacy format).

        Legacy format uses nested defaults/gold sections:
            validation:
              defaults:
                orphan_models: error
              gold:
                orphan_models: error

        Args:
            data: Validation config dict from YAML

        Returns:
            ValidationConfig instance
        """
        severity_map = {
            "error": RuleSeverity.ERROR,
            "warn": RuleSeverity.WARN,
            "ignore": RuleSeverity.IGNORE,
        }

        config = ValidationConfig()

        # Parse defaults section
        defaults = data.get("defaults", {})
        for rule_name in [
            "orphan_models",
            "unimplemented_concepts",
            "missing_definitions",
        ]:
            if rule_name in defaults:
                severity_str = str(defaults[rule_name]).lower()
                if severity_str in severity_map:
                    if rule_name == "orphan_models":
                        config.orphan_models = severity_map[severity_str]
                    elif rule_name == "unimplemented_concepts":
                        config.unimplemented_concepts = severity_map[severity_str]
                    elif rule_name == "missing_definitions":
                        config.missing_definitions = severity_map[severity_str]

        # Parse gold layer overrides
        gold_data = data.get("gold", {})
        if gold_data:
            gold_config = LayerValidationConfig()
            for rule_name in [
                "orphan_models",
                "unimplemented_concepts",
                "missing_definitions",
            ]:
                if rule_name in gold_data:
                    severity_str = str(gold_data[rule_name]).lower()
                    if severity_str in severity_map:
                        if rule_name == "orphan_models":
                            gold_config.orphan_models = severity_map[severity_str]
                        elif rule_name == "unimplemented_concepts":
                            gold_config.unimplemented_concepts = severity_map[
                                severity_str
                            ]
                        elif rule_name == "missing_definitions":
                            gold_config.missing_definitions = severity_map[severity_str]
            config.gold = gold_config

        return config

    def get_layer(self, model_path: str) -> str | None:
        """Detect layer from path.

        For v1.0, only gold layer is supported.

        Args:
            model_path: Path to the model

        Returns:
            'gold' if path matches gold paths, None otherwise
        """
        for pattern in self.gold_paths:
            # Handle glob patterns
            if fnmatch.fnmatch(model_path, pattern):
                return "gold"
            # Also check if path starts with the non-glob portion
            base_pattern = pattern.split("*")[0].rstrip("/")
            if base_pattern and model_path.startswith(base_pattern):
                return "gold"

        return None
