"""MCP server setup and tool registration for dbt-conceptual.

The server supports three transport mechanisms:
- stdio (default): For Claude Code, Cursor, local agents
- SSE: For remote agents and team setups
- HTTP: Newer MCP spec direction

Tools are registered with proper schemas. The resolver is lazily initialized
on first tool call to avoid startup overhead.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("dbt-conceptual")

# Lazy initialization of resolver
_resolver: Any = None


def _get_resolver() -> Any:
    """Get or initialize the dbt project resolver.

    The resolver is lazily initialized on first tool call to avoid
    startup overhead and allow the server to start even if no dbt
    project is available.

    Returns:
        ProjectResolver instance

    Raises:
        RuntimeError: If resolver initialization fails
    """
    global _resolver
    if _resolver is None:
        # Import here to avoid circular dependencies
        from ..config import load_project_config
        from ..parser import parse_project
        from ..scanner import find_dbt_project

        try:
            # Find dbt project
            project_dir = find_dbt_project()
            if not project_dir:
                raise RuntimeError(
                    "Could not find dbt_project.yml. Run this command from within a dbt project."
                )

            # Load config and parse project
            config = load_project_config(project_dir)
            state = parse_project(project_dir, config)

            # Store both config and state for tool handlers
            _resolver = {"config": config, "state": state, "project_dir": project_dir}
        except Exception as e:
            raise RuntimeError(f"Failed to initialize dbt project resolver: {e}") from e

    return _resolver


@mcp.tool()
async def dbc_get_context(
    selector: str,
    format: str = "llm",
    depth: int = 1,
) -> str:
    """Get full context for concepts matching a selector.

    Retrieves comprehensive information about one or more concepts,
    including their definitions, relationships, and implementation details.

    Args:
        selector: Concept selector (name, pattern, or 'all')
        format: Output format - 'llm' (human-readable), 'json', or 'yaml'
        depth: Relationship traversal depth (1-3)

    Returns:
        Formatted context string containing concept information

    Example:
        >>> await dbc_get_context("customer", format="llm", depth=2)
        "# Concept: Customer\\n\\nDefinition: ...\\n\\nRelationships:\\n..."
    """
    try:
        resolver = _get_resolver()
        from .handlers import handle_get_context

        return handle_get_context(
            selector=selector,
            format=format,
            depth=depth,
            project_state=resolver["state"],
            config=resolver["config"],
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def dbc_list_concepts(
    domain: str | None = None,
    status: str | None = None,
) -> str:
    """List all concepts, optionally filtered by domain or status.

    Provides an overview of available concepts in the project,
    with optional filtering by domain or implementation status.

    Args:
        domain: Optional domain filter (e.g., 'sales', 'finance')
        status: Optional status filter (e.g., 'stub', 'draft', 'complete')

    Returns:
        Formatted list of concepts with basic metadata

    Example:
        >>> await dbc_list_concepts(domain="sales")
        "Found 5 concepts in domain 'sales':\\n- Customer\\n- Order\\n..."
    """
    try:
        resolver = _get_resolver()
        from .handlers import handle_list_concepts

        return handle_list_concepts(
            domain=domain,
            status=status,
            project_state=resolver["state"],
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def dbc_get_relationships(
    concept: str,
    depth: int = 1,
) -> str:
    """Get relationships for a concept.

    Retrieves relationship information for a specific concept,
    showing how it connects to other concepts in the model.

    Args:
        concept: Concept name
        depth: Relationship traversal depth (1-3)

    Returns:
        Formatted relationship information with grain warnings

    Example:
        >>> await dbc_get_relationships("customer", depth=2)
        "Relationships for Customer:\\n- has many Orders\\n- belongs to CustomerSegment\\n..."
    """
    try:
        resolver = _get_resolver()
        from .handlers import handle_get_relationships

        return handle_get_relationships(
            concept=concept,
            depth=depth,
            project_state=resolver["state"],
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def dbc_validate() -> str:
    """Run validation on the conceptual model.

    Validates the entire conceptual model against configured rules,
    checking for missing definitions, broken references, and other issues.

    Returns:
        Validation report with any errors or warnings

    Example:
        >>> await dbc_validate()
        "Validation Results:\\n✓ All concepts have definitions\\n⚠ Warning: Orphan model detected: stg_users\\n..."
    """
    try:
        resolver = _get_resolver()
        from .handlers import handle_validate

        return handle_validate(
            project_state=resolver["state"],
            config=resolver["config"],
        )
    except Exception as e:
        return f"Error: {e}"
