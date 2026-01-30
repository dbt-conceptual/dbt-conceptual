"""Tests for state models."""

from dbt_conceptual.state import ConceptState, ProjectState, RelationshipState


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
