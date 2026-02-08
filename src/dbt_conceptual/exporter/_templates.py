"""HTML/CSS template constants for HTML exporters.

Extracted from inline HTML/CSS in coverage.py and bus_matrix.py
to reduce file size and improve maintainability.
"""

# ---------------------------------------------------------------------------
# Shared base styles used across all HTML reports
# ---------------------------------------------------------------------------

_BASE_CSS = """\
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

        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #999;
        }

        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }"""


# ---------------------------------------------------------------------------
# Coverage report
# ---------------------------------------------------------------------------

COVERAGE_CSS = """\
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 2rem;
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
        }"""


# ---------------------------------------------------------------------------
# Bus matrix report
# ---------------------------------------------------------------------------

BUS_MATRIX_CSS = """\
        .container {
            max-width: 100%;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 2rem;
        }

        .info {
            background: #e8f4fd;
            border-left: 4px solid #2196F3;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 4px;
        }

        .info h2 {
            font-size: 1rem;
            margin-bottom: 0.5rem;
            color: #1976D2;
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
            background: #f5f4f2;
            padding: 1rem 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e8e6e3;
        }

        td {
            padding: 0.75rem;
            border-bottom: 1px solid #f0eeec;
        }

        tr:hover td {
            background: #fafaf9;
        }

        .status-complete {
            color: #4CAF50;
        }

        .status-stub {
            color: #e67e22;
        }"""


def html_head(title: str, extra_css: str) -> str:
    """Return the ``<!DOCTYPE html>`` through ``<body>`` opening tags.

    Args:
        title: Value for the ``<title>`` element.
        extra_css: Page-specific CSS rules appended after the base styles.
    """
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '    <meta charset="UTF-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"    <title>{title}</title>\n"
        "    <style>\n"
        f"{_BASE_CSS}\n\n{extra_css}\n"
        "    </style>\n"
        "</head>\n<body>"
    )


HTML_CLOSE = """    </div>
</body>
</html>
"""
