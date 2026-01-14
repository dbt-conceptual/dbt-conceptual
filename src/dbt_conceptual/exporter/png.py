"""PNG diagram exporter for dbt-conceptual."""

from io import BytesIO
from typing import BinaryIO, Dict, List, Tuple

from dbt_conceptual.state import ProjectState


def export_png(state: ProjectState, output: BinaryIO) -> None:
    """Export conceptual model as PNG diagram.

    Creates a visual diagram with:
    - Domain groupings (colored backgrounds)
    - Concept boxes
    - Relationship arrows

    Args:
        state: The conceptual model state
        output: Binary output stream for PNG file
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError(
            "PNG export requires Pillow. Install with: pip install dbt-conceptual[png]"
        )

    # Configuration
    WIDTH = 1200
    HEIGHT = 800
    PADDING = 60
    CONCEPT_WIDTH = 180
    CONCEPT_HEIGHT = 80
    FONT_SIZE_TITLE = 14
    FONT_SIZE_TEXT = 12

    # Colors
    DOMAIN_COLORS = [
        "#E3F2FD",  # Light blue
        "#FFF3E0",  # Light orange
        "#F3E5F5",  # Light purple
        "#E8F5E9",  # Light green
        "#FFF9C4",  # Light yellow
        "#FFEBEE",  # Light red
    ]
    CONCEPT_COLOR = "#FFFFFF"
    CONCEPT_BORDER = "#1976D2"
    TEXT_COLOR = "#000000"
    ARROW_COLOR = "#666666"

    # Create image
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    # Try to load fonts
    try:
        font_title = ImageFont.truetype("Arial.ttf", FONT_SIZE_TITLE)
        font_text = ImageFont.truetype("Arial.ttf", FONT_SIZE_TEXT)
    except Exception:
        try:
            font_title = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", FONT_SIZE_TITLE
            )
            font_text = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", FONT_SIZE_TEXT
            )
        except Exception:
            # Fallback to default font
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

    # Group concepts by domain
    domains_with_concepts: Dict[str, List[str]] = {}
    for concept_id, concept in state.concepts.items():
        domain = concept.domain or "default"
        if domain not in domains_with_concepts:
            domains_with_concepts[domain] = []
        domains_with_concepts[domain].append(concept_id)

    # Calculate layout
    num_domains = len(domains_with_concepts)
    domain_width = (WIDTH - 2 * PADDING) // max(num_domains, 1)
    concept_positions: Dict[str, Tuple[int, int]] = {}

    # Draw domains and concepts
    for idx, (domain_id, concept_ids) in enumerate(domains_with_concepts.items()):
        # Domain background
        domain_x = PADDING + idx * domain_width
        domain_color = DOMAIN_COLORS[idx % len(DOMAIN_COLORS)]

        # Convert hex to RGB
        r = int(domain_color[1:3], 16)
        g = int(domain_color[3:5], 16)
        b = int(domain_color[5:7], 16)

        draw.rectangle(
            [
                domain_x,
                PADDING,
                domain_x + domain_width - 10,
                HEIGHT - PADDING,
            ],
            fill=(r, g, b),
            outline=None,
        )

        # Domain label
        domain_obj = state.domains.get(domain_id)
        domain_name = domain_obj.display_name if domain_obj else domain_id
        draw.text(
            (domain_x + 10, PADDING + 10),
            domain_name,
            fill=TEXT_COLOR,
            font=font_title,
        )

        # Draw concepts in this domain
        num_concepts = len(concept_ids)
        for cidx, concept_id in enumerate(concept_ids):
            # Position concept
            concept_x = domain_x + 20
            concept_y = PADDING + 50 + cidx * (CONCEPT_HEIGHT + 20)

            concept_positions[concept_id] = (
                concept_x + CONCEPT_WIDTH // 2,
                concept_y + CONCEPT_HEIGHT // 2,
            )

            # Draw concept box
            draw.rectangle(
                [
                    concept_x,
                    concept_y,
                    concept_x + CONCEPT_WIDTH,
                    concept_y + CONCEPT_HEIGHT,
                ],
                fill=CONCEPT_COLOR,
                outline=CONCEPT_BORDER,
                width=2,
            )

            # Concept name
            concept = state.concepts[concept_id]
            concept_name = concept.name or concept_id
            draw.text(
                (concept_x + 10, concept_y + 10),
                concept_name,
                fill=TEXT_COLOR,
                font=font_title,
            )

            # Status indicator
            status_text = f"[{concept.status}]" if concept.status else ""
            draw.text(
                (concept_x + 10, concept_y + 30),
                status_text,
                fill=ARROW_COLOR,
                font=font_text,
            )

            # Coverage indicators
            s_count = len(concept.silver_models or [])
            g_count = len(concept.gold_models or [])
            coverage = f"S:{s_count} G:{g_count}"
            draw.text(
                (concept_x + 10, concept_y + 50),
                coverage,
                fill=ARROW_COLOR,
                font=font_text,
            )

    # Draw relationships as arrows
    for rel_id, rel in state.relationships.items():
        from_pos = concept_positions.get(rel.from_concept)
        to_pos = concept_positions.get(rel.to_concept)

        if from_pos and to_pos:
            # Draw arrow line
            draw.line(
                [from_pos, to_pos],
                fill=ARROW_COLOR,
                width=2,
            )

            # Draw arrowhead (simple triangle)
            dx = to_pos[0] - from_pos[0]
            dy = to_pos[1] - from_pos[1]
            length = (dx * dx + dy * dy) ** 0.5
            if length > 0:
                # Normalize
                dx /= length
                dy /= length

                # Arrow tip at 80% of line
                arrow_x = from_pos[0] + dx * length * 0.8
                arrow_y = from_pos[1] + dy * length * 0.8

                # Perpendicular for arrow wings
                perp_x = -dy * 8
                perp_y = dx * 8

                arrow_points = [
                    (arrow_x + perp_x, arrow_y + perp_y),
                    (arrow_x + dx * 15, arrow_y + dy * 15),
                    (arrow_x - perp_x, arrow_y - perp_y),
                ]

                draw.polygon(arrow_points, fill=ARROW_COLOR)

            # Draw relationship label
            mid_x = (from_pos[0] + to_pos[0]) // 2
            mid_y = (from_pos[1] + to_pos[1]) // 2
            label = rel.name or rel_id

            # Draw label background
            bbox = draw.textbbox((mid_x, mid_y), label, font=font_text)
            draw.rectangle(bbox, fill=CONCEPT_COLOR)

            draw.text(
                (mid_x, mid_y),
                label,
                fill=TEXT_COLOR,
                font=font_text,
                anchor="mm",
            )

    # Add title
    draw.text(
        (WIDTH // 2, 20),
        "Conceptual Model Diagram",
        fill=TEXT_COLOR,
        font=font_title,
        anchor="mm",
    )

    # Save to output
    img.save(output, format="PNG")
