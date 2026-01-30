"""Tests for diff_formatter module."""

import json

from dbt_conceptual.diff_formatter import (
    format_github,
    format_human,
    format_json,
    format_markdown,
)
from dbt_conceptual.differ import (
    ConceptChange,
    ConceptualDiff,
    DomainChange,
    RelationshipChange,
)
from dbt_conceptual.state import ConceptState, DomainState, RelationshipState


class TestFormatHuman:
    """Tests for format_human function."""

    def test_no_changes(self) -> None:
        """Test format_human with no changes."""
        diff = ConceptualDiff()
        result = format_human(diff)
        assert result == "No conceptual changes detected."

    def test_domain_added(self) -> None:
        """Test format_human with added domain."""
        domain = DomainState(name="party", display_name="Party Domain", color="#E3F2FD")
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(key="party", change_type="added", new_value=domain)
            ]
        )
        result = format_human(diff)

        assert "Conceptual Changes" in result
        assert "Domains:" in result
        assert "+ party - Party Domain" in result

    def test_domain_removed(self) -> None:
        """Test format_human with removed domain."""
        domain = DomainState(name="party", display_name="Party Domain")
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(key="party", change_type="removed", old_value=domain)
            ]
        )
        result = format_human(diff)

        assert "- party - Party Domain" in result

    def test_domain_modified(self) -> None:
        """Test format_human with modified domain."""
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(
                    key="party",
                    change_type="modified",
                    modified_fields={"display_name": ("Old Name", "New Name")},
                )
            ]
        )
        result = format_human(diff)

        assert "~ party" in result
        assert "display_name: 'Old Name'" in result
        assert "'New Name'" in result

    def test_concept_added(self) -> None:
        """Test format_human with added concept."""
        concept = ConceptState(name="Customer", domain="party")
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="added", new_value=concept)
            ]
        )
        result = format_human(diff)

        assert "Concepts:" in result
        assert "+ customer (party)" in result

    def test_concept_added_no_domain(self) -> None:
        """Test format_human with added concept without domain."""
        concept = ConceptState(name="Customer")
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="added", new_value=concept)
            ]
        )
        result = format_human(diff)

        assert "+ customer (no domain)" in result

    def test_concept_removed(self) -> None:
        """Test format_human with removed concept."""
        concept = ConceptState(name="Customer", domain="party")
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="removed", old_value=concept)
            ]
        )
        result = format_human(diff)

        assert "- customer (party)" in result

    def test_concept_modified(self) -> None:
        """Test format_human with modified concept."""
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(
                    key="customer",
                    change_type="modified",
                    modified_fields={"owner": ("team-a", "team-b")},
                )
            ]
        )
        result = format_human(diff)

        assert "~ customer" in result
        assert "owner: 'team-a'" in result
        assert "'team-b'" in result

    def test_concept_modified_definition_truncated(self) -> None:
        """Test format_human truncates long definitions."""
        long_def = "A" * 100
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(
                    key="customer",
                    change_type="modified",
                    modified_fields={"definition": ("old", long_def)},
                )
            ]
        )
        result = format_human(diff)

        assert "definition:" in result
        assert "..." in result  # Should be truncated

    def test_relationship_added(self) -> None:
        """Test format_human with added relationship."""
        rel = RelationshipState(
            verb="places",
            from_concept="customer",
            to_concept="order",
            cardinality="1:N",
        )
        diff = ConceptualDiff(
            relationship_changes=[
                RelationshipChange(
                    key="customer:places:order", change_type="added", new_value=rel
                )
            ]
        )
        result = format_human(diff)

        assert "Relationships:" in result
        assert "+ customer:places:order (1:N)" in result

    def test_relationship_removed(self) -> None:
        """Test format_human with removed relationship."""
        rel = RelationshipState(
            verb="places", from_concept="customer", to_concept="order"
        )
        diff = ConceptualDiff(
            relationship_changes=[
                RelationshipChange(
                    key="customer:places:order", change_type="removed", old_value=rel
                )
            ]
        )
        result = format_human(diff)

        assert "- customer:places:order" in result

    def test_relationship_modified(self) -> None:
        """Test format_human with modified relationship."""
        diff = ConceptualDiff(
            relationship_changes=[
                RelationshipChange(
                    key="customer:places:order",
                    change_type="modified",
                    modified_fields={"cardinality": ("1:1", "1:N")},
                )
            ]
        )
        result = format_human(diff)

        assert "~ customer:places:order" in result
        assert "cardinality: '1:1'" in result


class TestFormatGithub:
    """Tests for format_github function."""

    def test_no_changes(self, capsys) -> None:  # type: ignore
        """Test format_github with no changes."""
        diff = ConceptualDiff()
        result = format_github(diff)

        assert result == ""
        captured = capsys.readouterr()
        assert "::notice title=Conceptual Model::No changes detected" in captured.out

    def test_domain_added(self) -> None:
        """Test format_github with added domain."""
        domain = DomainState(name="party", display_name="Party Domain")
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(key="party", change_type="added", new_value=domain)
            ]
        )
        result = format_github(diff)

        assert "::notice title=New Domain::party - Party Domain" in result

    def test_domain_removed(self) -> None:
        """Test format_github with removed domain."""
        domain = DomainState(name="party", display_name="Party Domain")
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(key="party", change_type="removed", old_value=domain)
            ]
        )
        result = format_github(diff)

        assert "::warning title=Removed Domain::party" in result

    def test_domain_modified(self) -> None:
        """Test format_github with modified domain."""
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(
                    key="party",
                    change_type="modified",
                    modified_fields={"display_name": ("Old", "New")},
                )
            ]
        )
        result = format_github(diff)

        assert "::notice title=Modified Domain::party (display_name)" in result

    def test_concept_added_stub(self) -> None:
        """Test format_github with added stub concept shows warning."""
        concept = ConceptState(name="Customer")  # No domain = stub
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="added", new_value=concept)
            ]
        )
        result = format_github(diff)

        assert "::warning title=New Concept::customer" in result
        assert "stub" in result

    def test_concept_added_complete(self) -> None:
        """Test format_github with added complete concept shows notice."""
        concept = ConceptState(
            name="Customer", domain="party", silver_models=["dim_customer"]
        )
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="added", new_value=concept)
            ]
        )
        result = format_github(diff)

        assert "::notice title=New Concept::customer (party)" in result

    def test_concept_removed(self) -> None:
        """Test format_github with removed concept."""
        concept = ConceptState(name="Customer", domain="party")
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="removed", old_value=concept)
            ]
        )
        result = format_github(diff)

        assert "::warning title=Removed Concept::customer" in result

    def test_relationship_added_draft(self) -> None:
        """Test format_github with added draft relationship."""
        rel = RelationshipState(
            verb="places", from_concept="customer", to_concept="order"
        )  # No domains = draft
        diff = ConceptualDiff(
            relationship_changes=[
                RelationshipChange(
                    key="customer:places:order", change_type="added", new_value=rel
                )
            ]
        )
        result = format_github(diff)

        assert "::warning title=New Relationship::customer:places:order" in result
        assert "draft" in result


class TestFormatJson:
    """Tests for format_json function."""

    def test_no_changes(self) -> None:
        """Test format_json with no changes."""
        diff = ConceptualDiff()
        result = format_json(diff)
        data = json.loads(result)

        assert data["has_changes"] is False
        assert data["domain_changes"] == []
        assert data["concept_changes"] == []
        assert data["relationship_changes"] == []

    def test_concept_added(self) -> None:
        """Test format_json with added concept."""
        concept = ConceptState(name="Customer", domain="party", owner="team-a")
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="added", new_value=concept)
            ]
        )
        result = format_json(diff)
        data = json.loads(result)

        assert data["has_changes"] is True
        assert len(data["concept_changes"]) == 1
        change = data["concept_changes"][0]
        assert change["key"] == "customer"
        assert change["change_type"] == "added"
        assert change["new_value"]["name"] == "Customer"
        assert change["new_value"]["domain"] == "party"

    def test_concept_removed(self) -> None:
        """Test format_json with removed concept."""
        concept = ConceptState(name="Customer", domain="party")
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(key="customer", change_type="removed", old_value=concept)
            ]
        )
        result = format_json(diff)
        data = json.loads(result)

        change = data["concept_changes"][0]
        assert change["change_type"] == "removed"
        assert "old_value" in change
        assert change["old_value"]["name"] == "Customer"

    def test_concept_modified(self) -> None:
        """Test format_json with modified concept."""
        old_concept = ConceptState(name="Customer", owner="team-a")
        new_concept = ConceptState(name="Customer", owner="team-b")
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(
                    key="customer",
                    change_type="modified",
                    old_value=old_concept,
                    new_value=new_concept,
                    modified_fields={"owner": ("team-a", "team-b")},
                )
            ]
        )
        result = format_json(diff)
        data = json.loads(result)

        change = data["concept_changes"][0]
        assert change["change_type"] == "modified"
        assert "modified_fields" in change
        assert change["modified_fields"]["owner"]["old"] == "team-a"
        assert change["modified_fields"]["owner"]["new"] == "team-b"

    def test_all_change_types(self) -> None:
        """Test format_json with domain, concept, and relationship changes."""
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(
                    key="party",
                    change_type="added",
                    new_value=DomainState(name="party", display_name="Party"),
                )
            ],
            concept_changes=[
                ConceptChange(
                    key="customer",
                    change_type="added",
                    new_value=ConceptState(name="Customer"),
                )
            ],
            relationship_changes=[
                RelationshipChange(
                    key="customer:places:order",
                    change_type="added",
                    new_value=RelationshipState(
                        verb="places", from_concept="customer", to_concept="order"
                    ),
                )
            ],
        )
        result = format_json(diff)
        data = json.loads(result)

        assert len(data["domain_changes"]) == 1
        assert len(data["concept_changes"]) == 1
        assert len(data["relationship_changes"]) == 1


class TestFormatMarkdown:
    """Tests for format_markdown function."""

    def test_no_changes(self) -> None:
        """Test format_markdown with no changes."""
        diff = ConceptualDiff()
        result = format_markdown(diff)

        assert "No Conceptual Changes" in result
        assert "unchanged" in result

    def test_summary_table(self) -> None:
        """Test format_markdown includes summary table with counts."""
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(
                    key="customer",
                    change_type="added",
                    new_value=ConceptState(name="Customer"),
                ),
                ConceptChange(
                    key="order",
                    change_type="removed",
                    old_value=ConceptState(name="Order"),
                ),
            ]
        )
        result = format_markdown(diff)

        assert "Conceptual Model Changes" in result
        assert "| Count |" in result
        assert "Added | 1" in result
        assert "Removed | 1" in result

    def test_domain_section(self) -> None:
        """Test format_markdown includes domain section."""
        diff = ConceptualDiff(
            domain_changes=[
                DomainChange(
                    key="party",
                    change_type="added",
                    new_value=DomainState(name="party", display_name="Party"),
                ),
                DomainChange(
                    key="finance",
                    change_type="removed",
                    old_value=DomainState(name="finance", display_name="Finance"),
                ),
                DomainChange(
                    key="sales",
                    change_type="modified",
                    modified_fields={"color": ("#fff", "#000")},
                ),
            ]
        )
        result = format_markdown(diff)

        assert "### Domains" in result
        assert "`party`" in result
        assert "`finance`" in result
        assert "`sales`" in result

    def test_concept_section(self) -> None:
        """Test format_markdown includes concept section."""
        diff = ConceptualDiff(
            concept_changes=[
                ConceptChange(
                    key="customer",
                    change_type="added",
                    new_value=ConceptState(
                        name="Customer", domain="party", silver_models=["x"]
                    ),
                ),
            ]
        )
        result = format_markdown(diff)

        assert "### Concepts" in result
        assert "`customer`" in result
        assert "domain: party" in result

    def test_relationship_section(self) -> None:
        """Test format_markdown includes relationship section."""
        diff = ConceptualDiff(
            relationship_changes=[
                RelationshipChange(
                    key="customer:places:order",
                    change_type="added",
                    new_value=RelationshipState(
                        verb="places",
                        from_concept="customer",
                        to_concept="order",
                        cardinality="1:N",
                        domains=["sales"],
                    ),
                ),
            ]
        )
        result = format_markdown(diff)

        assert "### Relationships" in result
        assert "`customer:places:order`" in result
        assert "cardinality: 1:N" in result
