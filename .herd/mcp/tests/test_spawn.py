"""Tests for herd_spawn tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from herd_mcp.tools import spawn


@pytest.fixture
def seeded_db(in_memory_db):
    """Provide a database with test data for spawn tool."""
    conn = in_memory_db

    # Insert test agent definitions
    conn.execute(
        """
        INSERT INTO herd.agent_def
          (agent_code, agent_role, agent_status, default_model_code, created_at)
        VALUES
          ('grunt', 'backend', 'active', 'claude-sonnet-4', CURRENT_TIMESTAMP),
          ('pikasso', 'frontend', 'active', 'claude-opus-4', CURRENT_TIMESTAMP),
          ('mini-mao', 'architect', 'active', 'claude-opus-4', CURRENT_TIMESTAMP)
        """
    )

    # Insert a current instance for mini-mao (spawner)
    conn.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, agent_instance_started_at)
        VALUES ('inst-mao-001', 'mini-mao', 'claude-opus-4', CURRENT_TIMESTAMP)
        """
    )

    yield conn


@pytest.mark.asyncio
async def test_spawn_single_agent(seeded_db):
    """Test spawning a single agent."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await spawn.execute(
            count=1,
            role="backend",
            model=None,
            agent_name="mini-mao",
        )

        assert result["spawned"] == 1
        assert len(result["agents"]) == 1
        assert result["agents"][0].startswith("inst-")
        assert result["role"] == "backend"
        assert result["agent_code"] == "grunt"
        assert result["model"] == "claude-sonnet-4"  # Default from agent_def
        assert result["spawned_by"] == "mini-mao"
        assert result["spawned_by_instance"] == "inst-mao-001"

    # Verify instance was created
    instance = seeded_db.execute(
        "SELECT agent_code, model_code FROM herd.agent_instance WHERE agent_instance_code = ?",
        [result["agents"][0]],
    ).fetchone()
    assert instance is not None
    assert instance[0] == "grunt"
    assert instance[1] == "claude-sonnet-4"

    # Verify lifecycle activity was recorded
    activity = seeded_db.execute(
        """
        SELECT lifecycle_event_type, lifecycle_detail
        FROM herd.agent_instance_lifecycle_activity
        WHERE agent_instance_code = ?
        """,
        [result["agents"][0]],
    ).fetchone()
    assert activity is not None
    assert activity[0] == "spawned"
    assert "mini-mao" in activity[1]


@pytest.mark.asyncio
async def test_spawn_multiple_agents(seeded_db):
    """Test spawning multiple agents."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await spawn.execute(
            count=3,
            role="frontend",
            model=None,
            agent_name="mini-mao",
        )

        assert result["spawned"] == 3
        assert len(result["agents"]) == 3
        assert result["agent_code"] == "pikasso"

    # Verify all instances were created
    count = seeded_db.execute(
        "SELECT COUNT(*) FROM herd.agent_instance WHERE agent_code = 'pikasso'"
    ).fetchone()[0]
    assert count == 3


@pytest.mark.asyncio
async def test_spawn_with_model_override(seeded_db):
    """Test spawning with model override."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await spawn.execute(
            count=1,
            role="backend",
            model="claude-haiku-4",
            agent_name="mini-mao",
        )

        assert result["model"] == "claude-haiku-4"  # Override applied

    # Verify instance has overridden model
    instance = seeded_db.execute(
        "SELECT model_code FROM herd.agent_instance WHERE agent_instance_code = ?",
        [result["agents"][0]],
    ).fetchone()
    assert instance[0] == "claude-haiku-4"


@pytest.mark.asyncio
async def test_spawn_invalid_role(seeded_db):
    """Test spawning with invalid role."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await spawn.execute(
            count=1,
            role="nonexistent_role",
            model=None,
            agent_name="mini-mao",
        )

        assert result["spawned"] == 0
        assert len(result["agents"]) == 0
        assert "error" in result
        assert "No agent definition found" in result["error"]


@pytest.mark.asyncio
async def test_spawn_zero_count(seeded_db):
    """Test spawning with count=0."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await spawn.execute(
            count=0,
            role="backend",
            model=None,
            agent_name="mini-mao",
        )

        assert result["spawned"] == 0
        assert "error" in result
        assert "count must be at least 1" in result["error"]


@pytest.mark.asyncio
async def test_spawn_without_spawner_agent(seeded_db):
    """Test spawning without spawner agent (system spawn)."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await spawn.execute(
            count=1,
            role="backend",
            model=None,
            agent_name=None,  # No spawner
        )

        assert result["spawned"] == 1
        assert result["spawned_by"] is None
        assert result["spawned_by_instance"] is None

    # Verify lifecycle detail mentions "system"
    activity = seeded_db.execute(
        """
        SELECT lifecycle_detail
        FROM herd.agent_instance_lifecycle_activity
        WHERE agent_instance_code = ?
        """,
        [result["agents"][0]],
    ).fetchone()
    assert "system" in activity[0]


@pytest.mark.asyncio
async def test_spawn_updates_spawned_by_reference(seeded_db):
    """Test that spawned instances reference the spawner."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await spawn.execute(
            count=1,
            role="backend",
            model=None,
            agent_name="mini-mao",
        )

        # Verify spawned_by_agent_instance_code is set correctly
        instance = seeded_db.execute(
            """
            SELECT spawned_by_agent_instance_code
            FROM herd.agent_instance
            WHERE agent_instance_code = ?
            """,
            [result["agents"][0]],
        ).fetchone()
        assert instance[0] == "inst-mao-001"


@pytest.mark.asyncio
async def test_spawn_multiple_roles_sequentially(seeded_db):
    """Test spawning different roles sequentially."""
    with patch("herd_mcp.tools.spawn.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        # Spawn backend
        result1 = await spawn.execute(
            count=1,
            role="backend",
            model=None,
            agent_name="mini-mao",
        )

        # Spawn frontend
        result2 = await spawn.execute(
            count=1,
            role="frontend",
            model=None,
            agent_name="mini-mao",
        )

        assert result1["agent_code"] == "grunt"
        assert result2["agent_code"] == "pikasso"

    # Verify both were created
    grunt_count = seeded_db.execute(
        "SELECT COUNT(*) FROM herd.agent_instance WHERE agent_code = 'grunt'"
    ).fetchone()[0]
    pikasso_count = seeded_db.execute(
        "SELECT COUNT(*) FROM herd.agent_instance WHERE agent_code = 'pikasso'"
    ).fetchone()[0]

    assert grunt_count == 1
    assert pikasso_count == 1
