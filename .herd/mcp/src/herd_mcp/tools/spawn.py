"""Agent spawning tool implementation."""

from __future__ import annotations

import uuid

from herd_mcp.db import connection


async def execute(
    count: int,
    role: str,
    model: str | None,
    agent_name: str | None,
) -> dict:
    """Spawn new agent instances.

    Args:
        count: Number of agents to spawn.
        role: Agent role (backend, frontend, qa, docs).
        model: Optional model override.
        agent_name: Current agent identity (spawner).

    Returns:
        Dict with list of spawned agent instance codes.
    """
    if count < 1:
        return {
            "agents": [],
            "error": "count must be at least 1",
            "spawned": 0,
        }

    with connection() as conn:
        # Verify agent_def exists for the role
        agent_def = conn.execute(
            """
            SELECT agent_code, default_model_code, agent_status
            FROM herd.agent_def
            WHERE agent_role = ?
              AND deleted_at IS NULL
            LIMIT 1
            """,
            [role],
        ).fetchone()

        if not agent_def:
            return {
                "agents": [],
                "error": f"No agent definition found for role: {role}",
                "role": role,
                "spawned": 0,
            }

        agent_code = agent_def[0]
        default_model = agent_def[1] if agent_def[1] else "claude-sonnet-4"
        model_code = model if model else default_model

        # Get spawning agent's current instance (if available)
        spawned_by_instance = None
        if agent_name:
            spawner = conn.execute(
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

            if spawner:
                spawned_by_instance = spawner[0]

        # Spawn the requested number of agents
        spawned_instances = []
        for _ in range(count):
            instance_code = f"inst-{uuid.uuid4().hex[:8]}"

            # Insert agent_instance
            conn.execute(
                """
                INSERT INTO herd.agent_instance
                  (agent_instance_code, agent_code, model_code, ticket_code,
                   spawned_by_agent_instance_code, agent_instance_started_at)
                VALUES (?, ?, ?, NULL, ?, CURRENT_TIMESTAMP)
                """,
                [instance_code, agent_code, model_code, spawned_by_instance],
            )

            # Record lifecycle activity
            conn.execute(
                """
                INSERT INTO herd.agent_instance_lifecycle_activity
                  (agent_instance_code, lifecycle_event_type, lifecycle_detail, created_at)
                VALUES (?, 'spawned', ?, CURRENT_TIMESTAMP)
                """,
                [
                    instance_code,
                    f"Spawned by {agent_name or 'system'} with model {model_code}",
                ],
            )

            spawned_instances.append(instance_code)

        return {
            "agents": spawned_instances,
            "spawned": len(spawned_instances),
            "role": role,
            "agent_code": agent_code,
            "model": model_code,
            "spawned_by": agent_name,
            "spawned_by_instance": spawned_by_instance,
        }
