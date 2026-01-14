"""Excalidraw diagram exporter for conceptual models."""

import json
import random
from typing import Any, Optional, TextIO

from dbt_conceptual.state import ProjectState


def _generate_id() -> str:
    """Generate a random Excalidraw element ID."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(16))


def _get_domain_color(domain: Optional[str], state: ProjectState) -> str:
    """Get hex color for a domain, with fallback."""
    if domain and domain in state.domains:
        return state.domains[domain].color or "#E3F2FD"
    return "#E3F2FD"  # Default blue


def export_excalidraw(state: ProjectState, output: TextIO) -> None:
    """Export conceptual model as Excalidraw diagram.

    Args:
        state: Project state with concepts and relationships
        output: Text stream to write diagram to
    """
    elements: list[dict[str, Any]] = []
    concept_positions: dict[str, tuple[float, float]] = {}

    # Layout concepts in a grid
    concepts_list = list(state.concepts.keys())
    grid_cols = max(3, int(len(concepts_list) ** 0.5))

    x_spacing = 300
    y_spacing = 250
    start_x = 100
    start_y = 100

    # Create concept boxes
    for idx, (concept_id, concept) in enumerate(state.concepts.items()):
        row = idx // grid_cols
        col = idx % grid_cols

        x = start_x + col * x_spacing
        y = start_y + row * y_spacing

        concept_positions[concept_id] = (x, y)

        # Get color from domain
        bg_color = _get_domain_color(concept.domain, state)

        # Create box for concept
        box_id = _generate_id()
        box_width = 200
        box_height = 150

        elements.append(
            {
                "type": "rectangle",
                "version": 1,
                "versionNonce": random.randint(1, 2147483647),
                "isDeleted": False,
                "id": box_id,
                "fillStyle": "solid",
                "strokeWidth": 2,
                "strokeStyle": "solid",
                "roughness": 1,
                "opacity": 100,
                "angle": 0,
                "x": x,
                "y": y,
                "strokeColor": "#1e1e1e",
                "backgroundColor": bg_color,
                "width": box_width,
                "height": box_height,
                "seed": random.randint(1, 2147483647),
                "groupIds": [],
                "frameId": None,
                "roundness": {"type": 3},
                "boundElements": [],
                "updated": 1,
                "link": None,
                "locked": False,
            }
        )

        # Create text label for concept name
        text_lines = [concept.name]

        # Add status indicator
        status_icon = {
            "complete": "✓",
            "stub": "⚠",
            "draft": "◐",
            "deprecated": "✗",
        }.get(concept.status, "◐")

        text_lines.append(f"{status_icon} {concept.status}")

        # Add model counts
        if concept.silver_models or concept.gold_models:
            silver_count = len(concept.silver_models)
            gold_count = len(concept.gold_models)
            text_lines.append(f"S:{silver_count} G:{gold_count}")

        # Add owner if present
        if concept.owner:
            text_lines.append(f"👤 {concept.owner}")

        text_content = "\n".join(text_lines)

        elements.append(
            {
                "type": "text",
                "version": 1,
                "versionNonce": random.randint(1, 2147483647),
                "isDeleted": False,
                "id": _generate_id(),
                "fillStyle": "solid",
                "strokeWidth": 2,
                "strokeStyle": "solid",
                "roughness": 1,
                "opacity": 100,
                "angle": 0,
                "x": x + 10,
                "y": y + 20,
                "strokeColor": "#1e1e1e",
                "backgroundColor": "transparent",
                "width": box_width - 20,
                "height": 100,
                "seed": random.randint(1, 2147483647),
                "groupIds": [],
                "frameId": None,
                "roundness": None,
                "boundElements": [],
                "updated": 1,
                "link": None,
                "locked": False,
                "fontSize": 16,
                "fontFamily": 1,
                "text": text_content,
                "textAlign": "left",
                "verticalAlign": "top",
                "containerId": None,
                "originalText": text_content,
                "lineHeight": 1.25,
                "baseline": 14,
            }
        )

    # Create relationship arrows
    for _rel_id, rel in state.relationships.items():
        from_concept = rel.from_concept
        to_concept = rel.to_concept

        if from_concept not in concept_positions or to_concept not in concept_positions:
            continue

        from_x, from_y = concept_positions[from_concept]
        to_x, to_y = concept_positions[to_concept]

        # Calculate arrow start/end points (center of boxes)
        arrow_start_x: float = from_x + 100
        arrow_start_y: float = from_y + 75
        arrow_end_x: float = to_x + 100
        arrow_end_y: float = to_y + 75

        # Create arrow
        arrow_id = _generate_id()
        elements.append(
            {
                "type": "arrow",
                "version": 1,
                "versionNonce": random.randint(1, 2147483647),
                "isDeleted": False,
                "id": arrow_id,
                "fillStyle": "solid",
                "strokeWidth": 2,
                "strokeStyle": "solid",
                "roughness": 1,
                "opacity": 100,
                "angle": 0,
                "x": arrow_start_x,
                "y": arrow_start_y,
                "strokeColor": "#1e1e1e",
                "backgroundColor": "transparent",
                "width": arrow_end_x - arrow_start_x,
                "height": arrow_end_y - arrow_start_y,
                "seed": random.randint(1, 2147483647),
                "groupIds": [],
                "frameId": None,
                "roundness": {"type": 2},
                "boundElements": [],
                "updated": 1,
                "link": None,
                "locked": False,
                "startBinding": None,
                "endBinding": None,
                "lastCommittedPoint": None,
                "startArrowhead": None,
                "endArrowhead": "arrow",
                "points": [
                    [0, 0],
                    [arrow_end_x - arrow_start_x, arrow_end_y - arrow_start_y],
                ],
            }
        )

        # Add label for relationship
        label_x = (arrow_start_x + arrow_end_x) / 2
        label_y = (arrow_start_y + arrow_end_y) / 2 - 20

        label_text = rel.name
        if rel.realized_by:
            label_text += f"\n({len(rel.realized_by)} facts)"

        elements.append(
            {
                "type": "text",
                "version": 1,
                "versionNonce": random.randint(1, 2147483647),
                "isDeleted": False,
                "id": _generate_id(),
                "fillStyle": "solid",
                "strokeWidth": 2,
                "strokeStyle": "solid",
                "roughness": 1,
                "opacity": 100,
                "angle": 0,
                "x": label_x,
                "y": label_y,
                "strokeColor": "#1e1e1e",
                "backgroundColor": "#ffffff",
                "width": 100,
                "height": 25,
                "seed": random.randint(1, 2147483647),
                "groupIds": [],
                "frameId": None,
                "roundness": None,
                "boundElements": [],
                "updated": 1,
                "link": None,
                "locked": False,
                "fontSize": 14,
                "fontFamily": 1,
                "text": label_text,
                "textAlign": "center",
                "verticalAlign": "middle",
                "containerId": None,
                "originalText": label_text,
                "lineHeight": 1.25,
                "baseline": 18,
            }
        )

    # Create Excalidraw JSON structure
    diagram = {
        "type": "excalidraw",
        "version": 2,
        "source": "dbt-conceptual",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
        },
        "files": {},
    }

    json.dump(diagram, output, indent=2)
