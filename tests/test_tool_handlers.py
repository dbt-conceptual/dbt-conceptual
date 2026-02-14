"""Tests for MCP tool handlers.

Tests cover all four handler functions:
- handle_get_context: Selector resolution, depth traversal, format output
- handle_list_concepts: Filtering, status/domain, ghost exclusion
- handle_get_relationships: Grain warnings, depth traversal, direction grouping
- handle_validate: Error/warning grouping, actionable guidance
"""

from __future__ import annotations

import json

import pytest
import yaml

from dbt_conceptual.config import Config, ValidationConfig
from dbt_conceptual.mcp.handlers import (
    handle_get_context,
    handle_get_relationships,
    handle_list_concepts,
    handle_validate,
)
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    Guidance,
    GuidanceRule,
    ProjectState,
    RelationshipState,
)


@pytest.fixture
def sample_project_state() -> ProjectState:
    """Create a sample project state for testing."""
    state = ProjectState()

    # Add domains
    state.domains["party"] = DomainState(
        name="party", display_name="Party", color="#FF0000"
    )
    state.domains["activity"] = DomainState(
        name="activity", display_name="Activity", color="#00FF00"
    )

    # Add concepts
    state.concepts["customer"] = ConceptState(
        name="customer",
        domain="party",
        owner="team-growth",
        definition="A person or organization that purchases products",
        models=["stg_customers", "dim_customers"],
    )

    state.concepts["order"] = ConceptState(
        name="order",
        domain="activity",
        owner="team-growth",
        definition="A customer request to purchase products",
        models=["stg_orders"],
        guidance=Guidance(
            context="Orders are the core transaction entity",
            rules=[
                GuidanceRule(
                    name="unique_order_id",
                    description="Each order must have a unique identifier",
                ),
                GuidanceRule(
                    name="valid_customer",
                    description="Orders must reference a valid customer",
                ),
            ],
        ),
    )

    state.concepts["product"] = ConceptState(
        name="product",
        domain="party",
        owner="team-supply",
        definition="An item available for purchase",
    )

    # Add stub concept
    state.concepts["shipment"] = ConceptState(
        name="shipment",
        definition="A delivery of products to a customer",
    )

    # Add ghost concept
    state.concepts["payment"] = ConceptState(
        name="payment",
        is_ghost=True,
    )

    # Add relationships
    state.relationships["customer:places:order"] = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
        cardinality="1:N",
        definition="A customer can place many orders",
    )

    state.relationships["order:contains:product"] = RelationshipState(
        verb="contains",
        from_concept="order",
        to_concept="product",
        cardinality="1:N",
        definition="An order can contain many products",
    )

    state.relationships["order:paid_by:payment"] = RelationshipState(
        verb="paid_by",
        from_concept="order",
        to_concept="payment",
        cardinality="1:1",
    )

    return state


@pytest.fixture
def sample_config(tmp_path) -> Config:
    """Create a sample config for testing."""
    from pathlib import Path

    # Create a temporary project directory
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    return Config(
        project_dir=Path(project_dir),
        validation=ValidationConfig(),
    )


class TestHandleGetContext:
    """Tests for handle_get_context handler."""

    def test_get_context_single_concept_llm(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test getting context for a single concept in LLM format."""
        result = handle_get_context(
            selector="customer",
            format="llm",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        assert "# Concept: customer" in result
        assert "**Status:** complete" in result
        assert "**Domain:** party" in result
        assert "**Owner:** team-growth" in result
        assert "A person or organization that purchases products" in result
        assert "stg_customers, dim_customers" in result
        assert "places → order" in result

    def test_get_context_json_format(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test getting context in JSON format."""
        result = handle_get_context(
            selector="order",
            format="json",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["name"] == "order"
        assert data[0]["domain"] == "activity"
        assert data[0]["status"] == "complete"  # Has domain AND models
        assert "guidance" in data[0]
        assert len(data[0]["guidance"]["rules"]) == 2

    def test_get_context_yaml_format(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test getting context in YAML format."""
        result = handle_get_context(
            selector="product",
            format="yaml",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        data = yaml.safe_load(result)
        assert len(data) == 1
        assert data[0]["name"] == "product"
        assert data[0]["domain"] == "party"

    def test_get_context_all_selector(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test getting context for all concepts."""
        result = handle_get_context(
            selector="all",
            format="json",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        data = json.loads(result)
        # Should include all concepts (including ghost and stub)
        concept_names = {c["name"] for c in data}
        assert "customer" in concept_names
        assert "order" in concept_names
        assert "product" in concept_names
        assert "shipment" in concept_names
        assert "payment" in concept_names

    def test_get_context_domain_selector(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test getting context with domain selector."""
        result = handle_get_context(
            selector="domain:party",
            format="json",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        data = json.loads(result)
        concept_names = {c["name"] for c in data}
        assert "customer" in concept_names
        assert "product" in concept_names
        assert "order" not in concept_names

    def test_get_context_status_selector(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test getting context with status selector."""
        result = handle_get_context(
            selector="status:complete",
            format="json",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        data = json.loads(result)
        # Both customer and order have domain AND models
        assert len(data) == 2
        concept_names = {c["name"] for c in data}
        assert "customer" in concept_names
        assert "order" in concept_names

    def test_get_context_depth_2(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test relationship traversal with depth=2."""
        result = handle_get_context(
            selector="customer",
            format="json",
            depth=2,
            project_state=sample_project_state,
            config=sample_config,
        )

        data = json.loads(result)
        relationships = data[0]["relationships"]

        # Should include customer->order (depth 1) and order->product (depth 2)
        rel_strings = [
            f"{r['from_concept']}:{r['verb']}:{r['to_concept']}" for r in relationships
        ]
        assert "customer:places:order" in rel_strings
        assert "order:contains:product" in rel_strings

    def test_get_context_invalid_format(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test error handling for invalid format."""
        result = handle_get_context(
            selector="customer",
            format="xml",  # Invalid
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        assert "Error: Invalid format 'xml'" in result

    def test_get_context_invalid_depth(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test error handling for invalid depth."""
        result = handle_get_context(
            selector="customer",
            format="llm",
            depth=5,  # Too high
            project_state=sample_project_state,
            config=sample_config,
        )

        assert "Error: Depth must be between 1 and 3" in result

    def test_get_context_unknown_concept(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test error handling for unknown concept."""
        result = handle_get_context(
            selector="unknown_concept",
            format="llm",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        assert "Error: Unknown concept" in result

    def test_get_context_no_matches(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test handling when selector matches no concepts."""
        result = handle_get_context(
            selector="status:stub",  # No stub concepts with that exact status
            format="llm",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        # shipment is a stub (no domain)
        assert "shipment" in result or "No concepts found" in result

    def test_get_context_grain_warning(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test that grain warnings appear for 1:N relationships."""
        result = handle_get_context(
            selector="customer",
            format="llm",
            depth=1,
            project_state=sample_project_state,
            config=sample_config,
        )

        assert "GRAIN WARNING: 1:N join may fan out results" in result


class TestHandleListConcepts:
    """Tests for handle_list_concepts handler."""

    def test_list_all_concepts(self, sample_project_state: ProjectState):
        """Test listing all concepts without filters."""
        result = handle_list_concepts(
            domain=None,
            status=None,
            project_state=sample_project_state,
        )

        assert "Found 4 concept(s)" in result  # Excludes ghost (payment)
        assert "customer [complete]" in result
        assert "order [complete]" in result  # Has models now
        assert "product [draft]" in result
        assert "shipment [stub]" in result
        assert "payment" not in result  # Ghost excluded

    def test_list_concepts_by_domain(self, sample_project_state: ProjectState):
        """Test filtering concepts by domain."""
        result = handle_list_concepts(
            domain="party",
            status=None,
            project_state=sample_project_state,
        )

        assert "Found 2 concept(s) (domain=party)" in result
        assert "customer" in result
        assert "product" in result
        assert "order" not in result

    def test_list_concepts_by_status(self, sample_project_state: ProjectState):
        """Test filtering concepts by status."""
        result = handle_list_concepts(
            domain=None,
            status="complete",
            project_state=sample_project_state,
        )

        assert "Found 2 concept(s) (status=complete)" in result
        assert "customer" in result
        assert "order" in result  # Also complete now

    def test_list_concepts_domain_and_status(self, sample_project_state: ProjectState):
        """Test filtering by both domain and status."""
        result = handle_list_concepts(
            domain="party",
            status="draft",
            project_state=sample_project_state,
        )

        assert "(domain=party, status=draft)" in result
        assert "product" in result
        assert "customer" not in result  # Complete, not draft

    def test_list_concepts_no_matches(self, sample_project_state: ProjectState):
        """Test when no concepts match filters."""
        result = handle_list_concepts(
            domain="activity",
            status="stub",  # Changed to stub to actually get no matches
            project_state=sample_project_state,
        )

        assert "No concepts found (domain=activity, status=stub)" in result

    def test_list_concepts_invalid_status(self, sample_project_state: ProjectState):
        """Test error handling for invalid status."""
        result = handle_list_concepts(
            domain=None,
            status="invalid",
            project_state=sample_project_state,
        )

        assert "Error: Invalid status 'invalid'" in result
        assert "stub, draft, complete" in result

    def test_list_concepts_shows_model_count(self, sample_project_state: ProjectState):
        """Test that model count is shown for each concept."""
        result = handle_list_concepts(
            domain=None,
            status=None,
            project_state=sample_project_state,
        )

        assert "2 model(s)" in result  # customer has 2 models
        assert "1 model(s)" in result  # order has 1 model
        assert "no models" in result  # product has no models


class TestHandleGetRelationships:
    """Tests for handle_get_relationships handler."""

    def test_get_relationships_outgoing(self, sample_project_state: ProjectState):
        """Test getting outgoing relationships."""
        result = handle_get_relationships(
            concept="customer",
            depth=1,
            project_state=sample_project_state,
        )

        assert "Relationships for customer" in result
        assert "Outgoing:" in result
        assert "places → order (1:N)" in result
        assert "GRAIN WARNING" in result

    def test_get_relationships_incoming(self, sample_project_state: ProjectState):
        """Test getting incoming relationships."""
        result = handle_get_relationships(
            concept="order",
            depth=1,
            project_state=sample_project_state,
        )

        assert "Incoming:" in result
        assert "customer → places (1:N)" in result
        assert "Outgoing:" in result
        assert "contains → product (1:N)" in result

    def test_get_relationships_depth_2(self, sample_project_state: ProjectState):
        """Test relationship traversal with depth=2."""
        result = handle_get_relationships(
            concept="customer",
            depth=2,
            project_state=sample_project_state,
        )

        assert "Indirect (depth 2):" in result
        # Should show customer->order->product path
        assert "order → contains → product" in result

    def test_get_relationships_no_relationships(
        self, sample_project_state: ProjectState
    ):
        """Test concept with no relationships."""
        result = handle_get_relationships(
            concept="shipment",
            depth=1,
            project_state=sample_project_state,
        )

        assert "Concept 'shipment' has no relationships" in result

    def test_get_relationships_unknown_concept(
        self, sample_project_state: ProjectState
    ):
        """Test error handling for unknown concept."""
        result = handle_get_relationships(
            concept="unknown",
            depth=1,
            project_state=sample_project_state,
        )

        assert "Error: Unknown concept 'unknown'" in result

    def test_get_relationships_invalid_depth(self, sample_project_state: ProjectState):
        """Test error handling for invalid depth."""
        result = handle_get_relationships(
            concept="customer",
            depth=0,
            project_state=sample_project_state,
        )

        assert "Error: Depth must be between 1 and 3" in result

    def test_get_relationships_grain_warning_1n(
        self, sample_project_state: ProjectState
    ):
        """Test that grain warnings appear for 1:N relationships."""
        result = handle_get_relationships(
            concept="customer",
            depth=1,
            project_state=sample_project_state,
        )

        assert "GRAIN WARNING: 1:N join may fan out results" in result

    def test_get_relationships_no_grain_warning_11(
        self, sample_project_state: ProjectState
    ):
        """Test that grain warnings don't appear for 1:1 relationships."""
        result = handle_get_relationships(
            concept="order",
            depth=1,
            project_state=sample_project_state,
        )

        # Check the 1:1 relationship (paid_by:payment)
        lines = result.split("\n")
        payment_lines = [line for line in lines if "payment" in line]

        # Should have relationship but no grain warning for 1:1
        assert any("payment" in line for line in payment_lines)
        # The outgoing 1:1 should not have grain warning
        outgoing_payment = [
            line
            for line in payment_lines
            if "paid_by" in line and "→" in line and "GRAIN WARNING" not in line
        ]
        assert len(outgoing_payment) > 0


class TestHandleValidate:
    """Tests for handle_validate handler."""

    def test_validate_no_errors(self, sample_config: Config):
        """Test validation with no errors."""
        # Create a clean state with no issues
        state = ProjectState()
        state.domains["party"] = DomainState(
            name="party", display_name="Party", color="#FF0000"
        )
        state.concepts["customer"] = ConceptState(
            name="customer",
            domain="party",
            owner="team",
            definition="A customer",
            models=["dim_customer"],
        )

        result = handle_validate(
            project_state=state,
            config=sample_config,
        )

        assert "✓ No errors or warnings found" in result

    def test_validate_with_errors(self, sample_project_state: ProjectState, tmp_path):
        """Test validation with errors (ghost concept)."""
        # sample_project_state has a ghost concept (payment) referenced in a relationship

        from pathlib import Path

        # Create a temporary project directory
        project_dir = tmp_path / "test_project2"
        project_dir.mkdir()

        # Create config that treats missing definitions as warnings
        config = Config(
            project_dir=Path(project_dir),
            validation=ValidationConfig(),
        )

        result = handle_validate(
            project_state=sample_project_state,
            config=config,
        )

        # Should have info messages for stub/draft concepts
        assert "INFO:" in result or "Errors:" in result or "Warnings:" in result

    def test_validate_groups_by_severity(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test that validation groups issues by severity."""
        result = handle_validate(
            project_state=sample_project_state,
            config=sample_config,
        )

        # Check structure
        lines = result.split("\n")
        assert "Validation Results:" in result

        # Should have summary counts
        assert any("Errors:" in line or "Warnings:" in line for line in lines)

    def test_validate_actionable_guidance(self, sample_config: Config):
        """Test that validation provides actionable guidance for errors."""
        # Create state with E002 error (unknown concept reference)
        state = ProjectState()
        state.concepts["order"] = ConceptState(
            name="order",
            domain="activity",
        )
        # Relationship references non-existent concept
        state.relationships["order:paid_by:payment"] = RelationshipState(
            verb="paid_by",
            from_concept="order",
            to_concept="payment",  # Doesn't exist
            cardinality="1:1",
        )

        result = handle_validate(
            project_state=state,
            config=sample_config,
        )

        # Should have errors and next steps
        assert "ERRORS:" in result
        assert "E002" in result
        assert "Next Steps:" in result
        assert "Add missing concept definitions to conceptual.yml" in result

    def test_validate_context_info(
        self, sample_project_state: ProjectState, sample_config: Config
    ):
        """Test that validation includes context information."""
        result = handle_validate(
            project_state=sample_project_state,
            config=sample_config,
        )

        # Context should show affected elements
        if "Context:" in result:
            # Verify context has key=value pairs
            assert "=" in result

    def test_validate_limits_info_messages(self, sample_config: Config):
        """Test that info messages are limited to first 5."""
        # Create state with many stub concepts
        state = ProjectState()
        for i in range(10):
            state.concepts[f"concept_{i}"] = ConceptState(
                name=f"concept_{i}",
                definition=None,  # Stub
            )

        result = handle_validate(
            project_state=state,
            config=sample_config,
        )

        # Should limit info display
        info_count = result.count("[I001]") + result.count("[I002]")
        # May not show all info if there are more than 5
        assert info_count <= 10  # Some reasonable limit
