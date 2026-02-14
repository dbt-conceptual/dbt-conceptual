"""Tests for context resolution engine."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.context import (
    ContextMetadata,
    ContextResolver,
    FullContext,
    ModelContext,
    resolve_full_context,
)
from dbt_conceptual.inference import InferenceType


@pytest.fixture
def temp_project():
    """Create a temporary dbt project structure."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create conceptual.yml
        conceptual_data = {
            "domains": {
                "party": {
                    "name": "Party",
                    "display_name": "Party Domain",
                    "owner": "data-team",
                }
            },
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "definition": "A person or organization that purchases products",
                    "guidance": {
                        "context": "Core business entity",
                        "rules": [
                            {
                                "name": "uniqueness",
                                "description": "Each customer must have unique ID",
                            }
                        ],
                    },
                },
                "order": {
                    "name": "Order",
                    "domain": "party",
                    "owner": "analytics-team",  # Override domain owner
                    "definition": "A purchase transaction",
                },
            },
            "relationships": [
                {
                    "from": "customer",
                    "to": "order",
                    "verb": "places",
                    "cardinality": "1:N",
                }
            ],
        }

        conceptual_file = project_dir / "conceptual.yml"
        conceptual_file.write_text(yaml.dump(conceptual_data))

        # Create manifest.json
        manifest_data = {
            "metadata": {"project_name": "test_project"},
            "nodes": {
                "model.test_project.dim_customer": {
                    "unique_id": "model.test_project.dim_customer",
                    "name": "dim_customer",
                    "resource_type": "model",
                    "description": "Customer dimension table",
                    "schema": "analytics",
                    "config": {"materialized": "table"},
                    "original_file_path": "models/marts/dim_customer.sql",
                    "columns": {
                        "customer_id": {
                            "name": "customer_id",
                            "description": "Primary key",
                        },
                        "customer_name": {
                            "name": "customer_name",
                            "description": "Full name",
                        },
                    },
                    "depends_on": {"nodes": ["source.raw.customers"]},
                },
                "model.test_project.fct_orders": {
                    "unique_id": "model.test_project.fct_orders",
                    "name": "fct_orders",
                    "resource_type": "model",
                    "description": "Orders fact table",
                    "schema": "analytics",
                    "config": {"materialized": "incremental"},
                    "original_file_path": "models/marts/fct_orders.sql",
                    "columns": {
                        "order_id": {"name": "order_id", "description": "Primary key"},
                    },
                    "depends_on": {"nodes": ["model.test_project.dim_customer"]},
                },
                "test.test_project.unique_customer_id": {
                    "unique_id": "test.test_project.unique_customer_id",
                    "name": "unique_customer_id",
                    "resource_type": "test",
                    "test_metadata": {
                        "name": "unique",
                        "kwargs": {"column_name": "customer_id"},
                    },
                    "column_name": "customer_id",
                    "attached_node": "model.test_project.dim_customer",
                },
                "test.test_project.not_null_customer_id": {
                    "unique_id": "test.test_project.not_null_customer_id",
                    "name": "not_null_customer_id",
                    "resource_type": "test",
                    "test_metadata": {
                        "name": "not_null",
                        "kwargs": {"column_name": "customer_id"},
                    },
                    "column_name": "customer_id",
                    "attached_node": "model.test_project.dim_customer",
                },
            },
        }

        target_dir = project_dir / "target"
        target_dir.mkdir()
        manifest_file = target_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data))

        # Create catalog.json
        catalog_data = {
            "nodes": {
                "model.test_project.dim_customer": {
                    "stats": {"row_count": {"value": 1000}},
                    "columns": {
                        "customer_id": {"name": "customer_id", "type": "INTEGER"},
                        "customer_name": {"name": "customer_name", "type": "VARCHAR"},
                    },
                },
                "model.test_project.fct_orders": {
                    "stats": {"row_count": {"value": 5000}},
                    "columns": {"order_id": {"name": "order_id", "type": "INTEGER"}},
                },
            }
        }

        catalog_file = target_dir / "catalog.json"
        catalog_file.write_text(json.dumps(catalog_data))

        # Create models directory with schema files
        models_dir = project_dir / "models" / "marts"
        models_dir.mkdir(parents=True)

        schema_data = {
            "models": [
                {
                    "name": "dim_customer",
                    "description": "Customer dimension",
                    "meta": {"concept": "customer"},
                },
                {
                    "name": "fct_orders",
                    "description": "Orders fact",
                    "meta": {"concept": "order"},
                },
            ]
        }

        schema_file = models_dir / "schema.yml"
        schema_file.write_text(yaml.dump(schema_data))

        yield project_dir


class TestContextResolver:
    """Tests for ContextResolver class."""

    def test_resolve_full_context_basic(self, temp_project):
        """Should resolve full context for a concept."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        assert isinstance(context, FullContext)
        assert context.concept_key == "customer"
        assert context.concept.name == "Customer"
        assert context.concept.domain == "party"
        assert (
            context.concept.definition
            == "A person or organization that purchases products"
        )

    def test_resolve_inheritance(self, temp_project):
        """Should inherit owner from domain when not set."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        # Customer should inherit owner from party domain
        assert context.concept.owner == "data-team"

    def test_no_inheritance_when_owner_set(self, temp_project):
        """Should not inherit owner when concept has explicit owner."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("order")

        # Order has explicit owner, should not inherit
        assert context.concept.owner == "analytics-team"

    def test_resolve_models(self, temp_project):
        """Should resolve models for concept."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        assert len(context.models) == 1
        model = context.models[0]
        assert isinstance(model, ModelContext)
        assert model.name == "dim_customer"

    def test_model_from_manifest(self, temp_project):
        """Should enrich model from manifest.json."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")
        model = context.models[0]

        assert model.description == "Customer dimension table"
        assert model.materialization == "table"
        assert model.schema == "analytics"
        assert model.path == "models/marts/dim_customer.sql"
        assert len(model.columns) == 2
        assert model.columns[0].name == "customer_id"
        assert model.columns[1].name == "customer_name"

    def test_model_from_catalog(self, temp_project):
        """Should enrich model from catalog.json."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")
        model = context.models[0]

        assert model.row_count == 1000
        assert model.columns[0].type == "INTEGER"
        assert model.columns[1].type == "VARCHAR"

    def test_model_constraints(self, temp_project):
        """Should translate tests to constraints."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")
        model = context.models[0]

        assert len(model.constraints) == 2
        assert "customer_id must be unique" in model.constraints
        assert "customer_id must not be null" in model.constraints

    def test_model_dependencies(self, temp_project):
        """Should track upstream and downstream dependencies."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        # Check customer model (has downstream)
        customer_context = resolver.resolve_full_context("customer")
        customer_model = customer_context.models[0]

        assert len(customer_model.downstream) == 1
        assert "fct_orders" in customer_model.downstream

        # Check order model (has upstream)
        order_context = resolver.resolve_full_context("order")
        order_model = order_context.models[0]

        assert len(order_model.upstream) == 1
        assert "dim_customer" in order_model.upstream

    def test_model_inferences(self, temp_project):
        """Should run inference engine on models."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")
        model = context.models[0]

        assert len(model.inferences) > 0

    def test_relationships(self, temp_project):
        """Should include related relationships."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        assert len(context.relationships) == 1
        rel = context.relationships[0]
        assert rel.from_concept == "customer"
        assert rel.to_concept == "order"
        assert rel.verb == "places"

    def test_guidance(self, temp_project):
        """Should include guidance from conceptual model."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        assert context.guidance is not None
        assert context.guidance.context == "Core business entity"
        assert len(context.guidance.rules) == 1
        assert context.guidance.rules[0].name == "uniqueness"

    def test_metadata(self, temp_project):
        """Should track source metadata."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        assert context.metadata is not None
        assert isinstance(context.metadata, ContextMetadata)
        assert "conceptual.yml" in context.metadata.conceptual_file
        assert "manifest.json" in context.metadata.manifest_file
        assert "catalog.json" in context.metadata.catalog_file

    def test_missing_concept(self, temp_project):
        """Should raise ValueError for missing concept."""
        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        with pytest.raises(ValueError, match="Concept 'nonexistent' not found"):
            resolver.resolve_full_context("nonexistent")

    def test_missing_catalog_graceful(self, temp_project):
        """Should handle missing catalog.json gracefully."""
        # Remove catalog file
        catalog_file = temp_project / "target" / "catalog.json"
        catalog_file.unlink()

        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        # Should still resolve, but without catalog data
        model = context.models[0]
        assert model.row_count is None
        assert model.columns[0].type is None
        assert context.metadata.catalog_file is None

    def test_missing_manifest_graceful(self, temp_project):
        """Should handle missing manifest.json gracefully."""
        # Remove manifest file
        manifest_file = temp_project / "target" / "manifest.json"
        manifest_file.unlink()

        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        context = resolver.resolve_full_context("customer")

        # Should still resolve, but models will be minimal
        assert len(context.models) == 0  # No models without manifest
        assert context.metadata.manifest_file is None


class TestConvenienceFunction:
    """Tests for resolve_full_context convenience function."""

    def test_convenience_function(self, temp_project):
        """Should work as shorthand for resolver."""
        config = Config.load(temp_project)

        context = resolve_full_context(config, "customer")

        assert isinstance(context, FullContext)
        assert context.concept_key == "customer"
        assert len(context.models) == 1


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_concept_with_no_models(self, temp_project):
        """Should handle concept with no models."""
        # Add concept with no models
        conceptual_file = temp_project / "conceptual.yml"
        data = yaml.safe_load(conceptual_file.read_text())
        data["concepts"]["empty"] = {
            "name": "Empty Concept",
            "domain": "party",
        }
        conceptual_file.write_text(yaml.dump(data))

        config = Config.load(temp_project)
        context = resolve_full_context(config, "empty")

        assert len(context.models) == 0
        assert context.concept.status == "draft"

    def test_malformed_manifest(self, temp_project):
        """Should handle malformed manifest gracefully."""
        # Write invalid JSON
        manifest_file = temp_project / "target" / "manifest.json"
        manifest_file.write_text("{ invalid json")

        config = Config.load(temp_project)
        resolver = ContextResolver(config)

        # Should still work, just without manifest data
        context = resolver.resolve_full_context("customer")
        assert context.metadata.manifest_file is None

    def test_incremental_materialization_inference(self, temp_project):
        """Should infer materialization guidance for incremental models."""
        config = Config.load(temp_project)
        context = resolve_full_context(config, "order")

        model = context.models[0]
        assert model.materialization == "incremental"

        # Should have materialization inference
        mat_inferences = [
            i for i in model.inferences if i.type == InferenceType.MATERIALIZATION
        ]
        assert len(mat_inferences) > 0
        assert "incremental" in mat_inferences[0].message.lower()
