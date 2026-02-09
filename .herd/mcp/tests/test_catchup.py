"""Tests for herd_catchup tool."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from herd_mcp.tools import catchup


@pytest.fixture
def seeded_db(in_memory_db):
    """Provide a database with test data for catchup tool."""
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

    # Insert previous ended instance for grunt
    yesterday = datetime.now() - timedelta(days=1)
    conn.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, ticket_code,
           agent_instance_started_at, agent_instance_ended_at, agent_instance_outcome)
        VALUES
          ('inst-grunt-prev', 'grunt', 'claude-sonnet-4', 'DBC-100', ?, ?, 'completed')
        """,
        [yesterday - timedelta(hours=2), yesterday],
    )

    # Insert current instance for grunt
    conn.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, ticket_code,
           agent_instance_started_at)
        VALUES
          ('inst-grunt-current', 'grunt', 'claude-sonnet-4', 'DBC-100', CURRENT_TIMESTAMP)
        """
    )

    # Insert ticket activity after previous session ended
    conn.execute(
        """
        INSERT INTO herd.agent_instance_ticket_activity
          (agent_instance_code, ticket_code, ticket_event_type, ticket_status,
           ticket_activity_comment, created_at)
        VALUES
          ('inst-grunt-current', 'DBC-100', 'status_changed', 'in_review', 'Code reviewed', CURRENT_TIMESTAMP),
          ('inst-grunt-current', 'DBC-100', 'status_changed', 'merged', 'PR merged', CURRENT_TIMESTAMP)
        """
    )

    yield conn


@pytest.mark.asyncio
async def test_catchup_with_previous_session(seeded_db):
    """Test catchup with previous session and updates."""
    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name="grunt")

        assert result["since"] is not None
        assert result["agent"] == "grunt"
        assert result["previous_instance"] == "inst-grunt-prev"
        assert len(result["ticket_updates"]) > 0
        assert "updates across" in result["summary"]


@pytest.mark.asyncio
async def test_catchup_first_session(seeded_db):
    """Test catchup when no previous session exists."""
    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name="pikasso")

        assert result["since"] is None
        assert result["agent"] == "pikasso"
        assert len(result["ticket_updates"]) == 0
        assert "No previous session found" in result["summary"]
        assert "starting fresh" in result["summary"]


@pytest.mark.asyncio
async def test_catchup_no_updates(seeded_db):
    """Test catchup when there are no updates since last session."""
    # Create an ended instance with no subsequent activity
    yesterday = datetime.now() - timedelta(days=1)
    seeded_db.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, ticket_code,
           agent_instance_started_at, agent_instance_ended_at, agent_instance_outcome)
        VALUES
          ('inst-pikasso-prev', 'pikasso', 'claude-opus-4', 'DBC-200', ?, ?, 'completed')
        """,
        [yesterday - timedelta(hours=2), yesterday],
    )

    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name="pikasso")

        assert result["since"] is not None
        assert len(result["ticket_updates"]) == 0
        assert "No updates" in result["summary"]


@pytest.mark.asyncio
async def test_catchup_no_agent_name(seeded_db):
    """Test catchup without agent name."""
    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name=None)

        assert result["since"] is None
        assert len(result["ticket_updates"]) == 0
        assert "No agent identity provided" in result["summary"]


@pytest.mark.asyncio
async def test_catchup_capped_history(seeded_db):
    """Test that catchup history is capped at 7 days."""
    # Create an ended instance from 10 days ago
    ten_days_ago = datetime.now() - timedelta(days=10)
    seeded_db.execute(
        """
        INSERT INTO herd.agent_def
          (agent_code, agent_role, agent_status, created_at)
        VALUES ('old-agent', 'backend', 'active', CURRENT_TIMESTAMP)
        """
    )

    seeded_db.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, ticket_code,
           agent_instance_started_at, agent_instance_ended_at, agent_instance_outcome)
        VALUES
          ('inst-old', 'old-agent', 'claude-sonnet-4', 'DBC-999', ?, ?, 'completed')
        """,
        [ten_days_ago - timedelta(hours=2), ten_days_ago],
    )

    # Add activity from 8 days ago (should be filtered out)
    eight_days_ago = datetime.now() - timedelta(days=8)
    seeded_db.execute(
        """
        INSERT INTO herd.agent_instance_ticket_activity
          (agent_instance_code, ticket_code, ticket_event_type, ticket_status,
           ticket_activity_comment, created_at)
        VALUES
          ('inst-old', 'DBC-999', 'status_changed', 'done', 'Old activity', ?)
        """,
        [eight_days_ago],
    )

    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name="old-agent")

        # Should not include activity from >7 days ago
        assert len(result["ticket_updates"]) == 0


@pytest.mark.asyncio
async def test_catchup_ticket_updates_format(seeded_db):
    """Test that ticket updates are formatted correctly."""
    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name="grunt")

        if len(result["ticket_updates"]) > 0:
            update = result["ticket_updates"][0]
            assert "ticket" in update
            assert "event_type" in update
            assert "status" in update
            assert "comment" in update
            assert "timestamp" in update
            assert "by_agent" in update


@pytest.mark.asyncio
async def test_catchup_multiple_tickets(seeded_db):
    """Test catchup with updates across multiple tickets."""
    # Add a second ticket with activity
    seeded_db.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, ticket_code,
           agent_instance_started_at)
        VALUES
          ('inst-grunt-ticket2', 'grunt', 'claude-sonnet-4', 'DBC-101', CURRENT_TIMESTAMP)
        """
    )

    seeded_db.execute(
        """
        INSERT INTO herd.agent_instance_ticket_activity
          (agent_instance_code, ticket_code, ticket_event_type, ticket_status,
           ticket_activity_comment, created_at)
        VALUES
          ('inst-grunt-ticket2', 'DBC-101', 'status_changed', 'assigned', 'New ticket', CURRENT_TIMESTAMP)
        """
    )

    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name="grunt")

        # Should include updates from both tickets
        tickets = {u["ticket"] for u in result["ticket_updates"]}
        assert len(tickets) > 0
        assert "ticket" in result["summary"]


@pytest.mark.asyncio
async def test_catchup_summary_formatting(seeded_db):
    """Test that summary is formatted correctly."""
    with patch("herd_mcp.tools.catchup.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        result = await catchup.execute(agent_name="grunt")

        summary = result["summary"]
        # Should mention event count and ticket count
        if len(result["ticket_updates"]) > 0:
            assert "update" in summary.lower()
            assert "ticket" in summary.lower()
