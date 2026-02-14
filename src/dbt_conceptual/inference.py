"""Heuristic inference engine for enriching dbt model metadata.

Infers additional context from dbt project patterns to provide guidance and warnings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class InferenceType(str, Enum):
    """Types of inferences the engine can make."""

    GRAIN = "grain"  # Grain inference from unique tests
    RISK = "risk"  # Risk assessment from downstream count
    MATERIALIZATION = "materialization"  # Materialization guidance
    DATA_VAULT = "data_vault"  # Data Vault pattern detection
    STAGING = "staging"  # Staging layer detection
    LAYER = "layer"  # Layer classification
    QUALITY = "quality"  # Quality warnings
    RELATIONSHIP = "relationship"  # Relationship grain warnings


class Confidence(str, Enum):
    """Confidence levels for inferences."""

    HIGH = "high"  # >90% confident
    MEDIUM = "medium"  # 60-90% confident
    LOW = "low"  # <60% confident


@dataclass
class Inference:
    """Represents a single inference about a model."""

    type: InferenceType
    message: str
    confidence: Confidence
    metadata: dict[str, Any] | None = None


class InferenceEngine:
    """Engine for making heuristic inferences about dbt models."""

    def infer(self, model_metadata: dict[str, Any]) -> list[Inference]:
        """Run all inference rules on a model.

        Args:
            model_metadata: Dictionary containing model information with keys:
                - name (str): Model name
                - tests (list[dict]): List of test definitions
                - materialization (str): Materialization type (table, view, incremental, etc.)
                - depends_on (list[str]): List of upstream model names
                - downstream_count (int): Number of downstream dependents
                - description (str | None): Model description
                - path (str): File path to model

        Returns:
            List of Inference objects
        """
        inferences: list[Inference] = []

        # Run all heuristic rules
        inferences.extend(self._infer_grain(model_metadata))
        inferences.extend(self._infer_risk(model_metadata))
        inferences.extend(self._infer_materialization_guidance(model_metadata))
        inferences.extend(self._infer_data_vault_pattern(model_metadata))
        inferences.extend(self._infer_staging_layer(model_metadata))
        inferences.extend(self._infer_layer_classification(model_metadata))
        inferences.extend(self._infer_quality_warnings(model_metadata))
        inferences.extend(self._infer_relationship_grain(model_metadata))

        return inferences

    def _infer_grain(self, model_metadata: dict[str, Any]) -> list[Inference]:
        """Infer model grain from unique tests and primary key patterns.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of grain inferences
        """
        inferences: list[Inference] = []
        tests = model_metadata.get("tests", [])

        # Look for unique tests with column combinations
        unique_columns: list[str] = []
        for test in tests:
            if not isinstance(test, dict):
                continue

            # dbt test format: {"unique": {"column_name": "id"}}
            # or: {"dbt_utils.unique_combination_of_columns": {"combination_of_columns": ["a", "b"]}}
            test_type = next(iter(test.keys())) if test else None

            if test_type == "unique":
                config = test.get("unique", {})
                if isinstance(config, dict) and "column_name" in config:
                    unique_columns.append(config["column_name"])
            elif "unique_combination_of_columns" in str(test_type):
                config = test.get(test_type, {})
                if isinstance(config, dict) and "combination_of_columns" in config:
                    cols = config["combination_of_columns"]
                    if isinstance(cols, list):
                        unique_columns.extend(cols)

        if unique_columns:
            if len(unique_columns) == 1:
                message = f"Grain appears to be one row per {unique_columns[0]}"
                confidence = Confidence.HIGH
            else:
                cols_str = ", ".join(unique_columns)
                message = f"Grain appears to be one row per combination of ({cols_str})"
                confidence = Confidence.HIGH

            inferences.append(
                Inference(
                    type=InferenceType.GRAIN,
                    message=message,
                    confidence=confidence,
                    metadata={"grain_columns": unique_columns},
                )
            )

        # Check for primary key column naming pattern
        model_name = model_metadata.get("name", "")
        pk_pattern = re.compile(r"^(.+)_id$|^(.+)_key$")
        match = pk_pattern.match(model_name)
        if match and not unique_columns:
            # Infer from naming convention
            entity = match.group(1) or match.group(2)
            message = f"Model name suggests grain of one row per {entity}"
            inferences.append(
                Inference(
                    type=InferenceType.GRAIN,
                    message=message,
                    confidence=Confidence.LOW,
                    metadata={"inferred_entity": entity},
                )
            )

        return inferences

    def _infer_risk(self, model_metadata: dict[str, Any]) -> list[Inference]:
        """Assess risk from downstream dependent count.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of risk inferences
        """
        inferences: list[Inference] = []
        downstream_count = model_metadata.get("downstream_count", 0)

        if downstream_count >= 10:
            message = f"High-risk model: {downstream_count} downstream dependents. Changes may have wide impact."
            confidence = Confidence.HIGH
            inferences.append(
                Inference(
                    type=InferenceType.RISK,
                    message=message,
                    confidence=confidence,
                    metadata={
                        "downstream_count": downstream_count,
                        "risk_level": "high",
                    },
                )
            )
        elif downstream_count >= 5:
            message = f"Medium-risk model: {downstream_count} downstream dependents. Test changes carefully."
            confidence = Confidence.HIGH
            inferences.append(
                Inference(
                    type=InferenceType.RISK,
                    message=message,
                    confidence=confidence,
                    metadata={
                        "downstream_count": downstream_count,
                        "risk_level": "medium",
                    },
                )
            )

        return inferences

    def _infer_materialization_guidance(
        self, model_metadata: dict[str, Any]
    ) -> list[Inference]:
        """Provide materialization-specific guidance.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of materialization inferences
        """
        inferences: list[Inference] = []
        materialization = model_metadata.get("materialization", "").lower()

        if materialization == "incremental":
            message = "Incremental model: remember to run with --full-refresh when schema changes"
            inferences.append(
                Inference(
                    type=InferenceType.MATERIALIZATION,
                    message=message,
                    confidence=Confidence.HIGH,
                    metadata={"materialization": "incremental"},
                )
            )
        elif materialization == "ephemeral":
            message = "Ephemeral model: compiled as CTE in downstream models. Not queryable directly."
            inferences.append(
                Inference(
                    type=InferenceType.MATERIALIZATION,
                    message=message,
                    confidence=Confidence.HIGH,
                    metadata={"materialization": "ephemeral"},
                )
            )

        return inferences

    def _infer_data_vault_pattern(
        self, model_metadata: dict[str, Any]
    ) -> list[Inference]:
        """Detect Data Vault pattern from naming conventions.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of Data Vault pattern inferences
        """
        inferences: list[Inference] = []
        model_name = model_metadata.get("name", "").lower()

        patterns = {
            r"^hub_": ("Hub", "Core business entity in Data Vault architecture"),
            r"^sat_": (
                "Satellite",
                "Descriptive attributes for hub or link in Data Vault",
            ),
            r"^link_": ("Link", "Relationship between hubs in Data Vault architecture"),
            r"^pit_": (
                "Point-in-Time",
                "Snapshot table for historical querying in Data Vault",
            ),
            r"^bridge_": (
                "Bridge",
                "Many-to-many relationship resolver in Data Vault",
            ),
        }

        for pattern, (entity_type, description) in patterns.items():
            if re.match(pattern, model_name):
                message = f"{entity_type} table detected: {description}"
                inferences.append(
                    Inference(
                        type=InferenceType.DATA_VAULT,
                        message=message,
                        confidence=Confidence.HIGH,
                        metadata={"pattern": entity_type.lower()},
                    )
                )
                break

        return inferences

    def _infer_staging_layer(self, model_metadata: dict[str, Any]) -> list[Inference]:
        """Detect staging layer from naming convention.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of staging layer inferences
        """
        inferences: list[Inference] = []
        model_name = model_metadata.get("name", "").lower()

        if re.match(r"^stg_", model_name):
            message = "Staging layer model: should contain minimal transformations and no business logic"
            inferences.append(
                Inference(
                    type=InferenceType.STAGING,
                    message=message,
                    confidence=Confidence.HIGH,
                    metadata={"layer": "staging"},
                )
            )

        return inferences

    def _infer_layer_classification(
        self, model_metadata: dict[str, Any]
    ) -> list[Inference]:
        """Classify model layer from directory structure or naming.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of layer classification inferences
        """
        inferences: list[Inference] = []
        model_name = model_metadata.get("name", "").lower()
        path = model_metadata.get("path", "").lower()

        # Check path first (more reliable)
        layer_patterns = {
            r"/marts?/": ("mart", "Business-facing data mart layer"),
            r"/int/|/intermediate/": (
                "intermediate",
                "Intermediate transformation layer",
            ),
            r"/staging/|/stg/": ("staging", "Raw data staging layer"),
        }

        for pattern, (layer, description) in layer_patterns.items():
            if re.search(pattern, path):
                message = f"{layer.capitalize()} layer: {description}"
                inferences.append(
                    Inference(
                        type=InferenceType.LAYER,
                        message=message,
                        confidence=Confidence.HIGH,
                        metadata={"layer": layer},
                    )
                )
                return inferences

        # Fallback to naming patterns
        naming_patterns = {
            r"^int_": ("intermediate", "Intermediate transformation layer"),
            r"^mart_|^fct_|^dim_": ("mart", "Business-facing data mart layer"),
        }

        for pattern, (layer, description) in naming_patterns.items():
            if re.match(pattern, model_name):
                message = (
                    f"{layer.capitalize()} layer (inferred from name): {description}"
                )
                inferences.append(
                    Inference(
                        type=InferenceType.LAYER,
                        message=message,
                        confidence=Confidence.MEDIUM,
                        metadata={"layer": layer},
                    )
                )
                break

        return inferences

    def _infer_quality_warnings(
        self, model_metadata: dict[str, Any]
    ) -> list[Inference]:
        """Generate quality warnings for missing tests or descriptions.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of quality warning inferences
        """
        inferences: list[Inference] = []
        tests = model_metadata.get("tests", [])
        description = model_metadata.get("description")

        if not tests:
            message = "No tests defined. Consider adding data quality tests."
            inferences.append(
                Inference(
                    type=InferenceType.QUALITY,
                    message=message,
                    confidence=Confidence.HIGH,
                    metadata={"issue": "no_tests"},
                )
            )

        if not description or not description.strip():
            message = "No description provided. Documentation helps maintainability."
            inferences.append(
                Inference(
                    type=InferenceType.QUALITY,
                    message=message,
                    confidence=Confidence.HIGH,
                    metadata={"issue": "no_description"},
                )
            )

        return inferences

    def _infer_relationship_grain(
        self, model_metadata: dict[str, Any]
    ) -> list[Inference]:
        """Warn about relationship grain from cardinality analysis.

        Args:
            model_metadata: Model metadata dictionary

        Returns:
            List of relationship grain inferences
        """
        inferences: list[Inference] = []
        tests = model_metadata.get("tests", [])

        # Look for relationship tests that indicate cardinality
        for test in tests:
            if not isinstance(test, dict):
                continue

            test_type = next(iter(test.keys())) if test else None

            if "relationships" in str(test_type):
                config = test.get(test_type, {})
                if isinstance(config, dict):
                    # relationships test indicates foreign key
                    to_table = config.get("to", config.get("field", ""))
                    message = f"Foreign key relationship to {to_table}. Joining may fan out results (1:N)."
                    inferences.append(
                        Inference(
                            type=InferenceType.RELATIONSHIP,
                            message=message,
                            confidence=Confidence.MEDIUM,
                            metadata={"to_table": to_table, "cardinality": "1:N"},
                        )
                    )

        return inferences
