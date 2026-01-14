"""Scanner for finding dbt model files in a project."""

from collections.abc import Iterator
from pathlib import Path

import yaml

from dbt_conceptual.config import Config


class DbtProjectScanner:
    """Scans a dbt project for model files."""

    def __init__(self, config: Config):
        """Initialize the scanner.

        Args:
            config: Configuration object
        """
        self.config = config

    def find_schema_files(self) -> Iterator[Path]:
        """Find all schema.yml files in the project.

        Yields:
            Path objects for each found schema YAML file
        """
        project_dir = self.config.project_dir

        # Search in configured silver and gold paths
        search_paths = self.config.silver_paths + self.config.gold_paths

        for search_path in search_paths:
            full_path = project_dir / search_path
            if full_path.exists():
                # Find all .yml and .yaml files
                yield from full_path.rglob("*.yml")
                yield from full_path.rglob("*.yaml")

    def load_schema_file(self, schema_file: Path) -> dict:
        """Load and parse a schema YAML file.

        Args:
            schema_file: Path to the schema file

        Returns:
            Parsed YAML content as a dictionary
        """
        with open(schema_file) as f:
            content = yaml.safe_load(f)
            return content or {}

    def extract_models_from_schema(
        self, schema_data: dict, file_path: Path
    ) -> list[dict]:
        """Extract model definitions from a parsed schema file.

        Args:
            schema_data: Parsed schema YAML content
            file_path: Path to the schema file (for computing relative paths)

        Returns:
            List of model dictionaries with name, meta, and path information
        """
        models: list[dict] = []
        if "models" not in schema_data:
            return models

        # Calculate relative path from project root
        rel_path = file_path.relative_to(self.config.project_dir).parent

        for model in schema_data.get("models", []):
            if not isinstance(model, dict):
                continue

            model_name = model.get("name")
            if not model_name:
                continue

            meta = model.get("meta", {})

            # Determine layer
            layer = self.config.get_layer(str(rel_path))

            # Determine model type
            model_type = self.config.get_model_type(model_name)

            models.append(
                {
                    "name": model_name,
                    "meta": meta,
                    "path": str(rel_path),
                    "layer": layer,
                    "type": model_type,
                    "file": str(file_path),
                }
            )

        return models

    def scan(self) -> list[dict]:
        """Scan the entire dbt project for models with meta tags.

        Returns:
            List of all models found with their metadata
        """
        all_models = []

        for schema_file in self.find_schema_files():
            try:
                schema_data = self.load_schema_file(schema_file)
                models = self.extract_models_from_schema(schema_data, schema_file)
                all_models.extend(models)
            except yaml.YAMLError as e:
                # Log warning but continue scanning
                print(f"Warning: Failed to parse {schema_file}: {e}")
            except Exception as e:
                # Log warning but continue scanning
                print(f"Warning: Error processing {schema_file}: {e}")

        return all_models
