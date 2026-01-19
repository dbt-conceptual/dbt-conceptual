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
        silver_models=["stg_customer"],
        gold_models=["dim_customer"],
    )

    assert concept.name == "Customer"
    assert concept.domain == "party"
    assert concept.owner == "data_team"
    assert concept.definition == "A person who buys products"
    assert concept.status == "complete"  # Derived: has domain and models
    assert concept.silver_models == ["stg_customer"]
    assert concept.gold_models == ["dim_customer"]


def test_concept_status_derivation() -> None:
    """Test that concept status is correctly derived."""
    # Stub: no domain
    stub = ConceptState(name="Stub")
    assert stub.status == "stub"

    # Draft: has domain but no models
    draft = ConceptState(name="Draft", domain="party")
    assert draft.status == "draft"

    # Complete: has domain and at least one model
    complete = ConceptState(
        name="Complete", domain="party", gold_models=["dim_complete"]
    )
    assert complete.status == "complete"

    # Deprecated: replaced_by is set
    deprecated = ConceptState(
        name="Old", domain="party", replaced_by="new", gold_models=["dim_old"]
    )
    assert deprecated.status == "deprecated"


def test_relationship_state_creation() -> None:
    """Test creating a RelationshipState."""
    rel = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
        cardinality="1:N",
        domains=["transaction"],
    )

    assert rel.verb == "places"
    assert rel.name == "customer:places:order"  # Derived name
    assert rel.from_concept == "customer"
    assert rel.to_concept == "order"
    assert rel.cardinality == "1:N"
    assert rel.domains == ["transaction"]
    assert rel.realized_by == []


def test_relationship_status_derivation() -> None:
    """Test that relationship status is correctly derived."""
    # Stub: no verb (shouldn't happen in practice)
    stub = RelationshipState(verb="", from_concept="a", to_concept="b")
    assert stub.status == "stub"

    # Draft: no domains
    draft = RelationshipState(verb="relates", from_concept="a", to_concept="b")
    assert draft.status == "draft"

    # Draft: N:M without realization
    nm_draft = RelationshipState(
        verb="relates",
        from_concept="a",
        to_concept="b",
        cardinality="N:M",
        domains=["test"],
    )
    assert nm_draft.status == "draft"

    # Complete: has domain and not N:M
    complete = RelationshipState(
        verb="relates",
        from_concept="a",
        to_concept="b",
        cardinality="1:N",
        domains=["test"],
    )
    assert complete.status == "complete"

    # Complete: N:M with realization
    nm_complete = RelationshipState(
        verb="relates",
        from_concept="a",
        to_concept="b",
        cardinality="N:M",
        domains=["test"],
        realized_by=["bridge_table"],
    )
    assert nm_complete.status == "complete"


def test_relationship_custom_name() -> None:
    """Test relationship custom name override."""
    # Without custom_name: derived format
    rel = RelationshipState(verb="places", from_concept="customer", to_concept="order")
    assert rel.name == "customer:places:order"

    # With custom_name: use override
    custom_rel = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
        custom_name="customer_order_placement",
    )
    assert custom_rel.name == "customer_order_placement"


def test_project_state_creation() -> None:
    """Test creating a ProjectState."""
    state = ProjectState()

    assert state.concepts == {}
    assert state.relationships == {}
    assert state.groups == {}
    assert state.domains == {}
    assert state.orphan_models == []
    assert state.metadata == {}
