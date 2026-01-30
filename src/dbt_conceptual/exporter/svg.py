"""SVG diagram export for conceptual models."""

from typing import TextIO

from dbt_conceptual.state import ProjectState


def export_diagram_svg(state: ProjectState, output: TextIO) -> None:
    """Export conceptual model as SVG diagram.

    Creates a visual diagram showing concepts and relationships.

    Args:
        state: Project state containing concepts and relationships
        output: File-like object to write SVG to
    """
    # Calculate layout dimensions
    concepts_list = list(state.concepts.items())
    num_concepts = len(concepts_list)

    if num_concepts == 0:
        output.write(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">'
            '<text x="200" y="100" text-anchor="middle" fill="#666">'
            "No concepts defined</text></svg>"
        )
        return

    # Simple grid layout
    cols = min(4, num_concepts)
    rows = (num_concepts + cols - 1) // cols

    node_width = 160
    node_height = 80
    h_spacing = 200
    v_spacing = 120
    padding = 50

    width = cols * h_spacing + padding * 2
    height = rows * v_spacing + padding * 2

    # Calculate node positions
    positions: dict[str, tuple[int, int]] = {}
    for i, (concept_id, _concept) in enumerate(concepts_list):
        col = i % cols
        row = i // cols
        x = padding + col * h_spacing + node_width // 2
        y = padding + row * v_spacing + node_height // 2
        positions[concept_id] = (x, y)

    # Domain colors
    domain_colors: dict[str, str] = {}
    for domain_id, domain in state.domains.items():
        domain_colors[domain_id] = domain.color or "#3498db"

    # Start SVG
    output.write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">\n'
    )
    output.write("  <defs>\n")
    output.write('    <marker id="arrowhead" markerWidth="10" markerHeight="7" ')
    output.write('refX="9" refY="3.5" orient="auto">\n')
    output.write('      <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>\n')
    output.write("    </marker>\n")
    output.write("  </defs>\n")

    # Draw relationships (edges)
    for _rel_id, rel in state.relationships.items():
        if rel.from_concept in positions and rel.to_concept in positions:
            from_pos = positions[rel.from_concept]
            to_pos = positions[rel.to_concept]

            # Calculate edge points (from edge of node, not center)
            dx = to_pos[0] - from_pos[0]
            dy = to_pos[1] - from_pos[1]
            dist = max(1, (dx * dx + dy * dy) ** 0.5)

            # Offset from center to edge
            from_x = from_pos[0] + (dx / dist) * (node_width // 2)
            from_y = from_pos[1] + (dy / dist) * (node_height // 2)
            to_x = to_pos[0] - (dx / dist) * (node_width // 2 + 10)
            to_y = to_pos[1] - (dy / dist) * (node_height // 2 + 10)

            output.write(f'  <line x1="{from_x}" y1="{from_y}" ')
            output.write(f'x2="{to_x}" y2="{to_y}" ')
            output.write(
                'stroke="#666" stroke-width="2" marker-end="url(#arrowhead)"/>\n'
            )

            # Relationship label
            mid_x = (from_x + to_x) // 2
            mid_y = (from_y + to_y) // 2
            output.write(f'  <text x="{mid_x}" y="{mid_y - 5}" ')
            output.write('text-anchor="middle" font-size="10" fill="#666">')
            output.write(f"{rel.verb}</text>\n")

    # Draw concepts (nodes)
    for concept_id, concept in concepts_list:
        x, y = positions[concept_id]
        color = domain_colors.get(concept.domain or "", "#3498db")

        # Status-based styling
        if concept.status == "stub":
            stroke_dash = "5,5"
            opacity = "0.7"
        elif concept.status == "draft":
            stroke_dash = "none"
            opacity = "0.85"
        else:
            stroke_dash = "none"
            opacity = "1"

        # Node rectangle
        output.write(f'  <rect x="{x - node_width // 2}" y="{y - node_height // 2}" ')
        output.write(f'width="{node_width}" height="{node_height}" ')
        output.write(f'rx="8" fill="white" stroke="{color}" stroke-width="2" ')
        output.write(f'stroke-dasharray="{stroke_dash}" opacity="{opacity}"/>\n')

        # Domain color bar
        output.write(f'  <rect x="{x - node_width // 2}" y="{y - node_height // 2}" ')
        output.write(f'width="{node_width}" height="6" rx="8" fill="{color}"/>\n')
        output.write(
            f'  <rect x="{x - node_width // 2}" y="{y - node_height // 2 + 3}" '
        )
        output.write(f'width="{node_width}" height="3" fill="{color}"/>\n')

        # Concept name
        output.write(f'  <text x="{x}" y="{y + 5}" ')
        output.write('text-anchor="middle" font-family="system-ui, sans-serif" ')
        output.write(
            f'font-size="14" font-weight="600" fill="#333">{concept.name}</text>\n'
        )

        # Status indicator
        status_icon = {"complete": "✓", "draft": "◐", "stub": "○"}.get(
            concept.status, "?"
        )
        output.write(f'  <text x="{x + node_width // 2 - 15}" ')
        output.write(f'y="{y - node_height // 2 + 20}" ')
        output.write(f'font-size="12" fill="{color}">{status_icon}</text>\n')

    output.write("</svg>\n")
