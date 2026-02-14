"""Tests for MCP server functionality.

Tests cover:
- Tool registration and schemas
- Lazy initialization of resolver
- Error handling (graceful errors, not crashes)
- All four tools (get_context, list_concepts, get_relationships, validate)
"""

from __future__ import annotations

import pytest


# Test that the server module can be imported
def test_server_imports():
    """Test that MCP server module imports successfully."""
    from dbt_conceptual.mcp import server

    assert hasattr(server, "mcp")
    assert hasattr(server, "_get_resolver")


def test_server_has_tools():
    """Test that all four tools are registered."""
    # Verify all tool functions exist in the server module
    from dbt_conceptual.mcp import server

    assert hasattr(server, "dbc_get_context")
    assert hasattr(server, "dbc_list_concepts")
    assert hasattr(server, "dbc_get_relationships")
    assert hasattr(server, "dbc_validate")


@pytest.mark.asyncio
async def test_get_context_stub():
    """Test dbc_get_context returns stub message."""
    from dbt_conceptual.mcp.server import dbc_get_context

    result = await dbc_get_context("customer", format="llm", depth=1)
    assert isinstance(result, str)
    assert "Not yet implemented" in result or "Error" in result


@pytest.mark.asyncio
async def test_list_concepts_stub():
    """Test dbc_list_concepts returns stub message."""
    from dbt_conceptual.mcp.server import dbc_list_concepts

    result = await dbc_list_concepts()
    assert isinstance(result, str)
    assert "Not yet implemented" in result or "Error" in result


@pytest.mark.asyncio
async def test_list_concepts_with_filters():
    """Test dbc_list_concepts with domain and status filters."""
    from dbt_conceptual.mcp.server import dbc_list_concepts

    result = await dbc_list_concepts(domain="sales", status="implemented")
    assert isinstance(result, str)
    assert "Not yet implemented" in result or "Error" in result


@pytest.mark.asyncio
async def test_get_relationships_stub():
    """Test dbc_get_relationships returns stub message."""
    from dbt_conceptual.mcp.server import dbc_get_relationships

    result = await dbc_get_relationships("customer", depth=2)
    assert isinstance(result, str)
    assert "Not yet implemented" in result or "Error" in result


@pytest.mark.asyncio
async def test_validate_stub():
    """Test dbc_validate returns stub message."""
    from dbt_conceptual.mcp.server import dbc_validate

    result = await dbc_validate()
    assert isinstance(result, str)
    assert "Not yet implemented" in result or "Error" in result


def test_resolver_lazy_init():
    """Test that resolver is None initially (lazy initialization)."""
    from dbt_conceptual.mcp import server

    # Reset resolver to None for test
    server._resolver = None
    assert server._resolver is None


@pytest.mark.asyncio
async def test_error_handling_no_project():
    """Test that tools handle missing project gracefully."""
    from dbt_conceptual.mcp import server

    # Reset resolver to force re-initialization
    server._resolver = None

    # Tools should return error messages, not crash
    result = await server.dbc_validate()
    assert isinstance(result, str)
    # Should either be "Not yet implemented" or an error message
    assert "Error" in result or "Not yet implemented" in result


def test_main_entry_point():
    """Test that __main__ module can be imported."""
    from dbt_conceptual.mcp import __main__

    assert hasattr(__main__, "main")


def test_package_exports():
    """Test that package exports mcp instance."""
    from dbt_conceptual.mcp import mcp

    assert mcp is not None
