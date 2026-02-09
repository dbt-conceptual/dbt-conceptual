"""Ticket assignment tool stub."""

from __future__ import annotations


async def execute(
    ticket_id: str,
    agent_name: str | None,
    priority: str,
) -> dict:
    """Assign a ticket to an agent.

    Args:
        ticket_id: Linear ticket ID.
        agent_name: Agent to assign to.
        priority: Assignment priority.

    Returns:
        Dict with assignment confirmation, agent, and ticket details.
    """
    return {
        "status": "stub",
        "message": "herd_assign not yet implemented",
        "assigned": False,
        "agent": agent_name,
        "ticket": ticket_id,
        "priority": priority,
    }
