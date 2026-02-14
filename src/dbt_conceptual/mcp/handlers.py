"""MCP tool handler implementations for dbt-conceptual.

Handlers connect MCP tool calls to the resolution engine and formatters.
Each handler parses input, resolves concepts/relationships, formats output,
and handles errors gracefully (returns error strings instead of raising).
"""

from __future__ import annotations

import json
from typing import Any

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.selector import SelectorError, select_concepts
from dbt_conceptual.state import ProjectState
from dbt_conceptual.validator import Severity, Validator


def handle_get_context(
    selector: str,
    format: str,
    depth: int,
    project_state: ProjectState,
    config: Config,
) -> str:
    """Get full context for concepts matching a selector.

    Args:
        selector: Concept selector (name, pattern, or 'all')
        format: Output format - 'llm' (human-readable), 'json', or 'yaml'
        depth: Relationship traversal depth (1-3)
        project_state: Project state to query
        config: Configuration object

    Returns:
        Formatted context string containing concept information
    """
    try:
        # Validate format
        if format not in ("llm", "json", "yaml"):
            return f"Error: Invalid format '{format}'. Must be one of: llm, json, yaml"

        # Validate depth
        if depth < 1 or depth > 3:
            return "Error: Depth must be between 1 and 3"

        # Resolve selector to concept names
        try:
            concept_names = select_concepts(project_state, selector)
        except SelectorError as e:
            return f"Error: {e}"

        if not concept_names:
            return f"No concepts found matching selector: {selector}"

        # Build context for each concept
        context_data: list[dict[str, Any]] = []
        for concept_name in sorted(concept_names):
            concept = project_state.concepts.get(concept_name)
            if not concept:
                continue

            concept_context = {
                "name": concept.name,
                "domain": concept.domain,
                "owner": concept.owner,
                "status": concept.status,
                "definition": concept.definition,
                "models": concept.models,
                "is_ghost": concept.is_ghost,
            }

            # Add guidance if present
            if concept.guidance:
                guidance_data = {
                    "context": concept.guidance.context,
                    "rules": [
                        {"name": rule.name, "description": rule.description}
                        for rule in concept.guidance.rules
                    ],
                }
                concept_context["guidance"] = guidance_data

            # Add relationships up to depth
            relationships = _get_relationships_for_concept(
                concept_name, depth, project_state
            )
            concept_context["relationships"] = relationships

            context_data.append(concept_context)

        # Format output
        if format == "json":
            return json.dumps(context_data, indent=2)
        elif format == "yaml":
            return yaml.dump(context_data, default_flow_style=False, sort_keys=False)
        else:  # llm format
            return _format_context_llm(context_data)

    except Exception as e:
        return f"Error: {e}"


def handle_list_concepts(
    domain: str | None,
    status: str | None,
    project_state: ProjectState,
) -> str:
    """List all concepts, optionally filtered by domain or status.

    Args:
        domain: Optional domain filter (e.g., 'sales', 'finance')
        status: Optional status filter (e.g., 'stub', 'draft', 'complete')
        project_state: Project state to query

    Returns:
        Formatted list of concepts with basic metadata
    """
    try:
        # Validate status if provided
        if status and status not in ("stub", "draft", "complete"):
            return f"Error: Invalid status '{status}'. Must be one of: stub, draft, complete"

        # Filter concepts
        filtered_concepts = []
        for concept_name, concept in project_state.concepts.items():
            # Skip ghosts in listing
            if concept.is_ghost:
                continue

            # Apply filters
            if domain and concept.domain != domain:
                continue
            if status and concept.status != status:
                continue

            filtered_concepts.append(concept)

        # Sort by name
        filtered_concepts.sort(key=lambda c: c.name)

        # Build filter description
        filters = []
        if domain:
            filters.append(f"domain={domain}")
        if status:
            filters.append(f"status={status}")
        filter_str = f" ({', '.join(filters)})" if filters else ""

        # Format output
        if not filtered_concepts:
            return f"No concepts found{filter_str}"

        lines = [f"Found {len(filtered_concepts)} concept(s){filter_str}:\n"]
        for concept in filtered_concepts:
            model_count = len(concept.models)
            models_str = f"{model_count} model(s)" if model_count > 0 else "no models"
            domain_str = concept.domain if concept.domain else "no domain"
            lines.append(
                f"  - {concept.name} [{concept.status}] ({domain_str}, {models_str})"
            )

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


def handle_get_relationships(
    concept: str,
    depth: int,
    project_state: ProjectState,
) -> str:
    """Get relationships for a concept with grain warnings.

    Args:
        concept: Concept name
        depth: Relationship traversal depth (1-3)
        project_state: Project state to query

    Returns:
        Formatted relationship information with grain warnings
    """
    try:
        # Validate depth
        if depth < 1 or depth > 3:
            return "Error: Depth must be between 1 and 3"

        # Check if concept exists
        if concept not in project_state.concepts:
            return f"Error: Unknown concept '{concept}'"

        # Get relationships
        relationships = _get_relationships_for_concept(concept, depth, project_state)

        if not relationships:
            return f"Concept '{concept}' has no relationships"

        # Format output
        lines = [f"Relationships for {concept}:\n"]

        # Group by direction
        outgoing = [r for r in relationships if r["from_concept"] == concept]
        incoming = [r for r in relationships if r["to_concept"] == concept]
        other = [
            r
            for r in relationships
            if r["from_concept"] != concept and r["to_concept"] != concept
        ]

        if outgoing:
            lines.append("Outgoing:")
            for rel in outgoing:
                grain_warning = (
                    " [GRAIN WARNING: 1:N join may fan out results]"
                    if rel["cardinality"] == "1:N"
                    else ""
                )
                lines.append(
                    f"  - {rel['verb']} → {rel['to_concept']} ({rel['cardinality']}){grain_warning}"
                )
            lines.append("")

        if incoming:
            lines.append("Incoming:")
            for rel in incoming:
                lines.append(
                    f"  - {rel['from_concept']} → {rel['verb']} ({rel['cardinality']})"
                )
            lines.append("")

        if other:
            lines.append(f"Indirect (depth {depth}):")
            for rel in other:
                lines.append(
                    f"  - {rel['from_concept']} → {rel['verb']} → {rel['to_concept']} ({rel['cardinality']})"
                )

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


def handle_validate(
    project_state: ProjectState,
    config: Config,
) -> str:
    """Run validation on the conceptual model.

    Args:
        project_state: Project state to validate
        config: Configuration object with validation settings

    Returns:
        Validation report with any errors or warnings
    """
    try:
        # Run validator
        validator = Validator(config, project_state, no_drafts=False)
        issues = validator.validate()

        # Get summary
        summary = validator.get_summary()

        # Build report
        lines = ["Validation Results:\n"]

        # Summary
        if summary["errors"] == 0 and summary["warnings"] == 0:
            lines.append("✓ No errors or warnings found")
            if summary["info"] > 0:
                lines.append(f"  ({summary['info']} info message(s))")
            return "\n".join(lines)

        lines.append(f"Errors: {summary['errors']}")
        lines.append(f"Warnings: {summary['warnings']}")
        lines.append(f"Info: {summary['info']}")
        lines.append("")

        # Group issues by severity
        errors = [i for i in issues if i.severity == Severity.ERROR]
        warnings = [i for i in issues if i.severity == Severity.WARNING]
        info = [i for i in issues if i.severity == Severity.INFO]

        # Show errors
        if errors:
            lines.append("ERRORS:")
            for issue in errors:
                lines.append(f"  [{issue.code}] {issue.message}")
                if issue.context:
                    context_str = ", ".join(
                        f"{k}={v}" for k, v in issue.context.items()
                    )
                    lines.append(f"    Context: {context_str}")
            lines.append("")

        # Show warnings
        if warnings:
            lines.append("WARNINGS:")
            for issue in warnings:
                lines.append(f"  [{issue.code}] {issue.message}")
                if issue.context:
                    context_str = ", ".join(
                        f"{k}={v}" for k, v in issue.context.items()
                    )
                    lines.append(f"    Context: {context_str}")
            lines.append("")

        # Optionally show info (limit to first 5)
        if info and len(info) <= 5:
            lines.append("INFO:")
            for issue in info:
                lines.append(f"  [{issue.code}] {issue.message}")
            lines.append("")

        # Add actionable guidance
        if validator.has_errors():
            lines.append("Next Steps:")
            lines.append(
                "  - Fix all errors before proceeding (errors indicate broken references)"
            )
            if any(i.code == "E002" for i in errors):
                lines.append(
                    "  - E002 errors: Add missing concept definitions to conceptual.yml"
                )
            if any(i.code == "E003" for i in errors):
                lines.append(
                    "  - E003 errors: Rename duplicate guidance rules to be unique"
                )

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


# Helper functions


def _get_relationships_for_concept(
    concept_name: str, depth: int, project_state: ProjectState
) -> list[dict[str, Any]]:
    """Get all relationships for a concept up to a given depth.

    Args:
        concept_name: Starting concept name
        depth: Maximum depth to traverse
        project_state: Project state to query

    Returns:
        List of relationship dictionaries with from/to/verb/cardinality
    """
    visited_concepts: set[str] = set()
    visited_rels: set[str] = set()
    relationships: list[dict[str, Any]] = []

    def traverse(current_concept: str, current_depth: int) -> None:
        if current_depth > depth or current_concept in visited_concepts:
            return

        visited_concepts.add(current_concept)

        # Find all relationships involving this concept
        for rel_id, rel in project_state.relationships.items():
            if rel_id in visited_rels:
                continue

            if rel.from_concept == current_concept or rel.to_concept == current_concept:
                visited_rels.add(rel_id)
                relationships.append(
                    {
                        "from_concept": rel.from_concept,
                        "verb": rel.verb,
                        "to_concept": rel.to_concept,
                        "cardinality": rel.cardinality,
                        "definition": rel.definition,
                    }
                )

                # Traverse to connected concepts
                if rel.from_concept == current_concept:
                    traverse(rel.to_concept, current_depth + 1)
                else:
                    traverse(rel.from_concept, current_depth + 1)

    traverse(concept_name, 0)
    return relationships


def _format_context_llm(context_data: list[dict[str, Any]]) -> str:
    """Format context data for LLM consumption (human-readable).

    Args:
        context_data: List of concept context dictionaries

    Returns:
        Human-readable formatted string
    """
    lines = []

    for concept in context_data:
        lines.append(f"# Concept: {concept['name']}\n")

        if concept.get("is_ghost"):
            lines.append("**Status:** GHOST (referenced but not defined)\n")
        else:
            lines.append(f"**Status:** {concept['status']}")
            if concept.get("domain"):
                lines.append(f"**Domain:** {concept['domain']}")
            if concept.get("owner"):
                lines.append(f"**Owner:** {concept['owner']}")
            lines.append("")

        # Definition
        if concept.get("definition"):
            lines.append(f"**Definition:**\n{concept['definition']}\n")

        # Models
        if concept.get("models"):
            lines.append(f"**Models:** {', '.join(concept['models'])}\n")

        # Guidance
        if concept.get("guidance"):
            guidance = concept["guidance"]
            lines.append("**Guidance:**")
            if guidance.get("context"):
                lines.append(f"  Context: {guidance['context']}")
            if guidance.get("rules"):
                lines.append("  Rules:")
                for rule in guidance["rules"]:
                    lines.append(f"    - {rule['name']}: {rule['description']}")
            lines.append("")

        # Relationships
        if concept.get("relationships"):
            lines.append("**Relationships:**")
            rels = concept["relationships"]

            # Group by direction
            outgoing = [r for r in rels if r["from_concept"] == concept["name"]]
            incoming = [r for r in rels if r["to_concept"] == concept["name"]]
            other = [
                r
                for r in rels
                if r["from_concept"] != concept["name"]
                and r["to_concept"] != concept["name"]
            ]

            if outgoing:
                lines.append("  Outgoing:")
                for rel in outgoing:
                    grain_warning = (
                        " [GRAIN WARNING: 1:N join may fan out results]"
                        if rel["cardinality"] == "1:N"
                        else ""
                    )
                    lines.append(
                        f"    - {rel['verb']} → {rel['to_concept']} ({rel['cardinality']}){grain_warning}"
                    )

            if incoming:
                lines.append("  Incoming:")
                for rel in incoming:
                    lines.append(
                        f"    - {rel['from_concept']} → {rel['verb']} ({rel['cardinality']})"
                    )

            if other:
                lines.append("  Indirect:")
                for rel in other:
                    lines.append(
                        f"    - {rel['from_concept']} → {rel['verb']} → {rel['to_concept']} ({rel['cardinality']})"
                    )

            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)
