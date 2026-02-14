"""Output formatters for concept context.

Provides three output formats for the same conceptual model context:
- LLM: Natural language optimized for agent consumption
- JSON: Structured data for programmatic use
- Markdown: Human-readable documentation format

All formatters consume the same context dictionary structure.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Protocol


class Formatter(Protocol):
    """Protocol for output formatters."""

    def format(self, context: dict[str, Any]) -> str:
        """Format context data into the target output format.

        Args:
            context: Dictionary containing concept context data

        Returns:
            Formatted string output
        """
        ...


class BaseFormatter(ABC):
    """Base class for formatters with common utilities."""

    @abstractmethod
    def format(self, context: dict[str, Any]) -> str:
        """Format context data into the target output format.

        Args:
            context: Dictionary containing concept context data

        Returns:
            Formatted string output
        """
        pass

    def _get_concept_info(self, context: dict[str, Any]) -> dict[str, Any]:
        """Extract concept information from context.

        Args:
            context: Context dictionary

        Returns:
            Dict with concept metadata
        """
        return {
            "name": context.get("name", "Unknown"),
            "domain": context.get("domain"),
            "description": context.get("description"),
            "status": context.get("status"),
            "owner": context.get("owner"),
        }

    def _get_guidance(self, context: dict[str, Any]) -> dict[str, Any] | None:
        """Extract guidance from context.

        Args:
            context: Context dictionary

        Returns:
            Dict with guidance data or None
        """
        return context.get("guidance")  # type: ignore[return-value]

    def _get_models(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract model information from context.

        Args:
            context: Context dictionary

        Returns:
            List of model dicts
        """
        result = context.get("models", [])
        if not isinstance(result, list):
            return []
        return result  # type: ignore[return-value]

    def _get_relationships(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract relationships from context.

        Args:
            context: Context dictionary

        Returns:
            List of relationship dicts
        """
        result = context.get("relationships", [])
        if not isinstance(result, list):
            return []
        return result  # type: ignore[return-value]

    def _get_inferences(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract inferences from context.

        Args:
            context: Context dictionary

        Returns:
            List of inference dicts
        """
        result = context.get("inferences", [])
        if not isinstance(result, list):
            return []
        return result  # type: ignore[return-value]


class LLMFormatter(BaseFormatter):
    """Formatter optimized for LLM/agent consumption.

    Produces natural language prose with:
    - Explicit grain statements
    - Negative guidance (what NOT to do)
    - Contextual join implications
    - Clear source attribution
    - XML-like tags for structure
    """

    def format(self, context: dict[str, Any]) -> str:
        """Format context as LLM-optimized prose.

        Args:
            context: Dictionary containing concept context data

        Returns:
            Natural language formatted string
        """
        output_lines: list[str] = []

        # Header with concept info
        concept = self._get_concept_info(context)
        output_lines.append(f"<concept name=\"{concept['name']}\">")
        output_lines.append("")

        # Definition section
        output_lines.append("<definition>")
        if concept["description"]:
            output_lines.append(concept["description"])
        else:
            output_lines.append(
                f"CONCEPT DEFINITION NOT PROVIDED. {concept['name']} is currently a stub."
            )

        if concept["domain"]:
            output_lines.append(f"\nDomain: {concept['domain']}")
        if concept["owner"]:
            output_lines.append(f"Owner: {concept['owner']}")
        if concept["status"]:
            output_lines.append(f"Status: {concept['status']}")
        output_lines.append("</definition>")
        output_lines.append("")

        # Guidance section
        guidance = self._get_guidance(context)
        if guidance:
            output_lines.append("<guidance>")
            if guidance.get("context"):
                output_lines.append("BUSINESS CONTEXT:")
                output_lines.append(guidance["context"])
                output_lines.append("")

            rules = guidance.get("rules", [])
            if rules:
                output_lines.append("IMPLEMENTATION RULES:")
                for rule in rules:
                    rule_name = rule.get("name", "Unnamed rule")
                    rule_desc = rule.get("description", "")
                    output_lines.append(f"- {rule_name}: {rule_desc}")
                output_lines.append("")
            output_lines.append("</guidance>")
            output_lines.append("")

        # Models section
        models = self._get_models(context)
        if models:
            output_lines.append("<models>")
            output_lines.append(
                f"This concept is implemented by {len(models)} model(s) in the dbt project:"
            )
            output_lines.append("")

            for model in models:
                model_name = model.get("name", "Unknown")
                output_lines.append(f"MODEL: {model_name}")

                materialization = model.get("materialization")
                if materialization:
                    output_lines.append(f"  Materialization: {materialization}")

                # Grain information
                grain = model.get("grain")
                if grain:
                    grain_cols = grain.get("columns", [])
                    if len(grain_cols) == 1:
                        output_lines.append(
                            f"  GRAIN: One row per {grain_cols[0]}. This is the uniqueness constraint."
                        )
                    elif len(grain_cols) > 1:
                        cols_str = ", ".join(grain_cols)
                        output_lines.append(
                            f"  GRAIN: One row per combination of ({cols_str}). These columns together form the uniqueness constraint."
                        )

                # Columns
                columns = model.get("columns", [])
                if columns:
                    output_lines.append(f"  Columns ({len(columns)}):")
                    for col in columns:
                        col_name = col.get("name", "unknown")
                        col_desc = col.get("description", "")
                        if col_desc:
                            output_lines.append(f"    - {col_name}: {col_desc}")
                        else:
                            output_lines.append(f"    - {col_name}")

                # Constraints
                constraints = model.get("constraints", [])
                if constraints:
                    output_lines.append("  Constraints:")
                    for constraint in constraints:
                        output_lines.append(f"    - {constraint}")

                output_lines.append("")

            output_lines.append("</models>")
            output_lines.append("")

        # Relationships section
        relationships = self._get_relationships(context)
        if relationships:
            output_lines.append("<relationships>")
            output_lines.append(
                f"This concept has {len(relationships)} relationship(s) with other concepts:"
            )
            output_lines.append("")

            for rel in relationships:
                from_concept = rel.get("from_concept", "")
                to_concept = rel.get("to_concept", "")
                verb = rel.get("verb", "relates to")
                cardinality = rel.get("cardinality", "1:N")

                output_lines.append(f"{from_concept} {verb} {to_concept}")
                output_lines.append(f"  Cardinality: {cardinality}")

                if cardinality == "1:N":
                    output_lines.append(
                        f"  JOIN IMPLICATION: Joining from {from_concept} to {to_concept} may fan out results (one-to-many)."
                    )
                elif cardinality == "1:1":
                    output_lines.append(
                        f"  JOIN IMPLICATION: Joining from {from_concept} to {to_concept} preserves grain (one-to-one)."
                    )

                definition = rel.get("definition")
                if definition:
                    output_lines.append(f"  Definition: {definition}")

                output_lines.append("")

            output_lines.append("</relationships>")
            output_lines.append("")

        # Inferences section
        inferences = self._get_inferences(context)
        if inferences:
            output_lines.append("<inferences>")
            output_lines.append(
                "AUTOMATED INFERENCES (heuristic analysis, verify before relying on):"
            )
            output_lines.append("")

            for inf in inferences:
                inf_type = inf.get("type", "unknown")
                message = inf.get("message", "")
                confidence = inf.get("confidence", "unknown")
                output_lines.append(f"[{inf_type.upper()}] {message}")
                output_lines.append(f"  Confidence: {confidence}")
                output_lines.append("")

            output_lines.append("</inferences>")
            output_lines.append("")

        # Attribution
        output_lines.append("<attribution>")
        output_lines.append(
            "SOURCE ATTRIBUTION: Concept definition, guidance, and relationships are sourced from conceptual.yml."
        )
        output_lines.append(
            "Model metadata (columns, constraints, grain) is sourced from dbt manifest and schema files."
        )
        output_lines.append(
            "Inferences are machine-generated heuristics and should be verified."
        )
        output_lines.append("</attribution>")
        output_lines.append("")

        output_lines.append("</concept>")

        return "\n".join(output_lines)


class JSONFormatter(BaseFormatter):
    """Formatter producing structured JSON output.

    Output is typed and suitable for programmatic consumption.
    """

    def format(self, context: dict[str, Any]) -> str:
        """Format context as JSON.

        Args:
            context: Dictionary containing concept context data

        Returns:
            JSON string
        """
        # Build structured output
        output = {
            "concept": self._get_concept_info(context),
            "guidance": self._get_guidance(context),
            "models": self._get_models(context),
            "relationships": self._get_relationships(context),
            "inferences": self._get_inferences(context),
            "attribution": {
                "conceptual_data": "sourced from conceptual.yml",
                "model_metadata": "sourced from dbt manifest and schema files",
                "inferences": "machine-generated heuristics",
            },
        }

        return json.dumps(output, indent=2)


class MarkdownFormatter(BaseFormatter):
    """Formatter producing standard Markdown output.

    Human-readable documentation with tables and headers.
    """

    def format(self, context: dict[str, Any]) -> str:
        """Format context as Markdown.

        Args:
            context: Dictionary containing concept context data

        Returns:
            Markdown string
        """
        output_lines: list[str] = []

        # Header
        concept = self._get_concept_info(context)
        output_lines.append(f"# {concept['name']}")
        output_lines.append("")

        # Metadata table
        output_lines.append("## Overview")
        output_lines.append("")
        output_lines.append("| Property | Value |")
        output_lines.append("|----------|-------|")
        if concept["domain"]:
            output_lines.append(f"| Domain | {concept['domain']} |")
        if concept["owner"]:
            output_lines.append(f"| Owner | {concept['owner']} |")
        if concept["status"]:
            output_lines.append(f"| Status | {concept['status']} |")
        output_lines.append("")

        # Definition
        if concept["description"]:
            output_lines.append("## Definition")
            output_lines.append("")
            output_lines.append(concept["description"])
            output_lines.append("")

        # Guidance
        guidance = self._get_guidance(context)
        if guidance:
            output_lines.append("## Guidance")
            output_lines.append("")

            if guidance.get("context"):
                output_lines.append("### Business Context")
                output_lines.append("")
                output_lines.append(guidance["context"])
                output_lines.append("")

            rules = guidance.get("rules", [])
            if rules:
                output_lines.append("### Implementation Rules")
                output_lines.append("")
                for rule in rules:
                    rule_name = rule.get("name", "Unnamed rule")
                    rule_desc = rule.get("description", "")
                    output_lines.append(f"**{rule_name}**: {rule_desc}")
                    output_lines.append("")

        # Models
        models = self._get_models(context)
        if models:
            output_lines.append("## Models")
            output_lines.append("")

            for model in models:
                model_name = model.get("name", "Unknown")
                output_lines.append(f"### {model_name}")
                output_lines.append("")

                # Model metadata table
                output_lines.append("| Property | Value |")
                output_lines.append("|----------|-------|")

                materialization = model.get("materialization")
                if materialization:
                    output_lines.append(f"| Materialization | {materialization} |")

                grain = model.get("grain")
                if grain:
                    grain_cols = grain.get("columns", [])
                    if grain_cols:
                        cols_str = ", ".join(grain_cols)
                        output_lines.append(f"| Grain | {cols_str} |")

                output_lines.append("")

                # Columns
                columns = model.get("columns", [])
                if columns:
                    output_lines.append("#### Columns")
                    output_lines.append("")
                    output_lines.append("| Column | Description |")
                    output_lines.append("|--------|-------------|")
                    for col in columns:
                        col_name = col.get("name", "unknown")
                        col_desc = col.get("description", "")
                        # Escape pipe characters in description
                        col_desc_escaped = col_desc.replace("|", "\\|")
                        output_lines.append(f"| {col_name} | {col_desc_escaped} |")
                    output_lines.append("")

                # Constraints
                constraints = model.get("constraints", [])
                if constraints:
                    output_lines.append("#### Constraints")
                    output_lines.append("")
                    for constraint in constraints:
                        output_lines.append(f"- {constraint}")
                    output_lines.append("")

        # Relationships
        relationships = self._get_relationships(context)
        if relationships:
            output_lines.append("## Relationships")
            output_lines.append("")
            output_lines.append("| From | Verb | To | Cardinality |")
            output_lines.append("|------|------|----|-------------|")

            for rel in relationships:
                from_concept = rel.get("from_concept", "")
                to_concept = rel.get("to_concept", "")
                verb = rel.get("verb", "relates to")
                cardinality = rel.get("cardinality", "1:N")

                output_lines.append(
                    f"| {from_concept} | {verb} | {to_concept} | {cardinality} |"
                )

            output_lines.append("")

            # Relationship details
            for rel in relationships:
                definition = rel.get("definition")
                if definition:
                    from_concept = rel.get("from_concept", "")
                    to_concept = rel.get("to_concept", "")
                    verb = rel.get("verb", "relates to")
                    output_lines.append(f"**{from_concept} {verb} {to_concept}**")
                    output_lines.append("")
                    output_lines.append(definition)
                    output_lines.append("")

        # Inferences
        inferences = self._get_inferences(context)
        if inferences:
            output_lines.append("## Inferences")
            output_lines.append("")
            output_lines.append(
                "_Automated heuristic analysis. Verify before relying on._"
            )
            output_lines.append("")

            for inf in inferences:
                inf_type = inf.get("type", "unknown")
                message = inf.get("message", "")
                confidence = inf.get("confidence", "unknown")
                output_lines.append(
                    f"- **[{inf_type}]** {message} _(confidence: {confidence})_"
                )

            output_lines.append("")

        # Attribution
        output_lines.append("---")
        output_lines.append("")
        output_lines.append("## Attribution")
        output_lines.append("")
        output_lines.append(
            "- **Concept definition, guidance, and relationships**: sourced from `conceptual.yml`"
        )
        output_lines.append(
            "- **Model metadata**: sourced from dbt manifest and schema files"
        )
        output_lines.append(
            "- **Inferences**: machine-generated heuristics (should be verified)"
        )

        return "\n".join(output_lines)


# Factory function for getting formatters
def get_formatter(format_type: str) -> Formatter:
    """Get a formatter instance by format type.

    Args:
        format_type: One of 'llm', 'json', 'markdown'

    Returns:
        Formatter instance

    Raises:
        ValueError: If format_type is not recognized
    """
    formatters: dict[str, Formatter] = {
        "llm": LLMFormatter(),
        "json": JSONFormatter(),
        "markdown": MarkdownFormatter(),
    }

    formatter = formatters.get(format_type.lower())
    if not formatter:
        raise ValueError(
            f"Unknown format type: {format_type}. Must be one of: {', '.join(formatters.keys())}"
        )

    return formatter
