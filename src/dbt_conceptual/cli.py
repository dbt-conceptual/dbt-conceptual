"""CLI for dbt-conceptual."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from dbt_conceptual.config import Config
from dbt_conceptual.parser import StateBuilder
from dbt_conceptual.state import ConceptState
from dbt_conceptual.validator import Severity, Validator

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """dbt-conceptual: Bridge the gap between conceptual models and your lakehouse."""
    pass


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory (default: current directory)",
)
@click.option(
    "--silver-paths",
    multiple=True,
    help="Override silver layer paths",
)
@click.option(
    "--gold-paths",
    multiple=True,
    help="Override gold layer paths",
)
def status(
    project_dir: Optional[Path],
    silver_paths: tuple[str, ...],
    gold_paths: tuple[str, ...],
) -> None:
    """Show status of conceptual model coverage."""
    # Load configuration
    config = Config.load(
        project_dir=project_dir,
        silver_paths=list(silver_paths) if silver_paths else None,
        gold_paths=list(gold_paths) if gold_paths else None,
    )

    # Check if conceptual.yml exists
    if not config.conceptual_file.exists():
        console.print(
            f"[red]Error: conceptual.yml not found at {config.conceptual_file}[/red]"
        )
        console.print("\nRun 'dbt-conceptual init' to create it.")
        raise click.Abort()

    # Build state
    builder = StateBuilder(config)
    state = builder.build()

    # Display concepts by domain
    console.print("\n[bold]Concepts by Domain[/bold]")
    console.print("=" * 50)

    if not state.domains:
        console.print("[yellow]No domains defined[/yellow]\n")
    else:
        for domain_id, domain in state.domains.items():
            # Count concepts in this domain
            domain_concepts = [
                (cid, c) for cid, c in state.concepts.items() if c.domain == domain_id
            ]

            console.print(
                f"\n[cyan]{domain.display_name}[/cyan] ({len(domain_concepts)} concepts)"
            )

            for concept_id, concept in domain_concepts:
                _print_concept_status(concept_id, concept)

    # Show concepts without domain
    no_domain = [(cid, c) for cid, c in state.concepts.items() if not c.domain]
    if no_domain:
        console.print("\n[cyan]No Domain[/cyan]")
        for concept_id, concept in no_domain:
            _print_concept_status(concept_id, concept)

    # Display relationships
    console.print("\n[bold]Relationships[/bold]")
    console.print("=" * 50)

    if not state.relationships:
        console.print("[yellow]No relationships defined[/yellow]")
    else:
        for _rel_id, rel in state.relationships.items():
            status_icon = "✓" if rel.realized_by else "○"
            status_color = "green" if rel.realized_by else "yellow"

            console.print(
                f"  [{status_color}]{status_icon}[/{status_color}] "
                f"{rel.name} ({rel.from_concept} → {rel.to_concept})"
            )

            if rel.realized_by:
                console.print(f"     realized by: {', '.join(rel.realized_by)}")

    # Display orphan models
    if state.orphan_models:
        console.print("\n[bold]Orphan Models[/bold]")
        console.print("=" * 50)
        console.print("[yellow]These models have no concept or realizes tags:[/yellow]")
        for model in state.orphan_models:
            console.print(f"  - {model}")
        console.print(
            "\n[dim]Tip: Run 'dbt-conceptual sync --create-stubs' to create stub concepts[/dim]"
        )

    # Summary: Concepts needing attention
    incomplete_concepts = [
        (cid, c)
        for cid, c in state.concepts.items()
        if c.status not in ["complete", "deprecated"]
        and (not c.domain or not c.owner or not c.definition)
    ]

    if incomplete_concepts:
        console.print("\n[bold]Concepts Needing Attention[/bold]")
        console.print("=" * 50)
        console.print(
            f"[yellow]{len(incomplete_concepts)} concept(s) missing required attributes:[/yellow]"
        )
        for concept_id, concept in incomplete_concepts:
            missing = []
            if not concept.domain:
                missing.append("domain")
            if not concept.owner:
                missing.append("owner")
            if not concept.definition:
                missing.append("definition")

            console.print(
                f"  • {concept_id} [{concept.status}] - missing: {', '.join(missing)}"
            )
        console.print(
            "\n[dim]Edit models/conceptual/conceptual.yml to add missing attributes[/dim]"
        )

    console.print()


def _print_concept_status(concept_id: str, concept: ConceptState) -> None:
    """Print status line for a concept."""

    # Status icon
    if concept.status == "complete":
        status_icon = "✓"
        status_color = "green"
    elif concept.status == "stub":
        status_icon = "⚠"
        status_color = "yellow"
    elif concept.status == "deprecated":
        status_icon = "✗"
        status_color = "red"
    else:
        status_icon = "◐"
        status_color = "blue"

    # Coverage badges
    s_count = len(concept.silver_models)
    g_count = len(concept.gold_models)
    s_badge = f"[S:{'●' * min(s_count, 3)}{'○' * (3 - min(s_count, 3))}]"
    g_badge = f"[G:{'●' * min(g_count, 3)}{'○' * (3 - min(g_count, 3))}]"

    console.print(
        f"  [{status_color}]{status_icon}[/{status_color}] "
        f"{concept_id} [{concept.status}]  {s_badge} {g_badge}"
    )

    # Show missing attributes for any non-complete, non-deprecated concept
    if concept.status not in ["complete", "deprecated"]:
        missing = []
        if not concept.domain:
            missing.append("domain")
        if not concept.owner:
            missing.append("owner")
        if not concept.definition:
            missing.append("definition")
        if missing:
            console.print(f"     [dim]missing: {', '.join(missing)}[/dim]")


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory (default: current directory)",
)
@click.option(
    "--silver-paths",
    multiple=True,
    help="Override silver layer paths",
)
@click.option(
    "--gold-paths",
    multiple=True,
    help="Override gold layer paths",
)
def validate(
    project_dir: Optional[Path],
    silver_paths: tuple[str, ...],
    gold_paths: tuple[str, ...],
) -> None:
    """Validate conceptual model correspondence (for CI)."""
    # Load configuration
    config = Config.load(
        project_dir=project_dir,
        silver_paths=list(silver_paths) if silver_paths else None,
        gold_paths=list(gold_paths) if gold_paths else None,
    )

    # Check if conceptual.yml exists
    if not config.conceptual_file.exists():
        console.print(
            f"[red]Error: conceptual.yml not found at {config.conceptual_file}[/red]"
        )
        console.print("\nRun 'dbt-conceptual init' to create it.")
        raise click.Abort()

    # Build state
    builder = StateBuilder(config)
    state = builder.build()

    # Run validation
    validator = Validator(config, state)
    issues = validator.validate()

    # Display concept coverage
    console.print("\n[bold]Concept Coverage[/bold]")
    console.print("=" * 80)

    for concept_id, concept in state.concepts.items():
        console.print(f"\n[cyan]{concept_id}[/cyan] ({concept.domain or 'no domain'})")

        if concept.silver_models:
            console.print(f"  silver: {', '.join(concept.silver_models)}")
        else:
            console.print("  silver: [dim]-[/dim]")

        if concept.gold_models:
            console.print(f"  gold: {', '.join(concept.gold_models)}")
        else:
            console.print("  gold: [dim]-[/dim]")

        # Status indicator
        if concept.status == "complete":
            status = "● complete"
            color = "green"
        elif concept.status == "stub":
            status = "◐ stub"
            color = "yellow"
        elif concept.status == "deprecated":
            status = "✗ deprecated"
            color = "red"
        else:
            status = f"◐ {concept.status}"
            color = "blue"

        # Special status for gold-only
        if concept.gold_models and not concept.silver_models:
            status = "◑ gold only"
            color = "yellow"

        console.print(f"  status: [{color}]{status}[/{color}]")

    # Display relationships
    console.print("\n[bold]Relationships[/bold]")
    console.print("=" * 80)

    for rel_id, rel in state.relationships.items():
        console.print(f"\n{rel_id}")

        if rel.realized_by:
            console.print(
                f"  [green]✓[/green] realized by: {', '.join(rel.realized_by)}"
            )
        else:
            console.print("  [red]✗ NOT REALIZED[/red]")

    # Display validation issues
    if issues:
        console.print("\n[bold]Validation Issues[/bold]")
        console.print("=" * 80)

        # Group by severity
        errors = [i for i in issues if i.severity == Severity.ERROR]
        warnings = [i for i in issues if i.severity == Severity.WARNING]
        infos = [i for i in issues if i.severity == Severity.INFO]

        if errors:
            console.print("\n[red bold]✗ ERRORS[/red bold]")
            for issue in errors:
                console.print(f"  [{issue.code}] {issue.message}")

        if warnings:
            console.print("\n[yellow bold]⚠ WARNINGS[/yellow bold]")
            for issue in warnings:
                console.print(f"  [{issue.code}] {issue.message}")

        if infos:
            console.print("\n[blue bold]ℹ INFO[/blue bold]")
            for issue in infos:
                console.print(f"  [{issue.code}] {issue.message}")

    # Summary
    summary = validator.get_summary()
    console.print(
        f"\n[bold]Summary:[/bold] "
        f"{summary['errors']} errors, "
        f"{summary['warnings']} warnings, "
        f"{summary['info']} info"
    )

    # Exit with appropriate code
    if validator.has_errors():
        console.print("\n[red]FAILED[/red]")
        raise SystemExit(1)
    else:
        console.print("\n[green]PASSED[/green]")
        raise SystemExit(0)


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory (default: current directory)",
)
def init(project_dir: Optional[Path]) -> None:
    """Initialize dbt-conceptual in a dbt project."""
    if project_dir is None:
        project_dir = Path.cwd()

    # Check if dbt_project.yml exists
    dbt_project = project_dir / "dbt_project.yml"
    if not dbt_project.exists():
        console.print(f"[red]Error: dbt_project.yml not found in {project_dir}[/red]")
        console.print("Make sure you're in a dbt project directory.")
        raise click.Abort()

    # Create conceptual directory
    conceptual_dir = project_dir / "models" / "conceptual"
    conceptual_dir.mkdir(parents=True, exist_ok=True)

    # Create conceptual.yml
    conceptual_file = conceptual_dir / "conceptual.yml"
    if conceptual_file.exists():
        console.print(
            f"[yellow]conceptual.yml already exists at {conceptual_file}[/yellow]"
        )
    else:
        template = """version: 1

metadata:
  name: "My Data Platform"

domains:
  # Define your domains here
  # Example:
  # party:
  #   name: "Party"
  #   color: "#E3F2FD"

concepts:
  # Define your concepts here
  # Example:
  # customer:
  #   name: "Customer"
  #   domain: party
  #   owner: data_team
  #   definition: "A person or organization that purchases products"
  #   status: complete

relationships:
  # Define relationships between concepts here
  # Example:
  # - name: places
  #   from: customer
  #   to: order
  #   cardinality: "1:N"
"""
        with open(conceptual_file, "w") as f:
            f.write(template)

        console.print(f"[green]✓[/green] Created {conceptual_file}")

    # Create layout.yml
    layout_file = conceptual_dir / "layout.yml"
    if not layout_file.exists():
        layout_template = """version: 1

positions:
  # Visual positions for the viewer
  # Example:
  # customer:
  #   x: 100
  #   y: 100
"""
        with open(layout_file, "w") as f:
            f.write(layout_template)

        console.print(f"[green]✓[/green] Created {layout_file}")

    console.print("\n[green bold]Initialization complete![/green bold]")
    console.print("\nNext steps:")
    console.print("  1. Edit models/conceptual/conceptual.yml to define your concepts")
    console.print("  2. Add meta.concept tags to your dbt models")
    console.print("  3. Run 'dbt-conceptual status' to see coverage")


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory (default: current directory)",
)
@click.option(
    "--create-stubs",
    is_flag=True,
    help="Create stub concepts for orphan models",
)
@click.option(
    "--model",
    help="Sync only a specific model by name",
)
def sync(project_dir: Optional[Path], create_stubs: bool, model: Optional[str]) -> None:
    """Discover dbt models and sync with conceptual model."""
    # Load configuration
    config = Config.load(project_dir=project_dir)

    # Check if conceptual.yml exists
    if not config.conceptual_file.exists():
        console.print(
            f"[red]Error: conceptual.yml not found at {config.conceptual_file}[/red]"
        )
        console.print("\nRun 'dbt-conceptual init' to create it.")
        raise click.Abort()

    # Build state
    builder = StateBuilder(config)
    state = builder.build()

    # Filter orphan models
    orphans = state.orphan_models
    if model:
        # Filter to specific model
        if model in orphans:
            orphans = [model]
        else:
            console.print(f"[yellow]Model '{model}' is not an orphan[/yellow]")
            if model in [m for c in state.concepts.values() for m in c.gold_models]:
                console.print(
                    f"Model '{model}' is already mapped to a concept in gold layer"
                )
            elif model in [m for c in state.concepts.values() for m in c.silver_models]:
                console.print(
                    f"Model '{model}' is already mapped to a concept in silver layer"
                )
            else:
                console.print(f"Model '{model}' not found in project")
            return

    if not orphans:
        console.print("[green]No orphan models found![/green]")
        console.print("All models are mapped to concepts.")
        return

    # Display orphans
    console.print(f"\n[bold]Found {len(orphans)} orphan model(s):[/bold]")
    for orphan in orphans:
        console.print(f"  - {orphan}")

    if not create_stubs:
        console.print(
            "\n[yellow]Tip:[/yellow] Use --create-stubs to automatically create stub concepts"
        )
        return

    # Create stubs
    import yaml

    # Read existing conceptual.yml
    with open(config.conceptual_file) as f:
        conceptual_data = yaml.safe_load(f) or {}

    if "concepts" not in conceptual_data:
        conceptual_data["concepts"] = {}

    # Create stub for each orphan
    stubs_created = []
    for orphan in orphans:
        # Generate concept ID from model name
        # Strip prefixes like dim_, fact_, stg_
        concept_id = orphan
        for prefix in ["dim_", "fact_", "stg_", "fct_", "bridge_"]:
            if concept_id.startswith(prefix):
                concept_id = concept_id[len(prefix) :]
                break

        # Check if concept already exists
        if concept_id in conceptual_data["concepts"]:
            console.print(
                f"[yellow]Skipping {orphan}: concept '{concept_id}' already exists[/yellow]"
            )
            continue

        # Create stub
        conceptual_data["concepts"][concept_id] = {
            "name": concept_id.replace("_", " ").title(),
            "status": "stub",
        }
        stubs_created.append((orphan, concept_id))

    if not stubs_created:
        console.print("[yellow]No stubs created (concepts already exist)[/yellow]")
        return

    # Write back to file
    with open(config.conceptual_file, "w") as f:
        yaml.dump(conceptual_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"\n[green]✓ Created {len(stubs_created)} stub concept(s):[/green]")
    for orphan, concept_id in stubs_created:
        console.print(f"  - {concept_id} (from {orphan})")

    console.print(
        f"\n[green bold]Sync complete![/green bold] Updated {config.conceptual_file}"
    )
    console.print(
        "\nNext steps:\n  1. Add meta.concept tags to your dbt models\n  2. Enrich stub concepts with domain, owner, definition"
    )


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory",
)
@click.option(
    "--format",
    type=click.Choice(
        ["mermaid", "excalidraw", "png", "coverage", "bus-matrix"],
        case_sensitive=False,
    ),
    default="mermaid",
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout)",
)
def export(project_dir: Optional[Path], format: str, output: Optional[Path]) -> None:
    """Export conceptual model to various formats.

    Examples:
        dbt-conceptual export --format mermaid
        dbt-conceptual export --format mermaid -o diagram.mmd
        dbt-conceptual export --format excalidraw -o diagram.excalidraw
        dbt-conceptual export --format png -o diagram.png
        dbt-conceptual export --format coverage -o coverage.html
        dbt-conceptual export --format bus-matrix -o bus-matrix.html
    """
    from dbt_conceptual.exporter import (
        export_bus_matrix,
        export_coverage,
        export_excalidraw,
        export_mermaid,
        export_png,
    )

    config = Config.load(project_dir=project_dir)

    # Check conceptual.yml exists
    if not config.conceptual_file.exists():
        console.print(
            f"[red]Error: conceptual.yml not found at {config.conceptual_file}[/red]"
        )
        console.print(
            "\n[yellow]Tip:[/yellow] Run 'dbt-conceptual init' to create a new conceptual model"
        )
        raise click.Abort()

    # Build state
    builder = StateBuilder(config)
    state = builder.build()

    # Export based on format
    if format == "mermaid":
        if output:
            with open(output, "w") as f:
                export_mermaid(state, f)
            console.print(f"[green]✓ Exported to {output}[/green]")
        else:
            import sys

            export_mermaid(state, sys.stdout)
    elif format == "excalidraw":
        if output:
            with open(output, "w") as f:
                export_excalidraw(state, f)
            console.print(f"[green]✓ Exported to {output}[/green]")
        else:
            import sys

            export_excalidraw(state, sys.stdout)
    elif format == "coverage":
        if output:
            with open(output, "w") as f:
                export_coverage(state, f)
            console.print(f"[green]✓ Exported to {output}[/green]")
        else:
            import sys

            export_coverage(state, sys.stdout)
    elif format == "bus-matrix":
        if output:
            with open(output, "w") as f:
                export_bus_matrix(state, f)
            console.print(f"[green]✓ Exported to {output}[/green]")
        else:
            import sys

            export_bus_matrix(state, sys.stdout)
    elif format == "png":
        if not output:
            console.print(
                "[red]Error: PNG export requires an output file (-o option)[/red]"
            )
            raise click.Abort()
        with open(output, "wb") as f:
            export_png(state, f)
        console.print(f"[green]✓ Exported to {output}[/green]")


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory (default: current directory)",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to (default: 127.0.0.1)",
)
@click.option(
    "--port",
    default=8050,
    type=int,
    help="Port to bind to (default: 8050)",
)
def serve(project_dir: Optional[Path], host: str, port: int) -> None:
    """Launch the interactive web UI for editing conceptual models.

    This starts a local web server with a visual editor for your conceptual
    model. The editor supports:

    - Interactive graph visualization of concepts and relationships
    - Drag-and-drop editing
    - Direct saving to conceptual.yml
    - Integrated coverage and bus matrix views

    Examples:
        dbt-conceptual serve
        dbt-conceptual serve --port 8080
        dbt-conceptual serve --host 0.0.0.0 --port 3000

    Note:
        Port 5000 is often occupied by macOS AirPlay Receiver.
        Default is 8050 to avoid conflicts.
    """
    try:
        from dbt_conceptual.server import run_server
    except ImportError:
        console.print(
            "[red]Error: Flask is not installed. Install with:[/red]\n"
            "  pip install dbt-conceptual[serve]\n"
            "or:\n"
            "  pip install flask"
        )
        return

    console.print("[cyan]Starting dbt-conceptual UI server...[/cyan]")
    console.print(f"[cyan]Open your browser to: http://{host}:{port}[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        run_server(project_dir or Path.cwd(), host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")


if __name__ == "__main__":
    main()
