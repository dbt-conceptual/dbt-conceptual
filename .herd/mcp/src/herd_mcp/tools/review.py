"""Code review tool stub."""

from __future__ import annotations


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
        verdict: Review verdict.
        findings: List of finding dicts.
        agent_name: Current agent identity (reviewer).

    Returns:
        Dict with review_id and posted status.
    """
    return {
        "status": "stub",
        "message": "herd_review not yet implemented",
        "review_id": None,
        "pr_number": pr_number,
        "ticket": ticket_id,
        "verdict": verdict,
        "findings_count": len(findings),
        "posted": False,
        "reviewer": agent_name,
    }
