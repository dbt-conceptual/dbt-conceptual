"""Coverage report exporter for conceptual models.

v1.0: Simplified model - single models[] array.
"""

from typing import TextIO

from dbt_conceptual.state import ConceptState, CoverageStats, ProjectState

# =============================================================================
# HTML Templates
# =============================================================================

_CSS_STYLES = """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #fafaf9; color: #333333; line-height: 1.6; padding: 2rem;
        }
        .container {
            max-width: 1200px; margin: 0 auto; background: white;
            border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 2rem;
        }
        h1 { font-size: 2rem; margin-bottom: 0.5rem; color: #1a1a1a; }
        h2 { font-size: 1.5rem; margin-bottom: 1rem; color: #333333; border-bottom: 2px solid #e8e6e3; padding-bottom: 0.5rem; }
        .subtitle { color: #666; margin-bottom: 2rem; font-size: 0.9rem; }
        section { margin-bottom: 3rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 3rem; }
        .stat-card { background: #f5f4f2; padding: 1.5rem; border-radius: 6px; border-left: 4px solid #4caf50; }
        .stat-label { font-size: 0.875rem; color: #666; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #1a1a1a; }
        .stat-secondary { font-size: 0.875rem; color: #666; margin-top: 0.5rem; }
        .progress-bar { width: 100%; height: 8px; background: #e8e6e3; border-radius: 4px; overflow: hidden; margin-top: 0.5rem; }
        .progress-fill { height: 100%; background: #4caf50; transition: width 0.3s ease; }
        .domain-section { margin-bottom: 2rem; }
        .domain-header { font-size: 1.125rem; font-weight: 600; margin-bottom: 0.75rem; color: #333; }
        .concept-list { display: grid; gap: 0.75rem; }
        .concept-item { background: #f5f4f2; padding: 1rem; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        .concept-name { font-weight: 500; color: #1a1a1a; }
        .concept-status { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .concept-status.complete { background: #C8E6C9; color: #2E7D32; }
        .concept-status.draft { background: #FFE0B2; color: #E65100; }
        .concept-status.stub { background: #FFCDD2; color: #C62828; }
        .concept-meta { font-size: 0.875rem; color: #666; margin-top: 0.5rem; }
        .attention-list { display: grid; gap: 1rem; }
        .attention-item { background: #fef5eb; border-left: 4px solid #e67e22; padding: 1rem; border-radius: 4px; }
        .attention-item.error { background: #fef2f2; border-left-color: #dc2626; }
        .attention-title { font-weight: 600; margin-bottom: 0.5rem; color: #1a1a1a; }
        .attention-detail { font-size: 0.875rem; color: #666; }
        .orphan-list { background: #f5f4f2; padding: 1rem; border-radius: 4px; max-height: 300px; overflow-y: auto; }
        .orphan-item { padding: 0.5rem; border-bottom: 1px solid #e8e6e3; font-family: 'Courier New', monospace; font-size: 0.875rem; }
        .orphan-item:last-child { border-bottom: none; }
    </style>
"""


def _render_stat_card(label: str, value: int, secondary: str) -> str:
    """Render a stat card with progress bar."""
    return f"""
            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}%</div>
                <div class="stat-secondary">{secondary}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {value}%"></div>
                </div>
            </div>"""


def _render_attention_item(
    icon: str, title: str, detail: str, css_class: str = ""
) -> str:
    """Render an attention item."""
    class_attr = (
        f'class="attention-item {css_class}"' if css_class else 'class="attention-item"'
    )
    return f"""
                <div {class_attr}>
                    <div class="attention-title">{icon} {title}</div>
                    <div class="attention-detail">{detail}</div>
                </div>"""


def _render_concept_item(concept: ConceptState) -> str:
    """Render a concept list item."""
    model_count = len(concept.models)
    if model_count > 0:
        meta = f"Models: {model_count}"
        if concept.owner:
            meta += f" | Owner: {concept.owner}"
    elif concept.owner:
        meta = f"Owner: {concept.owner}"
    else:
        meta = "No implementations"

    status = concept.status or "draft"
    return f"""
                    <div class="concept-item">
                        <div>
                            <div class="concept-name">{concept.name}</div>
                            <div class="concept-meta">{meta}</div>
                        </div>
                        <span class="concept-status {status}">{status}</span>
                    </div>"""


def _pluralize(count: int, singular: str) -> str:
    """Return singular or plural form based on count."""
    return f"{count} {singular}{'s' if count != 1 else ''}"


# =============================================================================
# Main Export Function
# =============================================================================


def export_coverage(state: ProjectState, output: TextIO) -> None:
    """Export coverage report as HTML dashboard.

    Args:
        state: Project state with concepts and relationships
        output: Text stream to write HTML to
    """
    stats = state.calculate_coverage_stats()
    domain_groups = state.concepts_by_domain()

    # Find incomplete concepts needing attention
    incomplete_concepts = [
        (cid, c)
        for cid, c in state.concepts.items()
        if c.status != "complete" and (not c.domain or not c.owner or not c.definition)
    ]

    # Write document head
    output.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dbt-conceptual Coverage Report</title>
{_CSS_STYLES}
</head>
<body>
    <div class="container">
        <h1>Coverage Report</h1>
        <p class="subtitle">Generated by dbt-conceptual</p>

        <div class="stats-grid">""")

    # Stats cards
    output.write(
        _render_stat_card(
            "Concept Completion",
            stats.completion_percent,
            f"{stats.complete_concepts} of {stats.total_concepts} concepts complete",
        )
    )
    output.write(
        _render_stat_card(
            "Model Coverage",
            stats.model_coverage_percent,
            f"{stats.concepts_with_models} concepts have models",
        )
    )
    output.write(
        _render_stat_card(
            "Relationships Complete",
            stats.relationship_percent,
            f"{stats.complete_relationships} of {stats.total_relationships} complete",
        )
    )

    output.write("""
        </div>
""")

    # Attention section
    _write_attention_section(output, stats, incomplete_concepts)

    # Concepts by domain section
    _write_concepts_section(output, state, domain_groups)

    # Orphan models section
    _write_orphans_section(output, state, stats)

    output.write("""
    </div>
</body>
</html>
""")


def _write_attention_section(
    output: TextIO,
    stats: CoverageStats,
    incomplete_concepts: list[tuple[str, ConceptState]],
) -> None:
    """Write the attention/needs work section."""
    if (
        not incomplete_concepts
        and stats.orphan_count == 0
        and stats.stub_concepts == 0
        and stats.draft_concepts == 0
    ):
        return

    output.write("""
        <section>
            <h2>Needs Attention</h2>
            <div class="attention-list">""")

    if stats.stub_concepts > 0:
        output.write(
            _render_attention_item(
                "\u26a0\ufe0f",
                _pluralize(stats.stub_concepts, "Stub Concept"),
                "These concepts were auto-generated and need definitions, owners, and domains.",
                "error",
            )
        )

    if stats.draft_concepts > 0:
        output.write(
            _render_attention_item(
                "\u25d0",
                _pluralize(stats.draft_concepts, "Draft Concept"),
                "These concepts have no implementing models yet.",
            )
        )

    if incomplete_concepts:
        # Build detail with missing attributes
        details = []
        for _cid, c in incomplete_concepts[:5]:
            missing = []
            if not c.domain:
                missing.append("domain")
            if not c.owner:
                missing.append("owner")
            if not c.definition:
                missing.append("definition")
            details.append(f"<strong>{c.name}</strong>: {', '.join(missing)}")
        detail_html = "<br>".join(details)
        if len(incomplete_concepts) > 5:
            detail_html += f"<br>...and {len(incomplete_concepts) - 5} more"

        output.write(
            _render_attention_item(
                "\ud83d\udcdd",
                _pluralize(len(incomplete_concepts), "Concept") + " Missing Attributes",
                detail_html,
            )
        )

    if stats.orphan_count > 0:
        output.write(
            _render_attention_item(
                "\ud83d\udd0d",
                _pluralize(stats.orphan_count, "Orphan Model"),
                "dbt models without concept tags. Run <code>dbt-conceptual sync</code> to discover them.",
            )
        )

    output.write("""
            </div>
        </section>
""")


def _write_concepts_section(
    output: TextIO,
    state: ProjectState,
    domain_groups: dict[str, list[tuple[str, ConceptState]]],
) -> None:
    """Write the concepts by domain section."""
    output.write("""
        <section>
            <h2>Concepts by Domain</h2>
""")

    for domain_id in sorted(domain_groups.keys()):
        concepts = domain_groups[domain_id]
        domain_name = domain_id
        if domain_id in state.domains:
            domain_name = (
                state.domains[domain_id].display_name or state.domains[domain_id].name
            )

        output.write(f"""
            <div class="domain-section">
                <div class="domain-header">{domain_name} ({len(concepts)})</div>
                <div class="concept-list">""")

        for _concept_id, concept in sorted(concepts, key=lambda x: x[1].name):
            output.write(_render_concept_item(concept))

        output.write("""
                </div>
            </div>
""")

    output.write("""
        </section>
""")


def _write_orphans_section(
    output: TextIO, state: ProjectState, stats: CoverageStats
) -> None:
    """Write the orphan models section."""
    if stats.orphan_count == 0:
        return

    output.write("""
        <section>
            <h2>Orphan Models</h2>
            <p style="color: #666; margin-bottom: 1rem; font-size: 0.875rem;">
                These models lack meta.concept tags.
            </p>
            <div class="orphan-list">""")

    for orphan in sorted(state.orphan_models, key=lambda o: o.name):
        output.write(f"""
                <div class="orphan-item">{orphan.name}</div>""")

    output.write("""
            </div>
        </section>
""")
