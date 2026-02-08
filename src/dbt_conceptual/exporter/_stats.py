"""Shared coverage statistics calculation for exporters.

This module centralizes the coverage stats logic used by multiple
export formats (HTML, JSON, markdown).
"""

from typing import Any

from dbt_conceptual.state import ProjectState


def calculate_coverage_stats(state: ProjectState) -> dict[str, Any]:
    """Calculate coverage statistics from project state.

    Returns a nested dict with concept, coverage, relationship, and orphan stats.

    Args:
        state: Project state with concepts, relationships, and orphan models.

    Returns:
        Dict with keys: concepts, coverage, relationships, orphans.
    """
    total_concepts = len(state.concepts)
    complete_concepts = sum(
        1 for c in state.concepts.values() if c.status == "complete"
    )
    stub_concepts = sum(1 for c in state.concepts.values() if c.status == "stub")
    draft_concepts = sum(1 for c in state.concepts.values() if c.status == "draft")

    concepts_with_models = sum(1 for c in state.concepts.values() if c.models)

    total_relationships = len(state.relationships)
    complete_relationships = sum(
        1
        for r in state.relationships.values()
        if r.get_status(state.concepts) == "complete"
    )

    return {
        "concepts": {
            "total": total_concepts,
            "complete": complete_concepts,
            "draft": draft_concepts,
            "stub": stub_concepts,
            "completion_percent": (
                int((complete_concepts / total_concepts) * 100)
                if total_concepts > 0
                else 0
            ),
        },
        "coverage": {
            "models": {
                "count": concepts_with_models,
                "percent": (
                    int((concepts_with_models / total_concepts) * 100)
                    if total_concepts > 0
                    else 0
                ),
            },
        },
        "relationships": {
            "total": total_relationships,
            "complete": complete_relationships,
            "percent": (
                int((complete_relationships / total_relationships) * 100)
                if total_relationships > 0
                else 0
            ),
        },
        "orphans": len(state.orphan_models),
    }
