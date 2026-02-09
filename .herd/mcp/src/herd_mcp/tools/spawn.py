"""Agent spawning tool stub."""

from __future__ import annotations


async def execute(
    count: int,
    role: str,
    model: str | None,
    agent_name: str | None,
) -> dict:
    """Spawn new agent instances.

    Args:
        count: Number of agents to spawn.
        role: Agent role.
        model: Optional model override.
        agent_name: Current agent identity (spawner).

    Returns:
        Dict with list of spawned agent instance codes.
    """
    return {
        "status": "stub",
        "message": "herd_spawn not yet implemented",
        "count": count,
        "role": role,
        "model": model,
        "agents": [],
        "spawned_by": agent_name,
    }
