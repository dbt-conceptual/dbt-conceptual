"""Export format implementations for dbt-conceptual.

Provides JSON and markdown exporters for various report types.

v1.0: Simplified model - single models[] array, no realized_by.
"""

import json
from typing import Any, TextIO

from dbt_conceptual.exporter._stats import calculate_coverage_stats
from dbt_conceptual.state import ProjectState
from dbt_conceptual.validator import ValidationIssue, Validator

# Module-level alias so any callers using the old private name still work.
_calculate_coverage_stats = calculate_coverage_stats


# ============================================================================
# Coverage Exporters
# ============================================================================


def export_coverage_json(state: ProjectState, output: TextIO) -> None:
    """Export coverage report as JSON."""
    stats = calculate_coverage_stats(state)

    # Add concept details
    concepts_by_domain: dict[str, list[dict[str, Any]]] = {}
    for concept_id, concept in state.concepts.items():
        domain = concept.domain or "uncategorized"
        if domain not in concepts_by_domain:
            concepts_by_domain[domain] = []
        concepts_by_domain[domain].append(
            {
                "id": concept_id,
                "name": concept.name,
                "status": concept.status,
                "owner": concept.owner,
                "models": concept.models,
            }
        )

    data = {
        "summary": stats,
        "concepts_by_domain": concepts_by_domain,
        "domains": {
            domain_id: {
                "name": domain.name,
                "display_name": domain.display_name,
                "color": domain.color,
            }
            for domain_id, domain in state.domains.items()
        },
    }

    json.dump(data, output, indent=2)
    output.write("\n")


def export_coverage_markdown(state: ProjectState, output: TextIO) -> None:
    """Export coverage report as markdown."""
    stats = calculate_coverage_stats(state)

    output.write("### Coverage Summary\n\n")
    output.write("| Metric | Value |\n")
    output.write("|--------|-------|\n")
    output.write(
        f"| Concept Completion | {stats['concepts']['completion_percent']}% "
        f"({stats['concepts']['complete']}/{stats['concepts']['total']}) |\n"
    )
    output.write(
        f"| Model Coverage | {stats['coverage']['models']['percent']}% "
        f"({stats['coverage']['models']['count']} concepts) |\n"
    )
    output.write(
        f"| Relationships Complete | {stats['relationships']['percent']}% "
        f"({stats['relationships']['complete']}/{stats['relationships']['total']}) |\n"
    )
    if stats["orphans"] > 0:
        output.write(f"| Orphan Models | {stats['orphans']} |\n")
    output.write("\n")

    # Concepts by status
    if stats["concepts"]["stub"] > 0 or stats["concepts"]["draft"] > 0:
        output.write("#### Attention Needed\n\n")
        if stats["concepts"]["stub"] > 0:
            output.write(
                f"- \u26a0\ufe0f **{stats['concepts']['stub']} stub concepts** "
            )
            output.write("need definitions and domain assignment\n")
        if stats["concepts"]["draft"] > 0:
            output.write(
                f"- \U0001f4dd **{stats['concepts']['draft']} draft concepts** "
            )
            output.write("have no model implementations yet\n")
        output.write("\n")


# ============================================================================
# Bus Matrix Exporters
# ============================================================================


def export_bus_matrix_json(state: ProjectState, output: TextIO) -> None:
    """Export bus matrix as JSON.

    Note: v1.0 removed realized_by from relationships, so this returns
    minimal data. Bus matrix will be enhanced in future versions.
    """
    relationships_list = [
        {
            "id": rel_id,
            "name": rel.name,
            "from": rel.from_concept,
            "to": rel.to_concept,
            "verb": rel.verb,
            "cardinality": rel.cardinality,
        }
        for rel_id, rel in sorted(
            state.relationships.items(), key=lambda x: (x[1].from_concept, x[1].name)
        )
    ]

    data = {
        "relationships": relationships_list,
        "summary": {
            "total_relationships": len(relationships_list),
        },
        "note": "Bus matrix realization tracking coming in future version",
    }

    json.dump(data, output, indent=2)
    output.write("\n")


def export_bus_matrix_markdown(state: ProjectState, output: TextIO) -> None:
    """Export bus matrix as markdown table.

    Note: v1.0 removed realized_by, so this shows relationships without
    realization info.
    """
    relationships_list = sorted(
        state.relationships.items(), key=lambda x: (x[1].from_concept, x[1].name)
    )

    output.write("### Bus Matrix\n\n")

    if not relationships_list:
        output.write("*No relationships defined.*\n\n")
        return

    output.write("| Relationship | From | To | Cardinality |\n")
    output.write("|-------------|------|-----|-------------|\n")

    for _rel_id, rel in relationships_list:
        output.write(
            f"| {rel.verb} | {rel.from_concept} | {rel.to_concept} | {rel.cardinality} |\n"
        )

    output.write("\n")
    output.write(
        "*Note: Relationship realization tracking will be added in a future version.*\n\n"
    )


# ============================================================================
# Status Exporters
# ============================================================================


def export_status_json(state: ProjectState, output: TextIO) -> None:
    """Export status report as JSON."""
    stats = calculate_coverage_stats(state)

    concepts_data = []
    for concept_id, concept in sorted(state.concepts.items()):
        concepts_data.append(
            {
                "id": concept_id,
                "name": concept.name,
                "domain": concept.domain,
                "status": concept.status,
                "owner": concept.owner,
                "model_count": len(concept.models),
            }
        )

    relationships_data = []
    for rel_id, rel in sorted(state.relationships.items()):
        relationships_data.append(
            {
                "id": rel_id,
                "name": rel.name,
                "from": rel.from_concept,
                "to": rel.to_concept,
                "status": rel.get_status(state.concepts),
            }
        )

    data = {
        "summary": stats,
        "concepts": concepts_data,
        "relationships": relationships_data,
    }

    json.dump(data, output, indent=2)
    output.write("\n")


def export_status_markdown(state: ProjectState, output: TextIO) -> None:
    """Export status report as markdown."""
    stats = calculate_coverage_stats(state)

    output.write("### Status Summary\n\n")
    output.write(f"**Concepts:** {stats['concepts']['total']} total ")
    output.write(f"({stats['concepts']['complete']} complete, ")
    output.write(f"{stats['concepts']['draft']} draft, ")
    output.write(f"{stats['concepts']['stub']} stub)\n\n")

    output.write(f"**Relationships:** {stats['relationships']['total']} total ")
    output.write(f"({stats['relationships']['complete']} complete)\n\n")

    # Group by domain
    domain_groups: dict[str, list[tuple[str, Any]]] = {}
    for concept_id, concept in state.concepts.items():
        domain = concept.domain or "uncategorized"
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append((concept_id, concept))

    output.write("#### Concepts by Domain\n\n")
    for domain_id in sorted(domain_groups.keys()):
        concepts = domain_groups[domain_id]
        domain_name = domain_id
        if domain_id in state.domains:
            domain_name = (
                state.domains[domain_id].display_name or state.domains[domain_id].name
            )

        output.write(f"**{domain_name}** ({len(concepts)} concepts)\n\n")
        output.write("| Concept | Status | Models |\n")
        output.write("|---------|--------|--------|\n")

        for _cid, c in sorted(concepts, key=lambda x: x[1].name):
            status_icon = {
                "complete": "\u2705",
                "draft": "\U0001f4dd",
                "stub": "\u26a0\ufe0f",
            }.get(c.status, "\u2753")
            output.write(f"| {c.name} | {status_icon} {c.status} | {len(c.models)} |\n")
        output.write("\n")


# ============================================================================
# Orphans Exporters
# ============================================================================


def export_orphans_json(state: ProjectState, output: TextIO) -> None:
    """Export orphan models as JSON."""
    orphans_data = [
        {
            "name": orphan.name,
            "path": orphan.path,
            "description": orphan.description,
        }
        for orphan in sorted(state.orphan_models, key=lambda o: o.name)
    ]

    data = {
        "count": len(orphans_data),
        "models": orphans_data,
    }

    json.dump(data, output, indent=2)
    output.write("\n")


def export_orphans_markdown(state: ProjectState, output: TextIO) -> None:
    """Export orphan models as markdown."""
    orphans = sorted(state.orphan_models, key=lambda o: o.name)

    output.write("### Orphan Models\n\n")

    if not orphans:
        output.write("\u2705 **No orphan models found!**\n\n")
        output.write("All models have `meta.concept` tags.\n\n")
        return

    output.write(f"Found **{len(orphans)} models** without conceptual tags:\n\n")
    output.write("| Model | Path |\n")
    output.write("|-------|------|\n")

    for orphan in orphans:
        path = orphan.path or "-"
        output.write(f"| `{orphan.name}` | {path} |\n")

    output.write("\n")


# ============================================================================
# Validation Exporters
# ============================================================================


def export_validation_json(
    validator: Validator, issues: list[ValidationIssue], output: TextIO
) -> None:
    """Export validation results as JSON."""
    summary = validator.get_summary()

    issues_data = [
        {
            "code": issue.code,
            "severity": issue.severity.value,
            "message": issue.message,
            "context": issue.context,
        }
        for issue in issues
    ]

    data = {
        "passed": not validator.has_errors(),
        "summary": {
            "errors": summary["errors"],
            "warnings": summary["warnings"],
            "info": summary["info"],
        },
        "issues": issues_data,
    }

    json.dump(data, output, indent=2)
    output.write("\n")


def export_validation_markdown(
    validator: Validator, issues: list[ValidationIssue], output: TextIO
) -> None:
    """Export validation results as markdown."""
    from dbt_conceptual.validator import Severity

    summary = validator.get_summary()

    if validator.has_errors():
        output.write("### \u274c Validation Failed\n\n")
    else:
        output.write("### \u2705 Validation Passed\n\n")

    # Summary table
    output.write("| | Count |\n")
    output.write("|---|-----|\n")
    if summary["errors"]:
        output.write(f"| \U0001f534 Errors | {summary['errors']} |\n")
    if summary["warnings"]:
        output.write(f"| \U0001f7e1 Warnings | {summary['warnings']} |\n")
    if summary["info"]:
        output.write(f"| \u2139\ufe0f Info | {summary['info']} |\n")
    output.write("\n")

    # Group issues by severity
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]

    if errors:
        output.write("#### Errors\n\n")
        for issue in errors:
            output.write(f"- **{issue.code}** \u2014 {issue.message}\n")
        output.write("\n")

    if warnings:
        output.write("#### Warnings\n\n")
        for issue in warnings:
            output.write(f"- **{issue.code}** \u2014 {issue.message}\n")
        output.write("\n")
