"""Tests for dbc mcp CLI command.

Tests cover:
- Command registration and basic invocation
- Mutually exclusive --sse and --http flags
- Port option handling
- Import error handling when MCP dependencies missing
- Default stdio transport behavior
- SSE/HTTP fallback warning messages
- Help text and default values
"""

from __future__ import annotations

import builtins
from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from dbt_conceptual.cli import main


def test_mcp_command_exists() -> None:
    """Test that mcp command is registered in CLI."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "mcp" in result.output


def test_mcp_help_text() -> None:
    """Test that mcp --help shows transport options and examples."""
    runner = CliRunner()
    result = runner.invoke(main, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "--sse" in result.output
    assert "--http" in result.output
    assert "--port" in result.output
    assert "3001" in result.output
    assert "MCP" in result.output


def test_mcp_mutually_exclusive_flags() -> None:
    """Test that --sse and --http cannot be used together."""
    runner = CliRunner()
    result = runner.invoke(main, ["mcp", "--sse", "--http"])
    assert result.exit_code == 1
    assert "mutually exclusive" in result.output


def test_mcp_stdio_default() -> None:
    """Test that stdio transport is used by default (dbc mcp)."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp"])

            assert result.exit_code == 0

            # Verify stdio startup message was shown
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("stdio transport" in c for c in calls)

            # Verify mcp.run() was called exactly once
            mock_mcp.run.assert_called_once()


def test_mcp_sse_flag() -> None:
    """Test --sse flag shows SSE startup message."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--sse"])

            assert result.exit_code == 0

            # Verify SSE startup message was shown
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("SSE transport" in c for c in calls)

            # Verify mcp.run() was still called (fallback)
            mock_mcp.run.assert_called_once()


def test_mcp_http_flag() -> None:
    """Test --http flag shows HTTP startup message."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--http"])

            assert result.exit_code == 0

            # Verify HTTP startup message was shown
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("HTTP transport" in c for c in calls)

            # Verify mcp.run() was still called (fallback)
            mock_mcp.run.assert_called_once()


def test_mcp_sse_with_port() -> None:
    """Test acceptance criteria: dbc mcp --sse --port 3001."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--sse", "--port", "3001"])

            assert result.exit_code == 0

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("SSE transport" in c and "3001" in c for c in calls)


def test_mcp_http_with_port() -> None:
    """Test acceptance criteria: dbc mcp --http --port 3001."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--http", "--port", "3001"])

            assert result.exit_code == 0

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("HTTP transport" in c and "3001" in c for c in calls)


def test_mcp_custom_port() -> None:
    """Test --port option accepts custom values."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--sse", "--port", "8080"])

            assert result.exit_code == 0

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("8080" in c for c in calls)


def test_mcp_sse_fallback_warning() -> None:
    """Test that SSE shows fallback warning since FastMCP support is limited."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--sse"])

            assert result.exit_code == 0

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("not fully supported" in c for c in calls)


def test_mcp_http_fallback_warning() -> None:
    """Test that HTTP shows fallback warning since FastMCP support is limited."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--http"])

            assert result.exit_code == 0

            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("not fully supported" in c for c in calls)


def test_mcp_import_error() -> None:
    """Test graceful handling when MCP dependencies are not installed."""
    runner = CliRunner()

    # Intercept the import inside the mcp() function body
    real_import = builtins.__import__

    def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "dbt_conceptual.mcp.server":
            raise ImportError("No module named 'mcp'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        result = runner.invoke(main, ["mcp"])

    assert result.exit_code == 0
    assert "not installed" in result.output


def test_mcp_default_port() -> None:
    """Test that default port is 3001."""
    runner = CliRunner()
    result = runner.invoke(main, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "3001" in result.output


def test_mcp_port_without_transport() -> None:
    """Test that --port alone (with stdio) still works."""
    runner = CliRunner()

    with patch("dbt_conceptual.cli.console") as mock_console:
        with patch("dbt_conceptual.mcp.server.mcp") as mock_mcp:
            mock_mcp.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(main, ["mcp", "--port", "5555"])

            assert result.exit_code == 0

            # With stdio transport, port is accepted but not used in message
            calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("stdio transport" in c for c in calls)


def test_serve_command_unchanged() -> None:
    """Test that dbc serve is still registered and has its own options."""
    runner = CliRunner()
    result = runner.invoke(main, ["serve", "--help"])
    assert result.exit_code == 0
    # serve has --host, --port with default 8050, --demo
    assert "--host" in result.output
    assert "--port" in result.output
    assert "8050" in result.output
    assert "--demo" in result.output
    # serve should NOT have MCP-specific flags
    assert "--sse" not in result.output
    assert "--http" not in result.output
