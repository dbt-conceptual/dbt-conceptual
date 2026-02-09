"""Catchup summary tool stub."""

from __future__ import annotations


async def execute(agent_name: str | None) -> dict:
    """Get a summary of what happened since agent was last active.

    Args:
        agent_name: Current agent identity.

    Returns:
        Dict with timestamp, slack mentions, ticket updates, and summary.
    """
    return {
        "status": "stub",
        "message": "herd_catchup not yet implemented",
        "since": None,
        "slack_mentions": [],
        "ticket_updates": [],
        "summary": "No activity recorded",
        "agent": agent_name,
    }
