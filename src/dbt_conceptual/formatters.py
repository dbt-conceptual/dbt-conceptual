"""Output formatters for MCP context responses.

Provides three output formats consuming the same resolved FullContext object:
- LLM: Natural language optimized for agent consumption
- JSON: Structured JSON for programmatic use
- Markdown: Standard markdown for human reading

All formatters clearly attribute authored vs inferred content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from dbt_conceptual.inference import Inference
from dbt_conceptual.state import ConceptState


@dataclass
class ModelContext:
    """Context for a single dbt model implementation."""

    name: str
    materialization: str | None = None
    schema: str | None = None
    description: str | None = None
    columns: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)  # Translated from tests
    upstream_models: list[str] = field(default_factory=list)
    downstream_models: list[str] = field(default_factory=list)
    path: str | None = None


@dataclass
class RelationshipContext:
    """Context for a relationship between concepts."""

    verb: str
    from_concept: str
    to_concept: str
    cardinality: str
    definition: str | None = None
    is_inferred: bool = False  # True if inferred from lineage


@dataclass
class FullContext:
    """Complete resolved context for one or more concepts.

    Contains all information needed to generate any output format.
    Clearly distinguishes authored content (from YAML) vs inferred content.
    """

    # Core concept info (from conceptual.yml)
    concepts: list[ConceptState] = field(default_factory=list)

    # Relationships (from conceptual.yml or inferred from lineage)
    relationships: list[RelationshipContext] = field(default_factory=list)

    # Model implementations (from dbt manifest)
    models: list[ModelContext] = field(default_factory=list)

    # Inferences (from inference engine)
    inferences: list[Inference] = field(default_factory=list)

    # Optional contract info (from dbt contracts)
    contracts: dict[str, Any] = field(default_factory=dict)

    # Optional catalog info (from dbt catalog)
    catalog: dict[str, Any] = field(default_factory=dict)


def format_llm(context: FullContext) -> str:
    """Format context as natural language optimized for LLM consumption.

    Design principles:
    - Prose sentences with explicit grain statements
    - Negative guidance (what NOT to do)
    - Contextual join implications
    - Clear source attribution (authored vs inferred)
    - XML-like tags for multi-concept output

    Args:
        context: The resolved context to format

    Returns:
        Natural language text optimized for agent consumption
    """
    output_lines: list[str] = []

    # Multi-concept wrapper
    if len(context.concepts) > 1:
        output_lines.append(f'<concepts count="{len(context.concepts)}">')
        output_lines.append("")

    for concept in context.concepts:
        output_lines.append(f"# Concept: {concept.name}")
        output_lines.append("")

        # Status and ownership
        status_desc = {
            "stub": "STUB (needs enrichment)",
            "draft": "DRAFT (needs implementation)",
            "complete": "COMPLETE (has models)",
        }.get(concept.status, concept.status)

        output_lines.append(f"**Status:** {status_desc}")

        if concept.domain:
            output_lines.append(f"**Domain:** {concept.domain}")
        else:
            output_lines.append("**Domain:** Not assigned (needs domain assignment)")

        if concept.owner:
            output_lines.append(f"**Owner:** {concept.owner}")

        output_lines.append("")

        # Definition (authored content)
        if concept.definition:
            output_lines.append("## Definition (Authored)")
            output_lines.append("")
            output_lines.append(concept.definition)
            output_lines.append("")
        else:
            output_lines.append("## Definition")
            output_lines.append("")
            output_lines.append(
                "*No definition provided. This concept needs documentation.*"
            )
            output_lines.append("")

        # Guidance (authored content)
        if concept.guidance:
            output_lines.append("## Implementation Guidance (Authored)")
            output_lines.append("")

            if concept.guidance.context:
                output_lines.append("**Business Context:**")
                output_lines.append("")
                output_lines.append(concept.guidance.context)
                output_lines.append("")

            if concept.guidance.rules:
                output_lines.append("**Rules:**")
                output_lines.append("")
                for rule in concept.guidance.rules:
                    output_lines.append(f"- **{rule.name}:** {rule.description}")
                output_lines.append("")

        # Relationships
        concept_rels = [
            r
            for r in context.relationships
            if r.from_concept == concept.name or r.to_concept == concept.name
        ]

        if concept_rels:
            output_lines.append("## Relationships")
            output_lines.append("")

            # Outbound relationships
            outbound = [r for r in concept_rels if r.from_concept == concept.name]
            if outbound:
                output_lines.append("**Outbound (from this concept):**")
                output_lines.append("")
                for rel in outbound:
                    source_tag = " (INFERRED)" if rel.is_inferred else " (AUTHORED)"
                    cardinality_note = (
                        " — Joining may fan out results (1:N relationship)"
                        if rel.cardinality == "1:N"
                        else " — One-to-one relationship (1:1)"
                    )
                    output_lines.append(
                        f"- {rel.verb} → **{rel.to_concept}** "
                        f"[{rel.cardinality}]{source_tag}{cardinality_note}"
                    )
                    if rel.definition:
                        output_lines.append(f"  *{rel.definition}*")
                output_lines.append("")

            # Inbound relationships
            inbound = [r for r in concept_rels if r.to_concept == concept.name]
            if inbound:
                output_lines.append("**Inbound (to this concept):**")
                output_lines.append("")
                for rel in inbound:
                    source_tag = " (INFERRED)" if rel.is_inferred else " (AUTHORED)"
                    output_lines.append(
                        f"- {rel.from_concept} → **{rel.verb}** [{rel.cardinality}]{source_tag}"
                    )
                    if rel.definition:
                        output_lines.append(f"  *{rel.definition}*")
                output_lines.append("")

        # Model implementations
        concept_models = [m for m in context.models if m.name in concept.models]

        if concept_models:
            output_lines.append("## Model Implementations")
            output_lines.append("")

            for model in concept_models:
                output_lines.append(f"### Model: {model.name}")
                output_lines.append("")

                if model.materialization:
                    output_lines.append(f"**Materialization:** {model.materialization}")

                if model.schema:
                    output_lines.append(f"**Schema:** {model.schema}")

                if model.path:
                    output_lines.append(f"**Path:** {model.path}")

                output_lines.append("")

                # Grain statement (explicit)
                grain_inferences = [
                    i
                    for i in context.inferences
                    if i.metadata
                    and i.metadata.get("model_name") == model.name
                    and i.type.value == "grain"
                ]
                if grain_inferences:
                    grain_inf = grain_inferences[0]
                    output_lines.append(f"**Grain (INFERRED):** {grain_inf.message}")
                    if grain_inf.metadata and "grain_columns" in grain_inf.metadata:
                        cols = grain_inf.metadata["grain_columns"]
                        output_lines.append(
                            f"  *Based on unique test on columns: {', '.join(cols)}*"
                        )
                    output_lines.append("")
                else:
                    output_lines.append(
                        "**Grain:** Not explicitly defined (no unique tests found)"
                    )
                    output_lines.append("")

                # Description
                if model.description:
                    output_lines.append("**Description:**")
                    output_lines.append("")
                    output_lines.append(model.description)
                    output_lines.append("")

                # Constraints (from dbt tests)
                if model.constraints:
                    output_lines.append("**Constraints (from dbt tests):**")
                    output_lines.append("")
                    for constraint in model.constraints:
                        output_lines.append(f"- {constraint}")
                    output_lines.append("")

                # Columns
                if model.columns:
                    output_lines.append("**Columns:**")
                    output_lines.append("")
                    for col in model.columns:
                        col_name = col.get("name", "unknown")
                        col_type = col.get("type", "unknown")
                        col_desc = col.get("description", "")
                        output_lines.append(f"- `{col_name}` ({col_type})")
                        if col_desc:
                            output_lines.append(f"  {col_desc}")
                    output_lines.append("")

                # Upstream/downstream
                if model.upstream_models:
                    output_lines.append(
                        f"**Upstream:** {', '.join(model.upstream_models)}"
                    )
                if model.downstream_models:
                    output_lines.append(
                        f"**Downstream:** {', '.join(model.downstream_models)}"
                    )
                if model.upstream_models or model.downstream_models:
                    output_lines.append("")

        else:
            output_lines.append("## Model Implementations")
            output_lines.append("")
            output_lines.append(
                "*No models implement this concept yet. This is a DRAFT concept.*"
            )
            output_lines.append("")

        # Inferences (from inference engine)
        concept_inferences = [
            i
            for i in context.inferences
            if i.metadata and i.metadata.get("concept_name") == concept.name
        ]

        # Filter out grain inferences (already shown above)
        other_inferences = [i for i in concept_inferences if i.type.value != "grain"]

        if other_inferences:
            output_lines.append("## Additional Inferences")
            output_lines.append("")
            for inf in other_inferences:
                confidence_icon = {
                    "high": "✓",
                    "medium": "~",
                    "low": "?",
                }.get(inf.confidence.value, "")
                output_lines.append(
                    f"- [{confidence_icon} {inf.confidence.value.upper()}] {inf.message}"
                )
            output_lines.append("")

        # Negative guidance
        output_lines.append("## Negative Guidance (What NOT to Do)")
        output_lines.append("")
        if concept.status == "stub":
            output_lines.append(
                "- Do NOT use this concept in production queries until it has a domain and definition"
            )
        if concept.status == "draft":
            output_lines.append(
                "- Do NOT reference models for this concept yet (no models exist)"
            )
        if not concept.guidance:
            output_lines.append(
                "- Do NOT make assumptions about implementation without consulting the owner"
            )

        # Warning about fan-out joins
        fan_out_rels = [
            r
            for r in concept_rels
            if r.from_concept == concept.name and r.cardinality == "1:N"
        ]
        if fan_out_rels:
            output_lines.append(
                f"- CAUTION: Joining to {', '.join(r.to_concept for r in fan_out_rels)} "
                "will fan out your results (1:N relationships)"
            )

        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

    # Multi-concept wrapper close
    if len(context.concepts) > 1:
        output_lines.append("</concepts>")
        output_lines.append("")

    # Summary for multi-concept output
    if len(context.concepts) > 1:
        output_lines.append("## Summary")
        output_lines.append("")
        output_lines.append(
            f"This context includes {len(context.concepts)} concepts, "
            f"{len(context.relationships)} relationships, and "
            f"{len(context.models)} model implementations."
        )
        output_lines.append("")

    return "\n".join(output_lines)


def format_json(context: FullContext) -> str:
    """Format context as structured JSON for programmatic consumption.

    Args:
        context: The resolved context to format

    Returns:
        Valid JSON string with typed, structured data
    """
    # Convert dataclasses to dicts, handling nested structures
    data = {
        "concepts": [
            {
                "name": c.name,
                "domain": c.domain,
                "owner": c.owner,
                "status": c.status,
                "definition": c.definition,
                "guidance": (
                    {
                        "context": c.guidance.context,
                        "rules": [
                            {"name": r.name, "description": r.description}
                            for r in c.guidance.rules
                        ],
                    }
                    if c.guidance
                    else None
                ),
                "models": c.models,
                "is_ghost": c.is_ghost,
                "validation_status": c.validation_status.value,
            }
            for c in context.concepts
        ],
        "relationships": [
            {
                "verb": r.verb,
                "from_concept": r.from_concept,
                "to_concept": r.to_concept,
                "cardinality": r.cardinality,
                "definition": r.definition,
                "is_inferred": r.is_inferred,
            }
            for r in context.relationships
        ],
        "models": [
            {
                "name": m.name,
                "materialization": m.materialization,
                "schema": m.schema,
                "description": m.description,
                "columns": m.columns,
                "constraints": m.constraints,
                "upstream_models": m.upstream_models,
                "downstream_models": m.downstream_models,
                "path": m.path,
            }
            for m in context.models
        ],
        "inferences": [
            {
                "type": i.type.value,
                "message": i.message,
                "confidence": i.confidence.value,
                "metadata": i.metadata,
            }
            for i in context.inferences
        ],
        "contracts": context.contracts,
        "catalog": context.catalog,
        "summary": {
            "concept_count": len(context.concepts),
            "relationship_count": len(context.relationships),
            "model_count": len(context.models),
            "inference_count": len(context.inferences),
        },
    }

    return json.dumps(data, indent=2)


def format_markdown(context: FullContext) -> str:
    """Format context as standard markdown for human reading.

    Uses standard markdown formatting with tables, headers, and lists.

    Args:
        context: The resolved context to format

    Returns:
        Standard markdown text
    """
    output_lines: list[str] = []

    # Handle empty context
    if not context.concepts:
        return "---"

    # Summary table for multi-concept output
    if len(context.concepts) > 1:
        output_lines.append("# Context Summary")
        output_lines.append("")
        output_lines.append("| Metric | Count |")
        output_lines.append("|--------|-------|")
        output_lines.append(f"| Concepts | {len(context.concepts)} |")
        output_lines.append(f"| Relationships | {len(context.relationships)} |")
        output_lines.append(f"| Models | {len(context.models)} |")
        output_lines.append(f"| Inferences | {len(context.inferences)} |")
        output_lines.append("")

    # Concept details
    for concept in context.concepts:
        output_lines.append(f"# {concept.name}")
        output_lines.append("")

        # Metadata table
        output_lines.append("| Property | Value |")
        output_lines.append("|----------|-------|")
        output_lines.append(f"| Status | {concept.status} |")
        output_lines.append(f"| Domain | {concept.domain or '*Not assigned*'} |")
        output_lines.append(f"| Owner | {concept.owner or '*Not assigned*'} |")
        output_lines.append(f"| Model Count | {len(concept.models)} |")
        output_lines.append("")

        # Definition
        output_lines.append("## Definition")
        output_lines.append("")
        if concept.definition:
            output_lines.append(concept.definition)
        else:
            output_lines.append("*No definition provided.*")
        output_lines.append("")

        # Guidance
        if concept.guidance:
            output_lines.append("## Implementation Guidance")
            output_lines.append("")

            if concept.guidance.context:
                output_lines.append("### Business Context")
                output_lines.append("")
                output_lines.append(concept.guidance.context)
                output_lines.append("")

            if concept.guidance.rules:
                output_lines.append("### Rules")
                output_lines.append("")
                for rule in concept.guidance.rules:
                    output_lines.append(f"**{rule.name}**")
                    output_lines.append("")
                    output_lines.append(rule.description)
                    output_lines.append("")

        # Relationships table
        concept_rels = [
            r
            for r in context.relationships
            if r.from_concept == concept.name or r.to_concept == concept.name
        ]

        if concept_rels:
            output_lines.append("## Relationships")
            output_lines.append("")
            output_lines.append(
                "| Direction | Verb | Related Concept | Cardinality | Source |"
            )
            output_lines.append(
                "|-----------|------|-----------------|-------------|--------|"
            )

            for rel in concept_rels:
                direction = "→" if rel.from_concept == concept.name else "←"
                related = (
                    rel.to_concept
                    if rel.from_concept == concept.name
                    else rel.from_concept
                )
                verb = rel.verb
                source = "Inferred" if rel.is_inferred else "Authored"
                output_lines.append(
                    f"| {direction} | {verb} | {related} | {rel.cardinality} | {source} |"
                )

            output_lines.append("")

        # Models table
        concept_models = [m for m in context.models if m.name in concept.models]

        if concept_models:
            output_lines.append("## Models")
            output_lines.append("")

            for model in concept_models:
                output_lines.append(f"### `{model.name}`")
                output_lines.append("")

                # Model metadata
                output_lines.append("| Property | Value |")
                output_lines.append("|----------|-------|")
                if model.materialization:
                    output_lines.append(
                        f"| Materialization | {model.materialization} |"
                    )
                if model.schema:
                    output_lines.append(f"| Schema | {model.schema} |")
                if model.path:
                    output_lines.append(f"| Path | `{model.path}` |")
                output_lines.append("")

                # Description
                if model.description:
                    output_lines.append("**Description:**")
                    output_lines.append("")
                    output_lines.append(model.description)
                    output_lines.append("")

                # Constraints
                if model.constraints:
                    output_lines.append("**Constraints:**")
                    output_lines.append("")
                    for constraint in model.constraints:
                        output_lines.append(f"- {constraint}")
                    output_lines.append("")

                # Columns table
                if model.columns:
                    output_lines.append("**Columns:**")
                    output_lines.append("")
                    output_lines.append("| Name | Type | Description |")
                    output_lines.append("|------|------|-------------|")
                    for col in model.columns:
                        col_name = col.get("name", "")
                        col_type = col.get("type", "")
                        col_desc = col.get("description", "")
                        output_lines.append(
                            f"| `{col_name}` | {col_type} | {col_desc} |"
                        )
                    output_lines.append("")

                # Dependencies
                if model.upstream_models or model.downstream_models:
                    output_lines.append("**Dependencies:**")
                    output_lines.append("")
                    if model.upstream_models:
                        output_lines.append(
                            f"- **Upstream:** {', '.join(f'`{m}`' for m in model.upstream_models)}"
                        )
                    if model.downstream_models:
                        output_lines.append(
                            f"- **Downstream:** {', '.join(f'`{m}`' for m in model.downstream_models)}"
                        )
                    output_lines.append("")

        # Inferences
        concept_inferences = [
            i
            for i in context.inferences
            if i.metadata and i.metadata.get("concept_name") == concept.name
        ]

        if concept_inferences:
            output_lines.append("## Inferences")
            output_lines.append("")
            output_lines.append("| Type | Confidence | Message |")
            output_lines.append("|------|------------|---------|")
            for inf in concept_inferences:
                output_lines.append(
                    f"| {inf.type.value} | {inf.confidence.value} | {inf.message} |"
                )
            output_lines.append("")

        output_lines.append("---")
        output_lines.append("")

    return "\n".join(output_lines)
