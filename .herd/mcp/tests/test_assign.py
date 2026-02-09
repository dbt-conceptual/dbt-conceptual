"""Tests for herd_assign tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from herd_mcp.tools import assign


@pytest.fixture
def seeded_db(in_memory_db):
    """Provide a database with test data for assign tool."""
    conn = in_memory_db

    # Insert test agents
    conn.execute(
        """
        INSERT INTO herd.agent_def
          (agent_code, agent_role, agent_status, created_at)
        VALUES
          ('grunt', 'backend', 'active', CURRENT_TIMESTAMP),
          ('pikasso', 'frontend', 'active', CURRENT_TIMESTAMP)
        """
    )

    # Insert test tickets
    conn.execute(
        """
        INSERT INTO herd.ticket_def
          (ticket_code, ticket_title, ticket_description, ticket_current_status, created_at)
        VALUES
          ('DBC-100', 'Test ticket', 'Test description', 'backlog', CURRENT_TIMESTAMP),
          ('DBC-101', 'Another ticket', 'Another description', 'backlog', CURRENT_TIMESTAMP)
        """
    )

    # Insert test agent instance for grunt
    conn.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, agent_instance_started_at)
        VALUES ('inst-001', 'grunt', 'claude-sonnet-4', CURRENT_TIMESTAMP)
        """
    )

    yield conn


@pytest.mark.asyncio
async def test_assign_success_with_instance(seeded_db):
    """Test successful ticket assignment with active agent instance."""
    with patch("herd_mcp.tools.assign.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await assign.execute(
            ticket_id="DBC-100",
            agent_name="grunt",
            priority="high",
        )

        assert result["assigned"] is True
        assert result["agent"] == "grunt"
        assert result["ticket"]["id"] == "DBC-100"
        assert result["ticket"]["title"] == "Test ticket"
        assert result["ticket"]["previous_status"] == "backlog"
        assert result["priority"] == "high"
        assert result["agent_instance_code"] == "inst-001"
        assert result["note"] is None

        # Verify ticket status was updated
        ticket_status = seeded_db.execute(
            "SELECT ticket_current_status FROM herd.ticket_def WHERE ticket_code = 'DBC-100'"
        ).fetchone()[0]
        assert ticket_status == "assigned"

        # Verify activity was recorded
        activity = seeded_db.execute(
            """
            SELECT ticket_event_type, ticket_status, ticket_activity_comment
            FROM herd.agent_instance_ticket_activity
            WHERE ticket_code = 'DBC-100'
            """
        ).fetchone()
        assert activity is not None
        assert activity[0] == "assigned"
        assert activity[1] == "assigned"
        assert "high" in activity[2]


@pytest.mark.asyncio
async def test_assign_without_agent_instance(seeded_db):
    """Test ticket assignment when agent has no active instance."""
    with patch("herd_mcp.tools.assign.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await assign.execute(
            ticket_id="DBC-101",
            agent_name="pikasso",  # Has no active instance
            priority="medium",
        )

        # Should still succeed but note the missing instance
        assert result["assigned"] is True
        assert result["agent"] == "pikasso"
        assert result["agent_instance_code"] is None
        assert result["note"] == "No active agent instance found"

        # Verify ticket status was updated
        ticket_status = seeded_db.execute(
            "SELECT ticket_current_status FROM herd.ticket_def WHERE ticket_code = 'DBC-101'"
        ).fetchone()[0]
        assert ticket_status == "assigned"

        # Verify NO activity was recorded (no instance)
        count = seeded_db.execute(
            "SELECT COUNT(*) FROM herd.agent_instance_ticket_activity WHERE ticket_code = 'DBC-101'"
        ).fetchone()[0]
        assert count == 0


@pytest.mark.asyncio
async def test_assign_missing_agent_name(seeded_db):
    """Test ticket assignment without agent name."""
    with patch("herd_mcp.tools.assign.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await assign.execute(
            ticket_id="DBC-100",
            agent_name=None,
            priority="high",
        )

        assert result["assigned"] is False
        assert "error" in result
        assert "agent_name is required" in result["error"]


@pytest.mark.asyncio
async def test_assign_ticket_not_found(seeded_db):
    """Test ticket assignment for nonexistent ticket."""
    with patch("herd_mcp.tools.assign.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await assign.execute(
            ticket_id="NONEXISTENT",
            agent_name="grunt",
            priority="high",
        )

        assert result["assigned"] is False
        assert "error" in result
        assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_assign_agent_not_found(seeded_db):
    """Test ticket assignment to nonexistent agent."""
    with patch("herd_mcp.tools.assign.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await assign.execute(
            ticket_id="DBC-100",
            agent_name="nonexistent",
            priority="high",
        )

        assert result["assigned"] is False
        assert "error" in result
        assert "Agent nonexistent not found" in result["error"]


@pytest.mark.asyncio
async def test_assign_inactive_agent(seeded_db):
    """Test ticket assignment to inactive agent."""
    # First set pikasso to inactive
    seeded_db.execute(
        "UPDATE herd.agent_def SET agent_status = 'inactive' WHERE agent_code = 'pikasso'"
    )

    with patch("herd_mcp.tools.assign.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await assign.execute(
            ticket_id="DBC-100",
            agent_name="pikasso",
            priority="high",
        )

        assert result["assigned"] is False
        assert "error" in result
        assert "not active" in result["error"]
        assert "inactive" in result["error"]


@pytest.mark.asyncio
async def test_assign_updates_modified_at(seeded_db):
    """Test that ticket modified_at is updated on assignment."""
    with patch("herd_mcp.tools.assign.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        # Perform assignment
        result = await assign.execute(
            ticket_id="DBC-100",
            agent_name="grunt",
            priority="high",
        )

        assert result["assigned"] is True

        # Verify modified_at was set
        modified_at = seeded_db.execute(
            "SELECT modified_at FROM herd.ticket_def WHERE ticket_code = 'DBC-100'"
        ).fetchone()[0]
        assert modified_at is not None
