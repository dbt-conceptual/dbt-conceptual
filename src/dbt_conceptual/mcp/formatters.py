"""Output formatters for MCP context resolution.

Provides three output formats consuming the same resolved FullContext object:
- LLM: Natural language optimized for agent consumption
- JSON: Structured JSON for programmatic use
- Markdown: Standard markdown for human reading

All formatters clearly attribute authored vs inferred content.
"""

from __future__ import annotations

import json
from typing import Any

from .context import FullContext


def format_context(context: FullContext, format: str) -> str:
    """Format a FullContext object in the specified format.

    Args:
        context: The resolved FullContext to format
        format: Output format - 'llm', 'json', or 'markdown'

    Returns:
        Formatted string

    Raises:
        ValueError: If format is not supported
    """
    if format == "llm":
        return format_llm(context)
    elif format == "json":
        return format_json(context)
    elif format == "markdown":
        return format_markdown(context)
    else:
        raise ValueError(
            f"Unsupported format '{format}'. Must be 'llm', 'json', or 'markdown'."
        )


def format_llm(context: FullContext) -> str:
    """Format context as natural language optimized for LLM consumption.

    Design principles:
    - Prose sentences with explicit grain statements
    - Negative guidance (what NOT to do)
    - Contextual join implications
    - Clear source attribution ([authored] vs [inferred])
    - XML-like tags for multi-concept output
    - Prominent guidance rules

    Args:
        context: The resolved context to format

    Returns:
        Natural language text optimized for agent consumption
    """
    lines: list[str] = []

    # Multi-concept wrapper
    if len(context.concepts) > 1:
        lines.append(f'<concepts count="{len(context.concepts)}">')
        lines.append("")

    for concept in context.concepts:
        # Concept header with XML tag for multi-concept output
        if len(context.concepts) > 1:
            lines.append(f'<concept name="{concept.name}">')
            lines.append("")

        lines.append(f"# Concept: {concept.name}")
        lines.append("")

        # Status and ownership [authored]
        status_parts = [f"Status: {concept.status} [authored]"]
        if concept.domain:
            status_parts.append(f"Domain: {concept.domain} [authored]")
        if concept.owner:
            status_parts.append(f"Owner: {concept.owner} [authored]")
        lines.append(". ".join(status_parts) + ".")
        lines.append("")

        # Definition [authored]
        if concept.definition:
            lines.append("## Definition [authored]")
            lines.append("")
            lines.append(concept.definition.strip())
            lines.append("")

        # Guidance - prominently surfaced [authored]
        if concept.guidance_context or concept.guidance_rules:
            lines.append("## Business Guidance [authored]")
            lines.append("")

            if concept.guidance_context:
                lines.append(concept.guidance_context.strip())
                lines.append("")

            if concept.guidance_rules:
                lines.append("IMPORTANT RULES:")
                for rule in concept.guidance_rules:
                    lines.append(f"- **{rule['name']}**: {rule['description']}")
                lines.append("")

        # Relationships with grain warnings
        concept_relationships = [
            r
            for r in context.relationships
            if r.from_concept == concept.name or r.to_concept == concept.name
        ]

        if concept_relationships:
            lines.append("## Relationships [authored]")
            lines.append("")

            for rel in concept_relationships:
                # Build relationship sentence
                rel_sentence = f"This concept {rel.verb} {rel.to_concept if rel.from_concept == concept.name else rel.from_concept}"
                if rel.definition:
                    rel_sentence += f": {rel.definition}"
                rel_sentence += "."

                lines.append(rel_sentence)

                # Grain warning for 1:N relationships
                if rel.cardinality == "1:N":
                    if rel.from_concept == concept.name:
                        lines.append(
                            f"  WARNING: This is a 1:N relationship. DO NOT join to {rel.to_concept} without accounting for fan-out. Aggregation or DISTINCT may be required."
                        )
                    else:
                        lines.append(
                            f"  Note: This is a 1:N relationship from {rel.from_concept}'s perspective."
                        )

                lines.append("")

        # Model implementations
        # Note: We output all models in the context
        # (In a full implementation, we'd filter by concept-to-model mapping)
        if context.models:
            lines.append("## Model Implementations")
            lines.append("")

            for model_name, model in context.models.items():
                lines.append(f"### Model: {model_name} [authored]")
                lines.append("")

                # Basic metadata
                lines.append(
                    f"This model is materialized as a {model.materialization} in schema {model.schema or 'default'}."
                )
                if model.description:
                    lines.append(f"Description: {model.description}")
                lines.append("")

                # Grain [inferred]
                inference = context.inferences.get(model_name)
                if inference and inference.grain:
                    lines.append(f"**Grain [inferred]**: {inference.grain}")
                    if inference.grain_columns:
                        col_list = ", ".join(inference.grain_columns)
                        lines.append(f"  Grain columns: {col_list}")
                    lines.append("")

                # Risk warnings [inferred]
                if inference and inference.risk_message:
                    risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        inference.risk_level or "", "⚪"
                    )
                    lines.append(
                        f"**Risk Assessment [inferred]**: {risk_emoji} {inference.risk_message}"
                    )
                    lines.append("")

                # Quality warnings [inferred]
                if inference and inference.quality_warnings:
                    lines.append("**Quality Warnings [inferred]**:")
                    for warning in inference.quality_warnings:
                        lines.append(f"- {warning}")
                    lines.append("")

                # Materialization guidance [inferred]
                if inference and inference.materialization_guidance:
                    lines.append(
                        f"**Materialization Guidance [inferred]**: {inference.materialization_guidance}"
                    )
                    lines.append("")

                # Data Vault pattern [inferred]
                if inference and inference.data_vault_pattern:
                    lines.append(
                        f"**Data Vault Pattern [inferred]**: {inference.data_vault_pattern}"
                    )
                    lines.append("")

                # Layer [inferred]
                if inference and inference.layer:
                    lines.append(f"**Layer [inferred]**: {inference.layer}")
                    lines.append("")

                # Columns [authored]
                if model.columns:
                    lines.append("**Columns [authored]**:")
                    for col in model.columns:
                        col_parts = [f"- `{col.name}`"]
                        if col.type:
                            col_parts.append(f"({col.type})")
                        if col.description:
                            col_parts.append(f": {col.description}")
                        if col.constraints:
                            col_parts.append(
                                f" [Constraints: {', '.join(col.constraints)}]"
                            )
                        lines.append(" ".join(col_parts))
                    lines.append("")

                # Table-level constraints [authored]
                if model.constraints:
                    lines.append("**Table Constraints [authored]**:")
                    for constraint in model.constraints:
                        lines.append(f"- {constraint}")
                    lines.append("")

                # Dependencies [authored]
                if model.upstream:
                    upstream_names = [u.split(".")[-1] for u in model.upstream]
                    lines.append(
                        f"**Upstream Dependencies [authored]**: {', '.join(upstream_names)}"
                    )
                    lines.append("")

                if model.downstream:
                    lines.append(
                        f"**Downstream Consumers [authored]**: {', '.join(model.downstream)}"
                    )
                    lines.append(
                        "  Note: Changes to this model may impact these downstream models."
                    )
                    lines.append("")

                # Catalog stats [authored]
                if model.row_count is not None:
                    lines.append(f"**Row Count [authored]**: {model.row_count:,}")
                    lines.append("")

                # Contract info [authored]
                contract = context.contracts.get(model_name)
                if contract and contract.enforcement_mode:
                    lines.append(
                        f"**Contract Enforcement [authored]**: {contract.enforcement_mode}"
                    )
                    if contract.checks:
                        lines.append("  Checks:")
                        for check in contract.checks:
                            lines.append(f"  - {check}")
                    lines.append("")

        # Close concept tag
        if len(context.concepts) > 1:
            lines.append("</concept>")
            lines.append("")

    # Close concepts wrapper
    if len(context.concepts) > 1:
        lines.append("</concepts>")

    return "\n".join(lines)


def format_json(context: FullContext) -> str:
    """Format context as structured JSON.

    Args:
        context: The resolved context to format

    Returns:
        Pretty-printed JSON string
    """

    def _to_dict(obj: Any) -> Any:
        """Recursively convert dataclass to dict."""
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: _to_dict(v) for k, v in obj.items()}
        else:
            return obj

    data = _to_dict(context)
    return json.dumps(data, indent=2)


def format_markdown(context: FullContext) -> str:
    """Format context as standard markdown for human reading.

    Args:
        context: The resolved context to format

    Returns:
        Markdown-formatted string
    """
    lines: list[str] = []

    # Title
    if len(context.concepts) == 1:
        lines.append(f"# Concept: {context.concepts[0].name}")
    else:
        lines.append(f"# Concepts ({len(context.concepts)})")
    lines.append("")

    for concept in context.concepts:
        if len(context.concepts) > 1:
            lines.append(f"## {concept.name}")
            lines.append("")

        # Metadata table
        lines.append("| Property | Value |")
        lines.append("|----------|-------|")
        lines.append(f"| **Status** | {concept.status} |")
        if concept.domain:
            lines.append(f"| **Domain** | {concept.domain} |")
        if concept.owner:
            lines.append(f"| **Owner** | {concept.owner} |")
        if concept.color:
            lines.append(f"| **Color** | {concept.color} |")
        lines.append("")

        # Definition
        if concept.definition:
            lines.append("### Definition")
            lines.append("")
            lines.append(concept.definition.strip())
            lines.append("")

        # Guidance
        if concept.guidance_context or concept.guidance_rules:
            lines.append("### Business Guidance")
            lines.append("")

            if concept.guidance_context:
                lines.append(concept.guidance_context.strip())
                lines.append("")

            if concept.guidance_rules:
                lines.append("**Rules:**")
                lines.append("")
                for rule in concept.guidance_rules:
                    lines.append(f"- **{rule['name']}**: {rule['description']}")
                lines.append("")

        # Relationships
        concept_relationships = [
            r
            for r in context.relationships
            if r.from_concept == concept.name or r.to_concept == concept.name
        ]

        if concept_relationships:
            lines.append("### Relationships")
            lines.append("")
            lines.append("| Verb | To/From | Cardinality | Definition |")
            lines.append("|------|---------|-------------|------------|")

            for rel in concept_relationships:
                target = (
                    rel.to_concept
                    if rel.from_concept == concept.name
                    else rel.from_concept
                )
                direction = "to" if rel.from_concept == concept.name else "from"
                definition = rel.definition or ""
                lines.append(
                    f"| {rel.verb} | {direction} {target} | {rel.cardinality} | {definition} |"
                )

            lines.append("")

        # Models
        if context.models:
            lines.append("### Model Implementations")
            lines.append("")

            for model_name, model in context.models.items():
                lines.append(f"#### {model_name}")
                lines.append("")

                # Model metadata
                lines.append("| Property | Value |")
                lines.append("|----------|-------|")
                lines.append(f"| **Materialization** | {model.materialization} |")
                if model.schema:
                    lines.append(f"| **Schema** | {model.schema} |")
                if model.path:
                    lines.append(f"| **Path** | `{model.path}` |")
                if model.row_count is not None:
                    lines.append(f"| **Row Count** | {model.row_count:,} |")

                # Add inference info
                inference = context.inferences.get(model_name)
                if inference:
                    if inference.grain:
                        grain_cols = (
                            f" ({', '.join(inference.grain_columns)})"
                            if inference.grain_columns
                            else ""
                        )
                        lines.append(
                            f"| **Grain** *(inferred)* | {inference.grain}{grain_cols} |"
                        )
                    if inference.risk_level:
                        lines.append(
                            f"| **Risk** *(inferred)* | {inference.risk_level} |"
                        )
                    if inference.data_vault_pattern:
                        lines.append(
                            f"| **Data Vault** *(inferred)* | {inference.data_vault_pattern} |"
                        )
                    if inference.layer:
                        lines.append(f"| **Layer** *(inferred)* | {inference.layer} |")

                lines.append("")

                # Description
                if model.description:
                    lines.append(f"**Description:** {model.description}")
                    lines.append("")

                # Columns
                if model.columns:
                    lines.append("**Columns:**")
                    lines.append("")
                    lines.append("| Name | Type | Description | Constraints |")
                    lines.append("|------|------|-------------|-------------|")

                    for col in model.columns:
                        col_type = col.type or ""
                        col_desc = col.description or ""
                        col_constraints = (
                            ", ".join(col.constraints) if col.constraints else ""
                        )
                        lines.append(
                            f"| `{col.name}` | {col_type} | {col_desc} | {col_constraints} |"
                        )

                    lines.append("")

                # Table constraints
                if model.constraints:
                    lines.append("**Table Constraints:**")
                    lines.append("")
                    for constraint in model.constraints:
                        lines.append(f"- {constraint}")
                    lines.append("")

                # Dependencies
                if model.upstream:
                    upstream_names = [u.split(".")[-1] for u in model.upstream]
                    lines.append(f"**Upstream:** {', '.join(upstream_names)}")
                    lines.append("")

                if model.downstream:
                    lines.append(f"**Downstream:** {', '.join(model.downstream)}")
                    lines.append("")

                # Warnings
                if inference and inference.quality_warnings:
                    lines.append("**Quality Warnings:**")
                    lines.append("")
                    for warning in inference.quality_warnings:
                        lines.append(f"- {warning}")
                    lines.append("")

                # Contract
                contract = context.contracts.get(model_name)
                if contract and contract.enforcement_mode:
                    lines.append(f"**Contract:** {contract.enforcement_mode}")
                    lines.append("")

    return "\n".join(lines)
