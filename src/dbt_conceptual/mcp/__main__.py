"""Entry point for dbt-conceptual MCP server.

Supports three transport mechanisms:
- stdio (default): For Claude Code, Cursor, local agents
- SSE: For remote agents and team setups
- HTTP: Newer MCP spec direction

Run with:
  python -m dbt_conceptual.mcp           # MCP stdio server (default)
  python -m dbt_conceptual.mcp --sse     # SSE transport
  python -m dbt_conceptual.mcp --http    # HTTP transport
"""

from __future__ import annotations

import sys

from .server import mcp


def main() -> None:
    """Main entry point with transport selection.

    Default is stdio transport. Use --sse or --http flags to select
    alternative transports.
    """
    # Check for transport flags
    if "--sse" in sys.argv:
        # SSE transport for remote agents
        # FastMCP.run() supports SSE via environment variables or config
        # For now, use stdio as FastMCP doesn't expose direct SSE mode
        # This will be enhanced when FastMCP adds SSE support
        print(
            "SSE transport requested but not yet fully supported by FastMCP.",
            file=sys.stderr,
        )
        print("Falling back to stdio transport.", file=sys.stderr)
        mcp.run()
    elif "--http" in sys.argv:
        # HTTP transport for newer MCP spec
        # Similar to SSE, this will be enhanced when FastMCP adds HTTP support
        print(
            "HTTP transport requested but not yet fully supported by FastMCP.",
            file=sys.stderr,
        )
        print("Falling back to stdio transport.", file=sys.stderr)
        mcp.run()
    else:
        # Default stdio transport
        mcp.run()


if __name__ == "__main__":
    main()
