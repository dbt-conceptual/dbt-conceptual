"""Configuration management for dbt-conceptual.

All configuration is loaded from conceptual.yml in the project root.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


class RuleSeverity(Enum):
    """Configurable validation rule severity."""

    ERROR = "error"
    WARN = "warn"
    IGNORE = "ignore"


@dataclass
class LayerValidationConfig:
    """Layer-specific validation overrides."""

    orphan_models: Optional[RuleSeverity] = None
    unimplemented_concepts: Optional[RuleSeverity] = None
    missing_definitions: Optional[RuleSeverity] = None


@dataclass
class ValidationConfig:
    """Validation rule configuration with defaults and layer overrides."""

    # Default severities
    orphan_models: RuleSeverity = RuleSeverity.WARN
    unimplemented_concepts: RuleSeverity = RuleSeverity.WARN
    missing_definitions: RuleSeverity = RuleSeverity.IGNORE

    # Layer-specific overrides
    gold: LayerValidationConfig = field(default_factory=LayerValidationConfig)

    def get_severity(self, rule: str, layer: Optional[str] = None) -> RuleSeverity:
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
            layer_override: Optional[RuleSeverity] = getattr(self.gold, rule, None)
            if layer_override is not None:
                return layer_override

        return default_severity


@dataclass
class Config:
    """Configuration for dbt-conceptual.

    All configuration is loaded from conceptual.yml in the project root.
    """

    project_dir: Path
    gold_paths: list[str] = field(default_factory=lambda: ["models/marts/**/*.yml"])
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    @property
    def conceptual_file(self) -> Path:
        """Get the path to conceptual.yml in project root."""
        return self.project_dir / "conceptual.yml"

    @property
    def layout_file(self) -> Path:
        """Get the path to conceptual_layout.json."""
        return self.project_dir / "conceptual_layout.json"

    @classmethod
    def load(
        cls,
        project_dir: Optional[Path] = None,
        gold_paths: Optional[list[str]] = None,
    ) -> "Config":
        """Load configuration from conceptual.yml.

        Priority: CLI flags > conceptual.yml config section > defaults

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
        config_gold_paths: list[str] = ["models/marts/**/*.yml"]
        validation_config = ValidationConfig()

        # Try to load from conceptual.yml
        conceptual_file = project_dir / "conceptual.yml"
        if conceptual_file.exists():
            with open(conceptual_file) as f:
                data = yaml.safe_load(f)

            if data and "config" in data:
                config_section = data["config"]

                # Parse scan paths
                if "scan" in config_section:
                    scan_config = config_section["scan"]
                    if "gold" in scan_config:
                        gold_val = scan_config["gold"]
                        if isinstance(gold_val, list):
                            config_gold_paths = gold_val
                        elif isinstance(gold_val, str):
                            config_gold_paths = [gold_val]

                # Parse validation config
                if "validation" in config_section:
                    validation_config = cls._parse_validation_config(
                        config_section["validation"]
                    )

        # Apply CLI overrides
        if gold_paths is not None:
            config_gold_paths = gold_paths

        return cls(
            project_dir=project_dir,
            gold_paths=config_gold_paths,
            validation=validation_config,
        )

    @classmethod
    def _parse_validation_config(cls, data: dict) -> ValidationConfig:
        """Parse validation config from YAML data.

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
                    setattr(config, rule_name, severity_map[severity_str])

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
                        setattr(gold_config, rule_name, severity_map[severity_str])
            config.gold = gold_config

        return config

    def get_layer(self, model_path: str) -> Optional[str]:
        """Detect layer from path.

        For v1.0, only gold layer is supported.

        Args:
            model_path: Path to the model

        Returns:
            'gold' if path matches gold paths, None otherwise
        """
        import fnmatch

        for pattern in self.gold_paths:
            # Handle glob patterns
            if fnmatch.fnmatch(model_path, pattern):
                return "gold"
            # Also check if path starts with the non-glob portion
            base_pattern = pattern.split("*")[0].rstrip("/")
            if base_pattern and model_path.startswith(base_pattern):
                return "gold"

        return None
