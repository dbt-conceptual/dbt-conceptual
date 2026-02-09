"""Status query tool stub."""

from __future__ import annotations


async def execute(scope: str, agent_name: str | None) -> dict:
    """Get current status of Herd agents, sprint, and blockers.

    Args:
        scope: Status scope - "all", "agents", "sprint", or "blockers".
        agent_name: Current agent identity.

    Returns:
        Dict with agents status, sprint info, and blocker list.
    """
    return {
        "status": "stub",
        "message": "herd_status not yet implemented",
        "scope": scope,
        "agents": [],
        "sprint": None,
        "blockers": [],
        "requesting_agent": agent_name,
    }
