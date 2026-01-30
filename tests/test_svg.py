"""Tests for SVG diagram export."""

from io import StringIO

from dbt_conceptual.exporter.svg import export_diagram_svg
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    ProjectState,
    RelationshipState,
)


class TestExportDiagramSvg:
    """Tests for export_diagram_svg function."""

    def test_empty_state(self) -> None:
        """Test SVG export with no concepts."""
        state = ProjectState()
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        assert '<svg xmlns="http://www.w3.org/2000/svg"' in result
        assert "No concepts defined" in result

    def test_single_concept(self) -> None:
        """Test SVG export with a single concept."""
        state = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer", domain="party"),
            },
            domains={
                "party": DomainState(
                    name="party", display_name="Party", color="#E3F2FD"
                ),
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        assert '<svg xmlns="http://www.w3.org/2000/svg"' in result
        assert "Customer" in result
        assert "#E3F2FD" in result  # Domain color

    def test_multiple_concepts(self) -> None:
        """Test SVG export with multiple concepts."""
        state = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer", domain="party"),
                "order": ConceptState(name="Order", domain="sales"),
                "product": ConceptState(name="Product"),
            },
            domains={
                "party": DomainState(name="party", display_name="Party"),
                "sales": DomainState(name="sales", display_name="Sales"),
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        assert "Customer" in result
        assert "Order" in result
        assert "Product" in result

    def test_concept_with_relationship(self) -> None:
        """Test SVG export includes relationship edges."""
        state = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer"),
                "order": ConceptState(name="Order"),
            },
            relationships={
                "customer:places:order": RelationshipState(
                    verb="places",
                    from_concept="customer",
                    to_concept="order",
                ),
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        # Check for edge elements
        assert "<line" in result
        assert "places" in result  # Relationship verb label
        assert 'marker-end="url(#arrowhead)"' in result

    def test_stub_concept_styling(self) -> None:
        """Test that stub concepts have dashed border styling."""
        state = ProjectState(
            concepts={
                "stub_concept": ConceptState(name="Stub"),  # No domain = stub
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        # Stub concepts should have dashed stroke
        assert 'stroke-dasharray="5,5"' in result
        assert 'opacity="0.7"' in result

    def test_draft_concept_styling(self) -> None:
        """Test that draft concepts have appropriate styling."""
        state = ProjectState(
            concepts={
                "draft_concept": ConceptState(
                    name="Draft", domain="test"
                ),  # Domain but no models = draft
            },
            domains={
                "test": DomainState(name="test", display_name="Test"),
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        assert 'opacity="0.85"' in result

    def test_complete_concept_styling(self) -> None:
        """Test that complete concepts have full opacity."""
        state = ProjectState(
            concepts={
                "complete_concept": ConceptState(
                    name="Complete",
                    domain="test",
                    silver_models=["stg_model"],
                ),
            },
            domains={
                "test": DomainState(name="test", display_name="Test"),
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        assert 'opacity="1"' in result

    def test_svg_structure(self) -> None:
        """Test that SVG has proper structure with defs and markers."""
        state = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer"),
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        # Check SVG structure
        assert "<defs>" in result
        assert "<marker" in result
        assert 'id="arrowhead"' in result
        assert "</svg>" in result

    def test_default_color_for_no_domain(self) -> None:
        """Test that concepts without domain use default color."""
        state = ProjectState(
            concepts={
                "orphan": ConceptState(name="Orphan"),  # No domain
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        # Default color should be used
        assert "#3498db" in result  # Default blue color

    def test_grid_layout(self) -> None:
        """Test that concepts are laid out in a grid."""
        # Create 5 concepts to test grid layout
        state = ProjectState(
            concepts={
                f"concept_{i}": ConceptState(name=f"Concept {i}") for i in range(5)
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        # All concepts should be rendered
        for i in range(5):
            assert f"Concept {i}" in result

    def test_relationship_with_missing_endpoint(self) -> None:
        """Test that relationships with missing endpoints are skipped."""
        state = ProjectState(
            concepts={
                "customer": ConceptState(name="Customer"),
            },
            relationships={
                "customer:places:nonexistent": RelationshipState(
                    verb="places",
                    from_concept="customer",
                    to_concept="nonexistent",
                ),
            },
        )
        output = StringIO()
        export_diagram_svg(state, output)
        result = output.getvalue()

        # Should still render customer but no line (to_concept missing)
        assert "Customer" in result
        # No line should be drawn since endpoint doesn't exist
        assert result.count("<line") == 0
