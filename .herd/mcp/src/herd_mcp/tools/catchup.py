"""Catchup summary tool implementation."""

from __future__ import annotations

from datetime import datetime, timedelta

from herd_mcp.db import connection


async def execute(agent_name: str | None) -> dict:
    """Get a summary of what happened since agent was last active.

    Args:
        agent_name: Current agent identity.

    Returns:
        Dict with timestamp, ticket updates, and summary.
    """
    if not agent_name:
        return {
            "since": None,
            "ticket_updates": [],
            "summary": "No agent identity provided. Cannot retrieve catchup.",
        }

    with connection() as conn:
        # Find the most recent ENDED instance for this agent
        previous_instance = conn.execute(
            """
            SELECT agent_instance_code, agent_instance_ended_at
            FROM herd.agent_instance
            WHERE agent_code = ?
              AND agent_instance_ended_at IS NOT NULL
            ORDER BY agent_instance_ended_at DESC
            LIMIT 1
            """,
            [agent_name],
        ).fetchone()

        if not previous_instance:
            return {
                "since": None,
                "ticket_updates": [],
                "summary": "No previous session found. You're starting fresh.",
                "agent": agent_name,
            }

        instance_code = previous_instance[0]
        ended_at = previous_instance[1]

        # Cap at 7 days of history
        seven_days_ago = datetime.now() - timedelta(days=7)
        cutoff = max(ended_at, seven_days_ago) if ended_at else seven_days_ago

        # Get ticket updates since the last session
        # Look for transitions on this agent's tickets
        ticket_activity = conn.execute(
            """
            SELECT
                ta.ticket_code,
                ta.ticket_event_type,
                ta.ticket_status,
                ta.ticket_activity_comment,
                ta.created_at,
                ai.agent_code
            FROM herd.agent_instance_ticket_activity ta
            JOIN herd.agent_instance ai
              ON ta.agent_instance_code = ai.agent_instance_code
            WHERE ta.created_at >= ?
              AND ta.ticket_code IN (
                SELECT DISTINCT ticket_code
                FROM herd.agent_instance
                WHERE agent_code = ?
                  AND ticket_code IS NOT NULL
              )
            ORDER BY ta.created_at ASC
            LIMIT 100
            """,
            [str(cutoff), agent_name],
        ).fetchall()

        ticket_updates = []
        for row in ticket_activity:
            ticket_updates.append({
                "ticket": row[0],
                "event_type": row[1],
                "status": row[2],
                "comment": row[3],
                "timestamp": str(row[4]),
                "by_agent": row[5],
            })

        # Build summary
        if not ticket_updates:
            summary = f"No updates on your tickets since {ended_at}."
        else:
            ticket_count = len({u["ticket"] for u in ticket_updates})
            event_count = len(ticket_updates)
            summary = (
                f"Since {ended_at}: {event_count} updates across {ticket_count} "
                f"ticket{'s' if ticket_count != 1 else ''}."
            )

        return {
            "since": str(ended_at),
            "ticket_updates": ticket_updates,
            "summary": summary,
            "agent": agent_name,
            "previous_instance": instance_code,
        }
