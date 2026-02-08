"""Scanner for finding dbt model files in a project.

v1.0: Only scans gold layer paths for models.
"""

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any, TypedDict

import yaml

from dbt_conceptual.config import Config

logger = logging.getLogger(__name__)


class ScannedModel(TypedDict):
    """Typed structure for a model extracted from a dbt schema file.

    All keys are always present in the output of extract_models_from_schema.
    """

    name: str
    description: Any  # str or None
    meta: dict
    path: str
    file: str
    tags: list
    databricks_tags: dict


class DbtProjectScanner:
    """Scans a dbt project for model files in gold layer paths."""

    def __init__(self, config: Config):
        """Initialize the scanner.

        Args:
            config: Configuration object
        """
        self.config = config

    def find_schema_files(self) -> Iterator[Path]:
        """Find all schema.yml files matching gold layer paths.

        Yields:
            Path objects for each found schema YAML file
        """
        project_dir = self.config.project_dir

        for pattern in self.config.gold_paths:
            # Handle glob patterns
            if "*" in pattern:
                # Use glob to find matching files
                yield from project_dir.glob(pattern)
            else:
                # Direct path
                full_path = project_dir / pattern
                if full_path.is_file():
                    yield full_path
                elif full_path.is_dir():
                    # Find all .yml and .yaml files in directory
                    yield from full_path.rglob("*.yml")
                    yield from full_path.rglob("*.yaml")

    def load_schema_file(self, schema_file: Path) -> dict:
        """Load and parse a schema YAML file.

        Args:
            schema_file: Path to the schema file

        Returns:
            Parsed YAML content as a dictionary
        """
        content = yaml.safe_load(schema_file.read_text())
        return content or {}

    def extract_models_from_schema(
        self, schema_data: dict, file_path: Path
    ) -> list[ScannedModel]:
        """Extract model definitions from a parsed schema file.

        Args:
            schema_data: Parsed schema YAML content
            file_path: Path to the schema file (for computing relative paths)

        Returns:
            List of ScannedModel dicts with name, meta, and path information
        """
        models: list[ScannedModel] = []
        if "models" not in schema_data:
            return models

        # Calculate relative path from project root
        try:
            rel_path = file_path.relative_to(self.config.project_dir)
        except ValueError:
            rel_path = file_path

        for model in schema_data.get("models", []):
            if not isinstance(model, dict):
                continue

            model_name = model.get("name")
            if not model_name:
                continue

            meta = model.get("meta", {})
            description = model.get("description")

            # Extract tags for databricks support
            config = model.get("config", {})
            tags = model.get("tags", []) or config.get("tags", [])
            if not isinstance(tags, list):
                tags = []

            # Extract databricks_tags for Unity Catalog format
            databricks_tags = config.get("databricks_tags", {})
            if not isinstance(databricks_tags, dict):
                databricks_tags = {}

            models.append(
                ScannedModel(
                    name=model_name,
                    description=description,
                    meta=meta,
                    path=str(rel_path),
                    file=str(file_path),
                    tags=tags,
                    databricks_tags=databricks_tags,
                )
            )

        return models

    def scan(self) -> list[ScannedModel]:
        """Scan the dbt project for models in gold layer paths.

        Returns:
            List of all ScannedModel dicts found with their metadata
        """
        all_models: list[ScannedModel] = []
        seen_files: set[Path] = set()

        for schema_file in self.find_schema_files():
            # Avoid processing the same file twice (glob patterns may overlap)
            resolved = schema_file.resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)

            try:
                schema_data = self.load_schema_file(schema_file)
                models = self.extract_models_from_schema(schema_data, schema_file)
                all_models.extend(models)
            except yaml.YAMLError as e:
                logger.warning("Failed to parse %s: %s", schema_file, e)
            except OSError as e:
                logger.warning("Failed to read %s: %s", schema_file, e)
            except (KeyError, TypeError, ValueError) as e:
                logger.warning("Malformed schema in %s: %s", schema_file, e)

        return all_models
