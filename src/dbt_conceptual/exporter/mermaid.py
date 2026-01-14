"""Mermaid diagram exporter for conceptual models."""

from typing import TextIO

from dbt_conceptual.state import ProjectState


def export_mermaid(state: ProjectState, output: TextIO) -> None:
    """Export conceptual model as Mermaid ER diagram.

    Args:
        state: Project state with concepts and relationships
        output: Text stream to write diagram to
    """
    output.write("erDiagram\n")

    # Group concepts by domain
    domain_concepts: dict[str, list[str]] = {}
    for concept_id, concept in state.concepts.items():
        domain = concept.domain or "default"
        if domain not in domain_concepts:
            domain_concepts[domain] = []
        domain_concepts[domain].append(concept_id)

    # Write concepts with attributes
    for concept_id, concept in state.concepts.items():
        # Write concept header
        output.write(f"    {concept_id.upper()} {{\n")

        # Add basic attributes
        output.write('        string id "Primary Key"\n')
        output.write('        string name "Display Name"\n')

        # Add metadata as comment
        if concept.owner:
            output.write(f"        %% Owner: {concept.owner}\n")
        if concept.definition:
            output.write(f"        %% Definition: {concept.definition}\n")
        if concept.status:
            output.write(f"        %% Status: {concept.status}\n")

        # Show which models implement this concept
        if concept.gold_models:
            models_str = ", ".join(concept.gold_models)
            output.write(f"        %% Gold: {models_str}\n")
        if concept.silver_models:
            models_str = ", ".join(concept.silver_models)
            output.write(f"        %% Silver: {models_str}\n")

        output.write("    }\n")

    # Write relationships
    for _rel_id, rel in state.relationships.items():
        # Parse cardinality
        cardinality = rel.cardinality or "1:N"
        from_card, to_card = cardinality.split(":")

        # Map cardinality to Mermaid syntax
        # Mermaid format: ENTITY1 ||--o{ ENTITY2 : "relationship"
        # || = exactly one, |o = zero or one, }o = zero or many, }| = one or many
        left_symbol = (
            "||" if from_card == "1" else "|o" if from_card == "0..1" else "}o"
        )
        right_symbol = "||" if to_card == "1" else "|o" if to_card == "0..1" else "o{"

        # Write relationship
        from_concept = rel.from_concept.upper()
        to_concept = rel.to_concept.upper()
        rel_name = rel.name

        output.write(
            f'    {from_concept} {left_symbol}--{right_symbol} {to_concept} : "{rel_name}"\n'
        )

        # Add relationship metadata as comment if realized
        if rel.realized_by:
            models_str = ", ".join(rel.realized_by)
            output.write(f"    %% Realized by: {models_str}\n")

    output.write("\n")
