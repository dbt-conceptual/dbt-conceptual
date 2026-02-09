"""Agent lifecycle tool stubs."""

from __future__ import annotations


async def decommission(agent_name: str, current_agent: str | None) -> dict:
    """Permanently decommission an agent instance.

    Args:
        agent_name: Agent instance to decommission.
        current_agent: Current agent identity (requesting decommission).

    Returns:
        Dict with success status and message.
    """
    return {
        "status": "stub",
        "message": "herd_decommission not yet implemented",
        "success": False,
        "target_agent": agent_name,
        "requested_by": current_agent,
    }


async def standdown(agent_name: str, current_agent: str | None) -> dict:
    """Temporarily stand down an agent instance.

    Args:
        agent_name: Agent instance to stand down.
        current_agent: Current agent identity (requesting standdown).

    Returns:
        Dict with success status and message.
    """
    return {
        "status": "stub",
        "message": "herd_standdown not yet implemented",
        "success": False,
        "target_agent": agent_name,
        "requested_by": current_agent,
    }
