"""CLI for dbt-conceptual.

Exit Code Conventions
---------------------
This CLI uses the following exit code patterns:

- click.Abort(): User errors (missing file, bad config, invalid input)
  Results in exit code 1 with "Aborted!" message.

- SystemExit(0/1): Validation/check commands where the exit code
  signals pass/fail to CI systems. Used by `validate` command.

- click.exceptions.Exit(1): Commands that signal changes exist
  (for CI workflows that need to detect changes). Used by `diff --format github`.

- Normal return: Informational commands that complete successfully.
"""

import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, TextIO

import click
from rich.console import Console

from dbt_conceptual.cli_utils import (
    ConceptualFileNotFound,
    load_project_state,
    project_options,
)
from dbt_conceptual.config import Config
from dbt_conceptual.git import (
    GitNotFoundError,
    NotAGitRepoError,
    RefNotFoundError,
    compute_diff_from_ref,
)
from dbt_conceptual.parser import StateBuilder
from dbt_conceptual.state import ConceptState, ProjectState
from dbt_conceptual.validator import Severity, Validator

console = Console()

# Global quiet flag - set by main() based on --quiet option
_quiet_mode = False


def _print(message: str, style: Optional[str] = None) -> None:
    """Print message unless quiet mode is enabled.

    Args:
        message: Message to print
        style: Optional rich style (e.g., "green", "red")
    """
    if _quiet_mode:
        return
    if style:
        console.print(f"[{style}]{message}[/{style}]")
    else:
        console.print(message)


def _configure_logging(verbose: int, quiet: bool) -> None:
    """Configure logging based on verbosity flags.

    Args:
        verbose: Verbosity level (0=normal, 1=info, 2+=debug)
        quiet: If True, suppress all non-error output
    """
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format=(
            "%(levelname)s: %(message)s"
            if verbose < 2
            else "%(levelname)s: %(name)s: %(message)s"
        ),
    )


@click.group()
@click.version_option()
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity (use -vv for debug)"
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-error output")
@click.pass_context
def main(ctx: click.Context, verbose: int, quiet: bool) -> None:
    """dbt-conceptual: Bridge the gap between conceptual models and your lakehouse."""
    global _quiet_mode
    _quiet_mode = quiet
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    _configure_logging(verbose, quiet)


@main.command()
@project_options
def status(
    project_dir: Optional[Path],
    gold_paths: tuple[str, ...],
) -> None:
    """Show status of conceptual model coverage."""
    try:
        state, _config = load_project_state(
            project_dir=project_dir,
            gold_paths=list(gold_paths) if gold_paths else None,
        )
    except ConceptualFileNotFound as e:
        console.print(f"[red]Error: conceptual.yml not found at {e.path}[/red]")
        console.print("\nRun 'dbt-conceptual init' to create it.")
        raise click.Abort() from None

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
            status = rel.get_status(state.concepts)
            status_icon = "✓" if status == "complete" else "○"
            status_color = "green" if status == "complete" else "yellow"

            console.print(
                f"  [{status_color}]{status_icon}[/{status_color}] "
                f"{rel.name} ({rel.from_concept} → {rel.to_concept})"
            )

    # Display orphan models
    if state.orphan_models:
        console.print("\n[bold]Orphan Models[/bold]")
        console.print("=" * 50)
        console.print("[yellow]These models have no concept tags:[/yellow]")
        for model in state.orphan_models:
            console.print(f"  - {model.name}")
        console.print(
            "\n[dim]Tip: Run 'dbt-conceptual sync --create-stubs' to create stub concepts[/dim]"
        )

    # Summary: Concepts needing attention
    incomplete_concepts = [
        (cid, c)
        for cid, c in state.concepts.items()
        if c.status != "complete" and (not c.domain or not c.owner or not c.definition)
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
        console.print("\n[dim]Edit conceptual.yml to add missing attributes[/dim]")

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
    else:
        status_icon = "◐"
        status_color = "blue"

    # Model count badge
    model_count = len(concept.models)
    model_badge = f"[{model_count} model{'s' if model_count != 1 else ''}]"

    console.print(
        f"  [{status_color}]{status_icon}[/{status_color}] "
        f"{concept_id} [{concept.status}]  {model_badge}"
    )

    # Show missing attributes for any non-complete concept
    if concept.status != "complete":
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
@project_options
def orphans(
    project_dir: Optional[Path],
    gold_paths: tuple[str, ...],
) -> None:
    """List models with no meta.concept tag.

    Shows models that need conceptual tagging. Useful for tracking
    adoption and identifying where to focus next.
    """
    try:
        state, _config = load_project_state(
            project_dir=project_dir,
            gold_paths=list(gold_paths) if gold_paths else None,
        )
    except ConceptualFileNotFound as e:
        console.print(f"[red]Error: conceptual.yml not found at {e.path}[/red]")
        console.print("\nRun 'dbt-conceptual init' to create it.")
        raise click.Abort() from None

    # Display orphan models
    if not state.orphan_models:
        console.print("[green]✓ No orphan models found![/green]")
        console.print("\nAll models have conceptual tags (meta.concept).")
        return

    console.print(f"[bold]Orphan Models ({len(state.orphan_models)})[/bold]")
    console.print("=" * 70)
    console.print("[yellow]These models have no meta.concept tag:[/yellow]\n")

    for model in sorted(state.orphan_models, key=lambda m: m.name):
        console.print(f"  • {model.name}")

    console.print(
        "\n[dim]Next steps:[/dim]"
        "\n[dim]  1. Run 'dbt-conceptual sync --create-stubs' to create stub concepts[/dim]"
        "\n[dim]  2. Edit conceptual.yml to enrich the stubs[/dim]"
        "\n[dim]  3. Add meta.concept tags to model YAML files[/dim]"
    )


@main.command()
@project_options
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["human", "github", "markdown"], case_sensitive=False),
    default="human",
    help="Output format: human (default), github (GitHub Actions annotations), or markdown (job summary)",
)
@click.option(
    "--no-drafts",
    is_flag=True,
    default=False,
    help="Fail if any concepts or relationships are incomplete (stub/draft status)",
)
def validate(
    project_dir: Optional[Path],
    gold_paths: tuple[str, ...],
    output_format: str,
    no_drafts: bool,
) -> None:
    """Validate conceptual model correspondence (for CI)."""
    try:
        state, config = load_project_state(
            project_dir=project_dir,
            gold_paths=list(gold_paths) if gold_paths else None,
        )
    except ConceptualFileNotFound as e:
        if output_format == "github":
            print(f"::error file={e.path}::conceptual.yml not found")
        else:
            console.print(f"[red]Error: conceptual.yml not found at {e.path}[/red]")
            console.print("\nRun 'dbt-conceptual init' to create it.")
        raise click.Abort() from None

    # Run validation
    validator = Validator(config, state, no_drafts=no_drafts)
    issues = validator.validate()

    if output_format == "github":
        _output_github_format(config, validator, issues)
    elif output_format == "markdown":
        _output_markdown_format(config, validator, issues)
    else:
        _output_human_format(config, state, validator, issues)

    # Exit with appropriate code
    if validator.has_errors():
        if output_format == "human":
            console.print("\n[red]FAILED[/red]")
        raise SystemExit(1)
    else:
        if output_format == "human":
            console.print("\n[green]PASSED[/green]")
        raise SystemExit(0)


def _output_github_format(
    config: Config,
    validator: Validator,
    issues: list,
) -> None:
    """Output validation results in GitHub Actions annotation format."""
    conceptual_file = str(config.conceptual_file)

    for issue in issues:
        if issue.severity == Severity.ERROR:
            level = "error"
        elif issue.severity == Severity.WARNING:
            level = "warning"
        else:
            level = "notice"

        # GitHub Actions annotation format: ::level file=path::message
        print(f"::{level} file={conceptual_file}::[{issue.code}] {issue.message}")

    # Print summary
    summary = validator.get_summary()
    print(
        f"Validation complete: {summary['errors']} errors, "
        f"{summary['warnings']} warnings, {summary['info']} info"
    )


def _output_markdown_format(
    config: Config,
    validator: Validator,
    issues: list,
) -> None:
    """Output validation results in GitHub-flavored markdown format."""
    summary = validator.get_summary()

    if validator.has_errors():
        print("## ❌ Validation Failed\n")
    else:
        print("## ✅ Validation Passed\n")

    # Summary table
    print("| | Count |")
    print("|---|-----|")
    if summary["errors"]:
        print(f"| 🔴 Errors | {summary['errors']} |")
    if summary["warnings"]:
        print(f"| 🟡 Warnings | {summary['warnings']} |")
    if summary["info"]:
        print(f"| ℹ️  Info | {summary['info']} |")
    print()

    # Group issues by severity
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]

    # Errors
    if errors:
        print("### Errors\n")
        for issue in errors:
            print(f"> **{issue.code}** — {issue.message}")
            print(">")
        print()

    # Warnings
    if warnings:
        print("### Warnings\n")
        for issue in warnings:
            print(f"> **{issue.code}** — {issue.message}")
            print(">")
        print()

    # Info
    if infos:
        print("### Info\n")
        for issue in infos:
            print(f"> **{issue.code}** — {issue.message}")
            print(">")
        print()


def _output_human_format(
    config: Config,
    state: ProjectState,
    validator: Validator,
    issues: list,
) -> None:
    """Output validation results in human-readable format."""
    # Display concept coverage
    console.print("\n[bold]Concept Coverage[/bold]")
    console.print("=" * 80)

    for concept_id, concept in state.concepts.items():
        console.print(f"\n[cyan]{concept_id}[/cyan] ({concept.domain or 'no domain'})")

        if concept.models:
            console.print(f"  models: {', '.join(concept.models)}")
        else:
            console.print("  models: [dim]-[/dim]")

        # Status indicator
        if concept.status == "complete":
            status = "● complete"
            color = "green"
        elif concept.status == "stub":
            status = "◐ stub"
            color = "yellow"
        else:
            status = f"◐ {concept.status}"
            color = "blue"

        console.print(f"  status: [{color}]{status}[/{color}]")

    # Display relationships
    console.print("\n[bold]Relationships[/bold]")
    console.print("=" * 80)

    for rel_id, rel in state.relationships.items():
        console.print(f"\n{rel_id}")
        rel_status = rel.get_status(state.concepts)
        if rel_status == "complete":
            console.print(f"  [green]✓[/green] {rel.cardinality}")
        else:
            console.print("  [yellow]○ stub[/yellow]")

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

    # Create conceptual.yml in project root
    conceptual_file = project_dir / "conceptual.yml"
    if conceptual_file.exists():
        console.print(
            f"[yellow]conceptual.yml already exists at {conceptual_file}[/yellow]"
        )
    else:
        template = """# dbt-conceptual configuration
# All configuration lives in this file.

config:
  scan:
    gold:
      - models/marts/**/*.yml

  validation:
    defaults:
      orphan_models: warn
      unimplemented_concepts: warn
      missing_definitions: ignore
    # gold:
    #   orphan_models: error
    #   missing_definitions: warn

domains:
  # Define your domains here
  # Example:
  # sales:
  #   display_name: Sales
  #   color: "#4a9eff"
  #   owner: "@sales-team"

concepts:
  # Define your concepts here
  # Example:
  # Customer:
  #   domain: sales
  #   owner: "@data-team"
  #   definition: |
  #     A person or organization that purchases products.

relationships:
  # Define relationships between concepts here
  # Example:
  # - from: Customer
  #   verb: places
  #   to: Order
  #   cardinality: "1:N"
"""
        with open(conceptual_file, "w") as f:
            f.write(template)

        console.print(f"[green]✓[/green] Created {conceptual_file}")

    console.print("\n[green bold]Initialization complete![/green bold]")
    console.print("\nNext steps:")
    console.print("  1. Edit conceptual.yml to define your concepts")
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
        orphan_names = [o.name for o in orphans]
        if model in orphan_names:
            orphans = [o for o in orphans if o.name == model]
        else:
            console.print(f"[yellow]Model '{model}' is not an orphan[/yellow]")
            if model in [m for c in state.concepts.values() for m in c.models]:
                console.print(f"Model '{model}' is already mapped to a concept")
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
        console.print(f"  - {orphan.name}")

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
        concept_id = orphan.name
        for prefix in ["dim_", "fact_", "stg_", "fct_", "bridge_"]:
            if concept_id.startswith(prefix):
                concept_id = concept_id[len(prefix) :]
                break

        # Check if concept already exists
        if concept_id in conceptual_data["concepts"]:
            console.print(
                f"[yellow]Skipping {orphan.name}: concept '{concept_id}' already exists[/yellow]"
            )
            continue

        # Create stub with data from model if available
        stub_data: dict[str, object] = {
            "name": concept_id.replace("_", " ").title(),
        }

        # Use model description as definition if available
        if orphan.description:
            stub_data["definition"] = orphan.description

        # Use meta.domain if available
        if orphan.domain:
            stub_data["domain"] = orphan.domain

        conceptual_data["concepts"][concept_id] = {
            k: v for k, v in stub_data.items() if v is not None
        }
        stubs_created.append((orphan.name, concept_id))

    if not stubs_created:
        console.print("[yellow]No stubs created (concepts already exist)[/yellow]")
        return

    # Write back to file
    with open(config.conceptual_file, "w") as f:
        yaml.dump(conceptual_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"\n[green]✓ Created {len(stubs_created)} stub concept(s):[/green]")
    for model_name, concept_id in stubs_created:
        console.print(f"  - {concept_id} (from {model_name})")

    console.print(
        f"\n[green bold]Sync complete![/green bold] Updated {config.conceptual_file}"
    )
    console.print(
        "\nNext steps:\n  1. Add meta.concept tags to your dbt models\n  2. Enrich stub concepts with domain, owner, definition"
    )


# Valid type/format combinations matrix
EXPORT_MATRIX: dict[str, set[str]] = {
    "diagram": {"svg"},
    "coverage": {"html", "markdown", "json"},
    "bus-matrix": {"html", "markdown", "json"},
    "status": {"markdown", "json"},
    "orphans": {"markdown", "json"},
    "validation": {"markdown", "json"},
    "diff": {"markdown", "json"},
}


def _validate_export_combination(export_type: str, export_format: str) -> None:
    """Validate that the type/format combination is supported."""
    valid_formats = EXPORT_MATRIX.get(export_type, set())
    if export_format not in valid_formats:
        valid_str = ", ".join(sorted(valid_formats)) if valid_formats else "none"
        console.print(
            f"[red]Error: --type {export_type} does not support --format {export_format}[/red]"
        )
        console.print(f"[yellow]Valid formats for {export_type}: {valid_str}[/yellow]")
        console.print("\n[dim]Export matrix:[/dim]")
        for t, formats in EXPORT_MATRIX.items():
            console.print(f"  {t}: {', '.join(sorted(formats))}")
        raise click.Abort()


@main.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory",
)
@click.option(
    "--type",
    "export_type",
    type=click.Choice(
        [
            "diagram",
            "coverage",
            "bus-matrix",
            "status",
            "orphans",
            "validation",
            "diff",
        ],
        case_sensitive=False,
    ),
    required=True,
    help="What to export: diagram, coverage, bus-matrix, status, orphans, validation, diff",
)
@click.option(
    "--format",
    "export_format",
    type=click.Choice(
        ["svg", "html", "markdown", "json"],
        case_sensitive=False,
    ),
    required=True,
    help="Output format: svg, html, markdown, json",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout for text formats)",
)
@click.option(
    "--no-drafts",
    is_flag=True,
    default=False,
    help="For validation: fail if any concepts are incomplete",
)
@click.option(
    "--base",
    default=None,
    help="Base git ref for diff (required when --type diff)",
)
def export(
    project_dir: Optional[Path],
    export_type: str,
    export_format: str,
    output: Optional[Path],
    no_drafts: bool,
    base: Optional[str],
) -> None:
    """Export conceptual model to various formats.

    Use --type to specify what to export and --format to specify the output format.

    \b
    Export Matrix:
      diagram:     svg
      coverage:    html, markdown, json
      bus-matrix:  html, markdown, json
      status:      markdown, json
      orphans:     markdown, json
      validation:  markdown, json
      diff:        markdown, json (requires --base)

    \b
    Examples:
        dbt-conceptual export --type coverage --format html -o coverage.html
        dbt-conceptual export --type coverage --format markdown >> $GITHUB_STEP_SUMMARY
        dbt-conceptual export --type status --format json | jq '.summary'
        dbt-conceptual export --type validation --format markdown
        dbt-conceptual export --type diagram --format svg -o diagram.svg
        dbt-conceptual export --type diff --format markdown --base main
    """
    from dbt_conceptual.exporter import (
        export_bus_matrix,
        export_bus_matrix_json,
        export_bus_matrix_markdown,
        export_coverage,
        export_coverage_json,
        export_coverage_markdown,
        export_diagram_svg,
        export_orphans_json,
        export_orphans_markdown,
        export_status_json,
        export_status_markdown,
        export_validation_json,
        export_validation_markdown,
    )

    # Validate type/format combination
    _validate_export_combination(export_type, export_format)

    # Validate --base is provided for diff type
    if export_type == "diff" and not base:
        console.print("[red]Error: --base is required when --type diff[/red]")
        console.print(
            "[yellow]Example: dbt-conceptual export --type diff --format markdown --base main[/yellow]"
        )
        raise click.Abort()

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

    # Warn about SVG to stdout
    if export_type == "diagram" and export_format == "svg" and output is None:
        click.echo(
            "Warning: SVG output to stdout may cause display issues.",
            err=True,
        )
        click.echo("Consider using -o to write to a file.", err=True)

    # Export based on type and format (context manager ensures file is closed)
    try:
        with _get_output_stream(output) as out:
            if export_type == "diagram":
                if export_format == "svg":
                    export_diagram_svg(state, out)

            elif export_type == "coverage":
                if export_format == "html":
                    export_coverage(state, out)
                elif export_format == "markdown":
                    export_coverage_markdown(state, out)
                elif export_format == "json":
                    export_coverage_json(state, out)

            elif export_type == "bus-matrix":
                if export_format == "html":
                    export_bus_matrix(state, out)
                elif export_format == "markdown":
                    export_bus_matrix_markdown(state, out)
                elif export_format == "json":
                    export_bus_matrix_json(state, out)

            elif export_type == "status":
                if export_format == "markdown":
                    export_status_markdown(state, out)
                elif export_format == "json":
                    export_status_json(state, out)

            elif export_type == "orphans":
                if export_format == "markdown":
                    export_orphans_markdown(state, out)
                elif export_format == "json":
                    export_orphans_json(state, out)

            elif export_type == "validation":
                validator = Validator(config, state, no_drafts=no_drafts)
                issues = validator.validate()
                if export_format == "markdown":
                    export_validation_markdown(validator, issues, out)
                elif export_format == "json":
                    export_validation_json(validator, issues, out)

            elif export_type == "diff":
                # Diff requires computing against base ref
                try:
                    diff_result = compute_diff_from_ref(config, base)  # type: ignore
                except GitNotFoundError:
                    console.print(
                        "[red]Error: git not found. This command requires git.[/red]"
                    )
                    raise click.Abort() from None
                except NotAGitRepoError:
                    console.print("[red]Error: Not a git repository[/red]")
                    raise click.Abort() from None
                except RefNotFoundError as e:
                    console.print(
                        f"[red]Error: Could not find conceptual.yml at ref '{e.ref}'[/red]"
                    )
                    if e.stderr:
                        console.print(f"[dim]{e.stderr}[/dim]")
                    raise click.Abort() from None
                if export_format == "markdown":
                    from dbt_conceptual.diff_formatter import format_markdown

                    out.write(format_markdown(diff_result))
                    out.write("\n")
                elif export_format == "json":
                    from dbt_conceptual.diff_formatter import format_json

                    out.write(format_json(diff_result))
                    out.write("\n")

        if output:
            console.print(f"[green]✓ Exported to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error during export: {e}[/red]")
        raise click.Abort() from e


@contextmanager
def _get_output_stream(output: Optional[Path]) -> Generator[TextIO, None, None]:
    """Context manager for getting output stream.

    Properly handles file closing on exceptions.

    Args:
        output: Path to output file, or None for stdout

    Yields:
        File handle or sys.stdout
    """
    if output:
        f = open(output, "w")
        try:
            yield f
        finally:
            f.close()
    else:
        yield sys.stdout


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
@click.option(
    "--demo",
    is_flag=True,
    default=False,
    help="Launch with a self-contained demo project (no dbt project required)",
)
def serve(project_dir: Optional[Path], host: str, port: int, demo: bool) -> None:
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
        dbt-conceptual serve --demo

    Note:
        Port 5000 is often occupied by macOS AirPlay Receiver.
        Default is 8050 to avoid conflicts.
    """
    try:
        from dbt_conceptual.server import run_server
    except ImportError:
        console.print(
            "[red]Error: Server dependencies not installed.[/red]\n\n"
            "Install with:\n"
            "  pip install dbt-conceptual[serve]"
        )
        return

    # Handle demo mode
    demo_dir: Optional[Path] = None
    if demo:
        import atexit
        import shutil

        from dbt_conceptual.demo import create_demo_project

        demo_dir = create_demo_project()
        console.print("[magenta]🎭 DEMO MODE[/magenta]")
        console.print(f"[dim]Demo project created at: {demo_dir}[/dim]")
        console.print("[dim]Changes will not be persisted after exit.[/dim]\n")

        # Register cleanup on exit
        def cleanup_demo() -> None:
            if demo_dir and demo_dir.exists():
                shutil.rmtree(demo_dir, ignore_errors=True)

        atexit.register(cleanup_demo)

        # Use demo directory instead of project_dir
        project_dir = demo_dir

    console.print("[cyan]Starting dbt-conceptual UI server...[/cyan]")
    console.print(f"[cyan]Open your browser to: http://{host}:{port}[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        run_server(project_dir or Path.cwd(), host=host, port=port, demo_mode=demo)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")


@main.command()
@click.option(
    "--base",
    required=True,
    help="Base git ref to compare against (e.g., main, origin/main, HEAD~1)",
)
@click.option(
    "--format",
    type=click.Choice(["human", "github", "json", "markdown"], case_sensitive=False),
    default="human",
    help="Output format",
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to dbt project directory (default: current directory)",
)
def diff(base: str, format: str, project_dir: Optional[Path]) -> None:
    """Compare conceptual model against a base git ref.

    Shows what concepts, relationships, and domains have been added, removed,
    or modified compared to the base branch/commit.

    Examples:

        # Compare against main branch
        dbt-conceptual diff --base main

        # Compare against origin/main
        dbt-conceptual diff --base origin/main

        # GitHub Actions format
        dbt-conceptual diff --base ${{ github.base_ref }} --format github
    """
    from dbt_conceptual.diff_formatter import (
        format_github,
        format_human,
        format_json,
        format_markdown,
    )

    project_dir = project_dir or Path.cwd()

    # Load current state
    config = Config.load(project_dir=project_dir)
    if not config.conceptual_file.exists():
        console.print(
            f"[red]Error: conceptual.yml not found at {config.conceptual_file}[/red]"
        )
        console.print("\nRun 'dbt-conceptual init' to create it.")
        raise click.Abort()

    # Compute diff against base ref
    try:
        conceptual_diff = compute_diff_from_ref(config, base)
    except GitNotFoundError:
        console.print("[red]Error: git not found. This command requires git.[/red]")
        raise click.Abort() from None
    except NotAGitRepoError:
        console.print("[red]Error: Not a git repository[/red]")
        raise click.Abort() from None
    except RefNotFoundError as e:
        console.print(
            f"[red]Error: Could not find conceptual.yml at ref '{e.ref}'[/red]"
        )
        if e.stderr:
            console.print(f"[dim]{e.stderr}[/dim]")
        raise click.Abort() from None

    # Format and output
    if format == "human":
        output = format_human(conceptual_diff)
        console.print(output)
    elif format == "github":
        output = format_github(conceptual_diff)
        print(output)  # Use print for GitHub Actions format
    elif format == "json":
        output = format_json(conceptual_diff)
        print(output)
    elif format == "markdown":
        output = format_markdown(conceptual_diff)
        print(output)

    # Exit with error if there are changes and format is github
    # (so CI can optionally fail on changes)
    if format == "github" and conceptual_diff.has_changes:
        raise click.exceptions.Exit(1)


if __name__ == "__main__":
    main()
