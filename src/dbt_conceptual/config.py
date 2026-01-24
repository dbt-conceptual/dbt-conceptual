"""Configuration management for dbt-conceptual."""

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
class TagValidationConfig:
    """Tag validation configuration.

    Controls validation of domain/owner tags on dbt models.
    """

    enabled: bool = False
    domains_allow_multiple: bool = True
    domains_format: str = "standard"  # "standard" or "databricks"


@dataclass
class ValidationConfig:
    """Validation rule configuration."""

    orphan_models: RuleSeverity = RuleSeverity.WARN
    unimplemented_concepts: RuleSeverity = RuleSeverity.WARN
    unrealized_relationships: RuleSeverity = RuleSeverity.WARN
    missing_definitions: RuleSeverity = RuleSeverity.IGNORE
    domain_mismatch: RuleSeverity = RuleSeverity.WARN
    tag_validation: TagValidationConfig = field(default_factory=TagValidationConfig)


@dataclass
class Config:
    """Configuration for dbt-conceptual."""

    project_dir: Path
    conceptual_path: str = "models/conceptual"
    bronze_paths: list[str] = field(
        default_factory=lambda: ["models/bronze", "models/raw"]
    )
    silver_paths: list[str] = field(default_factory=lambda: ["models/silver"])
    gold_paths: list[str] = field(default_factory=lambda: ["models/gold"])
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    @property
    def conceptual_file(self) -> Path:
        """Get the path to conceptual.yml."""
        return self.project_dir / self.conceptual_path / "conceptual.yml"

    @property
    def layout_file(self) -> Path:
        """Get the path to conceptual.layout.json."""
        return self.project_dir / self.conceptual_path / "conceptual.layout.json"

    @classmethod
    def load(
        cls,
        project_dir: Optional[Path] = None,
        conceptual_path: Optional[str] = None,
        bronze_paths: Optional[list[str]] = None,
        silver_paths: Optional[list[str]] = None,
        gold_paths: Optional[list[str]] = None,
    ) -> "Config":
        """Load configuration from dbt_project.yml and CLI overrides.

        Priority: CLI flags > dbt_project.yml > defaults
        """
        if project_dir is None:
            project_dir = Path.cwd()
        else:
            project_dir = Path(project_dir)

        # Start with defaults
        config_data: dict[str, object] = {
            "conceptual_path": "models/conceptual",
            "bronze_paths": ["models/bronze", "models/raw"],
            "silver_paths": ["models/silver"],
            "gold_paths": ["models/gold"],
        }
        validation_data: dict[str, str] = {}

        # Try to load from dbt_project.yml
        dbt_project_file = project_dir / "dbt_project.yml"
        if dbt_project_file.exists():
            with open(dbt_project_file) as f:
                dbt_project = yaml.safe_load(f)
                if dbt_project and "vars" in dbt_project:
                    dbt_conceptual_vars = dbt_project["vars"].get("dbt_conceptual", {})
                    # Extract validation config separately
                    if "validation" in dbt_conceptual_vars:
                        validation_data = dbt_conceptual_vars.pop("validation")
                    config_data.update(dbt_conceptual_vars)

        # Apply CLI overrides
        if conceptual_path is not None:
            config_data["conceptual_path"] = conceptual_path
        if bronze_paths is not None:
            config_data["bronze_paths"] = bronze_paths
        if silver_paths is not None:
            config_data["silver_paths"] = silver_paths
        if gold_paths is not None:
            config_data["gold_paths"] = gold_paths

        # Build validation config
        validation_config = cls._parse_validation_config(validation_data)

        # Cast to expected types
        bronze = config_data["bronze_paths"]
        silver = config_data["silver_paths"]
        gold = config_data["gold_paths"]

        return cls(
            project_dir=project_dir,
            conceptual_path=str(config_data["conceptual_path"]),
            bronze_paths=bronze if isinstance(bronze, list) else [str(bronze)],
            silver_paths=silver if isinstance(silver, list) else [str(silver)],
            gold_paths=gold if isinstance(gold, list) else [str(gold)],
            validation=validation_config,
        )

    @classmethod
    def _parse_validation_config(cls, data: dict) -> ValidationConfig:
        """Parse validation config from YAML data."""
        config = ValidationConfig()

        severity_map = {
            "error": RuleSeverity.ERROR,
            "warn": RuleSeverity.WARN,
            "ignore": RuleSeverity.IGNORE,
        }

        for rule_name in [
            "orphan_models",
            "unimplemented_concepts",
            "unrealized_relationships",
            "missing_definitions",
            "domain_mismatch",
        ]:
            if rule_name in data:
                severity_str = str(data[rule_name]).lower()
                if severity_str in severity_map:
                    setattr(config, rule_name, severity_map[severity_str])

        # Parse tag_validation config
        if "tag_validation" in data:
            tag_data = data["tag_validation"]
            if isinstance(tag_data, dict):
                tag_config = TagValidationConfig(
                    enabled=tag_data.get("enabled", False),
                    domains_allow_multiple=(
                        tag_data.get("domains", {}).get("allow_multiple", True)
                        if isinstance(tag_data.get("domains"), dict)
                        else True
                    ),
                    domains_format=(
                        tag_data.get("domains", {}).get("format", "standard")
                        if isinstance(tag_data.get("domains"), dict)
                        else "standard"
                    ),
                )
                config.tag_validation = tag_config

        return config

    def get_layer(self, model_path: str) -> Optional[str]:
        """Detect layer from path. Returns 'bronze', 'silver', 'gold', or None."""
        # Check bronze paths first
        for path in self.bronze_paths:
            if model_path.startswith(path):
                return "bronze"
        # Then silver paths
        for path in self.silver_paths:
            if model_path.startswith(path):
                return "silver"
        # Then gold paths
        for path in self.gold_paths:
            if model_path.startswith(path):
                return "gold"
        return None

    def get_model_type(self, model_name: str) -> str:
        """Detect model type from name prefix."""
        if model_name.startswith("dim_"):
            return "dimension"
        elif model_name.startswith("fact_"):
            return "fact"
        elif model_name.startswith("bridge_"):
            return "bridge"
        elif model_name.startswith("ref_"):
            return "reference"
        return "unknown"
