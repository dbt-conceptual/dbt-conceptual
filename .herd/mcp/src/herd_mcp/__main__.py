"""Entry point for Herd MCP server.

Run with:
  python -m herd_mcp       # MCP stdio server
  python -m herd_mcp serve # REST API server
"""

from __future__ import annotations

import os
import sys

from .server import mcp


def main() -> None:
    """Main entry point with subcommand support."""
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        from .rest_server import run_server

        host = os.getenv("HERD_API_HOST", "0.0.0.0")
        port = int(os.getenv("HERD_API_PORT", "8420"))
        run_server(host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
