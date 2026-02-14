"""Shared pytest fixtures for Herd MCP tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import duckdb
import pytest
from herd_mcp import db


@pytest.fixture
def in_memory_db() -> duckdb.DuckDBPyConnection:
    """Provide an in-memory DuckDB connection with schema initialized.

    Yields:
        DuckDB connection with herd schema.
    """
    conn = duckdb.connect(":memory:")
    db.init_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def empty_db() -> duckdb.DuckDBPyConnection:
    """Provide an in-memory DuckDB connection without schema.

    Yields:
        Empty DuckDB connection.
    """
    conn = duckdb.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def mock_vault_refresh():
    """Mock VaultRefreshManager in all integration tests.

    This prevents integration tests from executing real dbt run subprocesses
    when vault refresh is triggered by lifecycle/review/transition operations.
    """
    # Create a mock manager instance
    mock_manager = MagicMock()
    mock_manager.trigger_refresh = AsyncMock(
        return_value={"status": "mocked", "milestone": "test"}
    )

    # Patch both the singleton instance and get_manager to return our mock
    with patch("herd_mcp.vault_refresh.VaultRefreshManager._instance", mock_manager):
        with patch("herd_mcp.vault_refresh.get_manager", return_value=mock_manager):
            yield mock_manager
