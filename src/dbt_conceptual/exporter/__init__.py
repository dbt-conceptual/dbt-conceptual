"""Export modules for dbt-conceptual.

Provides export functionality for various output formats (HTML, JSON, Markdown, SVG).
"""

from typing import Protocol, TextIO

from dbt_conceptual.exporter.bus_matrix import export_bus_matrix
from dbt_conceptual.exporter.coverage import export_coverage
from dbt_conceptual.exporter.formats import (
    export_bus_matrix_json,
    export_bus_matrix_markdown,
    export_coverage_json,
    export_coverage_markdown,
    export_orphans_json,
    export_orphans_markdown,
    export_status_json,
    export_status_markdown,
    export_validation_json,
    export_validation_markdown,
)
from dbt_conceptual.exporter.svg import export_diagram_svg

# Import state for type hints (avoiding circular imports)
from dbt_conceptual.state import ProjectState


class StateExporter(Protocol):
    """Protocol for exporters that take ProjectState and write to TextIO.

    This is the common pattern for most exporters:
    - coverage (HTML, JSON, Markdown)
    - bus_matrix (HTML, JSON, Markdown)
    - status (JSON, Markdown)
    - orphans (JSON, Markdown)
    - diagram (SVG)

    Example usage:
        def export_to_format(
            state: ProjectState,
            output: TextIO,
            exporter: StateExporter
        ) -> None:
            exporter(state, output)
    """

    def __call__(self, state: ProjectState, output: TextIO) -> None:
        """Export project state to the output stream."""
        ...


# Registry of state exporters by format
STATE_EXPORTERS: dict[str, dict[str, StateExporter]] = {
    "coverage": {
        "html": export_coverage,
        "json": export_coverage_json,
        "markdown": export_coverage_markdown,
    },
    "bus_matrix": {
        "html": export_bus_matrix,
        "json": export_bus_matrix_json,
        "markdown": export_bus_matrix_markdown,
    },
    "status": {
        "json": export_status_json,
        "markdown": export_status_markdown,
    },
    "orphans": {
        "json": export_orphans_json,
        "markdown": export_orphans_markdown,
    },
    "diagram": {
        "svg": export_diagram_svg,
    },
}


__all__ = [
    # Protocol
    "StateExporter",
    # Registry
    "STATE_EXPORTERS",
    # HTML exporters
    "export_coverage",
    "export_bus_matrix",
    # SVG exporters
    "export_diagram_svg",
    # JSON exporters
    "export_coverage_json",
    "export_bus_matrix_json",
    "export_status_json",
    "export_orphans_json",
    "export_validation_json",
    # Markdown exporters
    "export_coverage_markdown",
    "export_bus_matrix_markdown",
    "export_status_markdown",
    "export_orphans_markdown",
    "export_validation_markdown",
]
