"""Code review tool implementation."""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from typing import Any

from herd_mcp.db import connection


def _post_to_slack(message: str, channel: str = "#herd-feed") -> dict[str, Any]:
    """Post message to Slack using urllib (no external deps).

    Args:
        message: Message to post.
        channel: Slack channel (with # prefix).

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
            "username": "Herd Review Bot",
            "icon_emoji": ":mag:",
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


def _post_review_to_github(pr_number: int, review_body: str) -> bool:
    """Post review to GitHub PR via gh CLI.

    Args:
        pr_number: GitHub PR number.
        review_body: Review comment body.

    Returns:
        True if posted successfully, False otherwise.
    """
    try:
        # Post comment to PR using gh api
        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/dbt-conceptual/dbt-conceptual/issues/{pr_number}/comments",
                "-f",
                f"body={review_body}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _format_review_body(verdict: str, findings: list[dict], review_code: str) -> str:
    """Format review findings into markdown for GitHub.

    Args:
        verdict: Review verdict (pass, fail, pass_with_advisory).
        findings: List of finding dicts.
        review_code: Review code for tracking.

    Returns:
        Formatted markdown review body.
    """
    verdict_emoji = {
        "pass": "✅",
        "fail": "❌",
        "pass_with_advisory": "⚠️",
    }

    lines = [
        f"## Code Review: {verdict_emoji.get(verdict, '❓')} {verdict.replace('_', ' ').title()}",
        "",
        f"**Review ID:** `{review_code}`",
        "",
    ]

    if findings:
        # Group findings by severity
        blocking = [f for f in findings if f.get("severity") == "blocking"]
        advisory = [f for f in findings if f.get("severity") == "advisory"]

        if blocking:
            lines.append("### 🚫 Blocking Issues")
            lines.append("")
            for f in blocking:
                category = f.get("category", "general")
                desc = f.get("description", "No description")
                lines.append(f"- **{category}**: {desc}")
            lines.append("")

        if advisory:
            lines.append("### 💡 Advisory Notes")
            lines.append("")
            for f in advisory:
                category = f.get("category", "general")
                desc = f.get("description", "No description")
                lines.append(f"- **{category}**: {desc}")
            lines.append("")
    else:
        lines.append("No specific findings noted.")
        lines.append("")

    lines.append("---")
    lines.append("*Review submitted via Herd MCP*")

    return "\n".join(lines)


async def execute(
    pr_number: int,
    ticket_id: str,
    verdict: str,
    findings: list[dict],
    agent_name: str | None,
) -> dict:
    """Submit a code review for a PR.

    Args:
        pr_number: GitHub PR number.
        ticket_id: Associated Linear ticket ID.
        verdict: Review verdict (pass, fail, pass_with_advisory).
        findings: List of finding dicts with severity, category, description.
        agent_name: Current agent identity (reviewer).

    Returns:
        Dict with review_id, posted status, and findings_count.
    """
    # Validate verdict
    valid_verdicts = {"pass", "fail", "pass_with_advisory"}
    if verdict not in valid_verdicts:
        return {
            "review_id": None,
            "posted": False,
            "error": f"Invalid verdict: {verdict}. Must be one of {valid_verdicts}",
        }

    with connection() as conn:
        # Get current agent instance
        agent_instance_code = None
        if agent_name:
            result = conn.execute(
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

            if result:
                agent_instance_code = result[0]

        # Generate codes
        review_code = f"REV-{uuid.uuid4().hex[:8]}"
        pr_code = f"PR-{pr_number}"

        # Determine review round (how many reviews already exist for this PR)
        review_round_result = conn.execute(
            """
            SELECT COUNT(*) + 1
            FROM herd.review_def
            WHERE pr_code = ?
            """,
            [pr_code],
        ).fetchone()
        review_round = review_round_result[0] if review_round_result else 1

        # Insert review_def
        conn.execute(
            """
            INSERT INTO herd.review_def
              (review_code, pr_code, reviewer_agent_instance_code, review_round,
               review_verdict, review_duration_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, NULL, CURRENT_TIMESTAMP)
            """,
            [review_code, pr_code, agent_instance_code, review_round, verdict],
        )

        # Insert findings
        for finding in findings:
            finding_code = f"RF-{uuid.uuid4().hex[:8]}"
            conn.execute(
                """
                INSERT INTO herd.review_finding
                  (review_finding_code, review_code, finding_category, finding_severity,
                   finding_description, finding_file_path, finding_line_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [
                    finding_code,
                    review_code,
                    finding.get("category", "general"),
                    finding.get("severity", "advisory"),
                    finding.get("description", ""),
                    finding.get("file_path"),
                    finding.get("line_number"),
                ],
            )

        # Record review activity
        if agent_instance_code:
            verdict_summary = f"{verdict} with {len(findings)} findings"
            conn.execute(
                """
                INSERT INTO herd.agent_instance_review_activity
                  (agent_instance_code, review_code, pr_code, review_event_type,
                   review_activity_detail, created_at)
                VALUES (?, ?, ?, 'review_submitted', ?, CURRENT_TIMESTAMP)
                """,
                [agent_instance_code, review_code, pr_code, verdict_summary],
            )

        # Format and post review to GitHub
        review_body = _format_review_body(verdict, findings, review_code)
        github_posted = _post_review_to_github(pr_number, review_body)

        # Post summary to Slack
        verdict_emoji = {
            "pass": "✅",
            "fail": "❌",
            "pass_with_advisory": "⚠️",
        }
        emoji = verdict_emoji.get(verdict, "❓")
        slack_message = (
            f"{emoji} Review submitted for PR #{pr_number} (Ticket: {ticket_id})\n"
            f"Verdict: *{verdict.replace('_', ' ').title()}*\n"
            f"Findings: {len(findings)} ({sum(1 for f in findings if f.get('severity') == 'blocking')} blocking)\n"
            f"Review ID: `{review_code}`"
        )
        slack_result = _post_to_slack(slack_message)

        return {
            "review_id": review_code,
            "posted": github_posted and slack_result.get("success", False),
            "github_posted": github_posted,
            "slack_posted": slack_result.get("success", False),
            "findings_count": len(findings),
            "verdict": verdict,
            "review_round": review_round,
            "pr_number": pr_number,
            "ticket": ticket_id,
            "reviewer": agent_name,
        }
