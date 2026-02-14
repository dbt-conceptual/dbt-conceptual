"""Tests for heuristic inference engine."""

from __future__ import annotations

import pytest

from dbt_conceptual.inference import (
    Confidence,
    Inference,
    InferenceEngine,
    InferenceType,
)


@pytest.fixture
def engine():
    """Create an inference engine instance."""
    return InferenceEngine()


class TestGrainInference:
    """Tests for grain inference from unique tests."""

    def test_single_unique_column(self, engine):
        """Should infer grain from single unique test."""
        metadata = {
            "name": "users",
            "tests": [{"unique": {"column_name": "user_id"}}],
        }

        inferences = engine._infer_grain(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.GRAIN
        assert "one row per user_id" in inferences[0].message
        assert inferences[0].confidence == Confidence.HIGH
        assert inferences[0].metadata == {"grain_columns": ["user_id"]}

    def test_composite_unique_columns(self, engine):
        """Should infer grain from unique combination test."""
        metadata = {
            "name": "daily_metrics",
            "tests": [
                {
                    "dbt_utils.unique_combination_of_columns": {
                        "combination_of_columns": ["date", "user_id"]
                    }
                }
            ],
        }

        inferences = engine._infer_grain(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.GRAIN
        assert "combination of (date, user_id)" in inferences[0].message
        assert inferences[0].confidence == Confidence.HIGH
        assert inferences[0].metadata == {"grain_columns": ["date", "user_id"]}

    def test_no_unique_tests(self, engine):
        """Should infer from naming convention when no unique tests."""
        metadata = {"name": "order_id", "tests": []}

        inferences = engine._infer_grain(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.GRAIN
        assert "one row per order" in inferences[0].message
        assert inferences[0].confidence == Confidence.LOW

    def test_key_suffix_inference(self, engine):
        """Should infer from _key suffix."""
        metadata = {"name": "customer_key", "tests": []}

        inferences = engine._infer_grain(metadata)

        assert len(inferences) == 1
        assert "one row per customer" in inferences[0].message

    def test_no_grain_inference(self, engine):
        """Should return empty list when no grain can be inferred."""
        metadata = {"name": "metrics", "tests": []}

        inferences = engine._infer_grain(metadata)

        assert len(inferences) == 0

    def test_malformed_test_structure(self, engine):
        """Should handle malformed test structures gracefully."""
        metadata = {"name": "users", "tests": ["not_a_dict", None, {}]}

        inferences = engine._infer_grain(metadata)

        assert len(inferences) == 0


class TestRiskInference:
    """Tests for risk assessment from downstream count."""

    def test_high_risk_model(self, engine):
        """Should flag high-risk models with many dependents."""
        metadata = {"name": "core_customers", "downstream_count": 15}

        inferences = engine._infer_risk(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.RISK
        assert "High-risk model" in inferences[0].message
        assert "15 downstream dependents" in inferences[0].message
        assert inferences[0].confidence == Confidence.HIGH
        assert inferences[0].metadata["risk_level"] == "high"

    def test_medium_risk_model(self, engine):
        """Should flag medium-risk models."""
        metadata = {"name": "orders", "downstream_count": 7}

        inferences = engine._infer_risk(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.RISK
        assert "Medium-risk model" in inferences[0].message
        assert inferences[0].metadata["risk_level"] == "medium"

    def test_low_risk_model(self, engine):
        """Should not flag low-risk models."""
        metadata = {"name": "staging_data", "downstream_count": 2}

        inferences = engine._infer_risk(metadata)

        assert len(inferences) == 0

    def test_no_downstream_count(self, engine):
        """Should handle missing downstream_count gracefully."""
        metadata = {"name": "leaf_model"}

        inferences = engine._infer_risk(metadata)

        assert len(inferences) == 0


class TestMaterializationGuidance:
    """Tests for materialization-specific guidance."""

    def test_incremental_materialization(self, engine):
        """Should provide incremental guidance."""
        metadata = {"name": "events", "materialization": "incremental"}

        inferences = engine._infer_materialization_guidance(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.MATERIALIZATION
        assert "--full-refresh" in inferences[0].message
        assert inferences[0].confidence == Confidence.HIGH

    def test_ephemeral_materialization(self, engine):
        """Should provide ephemeral guidance."""
        metadata = {"name": "helper", "materialization": "ephemeral"}

        inferences = engine._infer_materialization_guidance(metadata)

        assert len(inferences) == 1
        assert "Not queryable directly" in inferences[0].message

    def test_table_materialization(self, engine):
        """Should not provide guidance for table materialization."""
        metadata = {"name": "users", "materialization": "table"}

        inferences = engine._infer_materialization_guidance(metadata)

        assert len(inferences) == 0

    def test_case_insensitive_materialization(self, engine):
        """Should handle uppercase materialization."""
        metadata = {"name": "events", "materialization": "INCREMENTAL"}

        inferences = engine._infer_materialization_guidance(metadata)

        assert len(inferences) == 1


class TestDataVaultPattern:
    """Tests for Data Vault pattern detection."""

    @pytest.mark.parametrize(
        "prefix,pattern_type",
        [
            ("hub_", "Hub"),
            ("sat_", "Satellite"),
            ("link_", "Link"),
            ("pit_", "Point-in-Time"),
            ("bridge_", "Bridge"),
        ],
    )
    def test_data_vault_patterns(self, engine, prefix, pattern_type):
        """Should detect Data Vault patterns."""
        metadata = {"name": f"{prefix}customers"}

        inferences = engine._infer_data_vault_pattern(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.DATA_VAULT
        assert pattern_type in inferences[0].message
        assert inferences[0].confidence == Confidence.HIGH

    def test_no_data_vault_pattern(self, engine):
        """Should not detect patterns on non-DV models."""
        metadata = {"name": "customers"}

        inferences = engine._infer_data_vault_pattern(metadata)

        assert len(inferences) == 0

    def test_case_insensitive_pattern(self, engine):
        """Should detect patterns regardless of case."""
        metadata = {"name": "HUB_Customers"}

        inferences = engine._infer_data_vault_pattern(metadata)

        assert len(inferences) == 1
        assert "Hub" in inferences[0].message


class TestStagingLayer:
    """Tests for staging layer detection."""

    def test_staging_prefix(self, engine):
        """Should detect staging layer from stg_ prefix."""
        metadata = {"name": "stg_orders"}

        inferences = engine._infer_staging_layer(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.STAGING
        assert "no business logic" in inferences[0].message
        assert inferences[0].confidence == Confidence.HIGH

    def test_non_staging_model(self, engine):
        """Should not detect staging on other models."""
        metadata = {"name": "orders"}

        inferences = engine._infer_staging_layer(metadata)

        assert len(inferences) == 0


class TestLayerClassification:
    """Tests for layer classification from path and naming."""

    def test_mart_layer_from_path(self, engine):
        """Should classify mart layer from path."""
        metadata = {"name": "orders", "path": "models/marts/sales/orders.sql"}

        inferences = engine._infer_layer_classification(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.LAYER
        assert "mart" in inferences[0].message.lower()
        assert inferences[0].confidence == Confidence.HIGH

    def test_intermediate_layer_from_path(self, engine):
        """Should classify intermediate layer from path."""
        metadata = {"name": "prep", "path": "models/int/prep.sql"}

        inferences = engine._infer_layer_classification(metadata)

        assert len(inferences) == 1
        assert "intermediate" in inferences[0].message.lower()

    def test_staging_layer_from_path(self, engine):
        """Should classify staging layer from path."""
        metadata = {"name": "raw_orders", "path": "models/staging/raw_orders.sql"}

        inferences = engine._infer_layer_classification(metadata)

        assert len(inferences) == 1
        assert "staging" in inferences[0].message.lower()

    def test_intermediate_from_name(self, engine):
        """Should infer intermediate layer from int_ prefix."""
        metadata = {"name": "int_orders", "path": "models/orders.sql"}

        inferences = engine._infer_layer_classification(metadata)

        assert len(inferences) == 1
        assert "intermediate" in inferences[0].message.lower()
        assert inferences[0].confidence == Confidence.MEDIUM

    def test_mart_from_fct_prefix(self, engine):
        """Should infer mart layer from fct_ prefix."""
        metadata = {"name": "fct_orders", "path": "models/orders.sql"}

        inferences = engine._infer_layer_classification(metadata)

        assert len(inferences) == 1
        assert "mart" in inferences[0].message.lower()

    def test_mart_from_dim_prefix(self, engine):
        """Should infer mart layer from dim_ prefix."""
        metadata = {"name": "dim_customers", "path": "models/customers.sql"}

        inferences = engine._infer_layer_classification(metadata)

        assert len(inferences) == 1
        assert "mart" in inferences[0].message.lower()

    def test_no_layer_classification(self, engine):
        """Should return empty when no layer can be classified."""
        metadata = {"name": "model", "path": "models/model.sql"}

        inferences = engine._infer_layer_classification(metadata)

        assert len(inferences) == 0


class TestQualityWarnings:
    """Tests for quality warnings."""

    def test_no_tests_warning(self, engine):
        """Should warn when no tests are defined."""
        metadata = {"name": "orders", "tests": [], "description": "Orders table"}

        inferences = engine._infer_quality_warnings(metadata)

        no_tests = [i for i in inferences if i.metadata.get("issue") == "no_tests"]
        assert len(no_tests) == 1
        assert "No tests defined" in no_tests[0].message

    def test_no_description_warning(self, engine):
        """Should warn when no description is provided."""
        metadata = {
            "name": "orders",
            "tests": [{"unique": {"column_name": "id"}}],
            "description": None,
        }

        inferences = engine._infer_quality_warnings(metadata)

        no_desc = [i for i in inferences if i.metadata.get("issue") == "no_description"]
        assert len(no_desc) == 1
        assert "No description provided" in no_desc[0].message

    def test_empty_description_warning(self, engine):
        """Should warn when description is empty string."""
        metadata = {
            "name": "orders",
            "tests": [{"unique": {"column_name": "id"}}],
            "description": "   ",
        }

        inferences = engine._infer_quality_warnings(metadata)

        no_desc = [i for i in inferences if i.metadata.get("issue") == "no_description"]
        assert len(no_desc) == 1

    def test_both_quality_issues(self, engine):
        """Should warn about both missing tests and description."""
        metadata = {"name": "orders", "tests": [], "description": None}

        inferences = engine._infer_quality_warnings(metadata)

        assert len(inferences) == 2
        issues = {i.metadata["issue"] for i in inferences}
        assert issues == {"no_tests", "no_description"}

    def test_no_quality_warnings(self, engine):
        """Should not warn when quality checks pass."""
        metadata = {
            "name": "orders",
            "tests": [{"unique": {"column_name": "id"}}],
            "description": "Orders table",
        }

        inferences = engine._infer_quality_warnings(metadata)

        assert len(inferences) == 0


class TestRelationshipGrain:
    """Tests for relationship grain warnings."""

    def test_relationships_test_warning(self, engine):
        """Should warn about potential fan-out from relationships test."""
        metadata = {
            "name": "orders",
            "tests": [
                {
                    "relationships": {
                        "to": "customers",
                        "field": "customer_id",
                    }
                }
            ],
        }

        inferences = engine._infer_relationship_grain(metadata)

        assert len(inferences) == 1
        assert inferences[0].type == InferenceType.RELATIONSHIP
        assert "fan out" in inferences[0].message
        assert "customers" in inferences[0].message
        assert inferences[0].metadata["cardinality"] == "1:N"

    def test_no_relationships_test(self, engine):
        """Should not warn when no relationships test exists."""
        metadata = {"name": "orders", "tests": [{"unique": {"column_name": "id"}}]}

        inferences = engine._infer_relationship_grain(metadata)

        assert len(inferences) == 0


class TestFullInference:
    """Integration tests for full inference pipeline."""

    def test_comprehensive_model_metadata(self, engine):
        """Should run all inferences on comprehensive metadata."""
        metadata = {
            "name": "fct_orders",
            "tests": [
                {"unique": {"column_name": "order_id"}},
                {"relationships": {"to": "dim_customers", "field": "customer_id"}},
            ],
            "materialization": "incremental",
            "depends_on": ["stg_orders", "dim_customers"],
            "downstream_count": 12,
            "description": "Fact table for orders",
            "path": "models/marts/sales/fct_orders.sql",
        }

        inferences = engine.infer(metadata)

        # Should have multiple inferences
        assert len(inferences) > 0

        # Check inference types present
        types = {i.type for i in inferences}
        assert InferenceType.GRAIN in types
        assert InferenceType.RISK in types
        assert InferenceType.MATERIALIZATION in types
        assert InferenceType.LAYER in types
        assert InferenceType.RELATIONSHIP in types

    def test_minimal_model_metadata(self, engine):
        """Should handle minimal metadata gracefully."""
        metadata = {"name": "simple_model"}

        inferences = engine.infer(metadata)

        # Should still produce quality warnings
        quality = [i for i in inferences if i.type == InferenceType.QUALITY]
        assert len(quality) == 2  # no tests, no description

    def test_staging_model_with_issues(self, engine):
        """Should produce appropriate inferences for staging model."""
        metadata = {
            "name": "stg_raw_orders",
            "tests": [],
            "materialization": "view",
            "downstream_count": 3,
            "description": None,
            "path": "models/staging/stg_raw_orders.sql",
        }

        inferences = engine.infer(metadata)

        types = {i.type for i in inferences}
        assert InferenceType.STAGING in types
        assert InferenceType.LAYER in types
        assert InferenceType.QUALITY in types

    def test_data_vault_hub(self, engine):
        """Should detect Data Vault hub pattern."""
        metadata = {
            "name": "hub_customer",
            "tests": [{"unique": {"column_name": "customer_hk"}}],
            "materialization": "table",
            "description": "Customer hub",
            "path": "models/vault/hubs/hub_customer.sql",
        }

        inferences = engine.infer(metadata)

        types = {i.type for i in inferences}
        assert InferenceType.DATA_VAULT in types
        assert InferenceType.GRAIN in types


class TestInferenceDataclass:
    """Tests for Inference dataclass structure."""

    def test_inference_creation(self):
        """Should create inference with all fields."""
        inf = Inference(
            type=InferenceType.GRAIN,
            message="Test message",
            confidence=Confidence.HIGH,
            metadata={"key": "value"},
        )

        assert inf.type == InferenceType.GRAIN
        assert inf.message == "Test message"
        assert inf.confidence == Confidence.HIGH
        assert inf.metadata == {"key": "value"}

    def test_inference_without_metadata(self):
        """Should create inference without metadata."""
        inf = Inference(
            type=InferenceType.QUALITY,
            message="Warning",
            confidence=Confidence.MEDIUM,
        )

        assert inf.metadata is None
