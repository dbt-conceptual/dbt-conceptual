"""Formatters for diff output."""

import json
from typing import Any

from .differ import ConceptualDiff


def format_human(diff: ConceptualDiff) -> str:
    """Format diff for human-readable terminal output.

    Args:
        diff: The conceptual diff to format

    Returns:
        Formatted string for terminal display
    """
    if not diff.has_changes:
        return "No conceptual changes detected."

    lines = ["Conceptual Changes", "=" * 50, ""]

    # Domain changes
    if diff.domain_changes:
        lines.append("Domains:")
        lines.append("-" * 50)
        for domain_change in diff.domain_changes:
            if domain_change.change_type == "added":
                lines.append(f"  + {domain_change.key} - {domain_change.new_value.display_name}")  # type: ignore
            elif domain_change.change_type == "removed":
                lines.append(f"  - {domain_change.key} - {domain_change.old_value.display_name}")  # type: ignore
            elif domain_change.change_type == "modified":
                lines.append(f"  ~ {domain_change.key}")
                for field, (old, new) in domain_change.modified_fields.items():
                    lines.append(f"      {field}: {old!r} → {new!r}")
        lines.append("")

    # Concept changes
    if diff.concept_changes:
        lines.append("Concepts:")
        lines.append("-" * 50)
        for concept_change in diff.concept_changes:
            if concept_change.change_type == "added":
                concept = concept_change.new_value
                domain_info = f" ({concept.domain})" if concept.domain else " (no domain)"  # type: ignore
                status_info = f" - {concept.status}"  # type: ignore
                lines.append(f"  + {concept_change.key}{domain_info}{status_info}")
            elif concept_change.change_type == "removed":
                concept = concept_change.old_value
                domain_info = f" ({concept.domain})" if concept.domain else " (no domain)"  # type: ignore
                lines.append(f"  - {concept_change.key}{domain_info}")
            elif concept_change.change_type == "modified":
                lines.append(f"  ~ {concept_change.key}")
                for field, (old, new) in concept_change.modified_fields.items():
                    if field == "definition":
                        # Truncate long definitions
                        old_preview = (
                            (old[:50] + "...") if old and len(old) > 50 else old
                        )
                        new_preview = (
                            (new[:50] + "...") if new and len(new) > 50 else new
                        )
                        lines.append(
                            f"      {field}: {old_preview!r} → {new_preview!r}"
                        )
                    else:
                        lines.append(f"      {field}: {old!r} → {new!r}")
        lines.append("")

    # Relationship changes
    if diff.relationship_changes:
        lines.append("Relationships:")
        lines.append("-" * 50)
        for rel_change in diff.relationship_changes:
            if rel_change.change_type == "added":
                rel = rel_change.new_value
                cardinality_info = f" ({rel.cardinality})" if rel.cardinality else ""  # type: ignore
                lines.append(f"  + {rel_change.key}{cardinality_info}")
            elif rel_change.change_type == "removed":
                rel = rel_change.old_value
                cardinality_info = f" ({rel.cardinality})" if rel.cardinality else ""  # type: ignore
                lines.append(f"  - {rel_change.key}{cardinality_info}")
            elif rel_change.change_type == "modified":
                lines.append(f"  ~ {rel_change.key}")
                for field, (old, new) in rel_change.modified_fields.items():
                    if field == "definition":
                        # Truncate long definitions
                        old_preview = (
                            (old[:50] + "...") if old and len(old) > 50 else old
                        )
                        new_preview = (
                            (new[:50] + "...") if new and len(new) > 50 else new
                        )
                        lines.append(
                            f"      {field}: {old_preview!r} → {new_preview!r}"
                        )
                    else:
                        lines.append(f"      {field}: {old!r} → {new!r}")
        lines.append("")

    return "\n".join(lines)


def format_github(diff: ConceptualDiff) -> str:
    """Format diff for GitHub Actions annotations.

    Args:
        diff: The conceptual diff to format

    Returns:
        Formatted string with GitHub Actions annotations
    """
    if not diff.has_changes:
        print("::notice title=Conceptual Model::No changes detected")
        return ""

    lines = []

    # Domain changes
    for domain_change in diff.domain_changes:
        if domain_change.change_type == "added":
            lines.append(
                f"::notice title=New Domain::{domain_change.key} - {domain_change.new_value.display_name}"  # type: ignore
            )
        elif domain_change.change_type == "removed":
            lines.append(
                f"::warning title=Removed Domain::{domain_change.key} - {domain_change.old_value.display_name}"  # type: ignore
            )
        elif domain_change.change_type == "modified":
            modified_fields_str = ", ".join(domain_change.modified_fields.keys())
            lines.append(
                f"::notice title=Modified Domain::{domain_change.key} ({modified_fields_str})"
            )

    # Concept changes
    for concept_change in diff.concept_changes:
        if concept_change.change_type == "added":
            concept = concept_change.new_value
            domain_info = f" ({concept.domain})" if concept.domain else " (no domain)"  # type: ignore
            if concept.status in ("stub", "draft"):  # type: ignore
                lines.append(
                    f"::warning title=New Concept::{concept_change.key}{domain_info} - {concept.status}"  # type: ignore
                )
            else:
                lines.append(
                    f"::notice title=New Concept::{concept_change.key}{domain_info}"
                )
        elif concept_change.change_type == "removed":
            concept = concept_change.old_value
            domain_info = f" ({concept.domain})" if concept.domain else ""  # type: ignore
            lines.append(
                f"::warning title=Removed Concept::{concept_change.key}{domain_info}"
            )
        elif concept_change.change_type == "modified":
            modified_fields_str = ", ".join(concept_change.modified_fields.keys())
            lines.append(
                f"::notice title=Modified Concept::{concept_change.key} ({modified_fields_str})"
            )

    # Relationship changes (v1.0: relationships don't have a status property)
    for rel_change in diff.relationship_changes:
        if rel_change.change_type == "added":
            rel = rel_change.new_value
            cardinality_info = f" ({rel.cardinality})" if rel.cardinality else ""  # type: ignore
            lines.append(
                f"::notice title=New Relationship::{rel_change.key}{cardinality_info}"
            )
        elif rel_change.change_type == "removed":
            rel = rel_change.old_value
            cardinality_info = f" ({rel.cardinality})" if rel.cardinality else ""  # type: ignore
            lines.append(
                f"::warning title=Removed Relationship::{rel_change.key}{cardinality_info}"
            )
        elif rel_change.change_type == "modified":
            modified_fields_str = ", ".join(rel_change.modified_fields.keys())
            lines.append(
                f"::notice title=Modified Relationship::{rel_change.key} ({modified_fields_str})"
            )

    return "\n".join(lines)


def format_json(diff: ConceptualDiff) -> str:
    """Format diff as JSON.

    Args:
        diff: The conceptual diff to format

    Returns:
        JSON string representation of the diff
    """

    def _serialize_change(change: Any) -> dict[str, Any]:
        """Serialize a change object to dict."""
        result: dict[str, Any] = {
            "key": change.key,
            "change_type": change.change_type,
        }

        if change.old_value:
            result["old_value"] = {
                k: v
                for k, v in change.old_value.__dict__.items()
                if not k.startswith("_") and not callable(v)
            }

        if change.new_value:
            result["new_value"] = {
                k: v
                for k, v in change.new_value.__dict__.items()
                if not k.startswith("_") and not callable(v)
            }

        if change.modified_fields:
            result["modified_fields"] = {
                field: {"old": old, "new": new}
                for field, (old, new) in change.modified_fields.items()
            }

        return result

    output = {
        "has_changes": diff.has_changes,
        "domain_changes": [_serialize_change(c) for c in diff.domain_changes],
        "concept_changes": [_serialize_change(c) for c in diff.concept_changes],
        "relationship_changes": [
            _serialize_change(c) for c in diff.relationship_changes
        ],
    }

    return json.dumps(output, indent=2)


def format_markdown(diff: ConceptualDiff) -> str:
    """Format diff as GitHub-flavored markdown for job summaries.

    Args:
        diff: The conceptual diff to format

    Returns:
        Formatted markdown string
    """
    if not diff.has_changes:
        return "## ✅ No Conceptual Changes\n\nThe conceptual model is unchanged."

    lines = ["## 📊 Conceptual Model Changes\n"]

    # Summary table
    added = sum(
        1
        for c in (
            diff.domain_changes + diff.concept_changes + diff.relationship_changes
        )
        if c.change_type == "added"
    )
    modified = sum(
        1
        for c in (
            diff.domain_changes + diff.concept_changes + diff.relationship_changes
        )
        if c.change_type == "modified"
    )
    removed = sum(
        1
        for c in (
            diff.domain_changes + diff.concept_changes + diff.relationship_changes
        )
        if c.change_type == "removed"
    )

    lines.append("| | Count |")
    lines.append("|---|-----|")
    if added:
        lines.append(f"| ➕ Added | {added} |")
    if modified:
        lines.append(f"| ✏️ Modified | {modified} |")
    if removed:
        lines.append(f"| ➖ Removed | {removed} |")
    lines.append("")

    # Domain changes
    if diff.domain_changes:
        lines.append("### Domains\n")
        lines.append("| Change | Name | Detail |")
        lines.append("|--------|------|--------|")
        for domain_change in diff.domain_changes:
            if domain_change.change_type == "added":
                name = domain_change.key
                display = domain_change.new_value.display_name  # type: ignore
                lines.append(f"| ➕ | `{name}` | {display} |")
            elif domain_change.change_type == "removed":
                name = domain_change.key
                display = domain_change.old_value.display_name  # type: ignore
                lines.append(f"| ➖ | `{name}` | {display} |")
            elif domain_change.change_type == "modified":
                name = domain_change.key
                fields = ", ".join(domain_change.modified_fields.keys())
                lines.append(f"| ✏️ | `{name}` | modified: {fields} |")
        lines.append("")

    # Concept changes
    if diff.concept_changes:
        lines.append("### Concepts\n")
        lines.append("| Change | Name | Detail |")
        lines.append("|--------|------|--------|")
        for concept_change in diff.concept_changes:
            if concept_change.change_type == "added":
                concept = concept_change.new_value
                domain_info = f"domain: {concept.domain}" if concept.domain else "no domain"  # type: ignore
                status_info = f"status: {concept.status}"  # type: ignore
                lines.append(
                    f"| ➕ | `{concept_change.key}` | {domain_info}, {status_info} |"
                )
            elif concept_change.change_type == "removed":
                concept = concept_change.old_value
                domain_info = f"domain: {concept.domain}" if concept.domain else "no domain"  # type: ignore
                lines.append(f"| ➖ | `{concept_change.key}` | {domain_info} |")
            elif concept_change.change_type == "modified":
                fields = ", ".join(concept_change.modified_fields.keys())
                lines.append(f"| ✏️ | `{concept_change.key}` | modified: {fields} |")
        lines.append("")

    # Relationship changes (v1.0: relationships don't have a status property)
    if diff.relationship_changes:
        lines.append("### Relationships\n")
        lines.append("| Change | Name | Detail |")
        lines.append("|--------|------|--------|")
        for rel_change in diff.relationship_changes:
            if rel_change.change_type == "added":
                rel = rel_change.new_value
                cardinality_info = f"cardinality: {rel.cardinality}" if rel.cardinality else ""  # type: ignore
                lines.append(f"| ➕ | `{rel_change.key}` | {cardinality_info} |")
            elif rel_change.change_type == "removed":
                rel = rel_change.old_value
                cardinality_info = f"cardinality: {rel.cardinality}" if rel.cardinality else ""  # type: ignore
                lines.append(f"| ➖ | `{rel_change.key}` | {cardinality_info} |")
            elif rel_change.change_type == "modified":
                fields = ", ".join(rel_change.modified_fields.keys())
                lines.append(f"| ✏️ | `{rel_change.key}` | modified: {fields} |")
        lines.append("")

    return "\n".join(lines)
