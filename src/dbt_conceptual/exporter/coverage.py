"""Coverage report exporter for conceptual models."""

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

    concepts_with_silver = sum(1 for c in state.concepts.values() if c.silver_models)
    concepts_with_gold = sum(1 for c in state.concepts.values() if c.gold_models)

    total_relationships = len(state.relationships)
    realized_relationships = sum(
        1 for r in state.relationships.values() if r.realized_by
    )

    orphan_count = len(state.orphan_models)

    # Calculate completion percentage
    completion_pct = (
        int((complete_concepts / total_concepts) * 100) if total_concepts > 0 else 0
    )
    silver_pct = (
        int((concepts_with_silver / total_concepts) * 100) if total_concepts > 0 else 0
    )
    gold_pct = (
        int((concepts_with_gold / total_concepts) * 100) if total_concepts > 0 else 0
    )
    relationship_pct = (
        int((realized_relationships / total_relationships) * 100)
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
        if c.status not in ["complete", "deprecated"]
        and (not c.domain or not c.owner or not c.definition)
    ]

    unrealized_relationships = [
        (rid, r) for rid, r in state.relationships.items() if not r.realized_by
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
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
            background: #fafafa;
            padding: 1.5rem;
            border-radius: 6px;
            border-left: 4px solid #4CAF50;
        }

        .stat-card.warning {
            border-left-color: #FF9800;
        }

        .stat-card.error {
            border-left-color: #f44336;
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
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }

        .progress-fill {
            height: 100%;
            background: #4CAF50;
            transition: width 0.3s ease;
        }

        .progress-fill.warning {
            background: #FF9800;
        }

        .progress-fill.error {
            background: #f44336;
        }

        section {
            margin-bottom: 3rem;
        }

        h2 {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #1a1a1a;
            border-bottom: 2px solid #f0f0f0;
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
            background: #fafafa;
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
            background: #FFF9E6;
            border-left: 4px solid #FF9800;
            padding: 1rem;
            border-radius: 4px;
        }

        .attention-item.error {
            background: #FFEBEE;
            border-left-color: #f44336;
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
            background: #fafafa;
            padding: 1rem;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
        }

        .orphan-item {
            padding: 0.5rem;
            border-bottom: 1px solid #e0e0e0;
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
                <div class="stat-label">Silver Coverage</div>
                <div class="stat-value">""")
    output.write(f"{silver_pct}%")
    output.write("""</div>
                <div class="stat-secondary">""")
    output.write(f"{concepts_with_silver} concepts implemented")
    output.write("""</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: """)
    output.write(f"{silver_pct}%")
    output.write(""""></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Gold Coverage</div>
                <div class="stat-value">""")
    output.write(f"{gold_pct}%")
    output.write("""</div>
                <div class="stat-secondary">""")
    output.write(f"{concepts_with_gold} concepts implemented")
    output.write("""</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: """)
    output.write(f"{gold_pct}%")
    output.write(""""></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Relationships Realized</div>
                <div class="stat-value">""")
    output.write(f"{relationship_pct}%")
    output.write("""</div>
                <div class="stat-secondary">""")
    output.write(f"{realized_relationships} of {total_relationships} have facts")
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
    if incomplete_concepts or unrealized_relationships or orphan_count > 0:
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
                    <div class="attention-detail">These concepts are in progress but not yet complete.</div>
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

        if unrealized_relationships:
            output.write("""
                <div class="attention-item warning">
                    <div class="attention-title">🔗 """)
            output.write(
                f"{len(unrealized_relationships)} Unrealized Relationship{'s' if len(unrealized_relationships) != 1 else ''}"
            )
            output.write("""</div>
                    <div class="attention-detail">These relationships have no fact tables implementing them yet.</div>
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
                    <div class="attention-detail">dbt models without concept or realizes tags. Run <code>dbt-conceptual sync</code> to discover them.</div>
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

            # Show model counts
            silver_count = len(concept.silver_models)
            gold_count = len(concept.gold_models)
            if silver_count > 0 or gold_count > 0:
                output.write(f"Silver: {silver_count} | Gold: {gold_count}")
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
                These models are in silver or gold layers but lack concept/realizes tags.
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
