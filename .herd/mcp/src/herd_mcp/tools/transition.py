"""Ticket transition tool stub."""

from __future__ import annotations


async def execute(
    ticket_id: str,
    to_status: str,
    blocked_by: str | None,
    note: str | None,
    agent_name: str | None,
) -> dict:
    """Transition a ticket to a new status.

    Args:
        ticket_id: Linear ticket ID.
        to_status: Target status.
        blocked_by: Optional blocker ticket ID.
        note: Optional note about the transition.
        agent_name: Current agent identity.

    Returns:
        Dict with transition_id and elapsed time in previous status.
    """
    return {
        "status": "stub",
        "message": "herd_transition not yet implemented",
        "transition_id": None,
        "ticket": ticket_id,
        "to_status": to_status,
        "blocked_by": blocked_by,
        "elapsed_in_previous": None,
        "agent": agent_name,
    }
