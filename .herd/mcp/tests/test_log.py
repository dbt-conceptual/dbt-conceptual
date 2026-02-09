"""Tests for herd_log tool."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from herd_mcp.tools import log


@pytest.fixture
def seeded_db(in_memory_db):
    """Provide a database with test data for log tool."""
    conn = in_memory_db

    # Insert test agent
    conn.execute(
        """
        INSERT INTO herd.agent_def
          (agent_code, agent_role, agent_status, created_at)
        VALUES ('grunt', 'backend', 'active', CURRENT_TIMESTAMP)
        """
    )

    # Insert test agent instance
    conn.execute(
        """
        INSERT INTO herd.agent_instance
          (agent_instance_code, agent_code, model_code, agent_instance_started_at)
        VALUES ('inst-001', 'grunt', 'claude-sonnet-4', CURRENT_TIMESTAMP)
        """
    )

    yield conn


def test_classify_event_type_pr():
    """Test event classification for PR submissions."""
    assert log._classify_event_type("Created PR #123") == "pr_submitted"
    assert log._classify_event_type("Opened pull request") == "pr_submitted"


def test_classify_event_type_review():
    """Test event classification for reviews."""
    assert log._classify_event_type("Code review complete") == "review_complete"
    assert log._classify_event_type("QA passed") == "review_complete"


def test_classify_event_type_blocked():
    """Test event classification for blockers."""
    assert log._classify_event_type("Blocked by missing API") == "blocked"


def test_classify_event_type_started():
    """Test event classification for work start."""
    assert log._classify_event_type("Started working on DBC-91") == "work_started"
    assert log._classify_event_type("Beginning implementation") == "work_started"


def test_classify_event_type_commit():
    """Test event classification for commits."""
    assert log._classify_event_type("Pushed commit abc123") == "code_pushed"
    assert log._classify_event_type("New commit to branch") == "code_pushed"


def test_classify_event_type_default():
    """Test event classification for generic updates."""
    assert log._classify_event_type("Making progress") == "status_update"
    assert log._classify_event_type("Random message") == "status_update"


@pytest.mark.asyncio
async def test_execute_with_agent_instance(seeded_db):
    """Test log execution with valid agent instance."""
    # Create a mock connection that won't close
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = seeded_db.execute

    with patch("herd_mcp.tools.log.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        with patch("herd_mcp.tools.log._post_to_slack") as mock_slack:
            mock_slack.return_value = {"success": True, "response": {"ok": True}}

            result = await log.execute(
                message="Started working on DBC-91",
                channel="#herd-feed",
                await_response=False,
                agent_name="grunt",
            )

            assert result["posted"] is True
            assert result["agent"] == "grunt"
            assert result["event_type"] == "work_started"
            assert result["event_id"] is not None

            # Verify lifecycle activity was recorded
            activity = seeded_db.execute(
                """
                SELECT lifecycle_event_type, lifecycle_detail
                FROM herd.agent_instance_lifecycle_activity
                WHERE agent_instance_code = 'inst-001'
                """
            ).fetchone()

            assert activity is not None
            assert activity[0] == "work_started"
            assert activity[1] == "Started working on DBC-91"


@pytest.mark.asyncio
async def test_execute_without_agent_instance(in_memory_db):
    """Test log execution without active agent instance."""
    with patch("herd_mcp.tools.log.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=in_memory_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        with patch("herd_mcp.tools.log._post_to_slack") as mock_slack:
            mock_slack.return_value = {"success": True, "response": {"ok": True}}

            result = await log.execute(
                message="Testing without instance",
                channel="#herd-feed",
                await_response=False,
                agent_name="nonexistent",
            )

            assert result["posted"] is True
            assert result["agent"] == "nonexistent"
            assert result["event_type"] == "status_update"

            # Verify no lifecycle activity was recorded (no instance)
            count = in_memory_db.execute(
                "SELECT COUNT(*) FROM herd.agent_instance_lifecycle_activity"
            ).fetchone()[0]
            assert count == 0


@pytest.mark.asyncio
async def test_execute_slack_failure(seeded_db):
    """Test log execution when Slack posting fails."""
    with patch("herd_mcp.tools.log.connection") as mock_context:
        mock_context.return_value.__enter__ = MagicMock(return_value=seeded_db)
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        with patch("herd_mcp.tools.log._post_to_slack") as mock_slack:
            mock_slack.return_value = {"success": False, "error": "Token not set"}

            result = await log.execute(
                message="Test message",
                channel="#herd-feed",
                await_response=False,
                agent_name="grunt",
            )

            assert result["posted"] is False
            assert result["event_id"] is None
            assert "slack_response" in result
            assert result["slack_response"]["error"] == "Token not set"


def test_post_to_slack_no_token():
    """Test Slack posting without token."""
    with patch.dict(os.environ, {}, clear=True):
        result = log._post_to_slack("Test message", "#test", "TestAgent")
        assert result["success"] is False
        assert "error" in result
        assert "HERD_SLACK_TOKEN" in result["error"]


def test_post_to_slack_with_token():
    """Test Slack posting with token (mocked)."""
    with patch.dict(os.environ, {"HERD_SLACK_TOKEN": "xoxb-test-token"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            # Mock successful Slack API response
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"ok": true, "ts": "1234567890.123"}'
            mock_response.__enter__ = MagicMock(return_value=mock_response)
            mock_response.__exit__ = MagicMock(return_value=None)
            mock_urlopen.return_value = mock_response

            result = log._post_to_slack("Test message", "#test", "TestAgent")
            assert result["success"] is True
            assert "response" in result
            assert result["response"]["ok"] is True
