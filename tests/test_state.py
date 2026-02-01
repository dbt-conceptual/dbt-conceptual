"""Tests for state models."""

from dbt_conceptual.state import (
    ConceptState,
    CoverageStats,
    DomainState,
    OrphanModel,
    ProjectState,
    RelationshipState,
)


def test_concept_state_creation() -> None:
    """Test creating a ConceptState with derived status."""
    # Concept with domain and models should be "complete"
    concept = ConceptState(
        name="Customer",
        domain="party",
        owner="data_team",
        definition="A person who buys products",
        models=["dim_customer", "stg_customer"],
    )

    assert concept.name == "Customer"
    assert concept.domain == "party"
    assert concept.owner == "data_team"
    assert concept.definition == "A person who buys products"
    assert concept.status == "complete"  # Derived: has domain and models
    assert concept.models == ["dim_customer", "stg_customer"]


def test_concept_status_derivation() -> None:
    """Test that concept status is correctly derived."""
    # Stub: no domain
    stub = ConceptState(name="Stub")
    assert stub.status == "stub"

    # Draft: has domain but no models
    draft = ConceptState(name="Draft", domain="party")
    assert draft.status == "draft"

    # Complete: has domain and at least one model
    complete = ConceptState(name="Complete", domain="party", models=["dim_complete"])
    assert complete.status == "complete"


def test_relationship_state_creation() -> None:
    """Test creating a RelationshipState."""
    rel = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
        cardinality="1:N",
    )

    assert rel.verb == "places"
    assert rel.name == "customer:places:order"  # Derived name
    assert rel.from_concept == "customer"
    assert rel.to_concept == "order"
    assert rel.cardinality == "1:N"


def test_relationship_status_derivation() -> None:
    """Test that relationship status is correctly derived based on concepts."""
    # Create concepts for testing
    concepts = {
        "complete": ConceptState(name="Complete", domain="test", models=["model1"]),
        "draft": ConceptState(name="Draft", domain="test"),
        "stub": ConceptState(name="Stub"),  # No domain = stub
        "ghost": ConceptState(name="Ghost", is_ghost=True),
    }

    # Complete: both endpoints are draft or complete
    rel_complete = RelationshipState(
        verb="relates", from_concept="complete", to_concept="draft"
    )
    assert rel_complete.get_status(concepts) == "complete"

    # Stub: one endpoint is stub
    rel_stub_from = RelationshipState(
        verb="relates", from_concept="stub", to_concept="complete"
    )
    assert rel_stub_from.get_status(concepts) == "stub"

    # Stub: one endpoint is ghost
    rel_ghost = RelationshipState(
        verb="relates", from_concept="complete", to_concept="ghost"
    )
    assert rel_ghost.get_status(concepts) == "stub"


def test_project_state_creation() -> None:
    """Test creating a ProjectState."""
    state = ProjectState()

    assert state.concepts == {}
    assert state.relationships == {}
    assert state.domains == {}
    assert state.orphan_models == []
    assert state.metadata == {}


def test_coverage_stats_to_dict() -> None:
    """Test CoverageStats.to_dict() method."""
    stats = CoverageStats(
        total_concepts=10,
        complete_concepts=5,
        draft_concepts=3,
        stub_concepts=2,
        concepts_with_models=6,
        total_relationships=4,
        complete_relationships=3,
        orphan_count=2,
    )

    result = stats.to_dict()

    assert result["concepts"]["total"] == 10
    assert result["concepts"]["complete"] == 5
    assert result["concepts"]["draft"] == 3
    assert result["concepts"]["stub"] == 2
    assert result["concepts"]["completion_percent"] == 50

    assert result["coverage"]["models"]["count"] == 6
    assert result["coverage"]["models"]["percent"] == 60

    assert result["relationships"]["total"] == 4
    assert result["relationships"]["complete"] == 3
    assert result["relationships"]["percent"] == 75

    assert result["orphans"] == 2


def test_coverage_stats_to_dict_empty() -> None:
    """Test CoverageStats.to_dict() with empty stats (avoids division by zero)."""
    stats = CoverageStats()

    result = stats.to_dict()

    assert result["concepts"]["completion_percent"] == 0
    assert result["coverage"]["models"]["percent"] == 0
    assert result["relationships"]["percent"] == 0


def test_project_state_calculate_coverage_stats() -> None:
    """Test ProjectState.calculate_coverage_stats() method."""
    state = ProjectState(
        concepts={
            "customer": ConceptState(
                name="Customer", domain="party", models=["dim_customer"]
            ),
            "order": ConceptState(name="Order", domain="sales"),
            "product": ConceptState(name="Product"),
        },
        relationships={
            "customer:places:order": RelationshipState(
                verb="places", from_concept="customer", to_concept="order"
            ),
        },
        orphan_models=[OrphanModel(name="stg_unknown")],
    )

    stats = state.calculate_coverage_stats()

    assert stats.total_concepts == 3
    assert stats.complete_concepts == 1  # customer
    assert stats.draft_concepts == 1  # order
    assert stats.stub_concepts == 1  # product
    assert stats.concepts_with_models == 1
    assert stats.total_relationships == 1
    assert stats.complete_relationships == 1  # both endpoints are draft or complete
    assert stats.orphan_count == 1


def test_project_state_concepts_by_domain() -> None:
    """Test ProjectState.concepts_by_domain() method."""
    state = ProjectState(
        concepts={
            "customer": ConceptState(name="Customer", domain="party"),
            "supplier": ConceptState(name="Supplier", domain="party"),
            "order": ConceptState(name="Order", domain="sales"),
            "orphan": ConceptState(name="Orphan"),  # No domain
        },
        domains={
            "party": DomainState(name="party", display_name="Party"),
            "sales": DomainState(name="sales", display_name="Sales"),
        },
    )

    groups = state.concepts_by_domain()

    assert "party" in groups
    assert "sales" in groups
    assert "uncategorized" in groups

    # Check party domain
    party_ids = [cid for cid, _ in groups["party"]]
    assert "customer" in party_ids
    assert "supplier" in party_ids
    assert len(groups["party"]) == 2

    # Check sales domain
    assert len(groups["sales"]) == 1
    assert groups["sales"][0][0] == "order"

    # Check uncategorized
    assert len(groups["uncategorized"]) == 1
    assert groups["uncategorized"][0][0] == "orphan"
