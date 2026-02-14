"""Tests for concept selector parser."""

import pytest

from dbt_conceptual.selector import (
    SelectorError,
    SelectorExpression,
    SelectorParser,
    SelectorResolver,
    select_concepts,
)
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    ProjectState,
    RelationshipState,
)


@pytest.fixture
def empty_state() -> ProjectState:
    """Fixture for an empty project state."""
    return ProjectState()


@pytest.fixture
def sample_state() -> ProjectState:
    """Fixture for a sample project state with concepts and relationships.

    Graph structure:
        customer --has--> order --contains--> line_item
                   |
                   +--has--> payment

        product (separate, no relationships)

    Domains:
        - party: customer
        - transaction: order, payment, line_item
        - catalog: product

    Statuses:
        - stub: product (no domain)
        - draft: customer (has domain, no models)
        - complete: order, payment, line_item (has domain and models)
    """
    state = ProjectState()

    # Domains
    state.domains["party"] = DomainState(name="party", display_name="Party")
    state.domains["transaction"] = DomainState(
        name="transaction", display_name="Transaction"
    )
    state.domains["catalog"] = DomainState(name="catalog", display_name="Catalog")

    # Concepts
    state.concepts["customer"] = ConceptState(name="customer", domain="party")
    state.concepts["order"] = ConceptState(
        name="order", domain="transaction", models=["stg_orders"]
    )
    state.concepts["payment"] = ConceptState(
        name="payment", domain="transaction", models=["stg_payments"]
    )
    state.concepts["line_item"] = ConceptState(
        name="line_item", domain="transaction", models=["stg_line_items"]
    )
    state.concepts["product"] = ConceptState(name="product")  # No domain (stub status)

    # Relationships
    state.relationships["customer:has:order"] = RelationshipState(
        verb="has", from_concept="customer", to_concept="order"
    )
    state.relationships["order:contains:line_item"] = RelationshipState(
        verb="contains", from_concept="order", to_concept="line_item"
    )
    state.relationships["order:has:payment"] = RelationshipState(
        verb="has", from_concept="order", to_concept="payment"
    )

    return state


class TestSelectorParser:
    """Tests for SelectorParser."""

    def test_parse_empty_selector(self):
        """Test that empty selectors raise an error."""
        parser = SelectorParser()

        with pytest.raises(SelectorError, match="Selector cannot be empty"):
            parser.parse("")

        with pytest.raises(SelectorError, match="Selector cannot be empty"):
            parser.parse("   ")

    def test_parse_all_selector(self):
        """Test parsing 'all' selector."""
        parser = SelectorParser()
        expr = parser.parse("all")

        assert expr.selector_type == "all"
        assert expr.value == "all"
        assert expr.direction == "none"
        assert expr.depth is None

    def test_parse_single_concept(self):
        """Test parsing single concept selector."""
        parser = SelectorParser()
        expr = parser.parse("customer")

        assert expr.selector_type == "concept"
        assert expr.value == "customer"
        assert expr.direction == "none"
        assert expr.depth is None

    def test_parse_downstream_concept(self):
        """Test parsing downstream concept selector."""
        parser = SelectorParser()
        expr = parser.parse("customer+")

        assert expr.selector_type == "concept"
        assert expr.value == "customer"
        assert expr.direction == "downstream"
        assert expr.depth is None

    def test_parse_upstream_concept(self):
        """Test parsing upstream concept selector."""
        parser = SelectorParser()
        expr = parser.parse("+customer")

        assert expr.selector_type == "concept"
        assert expr.value == "customer"
        assert expr.direction == "upstream"
        assert expr.depth is None

    def test_parse_bidirectional_concept(self):
        """Test parsing bidirectional concept selector."""
        parser = SelectorParser()
        expr = parser.parse("+customer+")

        assert expr.selector_type == "concept"
        assert expr.value == "customer"
        assert expr.direction == "bidirectional"
        assert expr.depth is None

    def test_parse_downstream_with_depth(self):
        """Test parsing downstream concept selector with depth limit."""
        parser = SelectorParser()
        expr = parser.parse("customer+3")

        assert expr.selector_type == "concept"
        assert expr.value == "customer"
        assert expr.direction == "downstream"
        assert expr.depth == 3

    def test_parse_bidirectional_with_depth(self):
        """Test parsing bidirectional concept selector with depth limit."""
        parser = SelectorParser()
        expr = parser.parse("+customer+2")

        assert expr.selector_type == "concept"
        assert expr.value == "customer"
        assert expr.direction == "bidirectional"
        assert expr.depth == 2

    def test_parse_depth_invalid(self):
        """Test that invalid depth values raise an error."""
        parser = SelectorParser()

        with pytest.raises(SelectorError, match="Invalid depth value"):
            parser.parse("customer+abc")

        with pytest.raises(SelectorError, match="Depth must be a positive integer"):
            parser.parse("customer+0")

        with pytest.raises(SelectorError, match="Depth must be a positive integer"):
            parser.parse("customer+-1")

    def test_parse_domain_selector(self):
        """Test parsing domain selector."""
        parser = SelectorParser()
        expr = parser.parse("domain:party")

        assert expr.selector_type == "domain"
        assert expr.value == "party"
        assert expr.direction == "none"
        assert expr.depth is None

    def test_parse_domain_selector_with_downstream(self):
        """Test parsing domain selector with downstream operator."""
        parser = SelectorParser()
        expr = parser.parse("domain:party+")

        assert expr.selector_type == "domain"
        assert expr.value == "party"
        assert expr.direction == "downstream"
        assert expr.depth is None

    def test_parse_domain_selector_empty_domain(self):
        """Test that empty domain name raises an error."""
        parser = SelectorParser()

        with pytest.raises(
            SelectorError, match="Domain selector requires a domain name"
        ):
            parser.parse("domain:")

        with pytest.raises(
            SelectorError, match="Domain selector requires a domain name"
        ):
            parser.parse("domain:+")

    def test_parse_status_selector(self):
        """Test parsing status selector."""
        parser = SelectorParser()

        for status in ["stub", "draft", "complete"]:
            expr = parser.parse(f"status:{status}")
            assert expr.selector_type == "status"
            assert expr.value == status
            assert expr.direction == "none"
            assert expr.depth is None

    def test_parse_status_selector_invalid_status(self):
        """Test that invalid status values raise an error."""
        parser = SelectorParser()

        with pytest.raises(SelectorError, match="Invalid status value"):
            parser.parse("status:invalid")

        with pytest.raises(SelectorError, match="Invalid status value"):
            parser.parse("status:completed")

    def test_parse_status_selector_empty_status(self):
        """Test that empty status value raises an error."""
        parser = SelectorParser()

        with pytest.raises(
            SelectorError, match="Status selector requires a status value"
        ):
            parser.parse("status:")

    def test_parse_concept_selector_empty_concept(self):
        """Test that empty concept name raises an error."""
        parser = SelectorParser()

        with pytest.raises(
            SelectorError, match="Concept selector requires a concept name"
        ):
            parser.parse("+")

        with pytest.raises(
            SelectorError, match="Concept selector requires a concept name"
        ):
            parser.parse("++")


class TestSelectorResolver:
    """Tests for SelectorResolver."""

    def test_resolve_all_selector(self, sample_state):
        """Test resolving 'all' selector."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(selector_type="all", value="all", direction="none")

        result = resolver.resolve(expr)

        assert result == {"customer", "order", "payment", "line_item", "product"}

    def test_resolve_all_selector_empty_state(self, empty_state):
        """Test resolving 'all' selector with empty state."""
        resolver = SelectorResolver(empty_state)
        expr = SelectorExpression(selector_type="all", value="all", direction="none")

        result = resolver.resolve(expr)

        assert result == set()

    def test_resolve_single_concept(self, sample_state):
        """Test resolving single concept selector."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="concept", value="customer", direction="none"
        )

        result = resolver.resolve(expr)

        assert result == {"customer"}

    def test_resolve_single_concept_unknown(self, sample_state):
        """Test resolving unknown concept raises an error."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="concept", value="unknown", direction="none"
        )

        with pytest.raises(SelectorError, match="Unknown concept: unknown"):
            resolver.resolve(expr)

    def test_resolve_downstream_concept(self, sample_state):
        """Test resolving downstream concept selector."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="concept", value="customer", direction="downstream"
        )

        result = resolver.resolve(expr)

        # customer + order + payment + line_item (all downstream)
        assert result == {"customer", "order", "payment", "line_item"}

    def test_resolve_downstream_concept_no_children(self, sample_state):
        """Test resolving downstream concept with no children."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="concept", value="payment", direction="downstream"
        )

        result = resolver.resolve(expr)

        # payment has no downstream concepts
        assert result == {"payment"}

    def test_resolve_upstream_concept(self, sample_state):
        """Test resolving upstream concept selector."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="concept", value="line_item", direction="upstream"
        )

        result = resolver.resolve(expr)

        # line_item + order + customer (all upstream)
        assert result == {"line_item", "order", "customer"}

    def test_resolve_upstream_concept_no_parents(self, sample_state):
        """Test resolving upstream concept with no parents."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="concept", value="customer", direction="upstream"
        )

        result = resolver.resolve(expr)

        # customer has no upstream concepts
        assert result == {"customer"}

    def test_resolve_bidirectional_concept(self, sample_state):
        """Test resolving bidirectional concept selector."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="concept", value="order", direction="bidirectional"
        )

        result = resolver.resolve(expr)

        # order + customer (upstream) + payment + line_item (downstream)
        assert result == {"order", "customer", "payment", "line_item"}

    def test_resolve_downstream_with_depth_limit(self, sample_state):
        """Test resolving downstream concept with depth limit."""
        resolver = SelectorResolver(sample_state)

        # Depth 1: customer + order
        expr = SelectorExpression(
            selector_type="concept", value="customer", direction="downstream", depth=1
        )
        result = resolver.resolve(expr)
        assert result == {"customer", "order"}

        # Depth 2: customer + order + payment + line_item
        expr = SelectorExpression(
            selector_type="concept", value="customer", direction="downstream", depth=2
        )
        result = resolver.resolve(expr)
        assert result == {"customer", "order", "payment", "line_item"}

    def test_resolve_upstream_with_depth_limit(self, sample_state):
        """Test resolving upstream concept with depth limit."""
        resolver = SelectorResolver(sample_state)

        # Depth 1: line_item + order
        expr = SelectorExpression(
            selector_type="concept", value="line_item", direction="upstream", depth=1
        )
        result = resolver.resolve(expr)
        assert result == {"line_item", "order"}

        # Depth 2: line_item + order + customer
        expr = SelectorExpression(
            selector_type="concept", value="line_item", direction="upstream", depth=2
        )
        result = resolver.resolve(expr)
        assert result == {"line_item", "order", "customer"}

    def test_resolve_domain_selector(self, sample_state):
        """Test resolving domain selector."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="domain", value="transaction", direction="none"
        )

        result = resolver.resolve(expr)

        assert result == {"order", "payment", "line_item"}

    def test_resolve_domain_selector_unknown_domain(self, sample_state):
        """Test resolving unknown domain raises an error."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="domain", value="unknown", direction="none"
        )

        with pytest.raises(SelectorError, match="Unknown domain: unknown"):
            resolver.resolve(expr)

    def test_resolve_domain_selector_empty_domain(self, sample_state):
        """Test resolving domain with no concepts."""
        # Add an empty domain
        sample_state.domains["empty"] = DomainState(name="empty", display_name="Empty")

        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="domain", value="empty", direction="none"
        )

        result = resolver.resolve(expr)

        assert result == set()

    def test_resolve_domain_selector_with_downstream(self, sample_state):
        """Test resolving domain selector with downstream operator."""
        resolver = SelectorResolver(sample_state)
        expr = SelectorExpression(
            selector_type="domain", value="party", direction="downstream"
        )

        result = resolver.resolve(expr)

        # party domain has customer, downstream includes order, payment, line_item
        assert result == {"customer", "order", "payment", "line_item"}

    def test_resolve_status_selector(self, sample_state):
        """Test resolving status selector."""
        resolver = SelectorResolver(sample_state)

        # stub: product (no domain)
        expr = SelectorExpression(
            selector_type="status", value="stub", direction="none"
        )
        result = resolver.resolve(expr)
        assert result == {"product"}

        # draft: customer (has domain, no models)
        expr = SelectorExpression(
            selector_type="status", value="draft", direction="none"
        )
        result = resolver.resolve(expr)
        assert result == {"customer"}

        # complete: order, payment, line_item (has domain and models)
        expr = SelectorExpression(
            selector_type="status", value="complete", direction="none"
        )
        result = resolver.resolve(expr)
        assert result == {"order", "payment", "line_item"}

    def test_resolve_circular_relationships(self):
        """Test that circular relationships are handled correctly."""
        # Create a state with circular relationships: A -> B -> C -> A
        state = ProjectState()
        state.concepts["a"] = ConceptState(name="a", domain="test")
        state.concepts["b"] = ConceptState(name="b", domain="test")
        state.concepts["c"] = ConceptState(name="c", domain="test")

        state.relationships["a:to:b"] = RelationshipState(
            verb="to", from_concept="a", to_concept="b"
        )
        state.relationships["b:to:c"] = RelationshipState(
            verb="to", from_concept="b", to_concept="c"
        )
        state.relationships["c:to:a"] = RelationshipState(
            verb="to", from_concept="c", to_concept="a"
        )

        resolver = SelectorResolver(state)

        # Downstream should include all concepts
        expr = SelectorExpression(
            selector_type="concept", value="a", direction="downstream"
        )
        result = resolver.resolve(expr)
        assert result == {"a", "b", "c"}

        # Upstream should also include all concepts
        expr = SelectorExpression(
            selector_type="concept", value="a", direction="upstream"
        )
        result = resolver.resolve(expr)
        assert result == {"a", "b", "c"}


class TestSelectConcepts:
    """Tests for select_concepts convenience function."""

    def test_select_concepts(self, sample_state):
        """Test select_concepts convenience function."""
        result = select_concepts(sample_state, "customer+")

        assert result == {"customer", "order", "payment", "line_item"}

    def test_select_concepts_invalid_selector(self, sample_state):
        """Test select_concepts with invalid selector."""
        with pytest.raises(SelectorError):
            select_concepts(sample_state, "")

    def test_select_concepts_unknown_concept(self, sample_state):
        """Test select_concepts with unknown concept."""
        with pytest.raises(SelectorError, match="Unknown concept"):
            select_concepts(sample_state, "unknown")


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_depth_zero_is_invalid(self):
        """Test that depth of zero is rejected during parsing."""
        parser = SelectorParser()

        with pytest.raises(SelectorError, match="Depth must be a positive integer"):
            parser.parse("customer+0")

    def test_isolated_concept_graph_traversal(self):
        """Test graph traversal with isolated concept (no relationships)."""
        state = ProjectState()
        state.concepts["isolated"] = ConceptState(name="isolated", domain="test")

        resolver = SelectorResolver(state)

        # Downstream should only include the concept itself
        expr = SelectorExpression(
            selector_type="concept", value="isolated", direction="downstream"
        )
        result = resolver.resolve(expr)
        assert result == {"isolated"}

        # Upstream should only include the concept itself
        expr = SelectorExpression(
            selector_type="concept", value="isolated", direction="upstream"
        )
        result = resolver.resolve(expr)
        assert result == {"isolated"}

    def test_whitespace_handling(self):
        """Test that whitespace is properly trimmed."""
        parser = SelectorParser()

        expr = parser.parse("  customer  ")
        assert expr.value == "customer"

        expr = parser.parse("  domain:party  ")
        assert expr.value == "party"

        expr = parser.parse("  status:draft  ")
        assert expr.value == "draft"
