"""Shared pytest fixtures for Herd MCP tests."""

from __future__ import annotations

import pytest

import duckdb

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
