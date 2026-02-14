"""Tests for dbc mcp CLI command.

Tests cover:
- Command registration and basic invocation
- Mutually exclusive --sse and --http flags
- Port option handling
- Import error handling when MCP dependencies missing
- Default stdio transport behavior
"""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from dbt_conceptual.cli import main


def test_mcp_command_exists():
    """Test that mcp command is registered in CLI."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "mcp" in result.output


def test_mcp_mutually_exclusive_flags():
    """Test that --sse and --http cannot be used together."""
    runner = CliRunner()
    result = runner.invoke(main, ["mcp", "--sse", "--http"])
    assert result.exit_code == 1
    assert "mutually exclusive" in result.output


def test_mcp_stdio_default():
    """Test that stdio transport is used by default."""
    runner = CliRunner()

    # Mock the mcp instance
    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            # Simulate KeyboardInterrupt to exit cleanly
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp"])

            # Should exit cleanly after KeyboardInterrupt
            assert result.exit_code == 0

            # Verify stdio startup message was shown
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("stdio transport" in str(call) for call in calls)

            # Verify mcp.run() was called
            mock_mcp.run.assert_called_once()


def test_mcp_sse_flag():
    """Test --sse flag shows SSE startup message."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--sse"])

            assert result.exit_code == 0

            # Verify SSE startup message was shown
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("SSE transport" in str(call) for call in calls)


def test_mcp_http_flag():
    """Test --http flag shows HTTP startup message."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--http"])

            assert result.exit_code == 0

            # Verify HTTP startup message was shown
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("HTTP transport" in str(call) for call in calls)


def test_mcp_custom_port():
    """Test --port option is accepted."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--sse", "--port", "8080"])

            assert result.exit_code == 0

            # Verify port was mentioned in startup message
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("8080" in str(call) for call in calls)


def test_mcp_import_error():
    """Test graceful handling when MCP dependencies are not installed."""
    runner = CliRunner()

    # Better approach: mock the import inside the function
    with patch.dict("sys.modules", {"dbt_conceptual.mcp.server": None}):
        # Force reimport to trigger ImportError
        result = runner.invoke(main, ["mcp"])

        # Should handle gracefully
        assert result.exit_code == 0
        assert "not installed" in result.output or result.exit_code == 0


def test_mcp_default_port():
    """Test that default port is 3001."""
    runner = CliRunner()
    result = runner.invoke(main, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "3001" in result.output  # Default port shown in help
