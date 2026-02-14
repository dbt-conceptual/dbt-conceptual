"""Tests for session manager."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from herd_mcp.session_manager import Session, SessionManager


@pytest.fixture
def mock_process() -> MagicMock:
    """Create a mock subprocess process.

    Returns:
        Mock process object.
    """
    process = MagicMock()
    process.returncode = None
    process.stdout = AsyncMock()
    process.stderr = AsyncMock()
    process.wait = AsyncMock()
    process.terminate = MagicMock()
    process.kill = MagicMock()
    return process


@pytest.mark.asyncio
async def test_session_creation() -> None:
    """Test creating a new session spawns Claude process."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    with patch(
        "herd_mcp.session_manager.asyncio.create_subprocess_exec"
    ) as mock_exec:
        # Mock process with stdout that returns session_id
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = AsyncMock()

        async def mock_stdout_lines() -> list[bytes]:
            yield b'{"session_id": "test-session-123"}\n'
            yield b'{"text": "Hello from Mini-Mao"}\n'

        mock_process.stdout = mock_stdout_lines()
        mock_exec.return_value = mock_process

        response = await manager.send_message(
            "1234.5678", "Hello Mini-Mao", "Architect"
        )

        # Verify Claude was spawned with correct args
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "claude"
        assert args[1] == "-p"
        assert "Message from Architect: Hello Mini-Mao" in args[2]
        assert args[3] == "--output-format"
        assert args[4] == "stream-json"

        # Verify session was created
        assert "1234.5678" in manager.sessions
        session = manager.sessions["1234.5678"]
        assert session.session_id == "test-session-123"
        assert session.message_count == 1


@pytest.mark.asyncio
async def test_message_routing_to_existing_session() -> None:
    """Test follow-up messages route to existing session with --resume."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    # Create an existing session manually
    mock_process = MagicMock()
    mock_process.returncode = 0
    existing_session = Session(
        thread_ts="1234.5678",
        process=mock_process,
        session_id="existing-session-id",
        last_activity=time.time(),
        message_count=1,
    )
    manager.sessions["1234.5678"] = existing_session

    with patch(
        "herd_mcp.session_manager.asyncio.create_subprocess_exec"
    ) as mock_exec:
        # Mock follow-up process
        followup_process = MagicMock()
        followup_process.returncode = 0
        followup_process.wait = AsyncMock()

        async def mock_stdout_lines() -> list[bytes]:
            yield b'{"text": "Follow-up response"}\n'

        followup_process.stdout = mock_stdout_lines()
        mock_exec.return_value = followup_process

        response = await manager.send_message(
            "1234.5678", "Follow-up message", "Architect"
        )

        # Verify --resume was used
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "claude"
        assert "--resume" in args
        assert "existing-session-id" in args

        # Verify message count incremented
        assert manager.sessions["1234.5678"].message_count == 2


@pytest.mark.asyncio
async def test_idle_timeout_detection() -> None:
    """Test idle sessions are detected and closed."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=2)

    # Create an old session
    mock_process = MagicMock()
    mock_process.returncode = None
    mock_process.wait = AsyncMock()
    old_session = Session(
        thread_ts="old.thread",
        process=mock_process,
        session_id="old-session",
        last_activity=time.time() - 10,  # 10 seconds ago
        message_count=1,
    )
    manager.sessions["old.thread"] = old_session

    # Manually trigger idle check logic (one iteration)
    now = time.time()
    idle_threads = [
        thread_ts
        for thread_ts, session in manager.sessions.items()
        if now - session.last_activity > manager.idle_timeout
    ]
    for thread_ts in idle_threads:
        await manager.close_session(thread_ts, reason="idle")

    # Verify old session was closed
    assert "old.thread" not in manager.sessions
    mock_process.terminate.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_command_detection() -> None:
    """Test shutdown commands are detected correctly."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    test_cases = [
        ("go to sleep", "to sleep"),
        ("Go to sleep now", "to sleep"),
        ("stand down", "stand down"),
        ("Standdown please", "stand down"),
        ("terminate now", "terminate"),
        ("shutdown", "shutdown"),
    ]

    for text, expected_reason in test_cases:
        reason = manager._is_shutdown_command(text)
        assert reason == expected_reason, f"Failed for: {text}"

    # Non-shutdown messages
    assert manager._is_shutdown_command("Hello Mini-Mao") is None
    assert manager._is_shutdown_command("What's the status?") is None


@pytest.mark.asyncio
async def test_close_session_cleanup() -> None:
    """Test closing a session terminates process and removes from active."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    # Create a session
    mock_process = MagicMock()
    mock_process.returncode = None
    mock_process.wait = AsyncMock()
    session = Session(
        thread_ts="1234.5678",
        process=mock_process,
        session_id="test-session",
        last_activity=time.time(),
        message_count=1,
    )
    manager.sessions["1234.5678"] = session

    # Close it
    await manager.close_session("1234.5678", reason="test")

    # Verify cleanup
    assert "1234.5678" not in manager.sessions
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()


@pytest.mark.asyncio
async def test_close_session_forced_kill_on_timeout() -> None:
    """Test session is force-killed if terminate times out."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    # Create a session with process that hangs on wait
    mock_process = MagicMock()
    mock_process.returncode = None
    mock_process.wait = AsyncMock(side_effect=asyncio.TimeoutError())
    session = Session(
        thread_ts="1234.5678",
        process=mock_process,
        session_id="test-session",
        last_activity=time.time(),
        message_count=1,
    )
    manager.sessions["1234.5678"] = session

    # Patch wait_for to trigger timeout immediately
    with patch(
        "herd_mcp.session_manager.asyncio.wait_for",
        side_effect=asyncio.TimeoutError(),
    ):
        mock_process.wait = AsyncMock()  # Reset for kill wait
        await manager.close_session("1234.5678", reason="test")

    # Verify kill was called
    assert "1234.5678" not in manager.sessions
    mock_process.terminate.assert_called_once()
    mock_process.kill.assert_called_once()


@pytest.mark.asyncio
async def test_close_all() -> None:
    """Test close_all shuts down all active sessions."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    # Create multiple sessions
    for i in range(3):
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.wait = AsyncMock()
        session = Session(
            thread_ts=f"thread.{i}",
            process=mock_process,
            session_id=f"session-{i}",
            last_activity=time.time(),
            message_count=1,
        )
        manager.sessions[f"thread.{i}"] = session

    await manager.close_all()

    # Verify all sessions closed
    assert len(manager.sessions) == 0


@pytest.mark.asyncio
async def test_session_id_capture_from_claude_output() -> None:
    """Test session_id is captured from Claude CLI streaming JSON."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    with patch(
        "herd_mcp.session_manager.asyncio.create_subprocess_exec"
    ) as mock_exec:
        # Mock process with multiple JSON lines
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.wait = AsyncMock()

        async def mock_stdout_lines() -> list[bytes]:
            yield b'{"type": "start"}\n'
            yield b'{"session_id": "captured-session-id"}\n'
            yield b'{"text": "Response "}\n'
            yield b'{"text": "text"}\n'

        mock_process.stdout = mock_stdout_lines()
        mock_exec.return_value = mock_process

        await manager.send_message("1234.5678", "Test", "Architect")

        # Verify session_id was captured
        session = manager.sessions["1234.5678"]
        assert session.session_id == "captured-session-id"


@pytest.mark.asyncio
async def test_shutdown_command_closes_session() -> None:
    """Test shutdown command triggers session close."""
    manager = SessionManager(project_path="/tmp/test", idle_timeout=180)

    # Create a session
    mock_process = MagicMock()
    mock_process.returncode = None
    mock_process.wait = AsyncMock()
    session = Session(
        thread_ts="1234.5678",
        process=mock_process,
        session_id="test-session",
        last_activity=time.time(),
        message_count=1,
    )
    manager.sessions["1234.5678"] = session

    # Send shutdown command
    response = await manager.send_message("1234.5678", "go to sleep", "Architect")

    # Verify session closed
    assert "1234.5678" not in manager.sessions
    assert "to sleep" in response
    mock_process.terminate.assert_called_once()
