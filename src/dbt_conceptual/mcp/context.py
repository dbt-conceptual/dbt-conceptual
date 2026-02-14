"""Context resolution engine for dbt-conceptual MCP server.

Merges conceptual model definitions with dbt project metadata into unified
FullContext objects for agent consumption. Handles 5 layers of context:

1. Conceptual layer: definitions, domain, guidance, relationships
2. dbt layer: models, tests, materialization, columns, deps
3. Catalog layer: row counts, materialized types (optional)
4. Contract layer: enforcement mode, checks, SLAs (optional)
5. Inference layer: grain, risk, materialization guidance, patterns
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..constraint_translator import translate_test_to_constraint
from ..inference import InferenceEngine
from ..state import ProjectState

logger = logging.getLogger(__name__)


@dataclass
class ConceptContext:
    """Layer 1: Conceptual model definition."""

    name: str
    domain: str | None = None
    owner: str | None = None
    definition: str | None = None  # Markdown definition
    color: str | None = None
    guidance_context: str | None = None  # Guidance.context
    guidance_rules: list[dict[str, str]] = field(
        default_factory=list
    )  # [{name, description}]
    status: str = "stub"  # stub, draft, complete


@dataclass
class RelationshipContext:
    """Relationship information for a concept."""

    verb: str
    from_concept: str
    to_concept: str
    cardinality: str  # 1:1 or 1:N
    definition: str | None = None
    owner: str | None = None


@dataclass
class ColumnInfo:
    """Column metadata from dbt."""

    name: str
    type: str | None = None  # From catalog
    description: str | None = None  # From schema
    constraints: list[str] = field(default_factory=list)  # From tests


@dataclass
class ModelContext:
    """Layer 2: dbt model metadata."""

    name: str
    materialization: str = "view"
    schema: str | None = None
    description: str | None = None
    path: str | None = None
    columns: list[ColumnInfo] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)  # Table-level tests
    upstream: list[str] = field(default_factory=list)  # Depends on
    downstream: list[str] = field(default_factory=list)  # Depended on by
    row_count: int | None = None  # From catalog
    source_freshness_sla: dict[str, Any] | None = None  # From sources


@dataclass
class ContractContext:
    """Layer 4: Data contract metadata (optional)."""

    enforcement_mode: str | None = None  # strict, warn, ignore
    checks: list[str] = field(default_factory=list)
    sla_expectations: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceContext:
    """Layer 5: Heuristic inferences."""

    grain: str | None = None  # Grain inference
    grain_columns: list[str] = field(default_factory=list)
    risk_level: str | None = None  # high, medium, low
    risk_message: str | None = None
    materialization_guidance: str | None = None
    data_vault_pattern: str | None = None
    layer: str | None = None
    quality_warnings: list[str] = field(default_factory=list)


@dataclass
class FullContext:
    """Unified context for one or more concepts.

    Combines all 5 layers into a single object for agent consumption.
    """

    concepts: list[ConceptContext] = field(default_factory=list)
    relationships: list[RelationshipContext] = field(default_factory=list)
    models: dict[str, ModelContext] = field(default_factory=dict)  # Keyed by model name
    contracts: dict[str, ContractContext] = field(
        default_factory=dict
    )  # Keyed by model name
    inferences: dict[str, InferenceContext] = field(
        default_factory=dict
    )  # Keyed by model name


class ContextResolver:
    """Resolves full context for concepts by merging multiple data layers."""

    def __init__(
        self,
        state: ProjectState,
        project_dir: Path,
        manifest: dict[str, Any] | None = None,
        catalog: dict[str, Any] | None = None,
    ):
        """Initialize the context resolver.

        Args:
            state: ProjectState from conceptual.yml + dbt models
            project_dir: Path to dbt project root
            manifest: Parsed manifest.json (optional, will load if not provided)
            catalog: Parsed catalog.json (optional, graceful if missing)
        """
        self.state = state
        self.project_dir = project_dir
        self.manifest = manifest
        self.catalog = catalog
        self.inference_engine = InferenceEngine()

        # Load manifest if not provided
        if self.manifest is None:
            self.manifest = self._load_manifest()

        # Load catalog if not provided (graceful failure)
        if self.catalog is None:
            self.catalog = self._load_catalog()

    def _load_manifest(self) -> dict[str, Any]:
        """Load dbt manifest.json.

        Returns:
            Parsed manifest dict

        Raises:
            FileNotFoundError: If manifest.json doesn't exist
        """
        manifest_path = self.project_dir / "target" / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"manifest.json not found at {manifest_path}. Run 'dbt compile' or 'dbt run' first."
            )

        with open(manifest_path) as f:
            return json.load(f)

    def _load_catalog(self) -> dict[str, Any] | None:
        """Load dbt catalog.json (gracefully handle if missing).

        Returns:
            Parsed catalog dict, or None if file doesn't exist
        """
        catalog_path = self.project_dir / "target" / "catalog.json"
        if not catalog_path.exists():
            logger.info(
                "catalog.json not found. Row counts and materialized types will be unavailable. "
                "Run 'dbt docs generate' to create catalog."
            )
            return None

        try:
            with open(catalog_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load catalog.json: {e}")
            return None

    def resolve_full_context(self, concept_names: set[str]) -> FullContext:
        """Resolve full context for a set of concepts.

        Args:
            concept_names: Set of concept names to resolve

        Returns:
            FullContext object with all 5 layers assembled
        """
        context = FullContext()

        # Layer 1: Conceptual definitions
        for concept_name in concept_names:
            concept_state = self.state.concepts.get(concept_name)
            if not concept_state:
                logger.warning(f"Concept '{concept_name}' not found in state")
                continue

            # Resolve owner from domain if not set
            owner = concept_state.owner
            if not owner and concept_state.domain:
                domain_state = self.state.domains.get(concept_state.domain)
                if domain_state:
                    owner = domain_state.owner

            # Build guidance rules
            guidance_rules = []
            if concept_state.guidance and concept_state.guidance.rules:
                guidance_rules = [
                    {"name": rule.name, "description": rule.description}
                    for rule in concept_state.guidance.rules
                ]

            concept_context = ConceptContext(
                name=concept_state.name,
                domain=concept_state.domain,
                owner=owner,
                definition=concept_state.definition,
                color=concept_state.color,
                guidance_context=(
                    concept_state.guidance.context if concept_state.guidance else None
                ),
                guidance_rules=guidance_rules,
                status=concept_state.status,
            )
            context.concepts.append(concept_context)

        # Add relationships involving these concepts
        for rel_state in self.state.relationships.values():
            if (
                rel_state.from_concept in concept_names
                or rel_state.to_concept in concept_names
            ):
                rel_context = RelationshipContext(
                    verb=rel_state.verb,
                    from_concept=rel_state.from_concept,
                    to_concept=rel_state.to_concept,
                    cardinality=rel_state.cardinality,
                    definition=rel_state.definition,
                    owner=rel_state.owner,
                )
                context.relationships.append(rel_context)

        # Gather all model names for these concepts
        all_model_names: set[str] = set()
        for concept_name in concept_names:
            concept_state = self.state.concepts.get(concept_name)
            if concept_state:
                all_model_names.update(concept_state.models)

        # Layers 2-5: Model metadata, catalog, contracts, inferences
        for model_name in all_model_names:
            model_context = self._resolve_model_context(model_name)
            if model_context:
                context.models[model_name] = model_context

            # Layer 4: Data contracts (stub for now)
            # TODO: Implement contract detection in DBC-56
            context.contracts[model_name] = ContractContext()

            # Layer 5: Heuristic inferences
            inference_context = self._resolve_inference_context(model_name)
            if inference_context:
                context.inferences[model_name] = inference_context

        return context

    def _resolve_model_context(self, model_name: str) -> ModelContext | None:
        """Resolve Layer 2 context for a model.

        Args:
            model_name: Name of the dbt model

        Returns:
            ModelContext or None if model not found in manifest
        """
        if not self.manifest:
            return None

        # Find model node in manifest
        model_node = None
        for _node_id, node in self.manifest.get("nodes", {}).items():
            if node.get("resource_type") == "model" and node.get("name") == model_name:
                model_node = node
                break

        if not model_node:
            logger.warning(f"Model '{model_name}' not found in manifest")
            return None

        # Extract basic metadata
        model_context = ModelContext(
            name=model_name,
            materialization=model_node.get("config", {}).get("materialized", "view"),
            schema=model_node.get("schema"),
            description=model_node.get("description"),
            path=model_node.get("original_file_path"),
        )

        # Extract columns from model node
        columns_data = model_node.get("columns", {})
        for col_name, col_data in columns_data.items():
            column = ColumnInfo(
                name=col_name,
                description=col_data.get("description"),
            )

            # Add column type from catalog if available
            if self.catalog:
                catalog_node = self._find_catalog_node(model_name)
                if catalog_node:
                    catalog_columns = catalog_node.get("columns", {})
                    catalog_col = catalog_columns.get(col_name, {})
                    column.type = catalog_col.get("type")

            model_context.columns.append(column)

        # Extract dependencies
        depends_on = model_node.get("depends_on", {})
        model_context.upstream = depends_on.get("nodes", [])

        # Extract downstream deps (need to iterate all nodes)
        downstream = self._find_downstream_models(model_node.get("unique_id", ""))
        model_context.downstream = downstream

        # Extract tests and translate to constraints
        table_tests, column_tests = self._extract_tests(model_name)

        # Table-level constraints
        model_context.constraints = [
            translate_test_to_constraint(test) for test in table_tests
        ]

        # Column-level constraints
        for col_name, tests in column_tests.items():
            # Find the column and add constraints
            for column in model_context.columns:
                if column.name == col_name:
                    column.constraints = [
                        translate_test_to_constraint(test) for test in tests
                    ]
                    break

        # Extract row count from catalog if available
        if self.catalog:
            catalog_node = self._find_catalog_node(model_name)
            if catalog_node:
                stats = catalog_node.get("stats", {})
                row_count_stat = stats.get("row_count", {})
                if row_count_stat and "value" in row_count_stat:
                    model_context.row_count = row_count_stat["value"]

        # TODO: Extract source freshness SLA (would need to check if model is a source)

        return model_context

    def _find_catalog_node(self, model_name: str) -> dict[str, Any] | None:
        """Find a model node in the catalog.

        Args:
            model_name: Name of the model

        Returns:
            Catalog node dict or None
        """
        if not self.catalog:
            return None

        for _node_id, node in self.catalog.get("nodes", {}).items():
            if node.get("metadata", {}).get("name") == model_name:
                return node

        return None

    def _find_downstream_models(self, unique_id: str) -> list[str]:
        """Find all models that depend on a given model.

        Args:
            unique_id: Unique ID of the model (e.g., model.project.customer)

        Returns:
            List of downstream model names
        """
        if not self.manifest:
            return []

        downstream = []
        for _node_id, node in self.manifest.get("nodes", {}).items():
            if node.get("resource_type") != "model":
                continue

            depends_on = node.get("depends_on", {}).get("nodes", [])
            if unique_id in depends_on:
                downstream.append(node.get("name", ""))

        return [name for name in downstream if name]  # Filter out empty strings

    def _extract_tests(
        self, model_name: str
    ) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
        """Extract tests for a model from manifest.

        Args:
            model_name: Name of the model

        Returns:
            Tuple of (table_level_tests, column_level_tests_by_column)
        """
        if not self.manifest:
            return [], {}

        table_tests = []
        column_tests: dict[str, list[dict[str, Any]]] = {}

        # Find all test nodes that reference this model
        for _node_id, node in self.manifest.get("nodes", {}).items():
            if node.get("resource_type") != "test":
                continue

            # Check if this test is attached to our model
            attached_node = node.get("attached_node")
            if not attached_node or model_name not in attached_node:
                continue

            # Extract test metadata
            test_metadata = node.get("test_metadata", {})
            column_name = node.get("column_name")

            test_node = {
                "test_metadata": test_metadata,
                "column_name": column_name,
                "attached_node": attached_node,
            }

            if column_name:
                # Column-level test
                if column_name not in column_tests:
                    column_tests[column_name] = []
                column_tests[column_name].append(test_node)
            else:
                # Table-level test
                table_tests.append(test_node)

        return table_tests, column_tests

    def _resolve_inference_context(self, model_name: str) -> InferenceContext | None:
        """Resolve Layer 5 context (inferences) for a model.

        Args:
            model_name: Name of the model

        Returns:
            InferenceContext or None
        """
        if not self.manifest:
            return None

        # Find model node
        model_node = None
        for _node_id, node in self.manifest.get("nodes", {}).items():
            if node.get("resource_type") == "model" and node.get("name") == model_name:
                model_node = node
                break

        if not model_node:
            return None

        # Build model metadata for inference engine
        # Extract tests in the format expected by inference engine
        tests = []
        table_tests, column_tests = self._extract_tests(model_name)

        # Convert to inference engine format
        for test in table_tests:
            test_type = test.get("test_metadata", {}).get("name", "")
            if test_type:
                tests.append({test_type: {}})

        for col_name, col_tests in column_tests.items():
            for test in col_tests:
                test_type = test.get("test_metadata", {}).get("name", "")
                if test_type:
                    tests.append({test_type: {"column_name": col_name}})

        downstream_count = len(
            self._find_downstream_models(model_node.get("unique_id", ""))
        )

        model_metadata = {
            "name": model_name,
            "tests": tests,
            "materialization": model_node.get("config", {}).get("materialized", "view"),
            "depends_on": model_node.get("depends_on", {}).get("nodes", []),
            "downstream_count": downstream_count,
            "description": model_node.get("description"),
            "path": model_node.get("original_file_path", ""),
        }

        # Run inference engine
        inferences = self.inference_engine.infer(model_metadata)

        # Convert to InferenceContext
        context = InferenceContext()

        for inference in inferences:
            if inference.type.value == "grain":
                context.grain = inference.message
                if inference.metadata:
                    context.grain_columns = inference.metadata.get("grain_columns", [])
            elif inference.type.value == "risk":
                if inference.metadata:
                    context.risk_level = inference.metadata.get("risk_level")
                context.risk_message = inference.message
            elif inference.type.value == "materialization":
                context.materialization_guidance = inference.message
            elif inference.type.value == "data_vault":
                if inference.metadata:
                    context.data_vault_pattern = inference.metadata.get("pattern")
            elif inference.type.value == "layer":
                if inference.metadata:
                    context.layer = inference.metadata.get("layer")
            elif inference.type.value == "quality":
                context.quality_warnings.append(inference.message)

        return context
