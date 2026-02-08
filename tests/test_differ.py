"""Tests for differ module."""

from dbt_conceptual.differ import (
    ConceptChange,
    ConceptualDiff,
    DomainChange,
    RelationshipChange,
    _compare_entities,
    compute_diff,
)
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    ProjectState,
    RelationshipState,
)


class TestCompareEntities:
    """Tests for the generic _compare_entities function."""

    def test_added_entity(self) -> None:
        """Return an 'added' change when old is None and new exists."""
        new = ConceptState(name="Customer")
        result = _compare_entities(None, new, "customer", ("name",), ConceptChange)
        assert result is not None
        assert result.change_type == "added"
        assert result.new_value is new
        assert result.old_value is None

    def test_removed_entity(self) -> None:
        """Return a 'removed' change when old exists and new is None."""
        old = ConceptState(name="Customer")
        result = _compare_entities(old, None, "customer", ("name",), ConceptChange)
        assert result is not None
        assert result.change_type == "removed"
        assert result.old_value is old
        assert result.new_value is None

    def test_both_none(self) -> None:
        """Return None when both old and new are None."""
        result = _compare_entities(None, None, "customer", ("name",), ConceptChange)
        assert result is None

    def test_no_changes(self) -> None:
        """Return None when entities are identical."""
        old = ConceptState(name="Customer", domain="party")
        new = ConceptState(name="Customer", domain="party")
        result = _compare_entities(
            old, new, "customer", ("name", "domain"), ConceptChange
        )
        assert result is None

    def test_modified_entity(self) -> None:
        """Return a 'modified' change with correct modified_fields."""
        old = ConceptState(name="Customer", domain="party")
        new = ConceptState(name="Customer", domain="sales")
        result = _compare_entities(
            old, new, "customer", ("name", "domain"), ConceptChange
        )
        assert result is not None
        assert result.change_type == "modified"
        assert result.old_value is old
        assert result.new_value is new
        assert "domain" in result.modified_fields
        assert result.modified_fields["domain"] == ("party", "sales")
        assert "name" not in result.modified_fields

    def test_multiple_modified_fields(self) -> None:
        """Track all changed fields, not just the first."""
        old = ConceptState(name="Customer", domain="party", owner="team-a")
        new = ConceptState(name="Client", domain="sales", owner="team-a")
        result = _compare_entities(
            old,
            new,
            "customer",
            ("name", "domain", "owner"),
            ConceptChange,
        )
        assert result is not None
        assert result.change_type == "modified"
        assert "name" in result.modified_fields
        assert "domain" in result.modified_fields
        assert "owner" not in result.modified_fields

    def test_works_with_relationship_change(self) -> None:
        """Construct the correct change type for relationships."""
        old = RelationshipState(
            verb="places", from_concept="customer", to_concept="order"
        )
        new = RelationshipState(
            verb="creates", from_concept="customer", to_concept="order"
        )
        result = _compare_entities(
            old,
            new,
            "customer:places:order",
            ("verb", "from_concept", "to_concept"),
            RelationshipChange,
        )
        assert result is not None
        assert isinstance(result, RelationshipChange)
        assert result.modified_fields["verb"] == ("places", "creates")

    def test_works_with_domain_change(self) -> None:
        """Construct the correct change type for domains."""
        new = DomainState(name="sales", display_name="Sales")
        result = _compare_entities(
            None, new, "sales", ("name", "display_name"), DomainChange
        )
        assert result is not None
        assert isinstance(result, DomainChange)
        assert result.change_type == "added"


class TestConceptualDiff:
    """Tests for ConceptualDiff dataclass."""

    def test_has_changes_empty(self) -> None:
        """Empty diff has no changes."""
        diff = ConceptualDiff()
        assert diff.has_changes is False

    def test_has_changes_with_concepts(self) -> None:
        """Diff with concept changes reports has_changes."""
        diff = ConceptualDiff(
            concept_changes=[ConceptChange(key="x", change_type="added")]
        )
        assert diff.has_changes is True

    def test_has_changes_with_relationships(self) -> None:
        """Diff with relationship changes reports has_changes."""
        diff = ConceptualDiff(
            relationship_changes=[RelationshipChange(key="x", change_type="added")]
        )
        assert diff.has_changes is True

    def test_has_changes_with_domains(self) -> None:
        """Diff with domain changes reports has_changes."""
        diff = ConceptualDiff(
            domain_changes=[DomainChange(key="x", change_type="added")]
        )
        assert diff.has_changes is True


class TestComputeDiffConcepts:
    """Tests for compute_diff — concept scenarios."""

    def test_no_changes(self) -> None:
        """Identical states produce no changes."""
        state = ProjectState(
            concepts={"customer": ConceptState(name="Customer", domain="party")}
        )
        diff = compute_diff(state, state)
        assert diff.has_changes is False
        assert diff.concept_changes == []

    def test_concept_added(self) -> None:
        """New concept in current state is detected as added."""
        base = ProjectState()
        current = ProjectState(concepts={"customer": ConceptState(name="Customer")})
        diff = compute_diff(base, current)
        assert len(diff.concept_changes) == 1
        change = diff.concept_changes[0]
        assert change.key == "customer"
        assert change.change_type == "added"
        assert change.new_value is not None
        assert change.new_value.name == "Customer"

    def test_concept_removed(self) -> None:
        """Concept present in base but missing from current is detected as removed."""
        base = ProjectState(concepts={"customer": ConceptState(name="Customer")})
        current = ProjectState()
        diff = compute_diff(base, current)
        assert len(diff.concept_changes) == 1
        change = diff.concept_changes[0]
        assert change.key == "customer"
        assert change.change_type == "removed"
        assert change.old_value is not None
        assert change.old_value.name == "Customer"

    def test_concept_modified(self) -> None:
        """Changed concept fields are detected as modified."""
        base = ProjectState(
            concepts={
                "customer": ConceptState(
                    name="Customer", domain="party", owner="team-a"
                )
            }
        )
        current = ProjectState(
            concepts={
                "customer": ConceptState(
                    name="Customer", domain="sales", owner="team-b"
                )
            }
        )
        diff = compute_diff(base, current)
        assert len(diff.concept_changes) == 1
        change = diff.concept_changes[0]
        assert change.change_type == "modified"
        assert "domain" in change.modified_fields
        assert change.modified_fields["domain"] == ("party", "sales")
        assert "owner" in change.modified_fields
        assert change.modified_fields["owner"] == ("team-a", "team-b")

    def test_concept_unchanged_ignored(self) -> None:
        """Unchanged concepts produce no changes alongside changed ones."""
        base = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer"),
                "order": ConceptState(name="Order"),
            }
        )
        current = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer"),
                "order": ConceptState(name="Order", domain="commerce"),
            }
        )
        diff = compute_diff(base, current)
        assert len(diff.concept_changes) == 1
        assert diff.concept_changes[0].key == "order"

    def test_multiple_concept_operations(self) -> None:
        """Detect add, remove, and modify in a single diff."""
        base = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer"),
                "order": ConceptState(name="Order"),
            }
        )
        current = ProjectState(
            concepts={
                "customer": ConceptState(name="Client"),
                "product": ConceptState(name="Product"),
            }
        )
        diff = compute_diff(base, current)
        changes_by_type = {c.change_type: c for c in diff.concept_changes}
        assert "modified" in changes_by_type  # customer name changed
        assert "removed" in changes_by_type  # order removed
        assert "added" in changes_by_type  # product added
        assert changes_by_type["modified"].key == "customer"
        assert changes_by_type["removed"].key == "order"
        assert changes_by_type["added"].key == "product"


class TestComputeDiffRelationships:
    """Tests for compute_diff — relationship scenarios."""

    def test_relationship_added(self) -> None:
        """New relationship in current state is detected as added."""
        rel = RelationshipState(
            verb="places", from_concept="customer", to_concept="order"
        )
        base = ProjectState()
        current = ProjectState(relationships={"customer:places:order": rel})
        diff = compute_diff(base, current)
        assert len(diff.relationship_changes) == 1
        change = diff.relationship_changes[0]
        assert change.change_type == "added"
        assert change.key == "customer:places:order"

    def test_relationship_removed(self) -> None:
        """Relationship in base but missing from current is detected as removed."""
        rel = RelationshipState(
            verb="places", from_concept="customer", to_concept="order"
        )
        base = ProjectState(relationships={"customer:places:order": rel})
        current = ProjectState()
        diff = compute_diff(base, current)
        assert len(diff.relationship_changes) == 1
        change = diff.relationship_changes[0]
        assert change.change_type == "removed"
        assert change.key == "customer:places:order"

    def test_relationship_modified(self) -> None:
        """Changed relationship fields are detected as modified."""
        old_rel = RelationshipState(
            verb="places",
            from_concept="customer",
            to_concept="order",
            cardinality="1:N",
        )
        new_rel = RelationshipState(
            verb="places",
            from_concept="customer",
            to_concept="order",
            cardinality="1:1",
        )
        base = ProjectState(relationships={"customer:places:order": old_rel})
        current = ProjectState(relationships={"customer:places:order": new_rel})
        diff = compute_diff(base, current)
        assert len(diff.relationship_changes) == 1
        change = diff.relationship_changes[0]
        assert change.change_type == "modified"
        assert "cardinality" in change.modified_fields
        assert change.modified_fields["cardinality"] == ("1:N", "1:1")

    def test_relationship_no_changes(self) -> None:
        """Identical relationships produce no changes."""
        rel = RelationshipState(
            verb="places", from_concept="customer", to_concept="order"
        )
        state = ProjectState(relationships={"customer:places:order": rel})
        diff = compute_diff(state, state)
        assert diff.relationship_changes == []

    def test_multiple_relationship_operations(self) -> None:
        """Detect add, remove, and modify for relationships in a single diff."""
        old_rel = RelationshipState(
            verb="places", from_concept="customer", to_concept="order"
        )
        modified_rel_old = RelationshipState(
            verb="owns",
            from_concept="customer",
            to_concept="account",
            definition="Old def",
        )
        modified_rel_new = RelationshipState(
            verb="owns",
            from_concept="customer",
            to_concept="account",
            definition="New def",
        )
        new_rel = RelationshipState(
            verb="ships", from_concept="warehouse", to_concept="order"
        )
        base = ProjectState(
            relationships={
                "customer:places:order": old_rel,
                "customer:owns:account": modified_rel_old,
            }
        )
        current = ProjectState(
            relationships={
                "customer:owns:account": modified_rel_new,
                "warehouse:ships:order": new_rel,
            }
        )
        diff = compute_diff(base, current)
        changes_by_type = {c.change_type: c for c in diff.relationship_changes}
        assert "removed" in changes_by_type
        assert "modified" in changes_by_type
        assert "added" in changes_by_type


class TestComputeDiffDomains:
    """Tests for compute_diff — domain scenarios."""

    def test_domain_added(self) -> None:
        """New domain in current state is detected as added."""
        base = ProjectState()
        current = ProjectState(
            domains={"party": DomainState(name="party", display_name="Party")}
        )
        diff = compute_diff(base, current)
        assert len(diff.domain_changes) == 1
        change = diff.domain_changes[0]
        assert change.change_type == "added"
        assert change.key == "party"

    def test_domain_removed(self) -> None:
        """Domain in base but missing from current is detected as removed."""
        base = ProjectState(
            domains={"party": DomainState(name="party", display_name="Party")}
        )
        current = ProjectState()
        diff = compute_diff(base, current)
        assert len(diff.domain_changes) == 1
        change = diff.domain_changes[0]
        assert change.change_type == "removed"
        assert change.key == "party"
        assert change.old_value is not None

    def test_domain_modified(self) -> None:
        """Changed domain fields are detected as modified."""
        base = ProjectState(
            domains={
                "party": DomainState(
                    name="party", display_name="Party", color="#E3F2FD"
                )
            }
        )
        current = ProjectState(
            domains={
                "party": DomainState(
                    name="party", display_name="Party Domain", color="#E3F2FD"
                )
            }
        )
        diff = compute_diff(base, current)
        assert len(diff.domain_changes) == 1
        change = diff.domain_changes[0]
        assert change.change_type == "modified"
        assert "display_name" in change.modified_fields
        assert change.modified_fields["display_name"] == ("Party", "Party Domain")

    def test_domain_no_changes(self) -> None:
        """Identical domains produce no changes."""
        state = ProjectState(
            domains={"party": DomainState(name="party", display_name="Party")}
        )
        diff = compute_diff(state, state)
        assert diff.domain_changes == []

    def test_domain_color_change(self) -> None:
        """Domain color change is detected."""
        base = ProjectState(
            domains={
                "party": DomainState(
                    name="party", display_name="Party", color="#E3F2FD"
                )
            }
        )
        current = ProjectState(
            domains={
                "party": DomainState(
                    name="party", display_name="Party", color="#FF0000"
                )
            }
        )
        diff = compute_diff(base, current)
        assert len(diff.domain_changes) == 1
        assert diff.domain_changes[0].modified_fields["color"] == (
            "#E3F2FD",
            "#FF0000",
        )

    def test_multiple_domain_operations(self) -> None:
        """Detect add, remove, and modify for domains in a single diff."""
        base = ProjectState(
            domains={
                "party": DomainState(name="party", display_name="Party"),
                "finance": DomainState(name="finance", display_name="Finance"),
            }
        )
        current = ProjectState(
            domains={
                "party": DomainState(name="party", display_name="Party Dept"),
                "sales": DomainState(name="sales", display_name="Sales"),
            }
        )
        diff = compute_diff(base, current)
        changes_by_type = {c.change_type: c for c in diff.domain_changes}
        assert "removed" in changes_by_type  # finance removed
        assert "modified" in changes_by_type  # party modified
        assert "added" in changes_by_type  # sales added


class TestComputeDiffCombined:
    """Tests for compute_diff with multiple entity types changing simultaneously."""

    def test_all_entity_types_changed(self) -> None:
        """Detect changes across concepts, relationships, and domains."""
        base = ProjectState(
            concepts={"customer": ConceptState(name="Customer")},
            relationships={
                "customer:places:order": RelationshipState(
                    verb="places", from_concept="customer", to_concept="order"
                )
            },
            domains={"party": DomainState(name="party", display_name="Party")},
        )
        current = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer", domain="party"),
                "order": ConceptState(name="Order"),
            },
            relationships={},
            domains={
                "party": DomainState(name="party", display_name="Party"),
                "commerce": DomainState(name="commerce", display_name="Commerce"),
            },
        )
        diff = compute_diff(base, current)
        assert diff.has_changes is True
        # concept: customer modified + order added = 2
        assert len(diff.concept_changes) == 2
        # relationship: customer:places:order removed = 1
        assert len(diff.relationship_changes) == 1
        assert diff.relationship_changes[0].change_type == "removed"
        # domain: commerce added = 1
        assert len(diff.domain_changes) == 1
        assert diff.domain_changes[0].change_type == "added"

    def test_empty_states(self) -> None:
        """Two empty states produce no changes."""
        diff = compute_diff(ProjectState(), ProjectState())
        assert diff.has_changes is False

    def test_keys_are_sorted(self) -> None:
        """Changes are returned in sorted key order."""
        base = ProjectState()
        current = ProjectState(
            concepts={
                "zebra": ConceptState(name="Zebra"),
                "apple": ConceptState(name="Apple"),
                "mango": ConceptState(name="Mango"),
            }
        )
        diff = compute_diff(base, current)
        keys = [c.key for c in diff.concept_changes]
        assert keys == ["apple", "mango", "zebra"]
