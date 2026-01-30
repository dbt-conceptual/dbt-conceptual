"""Coverage report exporter for conceptual models.

v1.0: Simplified model - single models[] array.
"""

from typing import TextIO

from dbt_conceptual.state import ConceptState, ProjectState


def export_coverage(state: ProjectState, output: TextIO) -> None:
    """Export coverage report as HTML dashboard.

    Args:
        state: Project state with concepts and relationships
        output: Text stream to write HTML to
    """
    # Calculate statistics
    total_concepts = len(state.concepts)
    complete_concepts = sum(
        1 for c in state.concepts.values() if c.status == "complete"
    )
    stub_concepts = sum(1 for c in state.concepts.values() if c.status == "stub")
    draft_concepts = sum(1 for c in state.concepts.values() if c.status == "draft")

    concepts_with_models = sum(1 for c in state.concepts.values() if c.models)

    total_relationships = len(state.relationships)
    complete_relationships = sum(
        1
        for r in state.relationships.values()
        if r.get_status(state.concepts) == "complete"
    )

    orphan_count = len(state.orphan_models)

    # Calculate completion percentage
    completion_pct = (
        int((complete_concepts / total_concepts) * 100) if total_concepts > 0 else 0
    )
    model_coverage_pct = (
        int((concepts_with_models / total_concepts) * 100) if total_concepts > 0 else 0
    )
    relationship_pct = (
        int((complete_relationships / total_relationships) * 100)
        if total_relationships > 0
        else 0
    )

    # Group concepts by domain
    domain_groups: dict[str, list[tuple[str, ConceptState]]] = {}
    for concept_id, concept in state.concepts.items():
        domain = concept.domain or "uncategorized"
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append((concept_id, concept))

    # Find attention items
    incomplete_concepts = [
        (cid, c)
        for cid, c in state.concepts.items()
        if c.status != "complete" and (not c.domain or not c.owner or not c.definition)
    ]

    # Write HTML
    output.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dbt-conceptual Coverage Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #fafaf9;
            color: #333333;
            line-height: 1.6;
            padding: 2rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 2rem;
        }

        h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: #1a1a1a;
        }

        .subtitle {
            color: #666;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }

        .stat-card {
            background: #f5f4f2;
            padding: 1.5rem;
            border-radius: 6px;
            border-left: 4px solid #4caf50;
        }

        .stat-card.warning {
            border-left-color: #e67e22;
        }

        .stat-card.error {
            border-left-color: #dc2626;
        }

        .stat-label {
            font-size: 0.875rem;
            color: #666;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1a1a1a;
        }

        .stat-secondary {
            font-size: 0.875rem;
            color: #666;
            margin-top: 0.5rem;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e8e6e3;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }

        .progress-fill {
            height: 100%;
            background: #4caf50;
            transition: width 0.3s ease;
        }

        .progress-fill.warning {
            background: #e67e22;
        }

        .progress-fill.error {
            background: #dc2626;
        }

        section {
            margin-bottom: 3rem;
        }

        h2 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #333333;
            border-bottom: 2px solid #e8e6e3;
            padding-bottom: 0.5rem;
        }

        .domain-section {
            margin-bottom: 2rem;
        }

        .domain-header {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: #333;
        }

        .concept-list {
            display: grid;
            gap: 0.75rem;
        }

        .concept-item {
            background: #f5f4f2;
            padding: 1rem;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .concept-name {
            font-weight: 500;
            color: #1a1a1a;
        }

        .concept-status {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .concept-status.complete {
            background: #C8E6C9;
            color: #2E7D32;
        }

        .concept-status.draft {
            background: #FFE0B2;
            color: #E65100;
        }

        .concept-status.stub {
            background: #FFCDD2;
            color: #C62828;
        }

        .concept-meta {
            font-size: 0.875rem;
            color: #666;
            margin-top: 0.5rem;
        }

        .attention-list {
            display: grid;
            gap: 1rem;
        }

        .attention-item {
            background: #fef5eb;
            border-left: 4px solid #e67e22;
            padding: 1rem;
            border-radius: 4px;
        }

        .attention-item.error {
            background: #fef2f2;
            border-left-color: #dc2626;
        }

        .attention-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #1a1a1a;
        }

        .attention-detail {
            font-size: 0.875rem;
            color: #666;
        }

        .orphan-list {
            background: #f5f4f2;
            padding: 1rem;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
        }

        .orphan-item {
            padding: 0.5rem;
            border-bottom: 1px solid #e8e6e3;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
        }

        .orphan-item:last-child {
            border-bottom: none;
        }

        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #999;
        }

        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Coverage Report</h1>
        <p class="subtitle">Generated by dbt-conceptual</p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Concept Completion</div>
                <div class="stat-value">""")
    output.write(f"{completion_pct}%")
    output.write("""</div>
                <div class="stat-secondary">""")
    output.write(f"{complete_concepts} of {total_concepts} concepts complete")
    output.write("""</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: """)
    output.write(f"{completion_pct}%")
    output.write(""""></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Model Coverage</div>
                <div class="stat-value">""")
    output.write(f"{model_coverage_pct}%")
    output.write("""</div>
                <div class="stat-secondary">""")
    output.write(f"{concepts_with_models} concepts have models")
    output.write("""</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: """)
    output.write(f"{model_coverage_pct}%")
    output.write(""""></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Relationships Complete</div>
                <div class="stat-value">""")
    output.write(f"{relationship_pct}%")
    output.write("""</div>
                <div class="stat-secondary">""")
    output.write(f"{complete_relationships} of {total_relationships} complete")
    output.write("""</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: """)
    output.write(f"{relationship_pct}%")
    output.write(""""></div>
                </div>
            </div>
        </div>
""")

    # Attention items
    if incomplete_concepts or orphan_count > 0:
        output.write("""
        <section>
            <h2>Needs Attention</h2>
            <div class="attention-list">
""")

        if stub_concepts > 0:
            output.write("""
                <div class="attention-item error">
                    <div class="attention-title">⚠️ """)
            output.write(
                f"{stub_concepts} Stub Concept{'s' if stub_concepts != 1 else ''}"
            )
            output.write("""</div>
                    <div class="attention-detail">These concepts were auto-generated and need definitions, owners, and domains.</div>
                </div>
""")

        if draft_concepts > 0:
            output.write("""
                <div class="attention-item warning">
                    <div class="attention-title">◐ """)
            output.write(
                f"{draft_concepts} Draft Concept{'s' if draft_concepts != 1 else ''}"
            )
            output.write("""</div>
                    <div class="attention-detail">These concepts have no implementing models yet.</div>
                </div>
""")

        if incomplete_concepts:
            output.write("""
                <div class="attention-item warning">
                    <div class="attention-title">📝 """)
            output.write(
                f"{len(incomplete_concepts)} Concept{'s' if len(incomplete_concepts) != 1 else ''} Missing Attributes"
            )
            output.write("""</div>
                    <div class="attention-detail">""")
            for _cid, c in incomplete_concepts[:5]:
                missing = []
                if not c.domain:
                    missing.append("domain")
                if not c.owner:
                    missing.append("owner")
                if not c.definition:
                    missing.append("definition")
                output.write(f"<strong>{c.name}</strong>: {', '.join(missing)}<br>")
            if len(incomplete_concepts) > 5:
                output.write(f"...and {len(incomplete_concepts) - 5} more")
            output.write("""</div>
                </div>
""")

        if orphan_count > 0:
            output.write("""
                <div class="attention-item">
                    <div class="attention-title">🔍 """)
            output.write(
                f"{orphan_count} Orphan Model{'s' if orphan_count != 1 else ''}"
            )
            output.write("""</div>
                    <div class="attention-detail">dbt models without concept tags. Run <code>dbt-conceptual sync</code> to discover them.</div>
                </div>
""")

        output.write("""
            </div>
        </section>
""")

    # Concepts by domain
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

        output.write("""
            <div class="domain-section">
                <div class="domain-header">""")
        output.write(domain_name)
        output.write(f" ({len(concepts)})")
        output.write("""</div>
                <div class="concept-list">
""")

        for _concept_id, concept in sorted(concepts, key=lambda x: x[1].name):
            output.write("""
                    <div class="concept-item">
                        <div>
                            <div class="concept-name">""")
            output.write(concept.name)
            output.write("""</div>
                            <div class="concept-meta">""")

            # Show model count
            model_count = len(concept.models)
            if model_count > 0:
                output.write(f"Models: {model_count}")
                if concept.owner:
                    output.write(f" | Owner: {concept.owner}")
            elif concept.owner:
                output.write(f"Owner: {concept.owner}")
            else:
                output.write("No implementations")

            output.write("""</div>
                        </div>
                        <span class="concept-status """)
            output.write(concept.status or "draft")
            output.write("""">""")
            output.write(concept.status or "draft")
            output.write("""</span>
                    </div>
""")

        output.write("""
                </div>
            </div>
""")

    output.write("""
        </section>
""")

    # Orphan models section
    if orphan_count > 0:
        output.write("""
        <section>
            <h2>Orphan Models</h2>
            <p style="color: #666; margin-bottom: 1rem; font-size: 0.875rem;">
                These models lack meta.concept tags.
            </p>
            <div class="orphan-list">
""")

        for orphan in sorted(state.orphan_models, key=lambda o: o.name):
            output.write("""
                <div class="orphan-item">""")
            output.write(orphan.name)
            output.write("""</div>
""")

        output.write("""
            </div>
        </section>
""")

    output.write("""
    </div>
</body>
</html>
""")
