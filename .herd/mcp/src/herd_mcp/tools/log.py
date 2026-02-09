"""Slack logging tool implementation."""

from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any

from herd_mcp.db import connection


def _classify_event_type(message: str) -> str:
    """Classify the lifecycle event type based on message content.

    Args:
        message: Message content to classify.

    Returns:
        Event type string (pr_submitted, review_complete, blocked, work_started,
        code_pushed, or status_update).
    """
    message_lower = message.lower()

    # Use word boundaries and more specific patterns
    if re.search(r'\bpr\b|pull request|pull-request', message_lower):
        return "pr_submitted"
    elif "review" in message_lower or "qa" in message_lower:
        return "review_complete"
    elif "blocked" in message_lower:
        return "blocked"
    elif "started" in message_lower or "beginning" in message_lower:
        return "work_started"
    elif "commit" in message_lower or "pushed" in message_lower:
        return "code_pushed"
    else:
        return "status_update"


def _post_to_slack(message: str, channel: str, agent_name: str) -> dict[str, Any]:
    """Post message to Slack using urllib (no external deps).

    Args:
        message: Message to post.
        channel: Slack channel (with # prefix).
        agent_name: Agent name for display.

    Returns:
        Dict with success status and response data.
    """
    token = os.getenv("HERD_SLACK_TOKEN")
    if not token:
        return {"success": False, "error": "HERD_SLACK_TOKEN not set"}

    try:
        import urllib.request

        data = json.dumps({
            "channel": channel,
            "text": message,
            "username": agent_name,
            "icon_emoji": ":hammer:",
        }).encode()

        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())

        return {"success": result.get("ok", False), "response": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def execute(
    message: str,
    channel: str | None,
    await_response: bool,
    agent_name: str | None,
) -> dict:
    """Post a message to Slack and log the activity.

    Args:
        message: Message content to post.
        channel: Optional Slack channel.
        await_response: If True, wait for thread responses.
        agent_name: Current agent identity.

    Returns:
        Dict with posted timestamp, event_id, and optional responses.
    """
    # Set defaults
    agent_name = agent_name or "Unknown Agent"
    channel = channel or "#herd-feed"

    # Classify event type
    event_type = _classify_event_type(message)

    # Generate event ID
    event_id = str(uuid.uuid4())

    # Resolve agent identity and get current instance
    agent_instance_code = None
    with connection() as conn:
        # Look up current agent instance
        result = conn.execute(
            """
            SELECT ai.agent_instance_code
            FROM herd.agent_instance ai
            WHERE ai.agent_code = ?
              AND ai.agent_instance_ended_at IS NULL
            ORDER BY ai.agent_instance_started_at DESC
            LIMIT 1
            """,
            [agent_name],
        ).fetchone()

        if result:
            agent_instance_code = result[0]

            # Record to lifecycle activity
            conn.execute(
                """
                INSERT INTO herd.agent_instance_lifecycle_activity
                  (agent_instance_code, lifecycle_event_type, lifecycle_detail, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [agent_instance_code, event_type, message],
            )

    # Post to Slack
    slack_result = _post_to_slack(message, channel, agent_name)
    posted = slack_result.get("success", False)

    return {
        "posted": posted,
        "event_id": event_id if posted else None,
        "responses": [],  # TODO: implement await_response if needed
        "agent": agent_name,
        "event_type": event_type,
        "slack_response": slack_result if not posted else None,
    }
