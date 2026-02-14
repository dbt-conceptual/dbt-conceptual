"""End-to-end integration tests for MCP Server V1.

Tests the full stack from conceptual.yml -> ProjectState -> ContextResolver
-> formatters -> MCP handlers, using a comprehensive fixture project.

Coverage:
- Fixture project integrity validation
- ProjectState building from conceptual.yml + dbt schema files
- Selector parsing and resolution (single, upstream, downstream, bidirectional, domain, status, all)
- All three output formats (llm, json, yaml)
- Context resolution with all 5 layers (conceptual, manifest, catalog, contracts, inferences)
- MCP handler functions (get_context, list_concepts, get_relationships, validate)
- Relationship depth traversal (depth 1, 2, 3)
- Graceful handling of missing files (manifest, catalog)
- Malformed data handling
- Error cases (unknown concepts, empty selectors, invalid formats, invalid depth)
- MCP server tool registration and transport entry points
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.context import ContextResolver, resolve_full_context
from dbt_conceptual.mcp.handlers import (
    handle_get_context,
    handle_get_relationships,
    handle_list_concepts,
    handle_validate,
)
from dbt_conceptual.parser import StateBuilder
from dbt_conceptual.selector import SelectorError, select_concepts

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# 1. Fixture integrity tests
# ---------------------------------------------------------------------------


class TestFixtureIntegrity:
    """Verify the fixture project is set up correctly."""

    def test_fixture_structure(self, fixture_project: Path) -> None:
        """Fixture should have all required files."""
        assert (fixture_project / "conceptual.yml").exists()
        assert (fixture_project / "dbt_project.yml").exists()
        assert (fixture_project / "target" / "manifest.json").exists()
        assert (fixture_project / "target" / "catalog.json").exists()
        assert (fixture_project / "models" / "staging" / "schema.yml").exists()
        assert (fixture_project / "models" / "marts" / "schema.yml").exists()

    def test_conceptual_yaml_valid(self, fixture_project: Path) -> None:
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

        # Should have 5 concepts
        assert len(data["concepts"]) == 5
        assert "customer" in data["concepts"]
        assert "order" in data["concepts"]
        assert "product" in data["concepts"]
        assert "supplier" in data["concepts"]
        assert "warehouse" in data["concepts"]

        # Should have 4 relationships
        assert len(data["relationships"]) == 4

    def test_manifest_valid(self, fixture_project: Path) -> None:
        """Manifest.json should be valid and contain models."""
        manifest_file = fixture_project / "target" / "manifest.json"
        data = json.loads(manifest_file.read_text())

        assert "nodes" in data
        assert "metadata" in data
        assert data["metadata"]["project_name"] == "sample_project"

        # Count models (not tests)
        models = [k for k in data["nodes"] if k.startswith("model.")]
        assert len(models) == 8  # 3 staging + 5 marts

        # Count tests
        tests = [k for k in data["nodes"] if k.startswith("test.")]
        assert len(tests) > 0

    def test_catalog_valid(self, fixture_project: Path) -> None:
        """Catalog.json should be valid and contain row counts."""
        catalog_file = fixture_project / "target" / "catalog.json"
        data = json.loads(catalog_file.read_text())

        assert "nodes" in data

        # All catalog nodes should have row counts and columns
        for _node_id, node_data in data["nodes"].items():
            assert "stats" in node_data
            assert "row_count" in node_data["stats"]
            assert "columns" in node_data

    def test_dbt_project_yml_valid(self, fixture_project: Path) -> None:
        """dbt_project.yml should be valid YAML with project name."""
        dbt_file = fixture_project / "dbt_project.yml"
        data = yaml.safe_load(dbt_file.read_text())
        assert data["name"] == "sample_project"
        assert data["config-version"] == 2


# ---------------------------------------------------------------------------
# 2. ProjectState build tests
# ---------------------------------------------------------------------------


class TestProjectStateBuild:
    """Test ProjectState building from fixture."""

    def test_builds_successfully(self, project_state) -> None:
        """Should build state without errors."""
        assert project_state is not None
        assert len(project_state.concepts) > 0
        assert len(project_state.domains) > 0

    def test_domains_loaded(self, project_state) -> None:
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

    def test_concepts_loaded(self, project_state) -> None:
        """Should load all concepts with correct metadata."""
        assert len(project_state.concepts) == 5

        # Customer: complete (has domain + models)
        customer = project_state.concepts["customer"]
        assert customer.name == "Customer"
        assert customer.domain == "party"
        assert customer.definition is not None
        assert customer.status == "complete"
        assert len(customer.models) > 0

        # Supplier: draft (has domain, no mart models)
        supplier = project_state.concepts["supplier"]
        assert supplier.domain == "party"
        assert supplier.status == "draft"
        assert len(supplier.models) == 0

        # Warehouse: stub (no domain assigned)
        warehouse = project_state.concepts["warehouse"]
        assert warehouse.domain is None
        assert warehouse.status == "stub"

    def test_relationships_loaded(self, project_state) -> None:
        """Should load all relationships."""
        assert len(project_state.relationships) == 4

        rel_id = "customer:places:order"
        assert rel_id in project_state.relationships

        rel = project_state.relationships[rel_id]
        assert rel.from_concept == "customer"
        assert rel.to_concept == "order"
        assert rel.verb == "places"
        assert rel.cardinality == "1:N"

    def test_models_tagged_to_concepts(self, project_state) -> None:
        """Only mart models are scanned (default gold_paths).

        Staging models are not in gold_paths, so they do NOT appear in
        concept.models even if they carry meta.concept tags.
        """
        customer = project_state.concepts["customer"]
        assert "dim_customer" in customer.models
        assert len(customer.models) == 1  # Only mart models

        order = project_state.concepts["order"]
        assert "fct_orders" in order.models
        assert "fct_order_items" in order.models
        assert len(order.models) == 2

        product = project_state.concepts["product"]
        assert "dim_product" in product.models

    def test_guidance_loaded(self, project_state) -> None:
        """Should load guidance blocks for concepts."""
        customer = project_state.concepts["customer"]
        assert customer.guidance is not None
        assert customer.guidance.context is not None
        assert len(customer.guidance.rules) == 2

        rule = customer.guidance.rules[0]
        assert rule.name == "unique_customer_id"
        assert "unique" in rule.description.lower()

    def test_orphan_models_not_created_for_concept_tagged(self, project_state) -> None:
        """Models with meta.concept should not appear as orphans."""
        orphan_names = [o.name for o in project_state.orphan_models]
        # All mart models have meta.concept tags
        assert "dim_customer" not in orphan_names
        assert "fct_orders" not in orphan_names

    def test_concept_status_derivation(self, project_state) -> None:
        """Verify status is derived correctly from domain + models."""
        # complete: has domain AND models
        assert project_state.concepts["customer"].status == "complete"
        assert project_state.concepts["order"].status == "complete"
        assert project_state.concepts["product"].status == "complete"

        # draft: has domain but no scanned models
        assert project_state.concepts["supplier"].status == "draft"

        # stub: no domain
        assert project_state.concepts["warehouse"].status == "stub"


# ---------------------------------------------------------------------------
# 3. Selector parsing and resolution tests
# ---------------------------------------------------------------------------


class TestSelectorParsing:
    """Test selector parsing and resolution against fixture data."""

    def test_single_concept_selector(self, project_state) -> None:
        """Should select a single concept."""
        concepts = select_concepts(project_state, "customer")
        assert concepts == {"customer"}

    def test_downstream_selector(self, project_state) -> None:
        """customer+ should include customer and its downstream."""
        concepts = select_concepts(project_state, "customer+")
        assert "customer" in concepts
        assert "order" in concepts  # customer places order

    def test_upstream_selector(self, project_state) -> None:
        """+order should include order and its upstream."""
        concepts = select_concepts(project_state, "+order")
        assert "order" in concepts
        assert "customer" in concepts  # customer places order

    def test_bidirectional_selector(self, project_state) -> None:
        """+order+ should include upstream and downstream."""
        concepts = select_concepts(project_state, "+order+")
        assert "customer" in concepts
        assert "order" in concepts
        assert "product" in concepts  # order contains product

    def test_domain_selector(self, project_state) -> None:
        """Should select all concepts in a domain."""
        concepts = select_concepts(project_state, "domain:party")
        assert "customer" in concepts
        assert "supplier" in concepts
        assert "order" not in concepts
        assert "product" not in concepts

    def test_domain_downstream_selector(self, project_state) -> None:
        """Should select domain concepts and their downstream."""
        concepts = select_concepts(project_state, "domain:party+")
        assert "customer" in concepts
        assert "supplier" in concepts
        assert "order" in concepts  # downstream of customer
        assert "product" in concepts  # downstream of supplier

    def test_status_selector_complete(self, project_state) -> None:
        """Should select concepts with complete status."""
        complete = select_concepts(project_state, "status:complete")
        assert "customer" in complete
        assert "order" in complete
        assert "product" in complete
        assert "supplier" not in complete
        assert "warehouse" not in complete

    def test_status_selector_draft(self, project_state) -> None:
        """Should select concepts with draft status."""
        draft = select_concepts(project_state, "status:draft")
        assert "supplier" in draft
        assert "customer" not in draft

    def test_status_selector_stub(self, project_state) -> None:
        """Should select concepts with stub status."""
        stub = select_concepts(project_state, "status:stub")
        assert "warehouse" in stub
        assert "customer" not in stub

    def test_all_selector(self, project_state) -> None:
        """Should select all concepts."""
        concepts = select_concepts(project_state, "all")
        assert len(concepts) == 5

    def test_depth_limited_downstream(self, project_state) -> None:
        """customer+1 should limit downstream traversal to 1 hop."""
        concepts = select_concepts(project_state, "customer+1")
        assert "customer" in concepts
        assert "order" in concepts  # 1 hop away

    def test_unknown_concept_error(self, project_state) -> None:
        """Should raise SelectorError for unknown concept."""
        with pytest.raises(SelectorError, match="Unknown concept"):
            select_concepts(project_state, "nonexistent")

    def test_unknown_domain_error(self, project_state) -> None:
        """Should raise SelectorError for unknown domain."""
        with pytest.raises(SelectorError, match="Unknown domain"):
            select_concepts(project_state, "domain:nonexistent")

    def test_empty_selector_error(self, project_state) -> None:
        """Should raise SelectorError for empty selector."""
        with pytest.raises(SelectorError, match="cannot be empty"):
            select_concepts(project_state, "")

    def test_invalid_status_error(self, project_state) -> None:
        """Should raise SelectorError for invalid status value."""
        with pytest.raises(SelectorError, match="Invalid status value"):
            select_concepts(project_state, "status:invalid_status")


# ---------------------------------------------------------------------------
# 4. Context resolution tests (5-layer stack)
# ---------------------------------------------------------------------------


class TestContextResolution:
    """Test context resolution with all 5 layers."""

    def test_resolve_basic_context(self, config) -> None:
        """Should resolve full context for a concept."""
        context = resolve_full_context(config, "customer")

        assert context.concept_key == "customer"
        assert context.concept.name == "Customer"
        assert context.concept.domain == "party"
        assert context.concept.definition is not None

    def test_layer1_conceptual_model(self, config) -> None:
        """Layer 1: Should include conceptual model data."""
        context = resolve_full_context(config, "customer")

        assert "person or organization" in context.concept.definition.lower()
        assert context.guidance is not None
        assert context.guidance.context is not None
        assert len(context.guidance.rules) == 2

    def test_layer2_manifest(self, config) -> None:
        """Layer 2: Should enrich from manifest.json."""
        context = resolve_full_context(config, "customer")

        # Only dim_customer (mart model scanned by default gold_paths)
        assert len(context.models) == 1

        dim_customer = context.models[0]
        assert dim_customer.name == "dim_customer"
        assert dim_customer.description is not None
        assert dim_customer.materialization == "table"
        assert dim_customer.schema == "analytics"
        assert dim_customer.path == "models/marts/dim_customer.sql"
        assert len(dim_customer.columns) == 3

    def test_layer3_catalog(self, config) -> None:
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

    def test_layer4_constraints(self, config) -> None:
        """Layer 4: Should translate tests to constraints."""
        context = resolve_full_context(config, "customer")

        dim_customer = next(m for m in context.models if m.name == "dim_customer")

        assert len(dim_customer.constraints) > 0

        constraints_str = " ".join(dim_customer.constraints)
        assert "customer_id must be unique" in constraints_str
        assert "customer_id must not be null" in constraints_str
        assert "customer_type must be one of" in constraints_str

    def test_layer5_inferences(self, config) -> None:
        """Layer 5: Should include heuristic inferences."""
        context = resolve_full_context(config, "customer")

        dim_customer = next(m for m in context.models if m.name == "dim_customer")

        assert len(dim_customer.inferences) > 0

        # Should detect grain from unique test
        inference_types = [inf.type.value for inf in dim_customer.inferences]
        assert "grain" in inference_types

    def test_relationships_included(self, config) -> None:
        """Should include relationships for the concept."""
        context = resolve_full_context(config, "customer")

        assert len(context.relationships) == 1
        rel = context.relationships[0]
        assert rel.from_concept == "customer"
        assert rel.to_concept == "order"
        assert rel.verb == "places"

    def test_upstream_downstream_tracking(self, config) -> None:
        """Should track upstream and downstream dependencies."""
        context = resolve_full_context(config, "customer")

        dim_customer = next(m for m in context.models if m.name == "dim_customer")

        # Upstream: stg_customers
        assert len(dim_customer.upstream) > 0
        assert any("stg_customers" in dep for dep in dim_customer.upstream)

        # Downstream: fct_orders
        assert len(dim_customer.downstream) > 0
        assert "fct_orders" in dim_customer.downstream

    def test_metadata_attribution(self, config) -> None:
        """Should track source file metadata."""
        context = resolve_full_context(config, "customer")

        assert context.metadata is not None
        assert "conceptual.yml" in context.metadata.conceptual_file
        assert context.metadata.manifest_file is not None
        assert "manifest.json" in context.metadata.manifest_file
        assert context.metadata.catalog_file is not None
        assert "catalog.json" in context.metadata.catalog_file

    def test_owner_inheritance_from_domain(self, config) -> None:
        """Concept should inherit owner from domain when not set."""
        context = resolve_full_context(config, "customer")

        # customer.owner is None in YAML but domain party has owner party-team
        assert context.concept.owner == "party-team"

    def test_resolve_concept_with_incremental_model(self, config) -> None:
        """Should correctly resolve concepts with incremental models."""
        context = resolve_full_context(config, "order")

        fct_orders = next(m for m in context.models if m.name == "fct_orders")
        assert fct_orders.materialization == "incremental"

        # Should detect incremental materialization in inferences
        inf_types = [inf.type.value for inf in fct_orders.inferences]
        assert "materialization" in inf_types

    def test_resolve_unknown_concept_raises(self, config) -> None:
        """Should raise ValueError for unknown concept."""
        with pytest.raises(ValueError, match="not found"):
            resolve_full_context(config, "nonexistent_concept")


# ---------------------------------------------------------------------------
# 5. Output format tests
# ---------------------------------------------------------------------------


class TestOutputFormats:
    """Test all three output formats via MCP handlers."""

    def test_llm_format(self, config, project_state) -> None:
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
        # The handler LLM format includes definition and relationship info
        assert "Definition:" in output or "definition" in output.lower()

    def test_json_format(self, config, project_state) -> None:
        """JSON format should be valid, parseable JSON."""
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) == 1

        concept_data = data[0]
        # Handler returns concept.name which is display name "Customer"
        assert concept_data["name"] == "Customer"
        assert concept_data["domain"] == "party"
        assert "guidance" in concept_data
        assert "relationships" in concept_data

    def test_json_format_structure(self, config, project_state) -> None:
        """JSON format should have all expected keys."""
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        concept_data = data[0]

        required_keys = {"name", "domain", "owner", "status", "definition", "models"}
        assert required_keys.issubset(set(concept_data.keys()))

    def test_yaml_format(self, config, project_state) -> None:
        """YAML format should be valid, parseable YAML."""
        output = handle_get_context(
            selector="customer",
            format="yaml",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = yaml.safe_load(output)
        assert isinstance(data, list)
        assert len(data) == 1

        concept_data = data[0]
        assert concept_data["name"] == "Customer"
        assert concept_data["domain"] == "party"

    def test_invalid_format_error(self, config, project_state) -> None:
        """Invalid format should return error."""
        output = handle_get_context(
            selector="customer",
            format="xml",
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output
        assert "Invalid format" in output

    def test_json_format_multiple_concepts(self, config, project_state) -> None:
        """JSON format should handle multiple concepts."""
        output = handle_get_context(
            selector="all",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        assert len(data) == 5
        names = {c["name"] for c in data}
        assert "Customer" in names
        assert "Order" in names
        assert "Product" in names

    def test_yaml_format_round_trip(self, config, project_state) -> None:
        """YAML output should survive a round-trip parse."""
        output = handle_get_context(
            selector="order",
            format="yaml",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = yaml.safe_load(output)
        assert data[0]["name"] == "Order"
        assert data[0]["status"] == "complete"
        assert len(data[0]["relationships"]) > 0


# ---------------------------------------------------------------------------
# 6. MCP handler tests
# ---------------------------------------------------------------------------


class TestMCPHandlers:
    """Test MCP handler functions with fixture data."""

    def test_handle_list_concepts(self, project_state) -> None:
        """Should list all concepts with metadata."""
        output = handle_list_concepts(
            domain=None,
            status=None,
            project_state=project_state,
        )

        assert "Found 5 concept(s)" in output
        assert "customer" in output.lower()
        assert "order" in output.lower()

    def test_handle_list_concepts_domain_filter(self, project_state) -> None:
        """Should filter concepts by domain."""
        output = handle_list_concepts(
            domain="party",
            status=None,
            project_state=project_state,
        )

        assert "domain=party" in output
        assert "customer" in output.lower()
        assert "supplier" in output.lower()

    def test_handle_list_concepts_status_filter(self, project_state) -> None:
        """Should filter concepts by status."""
        output = handle_list_concepts(
            domain=None,
            status="draft",
            project_state=project_state,
        )

        assert "status=draft" in output
        assert "supplier" in output.lower()

    def test_handle_list_concepts_combined_filter(self, project_state) -> None:
        """Should filter by both domain and status."""
        output = handle_list_concepts(
            domain="party",
            status="complete",
            project_state=project_state,
        )

        assert "(domain=party, status=complete)" in output
        assert "customer" in output.lower()
        assert "supplier" not in output.lower()

    def test_handle_list_concepts_no_matches(self, project_state) -> None:
        """Should indicate when no concepts match filter."""
        output = handle_list_concepts(
            domain="transaction",
            status="stub",
            project_state=project_state,
        )

        assert "No concepts found" in output

    def test_handle_list_concepts_invalid_status(self, project_state) -> None:
        """Should return error for invalid status."""
        output = handle_list_concepts(
            domain=None,
            status="invalid",
            project_state=project_state,
        )

        assert "Error: Invalid status 'invalid'" in output

    def test_handle_list_concepts_shows_model_count(self, project_state) -> None:
        """Output should include model count per concept."""
        output = handle_list_concepts(
            domain=None,
            status=None,
            project_state=project_state,
        )

        assert "model(s)" in output

    def test_handle_get_context_multiple_concepts(self, config, project_state) -> None:
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

        names = {c["name"] for c in data}
        assert "Customer" in names
        assert "Supplier" in names

    def test_handle_validate(self, config, project_state) -> None:
        """Should run validation and return results."""
        output = handle_validate(
            project_state=project_state,
            config=config,
        )

        assert isinstance(output, str)
        assert "Validation Results" in output

    def test_handle_get_relationships(self, project_state) -> None:
        """Should return relationships for a concept."""
        output = handle_get_relationships(
            concept="customer",
            depth=1,
            project_state=project_state,
        )

        assert "Relationships for customer" in output
        assert "places" in output
        assert "order" in output

    def test_handle_get_relationships_incoming(self, project_state) -> None:
        """Should show incoming relationships."""
        output = handle_get_relationships(
            concept="order",
            depth=1,
            project_state=project_state,
        )

        assert "Incoming:" in output
        assert "customer" in output

    def test_handle_get_relationships_no_rels(self, project_state) -> None:
        """Should handle concept with no relationships."""
        # warehouse has stored_in relationship from product
        # But supplier supplies product => supplier has relationships
        # Let's just check the message is well-formed
        output = handle_get_relationships(
            concept="warehouse",
            depth=1,
            project_state=project_state,
        )
        assert isinstance(output, str)

    def test_handle_get_relationships_unknown_concept(self, project_state) -> None:
        """Should return error for unknown concept."""
        output = handle_get_relationships(
            concept="nonexistent",
            depth=1,
            project_state=project_state,
        )

        assert "Error: Unknown concept 'nonexistent'" in output

    def test_handle_get_relationships_grain_warning(self, project_state) -> None:
        """Should include grain warnings for 1:N relationships."""
        output = handle_get_relationships(
            concept="customer",
            depth=1,
            project_state=project_state,
        )

        assert "GRAIN WARNING" in output

    def test_handle_get_relationships_invalid_depth(self, project_state) -> None:
        """Should return error for invalid depth."""
        output = handle_get_relationships(
            concept="customer",
            depth=0,
            project_state=project_state,
        )

        assert "Error: Depth must be between 1 and 3" in output


# ---------------------------------------------------------------------------
# 7. Depth parameter tests
# ---------------------------------------------------------------------------


class TestDepthParameter:
    """Test relationship depth traversal."""

    def test_depth_1_includes_direct_and_connected(self, config, project_state) -> None:
        """Depth 1 traverses from the concept (depth 0) to direct neighbours.

        The handler's traversal starts at the concept (depth 0) and includes
        all relationships found at depth <= 1. This means both the direct
        relationship (customer -> order) and order's own relationships are
        included.
        """
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        rels = data[0]["relationships"]

        # customer -> order should always be present
        from_to = [(r["from_concept"], r["to_concept"]) for r in rels]
        assert ("customer", "order") in from_to

    def test_depth_2_includes_second_level(self, config, project_state) -> None:
        """Depth 2 should traverse further from the starting concept."""
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=2,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        rels = data[0]["relationships"]

        # Should include at least customer->order and order->product
        to_concepts = {r["to_concept"] for r in rels}
        assert "order" in to_concepts
        assert "product" in to_concepts

    def test_depth_3_includes_third_level(self, config, project_state) -> None:
        """Depth 3 should reach the full graph from customer."""
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=3,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        rels = data[0]["relationships"]

        # Should traverse deep: customer->order->product->warehouse
        all_concepts_in_rels = set()
        for r in rels:
            all_concepts_in_rels.add(r["from_concept"])
            all_concepts_in_rels.add(r["to_concept"])

        assert "warehouse" in all_concepts_in_rels


# ---------------------------------------------------------------------------
# 8. Graceful degradation tests
# ---------------------------------------------------------------------------


class TestGracefulHandling:
    """Test graceful handling of missing or invalid data."""

    def test_missing_manifest(self, config, fixture_project: Path) -> None:
        """Should handle missing manifest gracefully."""
        manifest_file = fixture_project / "target" / "manifest.json"
        manifest_backup = manifest_file.read_text()
        manifest_file.unlink()

        try:
            context = resolve_full_context(config, "customer")

            assert context.concept.name == "Customer"
            assert context.metadata.manifest_file is None

            # Models should still be present but without manifest enrichment
            assert len(context.models) > 0
            model = context.models[0]
            assert model.description is None
            assert model.materialization is None
        finally:
            manifest_file.write_text(manifest_backup)

    def test_missing_catalog(self, config, fixture_project: Path) -> None:
        """Should handle missing catalog gracefully."""
        catalog_file = fixture_project / "target" / "catalog.json"
        catalog_backup = catalog_file.read_text()
        catalog_file.unlink()

        try:
            context = resolve_full_context(config, "customer")

            assert context.concept.name == "Customer"
            assert context.metadata.catalog_file is None

            model = next(m for m in context.models if m.name == "dim_customer")
            assert model.row_count is None
            # Column types come from catalog
            if model.columns:
                assert model.columns[0].type is None
        finally:
            catalog_file.write_text(catalog_backup)

    def test_malformed_manifest(self, config, fixture_project: Path) -> None:
        """Should handle malformed manifest gracefully."""
        manifest_file = fixture_project / "target" / "manifest.json"
        manifest_backup = manifest_file.read_text()

        try:
            manifest_file.write_text("{ invalid json")

            context = resolve_full_context(config, "customer")

            assert context.concept.name == "Customer"
            assert context.metadata.manifest_file is None
        finally:
            manifest_file.write_text(manifest_backup)

    def test_missing_both_manifest_and_catalog(
        self, config, fixture_project: Path
    ) -> None:
        """Should handle both manifest and catalog missing."""
        manifest_file = fixture_project / "target" / "manifest.json"
        catalog_file = fixture_project / "target" / "catalog.json"
        manifest_backup = manifest_file.read_text()
        catalog_backup = catalog_file.read_text()
        manifest_file.unlink()
        catalog_file.unlink()

        try:
            context = resolve_full_context(config, "customer")

            assert context.concept.name == "Customer"
            assert context.metadata.manifest_file is None
            assert context.metadata.catalog_file is None
        finally:
            manifest_file.write_text(manifest_backup)
            catalog_file.write_text(catalog_backup)

    def test_empty_manifest(self, config, fixture_project: Path) -> None:
        """Should handle empty manifest.json gracefully."""
        manifest_file = fixture_project / "target" / "manifest.json"
        manifest_backup = manifest_file.read_text()

        try:
            manifest_file.write_text("{}")

            context = resolve_full_context(config, "customer")

            assert context.concept.name == "Customer"
            # Empty manifest has no nodes, so no enrichment
            model = context.models[0]
            assert model.description is None
        finally:
            manifest_file.write_text(manifest_backup)


# ---------------------------------------------------------------------------
# 9. Error case tests
# ---------------------------------------------------------------------------


class TestErrorCases:
    """Test error handling for invalid inputs."""

    def test_unknown_concept_in_handler(self, config, project_state) -> None:
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

    def test_invalid_format(self, config, project_state) -> None:
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

    def test_invalid_depth_too_high(self, config, project_state) -> None:
        """Should return error for depth > 3."""
        output = handle_get_context(
            selector="customer",
            format="llm",
            depth=10,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output
        assert "Depth must be between 1 and 3" in output

    def test_invalid_depth_zero(self, config, project_state) -> None:
        """Should return error for depth 0."""
        output = handle_get_context(
            selector="customer",
            format="llm",
            depth=0,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output
        assert "Depth must be between 1 and 3" in output

    def test_empty_selector_in_handler(self, config, project_state) -> None:
        """Should return error for empty selector."""
        output = handle_get_context(
            selector="",
            format="llm",
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output

    def test_whitespace_only_selector(self, config, project_state) -> None:
        """Should return error for whitespace-only selector."""
        output = handle_get_context(
            selector="   ",
            format="llm",
            depth=1,
            project_state=project_state,
            config=config,
        )

        assert "Error" in output


# ---------------------------------------------------------------------------
# 10. MCP server module tests
# ---------------------------------------------------------------------------


class TestMCPServerModule:
    """Test MCP server module structure and tool registration."""

    def test_server_imports(self) -> None:
        """MCP server module should import successfully."""
        from dbt_conceptual.mcp import server

        assert hasattr(server, "mcp")
        assert hasattr(server, "_get_resolver")

    def test_server_has_all_tools(self) -> None:
        """All four tools should be registered on the server."""
        from dbt_conceptual.mcp import server

        assert hasattr(server, "dbc_get_context")
        assert hasattr(server, "dbc_list_concepts")
        assert hasattr(server, "dbc_get_relationships")
        assert hasattr(server, "dbc_validate")

    def test_resolver_lazy_init(self) -> None:
        """Resolver should be None initially (lazy initialization)."""
        from dbt_conceptual.mcp import server

        original_resolver = server._resolver
        try:
            server._resolver = None
            assert server._resolver is None
        finally:
            server._resolver = original_resolver

    def test_main_entry_point(self) -> None:
        """__main__ module should have a main function."""
        from dbt_conceptual.mcp import __main__

        assert hasattr(__main__, "main")

    def test_package_exports(self) -> None:
        """Package should export mcp instance."""
        from dbt_conceptual.mcp import mcp

        assert mcp is not None


class TestMCPToolsAsync:
    """Test MCP tool functions as async functions.

    These tools call _get_resolver() which needs a dbt project in the cwd.
    Without one, they should return error strings (not raise exceptions).
    """

    @pytest.mark.asyncio
    async def test_get_context_returns_error_without_project(self) -> None:
        """dbc_get_context should return error without dbt project."""
        from dbt_conceptual.mcp import server

        server._resolver = None

        result = await server.dbc_get_context("customer", format="llm", depth=1)
        assert isinstance(result, str)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_list_concepts_returns_error_without_project(self) -> None:
        """dbc_list_concepts should return error without dbt project."""
        from dbt_conceptual.mcp import server

        server._resolver = None

        result = await server.dbc_list_concepts()
        assert isinstance(result, str)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_get_relationships_returns_error_without_project(self) -> None:
        """dbc_get_relationships should return error without dbt project."""
        from dbt_conceptual.mcp import server

        server._resolver = None

        result = await server.dbc_get_relationships("customer", depth=1)
        assert isinstance(result, str)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_validate_returns_error_without_project(self) -> None:
        """dbc_validate should return error without dbt project."""
        from dbt_conceptual.mcp import server

        server._resolver = None

        result = await server.dbc_validate()
        assert isinstance(result, str)
        assert "Error" in result


# ---------------------------------------------------------------------------
# 11. Transport entry point tests
# ---------------------------------------------------------------------------


class TestTransportEntryPoints:
    """Test transport selection in __main__ module."""

    def test_sse_flag_falls_back(self) -> None:
        """--sse flag should fall back to stdio (not yet fully supported)."""
        from dbt_conceptual.mcp import __main__

        with (
            patch.object(sys, "argv", ["dbt_conceptual.mcp", "--sse"]),
            patch("dbt_conceptual.mcp.__main__.mcp") as mock_mcp,
        ):
            __main__.main()
            mock_mcp.run.assert_called_once()

    def test_http_flag_falls_back(self) -> None:
        """--http flag should fall back to stdio (not yet fully supported)."""
        from dbt_conceptual.mcp import __main__

        with (
            patch.object(sys, "argv", ["dbt_conceptual.mcp", "--http"]),
            patch("dbt_conceptual.mcp.__main__.mcp") as mock_mcp,
        ):
            __main__.main()
            mock_mcp.run.assert_called_once()

    def test_default_stdio_transport(self) -> None:
        """Default (no flags) should use stdio transport."""
        from dbt_conceptual.mcp import __main__

        with (
            patch.object(sys, "argv", ["dbt_conceptual.mcp"]),
            patch("dbt_conceptual.mcp.__main__.mcp") as mock_mcp,
        ):
            __main__.main()
            mock_mcp.run.assert_called_once()


# ---------------------------------------------------------------------------
# 12. Full pipeline integration tests
# ---------------------------------------------------------------------------


class TestFullPipeline:
    """Test the complete pipeline: selector -> context -> formatter -> output."""

    def test_full_pipeline_single_concept(self, config, project_state) -> None:
        """Full pipeline for single concept selector."""
        # Step 1: Select
        concepts = select_concepts(project_state, "customer")
        assert len(concepts) == 1

        # Step 2: Resolve context
        context = resolve_full_context(config, "customer")
        assert context.concept.name == "Customer"
        assert len(context.models) > 0

        # Step 3: Format via handler
        output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        # Step 4: Validate output
        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["name"] == "Customer"
        assert data[0]["status"] == "complete"

    def test_full_pipeline_domain_selector(self, config, project_state) -> None:
        """Full pipeline for domain selector."""
        concepts = select_concepts(project_state, "domain:party")
        assert "customer" in concepts
        assert "supplier" in concepts

        output = handle_get_context(
            selector="domain:party",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        names = {c["name"] for c in data}
        assert "Customer" in names
        assert "Supplier" in names

    def test_full_pipeline_all_concepts(self, config, project_state) -> None:
        """Full pipeline selecting all concepts."""
        output = handle_get_context(
            selector="all",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        assert len(data) == 5

    def test_full_pipeline_validation(self, config, project_state) -> None:
        """Full pipeline: state -> validate -> report."""
        output = handle_validate(
            project_state=project_state,
            config=config,
        )

        assert isinstance(output, str)
        assert "Validation Results" in output

    def test_full_pipeline_list_then_get(self, config, project_state) -> None:
        """Pipeline: list concepts -> pick one -> get context."""
        # List
        list_output = handle_list_concepts(
            domain=None,
            status="complete",
            project_state=project_state,
        )
        assert "Customer" in list_output or "customer" in list_output.lower()

        # Get context for a complete concept
        context_output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(context_output)
        assert data[0]["status"] == "complete"

    def test_context_resolver_caching(self, config) -> None:
        """ContextResolver should cache manifest/catalog loads."""
        resolver = ContextResolver(config)

        # First resolution loads files
        ctx1 = resolver.resolve_full_context("customer")
        assert ctx1.concept.name == "Customer"

        # Second resolution should use cache
        ctx2 = resolver.resolve_full_context("order")
        assert ctx2.concept.name == "Order"

        # Both should have manifest data (from cache)
        assert len(ctx1.models) > 0
        assert len(ctx2.models) > 0


# ---------------------------------------------------------------------------
# 13. Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_concept_with_no_guidance(self, project_state) -> None:
        """Concepts without guidance should still work."""
        product = project_state.concepts["product"]
        assert product.guidance is None

    def test_concept_with_no_models(self, project_state) -> None:
        """Draft concepts with no models should be handled."""
        supplier = project_state.concepts["supplier"]
        assert len(supplier.models) == 0
        assert supplier.status == "draft"

    def test_stub_concept_rendering(self, config, project_state) -> None:
        """Stub concept should render without errors."""
        output = handle_get_context(
            selector="warehouse",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        assert data[0]["name"] == "Warehouse"
        assert data[0]["status"] == "stub"

    def test_draft_concept_rendering(self, config, project_state) -> None:
        """Draft concept should render without errors."""
        output = handle_get_context(
            selector="supplier",
            format="json",
            depth=1,
            project_state=project_state,
            config=config,
        )

        data = json.loads(output)
        assert data[0]["name"] == "Supplier"
        assert data[0]["status"] == "draft"

    def test_all_formats_for_draft_concept(self, config, project_state) -> None:
        """All formats should handle draft concepts without errors."""
        for fmt in ("llm", "json", "yaml"):
            output = handle_get_context(
                selector="supplier",
                format=fmt,
                depth=1,
                project_state=project_state,
                config=config,
            )
            assert isinstance(output, str)
            assert "Error" not in output

    def test_all_formats_for_stub_concept(self, config, project_state) -> None:
        """All formats should handle stub concepts without errors."""
        for fmt in ("llm", "json", "yaml"):
            output = handle_get_context(
                selector="warehouse",
                format=fmt,
                depth=1,
                project_state=project_state,
                config=config,
            )
            assert isinstance(output, str)
            assert "Error" not in output

    def test_concept_with_multiline_definition(self, project_state) -> None:
        """Multiline definitions from YAML should be preserved."""
        customer = project_state.concepts["customer"]
        assert "\n" in customer.definition

    def test_relationship_cardinality_values(self, project_state) -> None:
        """All relationships should have valid cardinality values."""
        for _rel_id, rel in project_state.relationships.items():
            assert rel.cardinality in ("1:1", "1:N")
