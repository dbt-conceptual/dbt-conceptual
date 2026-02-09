"""Ticket transition tool implementation."""

from __future__ import annotations

import uuid

from herd_mcp.db import connection
from herd_mcp.vault_refresh import get_manager


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
    with connection() as conn:
        # Get current ticket status
        ticket = conn.execute(
            """
            SELECT ticket_code, ticket_title, ticket_current_status
            FROM herd.ticket_def
            WHERE ticket_code = ?
              AND deleted_at IS NULL
            """,
            [ticket_id],
        ).fetchone()

        if not ticket:
            return {
                "transition_id": None,
                "ticket": ticket_id,
                "to_status": to_status,
                "error": f"Ticket {ticket_id} not found",
            }

        current_status = ticket[2]

        # Get agent's current instance
        agent_instance_code = None
        if agent_name:
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

            if instance:
                agent_instance_code = instance[0]

        # Calculate elapsed time in previous status
        elapsed_minutes = None
        last_activity = conn.execute(
            """
            SELECT created_at
            FROM herd.agent_instance_ticket_activity
            WHERE ticket_code = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [ticket_id],
        ).fetchone()

        if last_activity and last_activity[0]:
            # Calculate time difference in minutes
            time_diff = conn.execute(
                """
                SELECT EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ?::TIMESTAMP)) / 60.0
                """,
                [str(last_activity[0])],
            ).fetchone()

            if time_diff:
                elapsed_minutes = float(time_diff[0])

        # Determine event type based on transition
        event_type = "status_changed"
        if to_status == "blocked" or blocked_by:
            event_type = "blocked"
        elif current_status == "blocked" and to_status != "blocked":
            event_type = "unblocked"

        # Generate transition ID
        transition_id = str(uuid.uuid4())

        # Record transition (always, even with NULL agent_instance_code)
        conn.execute(
            """
            INSERT INTO herd.agent_instance_ticket_activity
              (agent_instance_code, ticket_code, ticket_event_type, ticket_status,
               blocker_ticket_code, blocker_description, ticket_activity_comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                agent_instance_code,
                ticket_id,
                event_type,
                to_status,
                blocked_by,
                note if blocked_by else None,
                note,
            ],
        )

        # Update ticket_def convenience denorm
        conn.execute(
            """
            UPDATE herd.ticket_def
            SET ticket_current_status = ?,
                modified_at = CURRENT_TIMESTAMP
            WHERE ticket_code = ?
            """,
            [to_status, ticket_id],
        )

        result = {
            "transition_id": transition_id,
            "ticket": {
                "id": ticket[0],
                "title": ticket[1],
                "previous_status": current_status,
                "new_status": to_status,
            },
            "elapsed_in_previous_minutes": elapsed_minutes,
            "event_type": event_type,
            "blocked_by": blocked_by,
            "agent": agent_name,
            "agent_instance_code": agent_instance_code,
            "note": (
                "No active agent instance found" if not agent_instance_code else None
            ),
        }

    # Trigger vault refresh if ticket transitioned to done
    if to_status == "done":
        refresh_manager = get_manager()
        await refresh_manager.trigger_refresh(
            "ticket_done",
            {
                "ticket_id": ticket_id,
                "ticket_title": ticket[1],
                "agent": agent_name,
                "previous_status": current_status,
            },
        )

    return result
