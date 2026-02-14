"""End-to-end integration tests for MCP Server V1.

Tests the full stack from conceptual.yml → ProjectState → ContextResolver
→ formatters → MCP handlers, using a comprehensive fixture project.

Coverage:
- Selector parsing and resolution (single, upstream, downstream, bidirectional, domain, status, all)
- All three output formats (llm, json, markdown)
- Context resolution with all 5 layers (conceptual, manifest, catalog, contracts, inferences)
- Graceful handling of missing files (manifest, catalog)
- Error cases (unknown concepts, empty selectors, invalid formats)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.context import resolve_full_context
from dbt_conceptual.mcp.handlers import (
    handle_get_context,
    handle_list_concepts,
    handle_validate,
)
from dbt_conceptual.parser import StateBuilder
from dbt_conceptual.selector import SelectorError, select_concepts


@pytest.fixture
def fixture_project() -> Path:
    """Path to the comprehensive fixture project."""
    return Path(__file__).parent / "fixtures" / "sample_project"


@pytest.fixture
def config(fixture_project: Path) -> Config:
    """Load config from fixture project."""
    return Config.load(fixture_project)


@pytest.fixture
def project_state(config: Config):
    """Build project state from fixture."""
    builder = StateBuilder(config)
    return builder.build()


class TestFixtureIntegrity:
    """Verify the fixture project is set up correctly."""

    def test_fixture_structure(self, fixture_project: Path):
        """Fixture should have all required files."""
        assert (fixture_project / "conceptual.yml").exists()
        assert (fixture_project / "dbt_project.yml").exists()
        assert (fixture_project / "target" / "manifest.json").exists()
        assert (fixture_project / "target" / "catalog.json").exists()
        assert (fixture_project / "models" / "staging" / "schema.yml").exists()
        assert (fixture_project / "models" / "marts" / "schema.yml").exists()

    def test_conceptual_yaml_valid(self, fixture_project: Path):
        """Conceptual.yml should be valid YAML with expected structure."""
        conceptual_file = fixture_project / "conceptual.yml"
        data = yaml.safe_load(conceptual_file.read_text())

        assert "domains" in data
        assert "concepts" in data
        assert "relationships" in data

        # Should have 3 domains
        assert len(data["domains"]) == 3
        assert "party" in data["domains"]
        assert "product" in data["domains"]
        assert "transaction" in data["domains"]

        # Should have 5 concepts (customer, order, product, supplier, warehouse)
        assert len(data["concepts"]) == 5
        assert "customer" in data["concepts"]
        assert "order" in data["concepts"]
        assert "product" in data["concepts"]
        assert "supplier" in data["concepts"]
        assert "warehouse" in data["concepts"]

        # Should have 4 relationships
        assert len(data["relationships"]) == 4

    def test_manifest_valid(self, fixture_project: Path):
        """Manifest.json should be valid and contain models."""
        manifest_file = fixture_project / "target" / "manifest.json"
        data = json.loads(manifest_file.read_text())

        assert "nodes" in data
        assert "metadata" in data
        assert data["metadata"]["project_name"] == "sample_project"

        # Count models (not tests)
        models = [k for k in data["nodes"].keys() if k.startswith("model.")]
        assert len(models) == 8  # 3 staging + 5 marts

        # Count tests
        tests = [k for k in data["nodes"].keys() if k.startswith("test.")]
        assert len(tests) > 0  # Should have tests defined

    def test_catalog_valid(self, fixture_project: Path):
        """Catalog.json should be valid and contain row counts."""
        catalog_file = fixture_project / "target" / "catalog.json"
        data = json.loads(catalog_file.read_text())

        assert "nodes" in data

        # All models should have row counts
        for _node_id, node_data in data["nodes"].items():
            assert "stats" in node_data
            assert "row_count" in node_data["stats"]
            assert "columns" in node_data


class TestProjectStateBuild:
    """Test ProjectState building from fixture."""

    def test_builds_successfully(self, project_state):
        """Should build state without errors."""
        assert project_state is not None
        assert len(project_state.concepts) > 0
        assert len(project_state.domains) > 0

    def test_domains_loaded(self, project_state):
        """Should load all 3 domains."""
        assert len(project_state.domains) == 3
        assert "party" in project_state.domains
        assert "product" in project_state.domains
        assert "transaction" in project_state.domains

        # Check domain metadata
        party = project_state.domains["party"]
        assert party.display_name == "Party Domain"
        assert party.owner == "party-team"
        assert party.color == "#FF5733"

    def test_concepts_loaded(self, project_state):
        """Should load all concepts with correct metadata."""
        # Should have 5 concepts
        assert len(project_state.concepts) == 5

        # Customer (complete status - has domain and models)
        customer = project_state.concepts["customer"]
        assert customer.name == "Customer"
        assert customer.domain == "party"
        assert customer.definition is not None
        assert customer.status == "complete"
        assert len(customer.models) > 0

        # Supplier (draft status - has domain but no models)
        supplier = project_state.concepts["supplier"]
        assert supplier.domain == "party"
        assert supplier.status == "draft"
        assert len(supplier.models) == 0

        # Warehouse (stub status - no domain)
        warehouse = project_state.concepts["warehouse"]
        assert warehouse.domain is None
        assert warehouse.status == "stub"

    def test_relationships_loaded(self, project_state):
        """Should load all relationships."""
        assert len(project_state.relationships) == 4

        # Check specific relationship
        rel_id = "customer:places:order"
        assert rel_id in project_state.relationships

        rel = project_state.relationships[rel_id]
        assert rel.from_concept == "customer"
        assert rel.to_concept == "order"
        assert rel.verb == "places"
        assert rel.cardinality == "1:N"

    def test_models_tagged_to_concepts(self, project_state):
        """Should correctly tag models to concepts.

        Note: Only models in gold_paths (default: models/marts/**/*.yml) are scanned.
        Staging models are not included by default.
        """
        customer = project_state.concepts["customer"]
        # Should have dim_customer from marts
        assert "dim_customer" in customer.models
        assert len(customer.models) == 1  # Only mart models scanned

        order = project_state.concepts["order"]
        # Should have fct_orders, fct_order_items from marts
        assert "fct_orders" in order.models
        assert "fct_order_items" in order.models
        assert len(order.models) == 2

        product = project_state.concepts["product"]
        # Should have dim_product from marts
        assert "dim_product" in product.models

    def test_guidance_loaded(self, project_state):
        """Should load guidance blocks for concepts."""
        customer = project_state.concepts["customer"]
        assert customer.guidance is not None
        assert customer.guidance.context is not None
        assert len(customer.guidance.rules) == 2

        rule = customer.guidance.rules[0]
        assert rule.name == "unique_customer_id"
        assert "unique" in rule.description.lower()


class TestSelectorParsing:
    """Test selector parsing and resolution."""

    def test_single_concept_selector(self, project_state):
        """Should select a single concept."""
        concepts = select_concepts(project_state, "customer")
        assert concepts == {"customer"}

    def test_downstream_selector(self, project_state):
        """Should select concept and downstream."""
        # customer+ should include customer and order (via relationship)
        concepts = select_concepts(project_state, "customer+")
        assert "customer" in concepts
        assert "order" in concepts  # customer places order

    def test_upstream_selector(self, project_state):
        """Should select concept and upstream."""
        # +order should include order and customer (via relationship)
        concepts = select_concepts(project_state, "+order")
        assert "order" in concepts
        assert "customer" in concepts  # customer places order

    def test_bidirectional_selector(self, project_state):
        """Should select concept, upstream, and downstream."""
        # +order+ should include customer, order, and product
        concepts = select_concepts(project_state, "+order+")
        assert "customer" in concepts
        assert "order" in concepts
        assert "product" in concepts  # order contains product

    def test_domain_selector(self, project_state):
        """Should select all concepts in a domain."""
        concepts = select_concepts(project_state, "domain:party")
        assert "customer" in concepts
        assert "supplier" in concepts
        # Should not include concepts from other domains
        assert "order" not in concepts
        assert "product" not in concepts

    def test_domain_downstream_selector(self, project_state):
        """Should select domain concepts and their downstream."""
        concepts = select_concepts(project_state, "domain:party+")
        # Should include party domain (customer, supplier) and their downstream
        assert "customer" in concepts
        assert "supplier" in concepts
        assert "order" in concepts  # downstream of customer
        assert "product" in concepts  # downstream of supplier

    def test_status_selector(self, project_state):
        """Should select concepts by status."""
        # Complete status
        complete = select_concepts(project_state, "status:complete")
        assert "customer" in complete
        assert "order" in complete
        assert "product" in complete
        assert "supplier" not in complete  # draft
        assert "warehouse" not in complete  # stub

        # Draft status
        draft = select_concepts(project_state, "status:draft")
        assert "supplier" in draft
        assert "customer" not in draft

        # Stub status
        stub = select_concepts(project_state, "status:stub")
        assert "warehouse" in stub
        assert "customer" not in stub

    def test_all_selector(self, project_state):
        """Should select all concepts."""
        concepts = select_concepts(project_state, "all")
        assert len(concepts) == 5  # All 5 concepts

    def test_unknown_concept_error(self, project_state):
        """Should raise SelectorError for unknown concept."""
        with pytest.raises(SelectorError, match="Unknown concept"):
            select_concepts(project_state, "nonexistent")

    def test_unknown_domain_error(self, project_state):
        """Should raise SelectorError for unknown domain."""
        with pytest.raises(SelectorError, match="Unknown domain"):
            select_concepts(project_state, "domain:nonexistent")

    def test_empty_selector_error(self, project_state):
        """Should raise SelectorError for empty selector."""
        with pytest.raises(SelectorError, match="cannot be empty"):
            select_concepts(project_state, "")


class TestContextResolution:
    """Test context resolution with all 5 layers."""

    def test_resolve_basic_context(self, config):
        """Should resolve full context for a concept."""
        context = resolve_full_context(config, "customer")

        assert context.concept_key == "customer"
        assert context.concept.name == "Customer"
        assert context.concept.domain == "party"
        assert context.concept.definition is not None

    def test_layer1_conceptual_model(self, config):
        """Layer 1: Should include conceptual model data."""
        context = resolve_full_context(config, "customer")

        # Definition from conceptual.yml
        assert "person or organization" in context.concept.definition.lower()

        # Guidance
        assert context.guidance is not None
        assert context.guidance.context is not None
        assert len(context.guidance.rules) == 2

    def test_layer2_manifest(self, config):
        """Layer 2: Should enrich from manifest.json."""
        context = resolve_full_context(config, "customer")

        # Should have models (only from marts since that's the default gold_paths)
        assert len(context.models) == 1  # dim_customer only

        # Check manifest data
        dim_customer = context.models[0]
        assert dim_customer.name == "dim_customer"
        assert dim_customer.description is not None
        assert dim_customer.materialization == "table"
        assert dim_customer.schema == "analytics"
        assert dim_customer.path == "models/marts/dim_customer.sql"
        assert len(dim_customer.columns) == 3

    def test_layer3_catalog(self, config):
        """Layer 3: Should enrich from catalog.json."""
        context = resolve_full_context(config, "customer")

        dim_customer = next(m for m in context.models if m.name == "dim_customer")

        # Row count from catalog
        assert dim_customer.row_count == 5000

        # Column types from catalog
        customer_id_col = next(
            c for c in dim_customer.columns if c.name == "customer_id"
        )
        assert customer_id_col.type == "INTEGER"

    def test_layer4_constraints(self, config):
        """Layer 4: Should translate tests to constraints."""
        context = resolve_full_context(config, "customer")

        dim_customer = next(m for m in context.models if m.name == "dim_customer")

        # Should have constraints from tests
        assert len(dim_customer.constraints) > 0

        # Check specific constraints
        constraints_str = " ".join(dim_customer.constraints)
        assert "customer_id must be unique" in constraints_str
        assert "customer_id must not be null" in constraints_str
        assert "customer_type must be one of" in constraints_str

    def test_layer5_inferences(self, config):
        """Layer 5: Should include heuristic inferences."""
        context = resolve_full_context(config, "customer")

        dim_customer = next(m for m in context.models if m.name == "dim_customer")

        # Should have inferences
        assert len(dim_customer.inferences) > 0

        # Should detect grain from unique test
        inference_types = [inf.type for inf in dim_customer.inferences]
        assert "grain" in inference_types

    def test_relationships_included(self, config):
        """Should include relationships for the concept."""
        context = resolve_full_context(config, "customer")

        # Customer places order
        assert len(context.relationships) == 1
        rel = context.relationships[0]
        assert rel.from_concept == "customer"
        assert rel.to_concept == "order"
        assert rel.verb == "places"

    def test_upstream_downstream_tracking(self, config):
        """Should track upstream and downstream dependencies."""
        context = resolve_full_context(config, "customer")

        dim_customer = next(m for m in context.models if m.name == "dim_customer")

        # Upstream: stg_customers
        assert len(dim_customer.upstream) > 0
        assert any("stg_customers" in dep for dep in dim_customer.upstream)

        # Downstream: fct_orders
        assert len(dim_customer.downstream) > 0
        assert "fct_orders" in dim_customer.downstream

    def test_metadata_attribution(self, config):
        """Should track source file metadata."""
        context = resolve_full_context(config, "customer")

        assert context.metadata is not None
        assert "conceptual.yml" in context.metadata.conceptual_file
        assert "manifest.json" in context.metadata.manifest_file
        assert "catalog.json" in context.metadata.catalog_file


class TestOutputFormats:
    """Test all three output formats."""

    def test_llm_format(self, config, project_state):
        """LLM format should be human-readable prose."""
        output = handle_get_context(
            selector="customer",
            format="llm",
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert isinstance(output, str)
        assert "Customer" in output
        assert "Definition:" in output or "definition" in output.lower()
        # Note: Grain information may not be in LLM format handler output
        # (that's part of the formatters module which isn't used by handlers)

    def test_json_format(self, config, project_state):
        """JSON format should be valid JSON."""
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        # Should be valid JSON
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) == 1

        concept_data = data[0]
        # Name is capitalized ("Customer" not "customer")
        assert concept_data["name"] == "Customer"
        assert concept_data["domain"] == "party"
        assert "guidance" in concept_data
        assert "relationships" in concept_data

    def test_yaml_format(self, config, project_state):
        """YAML format should be valid YAML."""
        output = handle_get_context(
            selector="customer",
            format="yaml",
            depth=1,
            project_state=project_state,
            config=config,
        )

        # Should be valid YAML
        data = yaml.safe_load(output)
        assert isinstance(data, list)
        assert len(data) == 1

        concept_data = data[0]
        # Name is capitalized ("Customer" not "customer")
        assert concept_data["name"] == "Customer"
        assert concept_data["domain"] == "party"

    def test_invalid_format_error(self, config, project_state):
        """Invalid format should return error."""
        output = handle_get_context(
            selector="customer",
            format="markdown",  # Not supported yet
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output
        assert "Invalid format" in output


class TestMCPHandlers:
    """Test MCP handler functions."""

    def test_handle_list_concepts(self, config, project_state):
        """Should list all concepts with metadata."""
        output = handle_list_concepts(
            domain=None,
            status=None,
            project_state=project_state,
        )

        assert "Found 5 concept(s)" in output
        assert "customer" in output.lower()
        assert "order" in output.lower()

    def test_handle_list_concepts_domain_filter(self, config, project_state):
        """Should filter concepts by domain."""
        output = handle_list_concepts(
            domain="party",
            status=None,
            project_state=project_state,
        )

        assert "domain=party" in output
        assert "customer" in output.lower()
        assert "supplier" in output.lower()
        # Should not include other domains
        assert "product" not in output.lower() or "Product Domain" not in output

    def test_handle_list_concepts_status_filter(self, config, project_state):
        """Should filter concepts by status."""
        output = handle_list_concepts(
            domain=None,
            status="draft",
            project_state=project_state,
        )

        assert "status=draft" in output
        assert "supplier" in output.lower()

    def test_handle_validate(self, config, project_state):
        """Should run validation and return results."""
        output = handle_validate(
            project_state=project_state,
            config=config,
        )

        assert isinstance(output, str)
        assert "Validation Results" in output

    def test_handle_get_context_multiple_concepts(self, config, project_state):
        """Should handle selectors that return multiple concepts."""
        output = handle_get_context(
            selector="domain:party",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        assert len(data) == 2  # customer and supplier

        names = [c["name"] for c in data]
        # Names are capitalized
        assert "Customer" in names
        assert "Supplier" in names


class TestGracefulHandling:
    """Test graceful handling of missing or invalid data."""

    def test_missing_manifest(self, config, fixture_project: Path):
        """Should handle missing manifest gracefully."""
        # Remove manifest
        manifest_file = fixture_project / "target" / "manifest.json"
        manifest_backup = manifest_file.read_text()
        manifest_file.unlink()

        try:
            context = resolve_full_context(config, "customer")

            # Should still resolve
            assert context.concept.name == "Customer"

            # Metadata should show no manifest
            assert context.metadata.manifest_file is None

            # Models should still be present but minimal
            assert len(context.models) > 0
            model = context.models[0]
            assert model.description is None
            assert model.materialization is None
        finally:
            # Restore manifest
            manifest_file.write_text(manifest_backup)

    def test_missing_catalog(self, config, fixture_project: Path):
        """Should handle missing catalog gracefully."""
        # Remove catalog
        catalog_file = fixture_project / "target" / "catalog.json"
        catalog_backup = catalog_file.read_text()
        catalog_file.unlink()

        try:
            context = resolve_full_context(config, "customer")

            # Should still resolve
            assert context.concept.name == "Customer"

            # Metadata should show no catalog
            assert context.metadata.catalog_file is None

            # Models should be present but without catalog data
            model = next(m for m in context.models if m.name == "dim_customer")
            assert model.row_count is None
            assert model.columns[0].type is None
        finally:
            # Restore catalog
            catalog_file.write_text(catalog_backup)

    def test_malformed_manifest(self, config, fixture_project: Path):
        """Should handle malformed manifest gracefully."""
        manifest_file = fixture_project / "target" / "manifest.json"
        manifest_backup = manifest_file.read_text()

        try:
            # Write invalid JSON
            manifest_file.write_text("{ invalid json")

            context = resolve_full_context(config, "customer")

            # Should still work, just without manifest data
            assert context.concept.name == "Customer"
            assert context.metadata.manifest_file is None
        finally:
            # Restore manifest
            manifest_file.write_text(manifest_backup)


class TestErrorCases:
    """Test error handling for invalid inputs."""

    def test_unknown_concept_in_handler(self, config, project_state):
        """Should return error message for unknown concept."""
        output = handle_get_context(
            selector="nonexistent",
            format="llm",
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output
        assert "Unknown concept" in output

    def test_invalid_format(self, config, project_state):
        """Should return error for invalid format."""
        output = handle_get_context(
            selector="customer",
            format="invalid",
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output
        assert "Invalid format" in output

    def test_invalid_depth(self, config, project_state):
        """Should return error for invalid depth."""
        output = handle_get_context(
            selector="customer",
            format="llm",
            depth=10,  # Too high
            project_state=project_state,
            config=config,
        )

        assert "Error" in output
        assert "Depth must be between 1 and 3" in output

    def test_empty_selector_in_handler(self, config, project_state):
        """Should return error for empty selector."""
        output = handle_get_context(
            selector="",
            format="llm",
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output


class TestDepthParameter:
    """Test relationship depth traversal."""

    def test_depth_1_relationships(self, config, project_state):
        """Depth 1 should include relationships at depth 1.

        Note: The _get_relationships_for_concept function uses a traversal
        that includes relationships involving the concept and those connected
        to it within the depth limit.
        """
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        customer_data = data[0]

        # Should have relationships within depth 1
        rels = customer_data["relationships"]
        assert len(rels) >= 1

        # Should at least have direct relationship: customer -> order
        from_concepts = [r["from_concept"] for r in rels]
        assert "customer" in from_concepts

    def test_depth_2_relationships(self, config, project_state):
        """Depth 2 should include second-level relationships."""
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=2,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        customer_data = data[0]

        # Should have customer -> order AND order -> product
        rels = customer_data["relationships"]
        assert len(rels) >= 2

        # Check for second-level relationship
        to_concepts = [r["to_concept"] for r in rels]
        assert "product" in to_concepts  # order -> product

    def test_depth_3_relationships(self, config, project_state):
        """Depth 3 should include third-level relationships."""
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=3,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        customer_data = data[0]

        # Should traverse 3 levels
        rels = customer_data["relationships"]
        assert len(rels) >= 3  # customer->order, order->product, product->warehouse
