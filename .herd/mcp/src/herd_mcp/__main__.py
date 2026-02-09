"""Entry point for Herd MCP server.

Run with: python -m herd_mcp
"""

from __future__ import annotations

from .server import mcp

if __name__ == "__main__":
    mcp.run()
