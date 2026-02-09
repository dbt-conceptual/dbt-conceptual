"""Ticket assignment tool implementation."""

from __future__ import annotations

from herd_mcp.db import connection


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
    if not agent_name:
        return {
            "assigned": False,
            "error": "agent_name is required",
            "ticket": ticket_id,
            "priority": priority,
        }

    with connection() as conn:
        # Verify ticket exists
        ticket = conn.execute(
            """
            SELECT ticket_code, ticket_title, ticket_description, ticket_current_status
            FROM herd.ticket_def
            WHERE ticket_code = ?
              AND deleted_at IS NULL
            """,
            [ticket_id],
        ).fetchone()

        if not ticket:
            return {
                "assigned": False,
                "error": f"Ticket {ticket_id} not found",
                "agent": agent_name,
                "ticket": ticket_id,
                "priority": priority,
            }

        # Verify agent exists and is active
        agent = conn.execute(
            """
            SELECT agent_code, agent_role, agent_status
            FROM herd.agent_def
            WHERE agent_code = ?
              AND deleted_at IS NULL
            """,
            [agent_name],
        ).fetchone()

        if not agent:
            return {
                "assigned": False,
                "error": f"Agent {agent_name} not found",
                "agent": agent_name,
                "ticket": {
                    "id": ticket[0],
                    "title": ticket[1],
                },
                "priority": priority,
            }

        if agent[2] != "active":
            return {
                "assigned": False,
                "error": f"Agent {agent_name} is not active (status: {agent[2]})",
                "agent": agent_name,
                "ticket": {
                    "id": ticket[0],
                    "title": ticket[1],
                },
                "priority": priority,
            }

        # Get or note agent's current active instance
        instance = conn.execute(
            """
            SELECT agent_instance_code
            FROM herd.agent_instance
            WHERE agent_code = ?
              AND agent_instance_ended_at IS NULL
            ORDER BY agent_instance_started_at DESC
            LIMIT 1
            """,
            [agent_name],
        ).fetchone()

        agent_instance_code = instance[0] if instance else None

        if not agent_instance_code:
            # Note: in production, we'd probably create an instance here
            # For now, we'll just note that no instance exists
            pass

        # Record assignment in ticket_activity (always, even with NULL agent_instance_code)
        conn.execute(
            """
            INSERT INTO herd.agent_instance_ticket_activity
              (agent_instance_code, ticket_code, ticket_event_type, ticket_status,
               ticket_activity_comment, created_at)
            VALUES (?, ?, 'assigned', 'assigned', ?, CURRENT_TIMESTAMP)
            """,
            [agent_instance_code, ticket_id, f"Assigned with priority: {priority}"],
        )

        # Update ticket_def convenience denorm
        conn.execute(
            """
            UPDATE herd.ticket_def
            SET ticket_current_status = 'assigned', modified_at = CURRENT_TIMESTAMP
            WHERE ticket_code = ?
            """,
            [ticket_id],
        )

        return {
            "assigned": True,
            "agent": agent_name,
            "ticket": {
                "id": ticket[0],
                "title": ticket[1],
                "description": ticket[2],
                "previous_status": ticket[3],
            },
            "priority": priority,
            "agent_instance_code": agent_instance_code,
            "note": None if agent_instance_code else "No active agent instance found",
        }
