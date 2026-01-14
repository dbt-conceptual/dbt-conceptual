"""Bus matrix exporter for conceptual models."""

from typing import TextIO

from dbt_conceptual.state import ProjectState


def export_bus_matrix(state: ProjectState, output: TextIO) -> None:
    """Export bus matrix as HTML table.

    The bus matrix shows which fact tables realize which relationships,
    following the Kimball dimensional modeling approach.

    Args:
        state: Project state with concepts and relationships
        output: Text stream to write HTML to
    """
    # Collect all fact tables (models that realize relationships)
    fact_tables: set[str] = set()
    for rel in state.relationships.values():
        if rel.realized_by:
            fact_tables.update(rel.realized_by)

    # Sort for consistent output
    fact_tables_list = sorted(fact_tables)
    relationships_list = sorted(
        state.relationships.items(), key=lambda x: (x[1].from_concept, x[1].name)
    )

    # Build matrix data
    matrix: dict[str, dict[str, bool]] = {}
    for fact in fact_tables_list:
        matrix[fact] = {}
        for rel_id, rel in relationships_list:
            matrix[fact][rel_id] = fact in (rel.realized_by or [])

    # Calculate statistics
    total_relationships = len(relationships_list)
    total_facts = len(fact_tables_list)
    total_realizations = sum(
        len(rel.realized_by) for rel in state.relationships.values() if rel.realized_by
    )

    output.write(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dbt-conceptual Bus Matrix</title>
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
            max-width: 100%;
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

        .info {
            background: #E3F2FD;
            border-left: 4px solid #2196F3;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 4px;
        }

        .info h2 {
            font-size: 1rem;
            margin-bottom: 0.5rem;
            color: #1565C0;
        }

        .info p {
            font-size: 0.875rem;
            color: #333;
            margin: 0;
        }

        .stats {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .stat {
            flex: 1;
            min-width: 150px;
        }

        .stat-label {
            font-size: 0.75rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.25rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1a1a1a;
        }

        .matrix-container {
            overflow-x: auto;
            margin-bottom: 2rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }

        th {
            background: #f5f5f5;
            padding: 1rem 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        th.rotate {
            height: 200px;
            white-space: nowrap;
            vertical-align: bottom;
            padding: 0;
        }

        th.rotate > div {
            transform: rotate(-45deg) translateY(50%);
            transform-origin: left bottom;
            width: 30px;
            padding-left: 0.5rem;
        }

        td {
            padding: 0.75rem;
            border-bottom: 1px solid #eee;
            text-align: center;
        }

        td.fact-name {
            text-align: left;
            font-weight: 500;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            background: #fafafa;
            position: sticky;
            left: 0;
            z-index: 5;
        }

        tr:hover td {
            background: #f9f9f9;
        }

        tr:hover td.fact-name {
            background: #f0f0f0;
        }

        .checkmark {
            display: inline-block;
            width: 20px;
            height: 20px;
            background: #4CAF50;
            border-radius: 50%;
            color: white;
            line-height: 20px;
            font-weight: bold;
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

        .legend {
            display: flex;
            gap: 2rem;
            padding: 1rem;
            background: #fafafa;
            border-radius: 4px;
            font-size: 0.875rem;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .legend-symbol {
            width: 20px;
            height: 20px;
            background: #4CAF50;
            border-radius: 50%;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Bus Matrix</h1>
        <p class="subtitle">Generated by dbt-conceptual</p>

        <div class="info">
            <h2>About the Bus Matrix</h2>
            <p>
                The bus matrix shows which fact tables realize which conceptual relationships.
                Each checkmark indicates that a fact table implements a specific relationship between concepts.
                This follows the Kimball dimensional modeling approach where fact tables tie dimensions together.
            </p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-label">Total Facts</div>
                <div class="stat-value">"""
    )
    output.write(str(total_facts))
    output.write(
        """</div>
            </div>
            <div class="stat">
                <div class="stat-label">Total Relationships</div>
                <div class="stat-value">"""
    )
    output.write(str(total_relationships))
    output.write(
        """</div>
            </div>
            <div class="stat">
                <div class="stat-label">Realizations</div>
                <div class="stat-value">"""
    )
    output.write(str(total_realizations))
    output.write(
        """</div>
            </div>
        </div>
"""
    )

    if not fact_tables_list:
        output.write(
            """
        <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <p>No fact tables found</p>
            <p style="font-size: 0.875rem; margin-top: 0.5rem; color: #999;">
                Add meta.realizes tags to your fact tables to populate the bus matrix
            </p>
        </div>
"""
        )
    else:
        output.write(
            """
        <div class="legend">
            <div class="legend-item">
                <span class="legend-symbol"></span>
                <span>Fact realizes this relationship</span>
            </div>
        </div>

        <div class="matrix-container">
            <table>
                <thead>
                    <tr>
                        <th>Fact Table</th>
"""
        )

        # Write relationship headers
        for _rel_id, rel in relationships_list:
            rel_label = f"{rel.from_concept}:{rel.name}:{rel.to_concept}"
            output.write(
                f"""                        <th class="rotate"><div>{rel_label}</div></th>
"""
            )

        output.write(
            """                    </tr>
                </thead>
                <tbody>
"""
        )

        # Write fact rows
        for fact in fact_tables_list:
            output.write(
                """                    <tr>
                        <td class="fact-name">"""
            )
            output.write(fact)
            output.write("</td>\n")

            for rel_id, _rel in relationships_list:
                if matrix[fact][rel_id]:
                    output.write(
                        """                        <td><span class="checkmark">✓</span></td>
"""
                    )
                else:
                    output.write(
                        """                        <td></td>
"""
                    )

            output.write(
                """                    </tr>
"""
            )

        output.write(
            """                </tbody>
            </table>
        </div>
"""
        )

    output.write(
        """    </div>
</body>
</html>
"""
    )
