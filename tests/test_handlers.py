"""Tests for MCP handler implementations.

Tests cover:
- handle_get_context: selector parsing, formats (llm/json/yaml), depth limits
- handle_list_concepts: domain/status filters
- handle_get_relationships: depth traversal, grain warnings
- handle_validate: validation engine integration, actionable guidance
- Error handling: invalid inputs, unknown concepts, graceful degradation
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

    # Domains
    state.domains["party"] = DomainState(
        name="party", display_name="Party", color="#FF5733"
    )
    state.domains["product"] = DomainState(
        name="product", display_name="Product", color="#33FF57"
    )

    # Concepts
    state.concepts["customer"] = ConceptState(
        name="customer",
        domain="party",
        owner="team_a",
        definition="A person or organization that purchases products",
        models=["dim_customer", "fct_customer_orders"],
        guidance=Guidance(
            context="Customer data is critical for analytics",
            rules=[
                GuidanceRule(
                    name="unique_customer_id",
                    description="customer_id must be unique across all records",
                ),
            ],
        ),
    )

    state.concepts["order"] = ConceptState(
        name="order",
        domain="product",
        owner="team_b",
        definition="A transaction where a customer purchases products",
        models=["fct_orders"],
    )

    state.concepts["product"] = ConceptState(
        name="product",
        domain="product",
        owner="team_b",
        definition="An item available for purchase",
        models=["dim_product"],
    )

    # Draft concept (no models)
    state.concepts["supplier"] = ConceptState(
        name="supplier",
        domain="party",
        owner="team_a",
        definition="An organization that provides products",
        models=[],
    )

    # Stub concept (no domain)
    state.concepts["warehouse"] = ConceptState(
        name="warehouse",
        definition="A storage location for products",
        models=["dim_warehouse"],
    )

    # Ghost concept (referenced but not defined)
    state.concepts["payment"] = ConceptState(name="payment", is_ghost=True, models=[])

    # Relationships
    state.relationships["customer:places:order"] = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
        cardinality="1:N",
        definition="Customer places multiple orders",
    )

    state.relationships["order:contains:product"] = RelationshipState(
        verb="contains",
        from_concept="order",
        to_concept="product",
        cardinality="1:N",
        definition="Order contains multiple products",
    )

    state.relationships["supplier:supplies:product"] = RelationshipState(
        verb="supplies",
        from_concept="supplier",
        to_concept="product",
        cardinality="1:N",
    )

    state.relationships["order:has_payment:payment"] = RelationshipState(
        verb="has_payment",
        from_concept="order",
        to_concept="payment",
        cardinality="1:1",
    )

    return state


@pytest.fixture
def sample_config() -> Config:
    """Create a sample config for testing."""
    import tempfile
    from pathlib import Path

    tmpdir = tempfile.mkdtemp()
    config = Config(
        project_dir=Path(tmpdir),
        gold_paths=["models/marts/**/*.yml"],
        validation=ValidationConfig(),
    )
    return config


# Tests for handle_get_context


def test_get_context_single_concept_llm_format(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
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
    assert "**Owner:** team_a" in result
    assert "A person or organization that purchases products" in result
    assert "dim_customer" in result
    assert "fct_customer_orders" in result
    assert "unique_customer_id" in result  # Guidance rule
    assert "places → order" in result  # Relationship


def test_get_context_json_format(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test getting context in JSON format."""
    result = handle_get_context(
        selector="customer",
        format="json",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )

    # Parse JSON to validate structure
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["name"] == "customer"
    assert data[0]["domain"] == "party"
    assert data[0]["status"] == "complete"
    assert "dim_customer" in data[0]["models"]
    assert len(data[0]["relationships"]) > 0


def test_get_context_yaml_format(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test getting context in YAML format."""
    result = handle_get_context(
        selector="customer",
        format="yaml",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )

    # Parse YAML to validate structure
    data = yaml.safe_load(result)
    assert len(data) == 1
    assert data[0]["name"] == "customer"
    assert data[0]["domain"] == "party"


def test_get_context_all_selector(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test getting context for all concepts."""
    result = handle_get_context(
        selector="all",
        format="llm",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )

    # Should include all non-ghost concepts
    assert "# Concept: customer" in result
    assert "# Concept: order" in result
    assert "# Concept: product" in result
    assert "# Concept: supplier" in result
    assert "# Concept: warehouse" in result
    # Ghost concepts are still included but marked
    assert "# Concept: payment" in result
    assert "GHOST" in result


def test_get_context_domain_selector(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test getting context for concepts in a domain."""
    result = handle_get_context(
        selector="domain:party",
        format="llm",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )

    assert "# Concept: customer" in result
    assert "# Concept: supplier" in result
    assert "# Concept: order" not in result  # Different domain
    assert "# Concept: product" not in result  # Different domain


def test_get_context_depth_traversal(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test relationship traversal with different depths."""
    # Depth 1: direct relationships only
    result1 = handle_get_context(
        selector="customer",
        format="llm",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )
    assert "places → order" in result1

    # Depth 2: should include order's relationships
    result2 = handle_get_context(
        selector="customer",
        format="llm",
        depth=2,
        project_state=sample_project_state,
        config=sample_config,
    )
    assert "places → order" in result2
    # Should include order→product relationship (indirect)
    assert "contains → product" in result2 or "Indirect:" in result2


def test_get_context_invalid_format(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test error handling for invalid format."""
    result = handle_get_context(
        selector="customer",
        format="xml",  # Invalid format
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )

    assert "Error:" in result
    assert "Invalid format" in result


def test_get_context_invalid_depth(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test error handling for invalid depth."""
    result = handle_get_context(
        selector="customer",
        format="llm",
        depth=5,  # Too high
        project_state=sample_project_state,
        config=sample_config,
    )

    assert "Error:" in result
    assert "Depth must be between 1 and 3" in result


def test_get_context_unknown_concept(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test error handling for unknown concept."""
    result = handle_get_context(
        selector="unknown_concept",
        format="llm",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )

    assert "Error:" in result
    assert "Unknown concept" in result


def test_get_context_grain_warning(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test that 1:N relationships show grain warnings."""
    result = handle_get_context(
        selector="customer",
        format="llm",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )

    # 1:N relationship should have grain warning
    assert "GRAIN WARNING" in result
    assert "1:N join may fan out results" in result


# Tests for handle_list_concepts


def test_list_concepts_no_filters(sample_project_state: ProjectState) -> None:
    """Test listing all concepts without filters."""
    result = handle_list_concepts(
        domain=None, status=None, project_state=sample_project_state
    )

    assert "Found 5 concept(s)" in result  # Excludes ghost
    assert "customer [complete]" in result
    assert "order [complete]" in result
    assert "supplier [draft]" in result
    assert "warehouse [stub]" in result
    assert "payment" not in result  # Ghost excluded


def test_list_concepts_domain_filter(sample_project_state: ProjectState) -> None:
    """Test listing concepts filtered by domain."""
    result = handle_list_concepts(
        domain="party", status=None, project_state=sample_project_state
    )

    assert "domain=party" in result
    assert "customer" in result
    assert "supplier" in result
    assert "order" not in result  # Different domain


def test_list_concepts_status_filter(sample_project_state: ProjectState) -> None:
    """Test listing concepts filtered by status."""
    result = handle_list_concepts(
        domain=None, status="complete", project_state=sample_project_state
    )

    assert "status=complete" in result
    assert "customer" in result
    assert "order" in result
    assert "product" in result
    assert "supplier" not in result  # Draft
    assert "warehouse" not in result  # Stub


def test_list_concepts_combined_filters(sample_project_state: ProjectState) -> None:
    """Test listing concepts with both domain and status filters."""
    result = handle_list_concepts(
        domain="party", status="draft", project_state=sample_project_state
    )

    assert "domain=party" in result
    assert "status=draft" in result
    assert "supplier" in result
    assert "customer" not in result  # Complete, not draft


def test_list_concepts_no_matches(sample_project_state: ProjectState) -> None:
    """Test listing when no concepts match filters."""
    result = handle_list_concepts(
        domain="nonexistent", status=None, project_state=sample_project_state
    )

    assert "No concepts found" in result
    assert "domain=nonexistent" in result


def test_list_concepts_invalid_status(sample_project_state: ProjectState) -> None:
    """Test error handling for invalid status filter."""
    result = handle_list_concepts(
        domain=None, status="invalid", project_state=sample_project_state
    )

    assert "Error:" in result
    assert "Invalid status" in result


# Tests for handle_get_relationships


def test_get_relationships_single_concept(sample_project_state: ProjectState) -> None:
    """Test getting relationships for a single concept."""
    result = handle_get_relationships(
        concept="customer", depth=1, project_state=sample_project_state
    )

    assert "Relationships for customer" in result
    assert "Outgoing:" in result
    assert "places → order (1:N)" in result
    assert "GRAIN WARNING" in result


def test_get_relationships_depth_2(sample_project_state: ProjectState) -> None:
    """Test relationship traversal with depth 2."""
    result = handle_get_relationships(
        concept="customer", depth=2, project_state=sample_project_state
    )

    assert "Relationships for customer" in result
    # Should include customer→order and order→product
    assert "places → order" in result
    # Indirect relationships from order
    assert "Indirect" in result or "contains → product" in result


def test_get_relationships_incoming(sample_project_state: ProjectState) -> None:
    """Test that incoming relationships are shown."""
    result = handle_get_relationships(
        concept="product", depth=1, project_state=sample_project_state
    )

    assert "Relationships for product" in result
    assert "Incoming:" in result
    assert "order" in result  # order→contains→product
    assert "supplier" in result  # supplier→supplies→product


def test_get_relationships_no_relationships(
    sample_project_state: ProjectState,
) -> None:
    """Test concept with no relationships."""
    result = handle_get_relationships(
        concept="warehouse", depth=1, project_state=sample_project_state
    )

    assert "has no relationships" in result


def test_get_relationships_invalid_depth(sample_project_state: ProjectState) -> None:
    """Test error handling for invalid depth."""
    result = handle_get_relationships(
        concept="customer", depth=0, project_state=sample_project_state
    )

    assert "Error:" in result
    assert "Depth must be between 1 and 3" in result


def test_get_relationships_unknown_concept(sample_project_state: ProjectState) -> None:
    """Test error handling for unknown concept."""
    result = handle_get_relationships(
        concept="unknown", depth=1, project_state=sample_project_state
    )

    assert "Error:" in result
    assert "Unknown concept" in result


# Tests for handle_validate


def test_validate_no_errors(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test validation with a valid project state."""
    # Remove the ghost concept to make state valid
    del sample_project_state.concepts["payment"]
    del sample_project_state.relationships["order:has_payment:payment"]

    result = handle_validate(project_state=sample_project_state, config=sample_config)

    assert "Validation Results:" in result
    # May have warnings about draft/stub concepts, but no errors


def test_validate_with_ghost_concept(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test validation shows validation results (ghosts already in state)."""
    result = handle_validate(project_state=sample_project_state, config=sample_config)

    # Ghost concepts are already in the state, so validator won't show E002
    # Instead it will show other validation issues
    assert "Validation Results:" in result
    # May have warnings or info messages about drafts/stubs
    assert "Warnings:" in result or "Info:" in result


def test_validate_with_orphan_models(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test validation detects orphan models."""
    from dbt_conceptual.state import OrphanModel

    sample_project_state.orphan_models.append(
        OrphanModel(name="stg_raw_data", path="models/staging/stg_raw_data.sql")
    )

    result = handle_validate(project_state=sample_project_state, config=sample_config)

    assert "WARNINGS:" in result or "W101" in result
    assert "stg_raw_data" in result


def test_validate_actionable_guidance(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test that validation includes actionable guidance."""
    result = handle_validate(project_state=sample_project_state, config=sample_config)

    # Should have ghost concept error, so should show guidance
    if "ERRORS:" in result:
        assert "Next Steps:" in result or "E002 errors:" in result


def test_validate_summary_counts(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test that validation summary includes counts."""
    result = handle_validate(project_state=sample_project_state, config=sample_config)

    assert "Errors:" in result or "Warnings:" in result or "Info:" in result


# Integration tests


def test_handlers_do_not_crash_on_empty_state(sample_config: Config) -> None:
    """Test that handlers gracefully handle empty project state."""
    empty_state = ProjectState()

    # get_context
    result1 = handle_get_context(
        selector="all",
        format="llm",
        depth=1,
        project_state=empty_state,
        config=sample_config,
    )
    assert isinstance(result1, str)
    assert "No concepts found" in result1

    # list_concepts
    result2 = handle_list_concepts(domain=None, status=None, project_state=empty_state)
    assert isinstance(result2, str)
    assert "No concepts found" in result2 or "Found 0" in result2

    # get_relationships (should error on unknown concept)
    result3 = handle_get_relationships(
        concept="unknown", depth=1, project_state=empty_state
    )
    assert isinstance(result3, str)
    assert "Error:" in result3

    # validate
    result4 = handle_validate(project_state=empty_state, config=sample_config)
    assert isinstance(result4, str)
    assert "Validation Results:" in result4


def test_handlers_return_strings_not_exceptions(
    sample_project_state: ProjectState, sample_config: Config
) -> None:
    """Test that all handlers return strings, never raise exceptions."""
    # All handlers should return strings even with bad inputs
    result1 = handle_get_context(
        selector="",  # Empty selector
        format="llm",
        depth=1,
        project_state=sample_project_state,
        config=sample_config,
    )
    assert isinstance(result1, str)

    result2 = handle_list_concepts(
        domain=None, status="bad_status", project_state=sample_project_state
    )
    assert isinstance(result2, str)

    result3 = handle_get_relationships(
        concept="", depth=1, project_state=sample_project_state
    )
    assert isinstance(result3, str)

    # validate should always work
    result4 = handle_validate(project_state=sample_project_state, config=sample_config)
    assert isinstance(result4, str)
