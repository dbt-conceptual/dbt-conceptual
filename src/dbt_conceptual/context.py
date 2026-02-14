"""Context resolution engine for dbt-conceptual.

Assembles full context for a concept by merging:
- Layer 1: Conceptual model definitions (conceptual.yml)
- Layer 2: dbt manifest.json (models, tests, dependencies)
- Layer 3: dbt catalog.json (row counts, column types)
- Layer 4: Data contracts (future - enforcement mode, checks)
- Layer 5: Heuristic inferences (grain, risk, patterns)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dbt_conceptual.config import Config
from dbt_conceptual.constraint_translator import ConstraintTranslator
from dbt_conceptual.inference import Inference, InferenceEngine
from dbt_conceptual.parser import ConceptualModelParser
from dbt_conceptual.state import ConceptState, Guidance, RelationshipState

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """Column metadata from manifest and catalog."""

    name: str
    type: str | None = None  # From catalog
    description: str | None = None  # From manifest


@dataclass
class ModelContext:
    """Enriched model information combining all layers."""

    name: str
    description: str | None = None
    materialization: str | None = None
    schema: str | None = None
    columns: list[ColumnInfo] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)  # Translated test constraints
    row_count: int | None = None  # From catalog
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    inferences: list[Inference] = field(default_factory=list)
    path: str | None = None


@dataclass
class ContextMetadata:
    """Source attribution for context assembly."""

    conceptual_file: str
    manifest_file: str | None = None
    catalog_file: str | None = None
    contract_file: str | None = None


@dataclass
class FullContext:
    """Complete assembled context for a concept.

    Combines conceptual model definitions with dbt project metadata
    and heuristic inferences.
    """

    concept_key: str
    concept: ConceptState
    models: list[ModelContext] = field(default_factory=list)
    relationships: list[RelationshipState] = field(default_factory=list)
    guidance: Guidance | None = None
    inferences: list[Inference] = field(default_factory=list)
    metadata: ContextMetadata | None = None


class ContextResolver:
    """Resolves full context for concepts by assembling multiple data sources."""

    def __init__(self, config: Config):
        """Initialize the context resolver.

        Args:
            config: Configuration object
        """
        self.config = config
        self.parser = ConceptualModelParser(config)
        self.constraint_translator = ConstraintTranslator()
        self.inference_engine = InferenceEngine()

        # Cached data
        self._manifest_cache: dict[str, Any] | None = None
        self._catalog_cache: dict[str, Any] | None = None

    def resolve_full_context(self, concept_key: str) -> FullContext:
        """Resolve full context for a single concept.

        Args:
            concept_key: The concept identifier to resolve

        Returns:
            FullContext with all layers assembled

        Raises:
            ValueError: If concept is not found in conceptual model
        """
        # Layer 1: Parse conceptual model
        state = self.parser.parse()

        if concept_key not in state.concepts:
            raise ValueError(f"Concept '{concept_key}' not found in conceptual model")

        concept = state.concepts[concept_key]

        # Resolve inheritance (concept inherits domain owner if not set)
        if concept.domain and not concept.owner:
            domain = state.domains.get(concept.domain)
            if domain and domain.owner:
                concept.owner = domain.owner

        # Layer 2-5: Load manifest, catalog, and enrich models
        manifest = self._load_manifest()
        catalog = self._load_catalog()

        models = self._resolve_models(concept, manifest, catalog)

        # Get relationships related to this concept
        relationships = [
            rel
            for rel in state.relationships.values()
            if rel.from_concept == concept_key or rel.to_concept == concept_key
        ]

        # Build metadata
        metadata = ContextMetadata(
            conceptual_file=str(self.config.conceptual_file),
            manifest_file=str(self._get_manifest_path()) if manifest else None,
            catalog_file=str(self._get_catalog_path()) if catalog else None,
        )

        return FullContext(
            concept_key=concept_key,
            concept=concept,
            models=models,
            relationships=relationships,
            guidance=concept.guidance,
            metadata=metadata,
        )

    def _resolve_models(
        self,
        concept: ConceptState,
        manifest: dict[str, Any] | None,
        catalog: dict[str, Any] | None,
    ) -> list[ModelContext]:
        """Resolve model contexts for a concept.

        Args:
            concept: The concept state
            manifest: dbt manifest.json data
            catalog: dbt catalog.json data

        Returns:
            List of enriched ModelContext objects
        """
        models: list[ModelContext] = []

        for model_name in concept.models:
            model_ctx = self._build_model_context(model_name, manifest, catalog)
            models.append(model_ctx)

        return models

    def _build_model_context(
        self,
        model_name: str,
        manifest: dict[str, Any] | None,
        catalog: dict[str, Any] | None,
    ) -> ModelContext:
        """Build enriched context for a single model.

        Args:
            model_name: The model name
            manifest: dbt manifest.json data
            catalog: dbt catalog.json data

        Returns:
            ModelContext with all layers assembled
        """
        model_ctx = ModelContext(name=model_name)

        # Layer 2: Extract from manifest
        if manifest:
            self._enrich_from_manifest(model_ctx, model_name, manifest)

        # Layer 3: Extract from catalog
        if catalog:
            self._enrich_from_catalog(model_ctx, model_name, catalog)

        # Layer 5: Run inference engine
        model_metadata = self._build_inference_metadata(model_ctx, manifest)
        inferences = self.inference_engine.infer(model_metadata)
        model_ctx.inferences = inferences

        return model_ctx

    def _enrich_from_manifest(
        self, model_ctx: ModelContext, model_name: str, manifest: dict[str, Any]
    ) -> None:
        """Enrich model context from manifest.json.

        Args:
            model_ctx: ModelContext to enrich (modified in place)
            model_name: The model name
            manifest: dbt manifest.json data
        """
        nodes = manifest.get("nodes", {})

        # Find the model node (try common prefixes)
        model_node = None
        for prefix in ["model.", f"model.{self._get_project_name(manifest)}"]:
            full_name = f"{prefix}.{model_name}"
            if full_name in nodes:
                model_node = nodes[full_name]
                break

        if not model_node:
            logger.debug(f"Model '{model_name}' not found in manifest")
            return

        # Extract basic metadata
        model_ctx.description = model_node.get("description")
        model_ctx.materialization = model_node.get("config", {}).get("materialized")
        model_ctx.schema = model_node.get("schema")
        model_ctx.path = model_node.get("original_file_path")

        # Extract columns
        columns_data = model_node.get("columns", {})
        for col_name, col_data in columns_data.items():
            column = ColumnInfo(
                name=col_name,
                description=col_data.get("description"),
            )
            model_ctx.columns.append(column)

        # Extract dependencies
        depends_on = model_node.get("depends_on", {})
        model_ctx.upstream = depends_on.get("nodes", [])

        # Extract and translate tests
        self._extract_tests(model_ctx, model_name, manifest)

        # Calculate downstream count
        model_ctx.downstream = self._calculate_downstream(model_name, manifest)

    def _extract_tests(
        self, model_ctx: ModelContext, model_name: str, manifest: dict[str, Any]
    ) -> None:
        """Extract and translate tests for a model.

        Args:
            model_ctx: ModelContext to enrich (modified in place)
            model_name: The model name
            manifest: dbt manifest.json data
        """
        nodes = manifest.get("nodes", {})

        # Find all test nodes that reference this model
        for node_id, node in nodes.items():
            if not node_id.startswith("test."):
                continue

            attached_node = node.get("attached_node")
            if not attached_node:
                continue

            # Check if test is attached to this model
            if model_name not in attached_node:
                continue

            # Translate test to natural language constraint
            constraint = self.constraint_translator.translate_test(node)
            model_ctx.constraints.append(constraint)

    def _calculate_downstream(
        self, model_name: str, manifest: dict[str, Any]
    ) -> list[str]:
        """Calculate downstream dependencies for a model.

        Args:
            model_name: The model name
            manifest: dbt manifest.json data

        Returns:
            List of downstream model names
        """
        nodes = manifest.get("nodes", {})
        downstream: list[str] = []

        # Find our model's full node ID
        our_node_id = None
        for node_id in nodes:
            if model_name in node_id and node_id.startswith("model."):
                our_node_id = node_id
                break

        if not our_node_id:
            return downstream

        # Scan all nodes to find those that depend on us
        for node_id, node in nodes.items():
            if not node_id.startswith("model."):
                continue

            depends_on = node.get("depends_on", {}).get("nodes", [])
            if our_node_id in depends_on:
                # Extract model name from node_id
                name = node.get("name")
                if name:
                    downstream.append(name)

        return downstream

    def _enrich_from_catalog(
        self, model_ctx: ModelContext, model_name: str, catalog: dict[str, Any]
    ) -> None:
        """Enrich model context from catalog.json.

        Args:
            model_ctx: ModelContext to enrich (modified in place)
            model_name: The model name
            catalog: dbt catalog.json data
        """
        nodes = catalog.get("nodes", {})

        # Find the model node
        model_node = None
        for node_id, node in nodes.items():
            if model_name in node_id and node_id.startswith("model."):
                model_node = node
                break

        if not model_node:
            logger.debug(f"Model '{model_name}' not found in catalog")
            return

        # Extract row count
        stats = model_node.get("stats", {})
        row_count_stat = stats.get("row_count")
        if row_count_stat and "value" in row_count_stat:
            try:
                model_ctx.row_count = int(row_count_stat["value"])
            except (ValueError, TypeError):
                pass

        # Enrich column types
        catalog_columns = model_node.get("columns", {})
        for column in model_ctx.columns:
            if column.name in catalog_columns:
                col_data = catalog_columns[column.name]
                column.type = col_data.get("type")

    def _build_inference_metadata(
        self, model_ctx: ModelContext, manifest: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Build metadata dict for inference engine.

        Args:
            model_ctx: The model context
            manifest: dbt manifest.json data

        Returns:
            Metadata dict for InferenceEngine.infer()
        """
        # Convert constraints back to test-like structure for inference
        # This is a simplified representation
        tests = []
        for constraint in model_ctx.constraints:
            # Extract test type from constraint text
            if "must be unique" in constraint:
                tests.append({"unique": {"column_name": constraint.split()[0]}})
            elif "combination of" in constraint and "must be unique" in constraint:
                # Parse composite unique
                # Format: "combination of (col1, col2) must be unique"
                parts = constraint.split("combination of (")
                if len(parts) > 1:
                    cols_str = parts[1].split(")")[0]
                    cols = [c.strip() for c in cols_str.split(",")]
                    tests.append(
                        {
                            "dbt_utils.unique_combination_of_columns": {
                                "combination_of_columns": cols  # type: ignore[dict-item]
                            }
                        }
                    )

        return {
            "name": model_ctx.name,
            "tests": tests,
            "materialization": model_ctx.materialization or "",
            "depends_on": model_ctx.upstream,
            "downstream_count": len(model_ctx.downstream),
            "description": model_ctx.description,
            "path": model_ctx.path or "",
        }

    def _load_manifest(self) -> dict[str, Any] | None:
        """Load dbt manifest.json file.

        Returns:
            Parsed manifest data or None if not found
        """
        if self._manifest_cache is not None:
            return self._manifest_cache

        manifest_path = self._get_manifest_path()
        if not manifest_path.exists():
            logger.debug("manifest.json not found")
            self._manifest_cache = None
            return None

        try:
            with open(manifest_path) as f:
                self._manifest_cache = json.load(f)
                return self._manifest_cache
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load manifest.json: {e}")
            self._manifest_cache = None
            return None

    def _load_catalog(self) -> dict[str, Any] | None:
        """Load dbt catalog.json file.

        Returns:
            Parsed catalog data or None if not found
        """
        if self._catalog_cache is not None:
            return self._catalog_cache

        catalog_path = self._get_catalog_path()
        if not catalog_path.exists():
            logger.debug("catalog.json not found (optional)")
            self._catalog_cache = None
            return None

        try:
            with open(catalog_path) as f:
                self._catalog_cache = json.load(f)
                return self._catalog_cache
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load catalog.json: {e}")
            self._catalog_cache = None
            return None

    def _get_manifest_path(self) -> Path:
        """Get path to manifest.json file.

        Returns:
            Path to manifest.json in target/ directory
        """
        return self.config.project_dir / "target" / "manifest.json"

    def _get_catalog_path(self) -> Path:
        """Get path to catalog.json file.

        Returns:
            Path to catalog.json in target/ directory
        """
        return self.config.project_dir / "target" / "catalog.json"

    def _get_project_name(self, manifest: dict[str, Any]) -> str:
        """Get project name from manifest metadata.

        Args:
            manifest: dbt manifest.json data

        Returns:
            Project name or empty string if not found
        """
        metadata = manifest.get("metadata", {})
        return str(metadata.get("project_name", ""))


def resolve_full_context(config: Config, concept_key: str) -> FullContext:
    """Convenience function to resolve full context for a concept.

    Args:
        config: Configuration object
        concept_key: The concept identifier

    Returns:
        FullContext with all layers assembled

    Raises:
        ValueError: If concept is not found
    """
    resolver = ContextResolver(config)
    return resolver.resolve_full_context(concept_key)
