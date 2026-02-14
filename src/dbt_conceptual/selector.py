"""Selector parser for dbt-style concept graph traversal.

Supports dbt-style selector syntax:
- Single concept: 'customer'
- Downstream: 'customer+'
- Upstream: '+customer'
- Bidirectional: '+customer+'
- Domain selector: 'domain:party', 'domain:party+'
- Status selector: 'status:draft', 'status:complete'
- All selector: 'all'
- Depth parameter: 'customer+3' (limit downstream depth to 3)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from dbt_conceptual.state import ProjectState

SelectorType = Literal["concept", "domain", "status", "all"]
Direction = Literal["upstream", "downstream", "bidirectional", "none"]
StatusValue = Literal["stub", "draft", "complete"]


@dataclass
class SelectorExpression:
    """Represents a parsed selector expression."""

    selector_type: SelectorType
    value: str  # concept name, domain name, status value, or "all"
    direction: Direction = "none"
    depth: int | None = None  # Depth limit for graph traversal


class SelectorError(Exception):
    """Raised when selector parsing or resolution fails."""

    pass


class SelectorParser:
    """Parses dbt-style selector expressions."""

    def parse(self, selector: str) -> SelectorExpression:
        """Parse a selector string into a SelectorExpression.

        Args:
            selector: The selector string to parse (e.g., 'customer+', 'domain:party')

        Returns:
            Parsed SelectorExpression

        Raises:
            SelectorError: If selector syntax is invalid
        """
        if not selector or not selector.strip():
            raise SelectorError("Selector cannot be empty")

        selector = selector.strip()

        # Handle 'all' selector
        if selector == "all":
            return SelectorExpression(
                selector_type="all", value="all", direction="none"
            )

        # Handle domain selector: 'domain:party' or 'domain:party+'
        if selector.startswith("domain:"):
            return self._parse_domain_selector(selector)

        # Handle status selector: 'status:draft' or 'status:complete'
        if selector.startswith("status:"):
            return self._parse_status_selector(selector)

        # Handle concept selector with graph operators
        return self._parse_concept_selector(selector)

    def _parse_domain_selector(self, selector: str) -> SelectorExpression:
        """Parse domain selector.

        Args:
            selector: Domain selector string (e.g., 'domain:party', 'domain:party+')

        Returns:
            Parsed SelectorExpression

        Raises:
            SelectorError: If domain selector syntax is invalid
        """
        # Remove 'domain:' prefix
        value_part = selector[7:]  # len('domain:') == 7

        if not value_part:
            raise SelectorError("Domain selector requires a domain name")

        # Check for downstream operator at end
        direction: Direction = "none"
        if value_part.endswith("+"):
            direction = "downstream"
            value_part = value_part[:-1]

        if not value_part:
            raise SelectorError("Domain selector requires a domain name")

        return SelectorExpression(
            selector_type="domain", value=value_part, direction=direction
        )

    def _parse_status_selector(self, selector: str) -> SelectorExpression:
        """Parse status selector.

        Args:
            selector: Status selector string (e.g., 'status:draft', 'status:complete')

        Returns:
            Parsed SelectorExpression

        Raises:
            SelectorError: If status selector syntax is invalid
        """
        # Remove 'status:' prefix
        value_part = selector[7:]  # len('status:') == 7

        if not value_part:
            raise SelectorError("Status selector requires a status value")

        # Validate status value
        valid_statuses = {"stub", "draft", "complete"}
        if value_part not in valid_statuses:
            raise SelectorError(
                f"Invalid status value '{value_part}'. Must be one of: {', '.join(sorted(valid_statuses))}"
            )

        return SelectorExpression(
            selector_type="status", value=value_part, direction="none"
        )

    def _parse_concept_selector(self, selector: str) -> SelectorExpression:
        """Parse concept selector with graph operators.

        Args:
            selector: Concept selector string (e.g., 'customer', '+customer', 'customer+', '+customer+3')

        Returns:
            Parsed SelectorExpression

        Raises:
            SelectorError: If concept selector syntax is invalid
        """
        direction: Direction = "none"
        depth: int | None = None
        value_part = selector

        # Check for upstream operator at start
        if value_part.startswith("+"):
            direction = "upstream"
            value_part = value_part[1:]

        # Check for downstream operator at end (with optional depth)
        if "+" in value_part:
            # Could be '+' or '+N' where N is depth
            parts = value_part.split("+", 1)
            value_part = parts[0]

            if len(parts) > 1:
                depth_str = parts[1]
                if depth_str:  # '+N' format
                    try:
                        depth = int(depth_str)
                        if depth < 1:
                            raise SelectorError("Depth must be a positive integer")
                    except ValueError:
                        raise SelectorError(
                            f"Invalid depth value '{depth_str}'. Must be a positive integer"
                        ) from None

                # Update direction based on prefix
                if direction == "upstream":
                    direction = "bidirectional"
                else:
                    direction = "downstream"

        if not value_part:
            raise SelectorError("Concept selector requires a concept name")

        return SelectorExpression(
            selector_type="concept", value=value_part, direction=direction, depth=depth
        )


class SelectorResolver:
    """Resolves selector expressions against a ProjectState."""

    def __init__(self, state: ProjectState):
        """Initialize the resolver.

        Args:
            state: The project state to resolve selectors against
        """
        self.state = state

    def resolve(self, expression: SelectorExpression) -> set[str]:
        """Resolve a selector expression to a set of concept names.

        Args:
            expression: The selector expression to resolve

        Returns:
            Set of concept names matching the selector

        Raises:
            SelectorError: If resolution fails (e.g., unknown concept)
        """
        if expression.selector_type == "all":
            return set(self.state.concepts.keys())

        if expression.selector_type == "domain":
            return self._resolve_domain(expression)

        if expression.selector_type == "status":
            return self._resolve_status(expression)

        if expression.selector_type == "concept":
            return self._resolve_concept(expression)

        raise SelectorError(f"Unknown selector type: {expression.selector_type}")

    def _resolve_domain(self, expression: SelectorExpression) -> set[str]:
        """Resolve a domain selector.

        Args:
            expression: Domain selector expression

        Returns:
            Set of concept names in the domain

        Raises:
            SelectorError: If domain is unknown
        """
        domain = expression.value

        # Check if domain exists
        if domain not in self.state.domains:
            raise SelectorError(f"Unknown domain: {domain}")

        # Find all concepts in this domain
        concepts = {
            name
            for name, concept in self.state.concepts.items()
            if concept.domain == domain
        }

        # If downstream operator, expand to include downstream concepts
        if expression.direction == "downstream":
            expanded = set(concepts)
            for concept in concepts:
                downstream = self._get_downstream(
                    concept, depth=expression.depth, visited=set()
                )
                expanded.update(downstream)
            return expanded

        return concepts

    def _resolve_status(self, expression: SelectorExpression) -> set[str]:
        """Resolve a status selector.

        Args:
            expression: Status selector expression

        Returns:
            Set of concept names with the specified status
        """
        status = expression.value

        return {
            name
            for name, concept in self.state.concepts.items()
            if concept.status == status
        }

    def _resolve_concept(self, expression: SelectorExpression) -> set[str]:
        """Resolve a concept selector with graph traversal.

        Args:
            expression: Concept selector expression

        Returns:
            Set of concept names

        Raises:
            SelectorError: If concept is unknown
        """
        concept = expression.value

        # Check if concept exists
        if concept not in self.state.concepts:
            raise SelectorError(f"Unknown concept: {concept}")

        result = {concept}

        if expression.direction == "none":
            return result

        if expression.direction in ("downstream", "bidirectional"):
            downstream = self._get_downstream(
                concept, depth=expression.depth, visited=set()
            )
            result.update(downstream)

        if expression.direction in ("upstream", "bidirectional"):
            upstream = self._get_upstream(
                concept, depth=expression.depth, visited=set()
            )
            result.update(upstream)

        return result

    def _get_downstream(
        self, concept: str, depth: int | None, visited: set[str]
    ) -> set[str]:
        """Get all downstream concepts from a starting concept.

        Args:
            concept: Starting concept name
            depth: Maximum depth to traverse (None for unlimited)
            visited: Set of already visited concepts (for cycle detection)

        Returns:
            Set of downstream concept names
        """
        if concept in visited:
            return set()

        if depth is not None and depth <= 0:
            return set()

        visited.add(concept)
        result = set()

        # Find all relationships where this concept is the source
        for rel in self.state.relationships.values():
            if rel.from_concept == concept:
                target = rel.to_concept
                result.add(target)

                # Recursively get downstream concepts
                next_depth = None if depth is None else depth - 1
                downstream = self._get_downstream(target, next_depth, visited)
                result.update(downstream)

        return result

    def _get_upstream(
        self, concept: str, depth: int | None, visited: set[str]
    ) -> set[str]:
        """Get all upstream concepts from a starting concept.

        Args:
            concept: Starting concept name
            depth: Maximum depth to traverse (None for unlimited)
            visited: Set of already visited concepts (for cycle detection)

        Returns:
            Set of upstream concept names
        """
        if concept in visited:
            return set()

        if depth is not None and depth <= 0:
            return set()

        visited.add(concept)
        result = set()

        # Find all relationships where this concept is the target
        for rel in self.state.relationships.values():
            if rel.to_concept == concept:
                source = rel.from_concept
                result.add(source)

                # Recursively get upstream concepts
                next_depth = None if depth is None else depth - 1
                upstream = self._get_upstream(source, next_depth, visited)
                result.update(upstream)

        return result


def select_concepts(state: ProjectState, selector: str) -> set[str]:
    """Parse and resolve a selector expression.

    Convenience function that combines parsing and resolution.

    Args:
        state: The project state to resolve against
        selector: The selector string to parse and resolve

    Returns:
        Set of concept names matching the selector

    Raises:
        SelectorError: If parsing or resolution fails
    """
    parser = SelectorParser()
    expression = parser.parse(selector)

    resolver = SelectorResolver(state)
    return resolver.resolve(expression)
