"""Shared CLI helpers and utilities."""

from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import click

from dbt_conceptual.config import Config
from dbt_conceptual.parser import StateBuilder
from dbt_conceptual.state import ProjectState

F = TypeVar("F", bound=Callable[..., Any])


class ConceptualFileNotFound(Exception):
    """Raised when conceptual.yml is not found."""

    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"conceptual.yml not found at {path}")


def load_project_state(
    project_dir: Optional[Path] = None,
    silver_paths: Optional[list[str]] = None,
    gold_paths: Optional[list[str]] = None,
) -> tuple[ProjectState, Config]:
    """Load project configuration and state.

    Args:
        project_dir: Path to dbt project directory (default: current directory)
        silver_paths: Override silver layer paths
        gold_paths: Override gold layer paths

    Returns:
        Tuple of (ProjectState, Config)

    Raises:
        ConceptualFileNotFound: If conceptual.yml doesn't exist
    """
    config = Config.load(
        project_dir=project_dir,
        silver_paths=silver_paths,
        gold_paths=gold_paths,
    )

    if not config.conceptual_file.exists():
        raise ConceptualFileNotFound(config.conceptual_file)

    builder = StateBuilder(config)
    state = builder.build()

    return state, config


def project_options(f: F) -> F:
    """Decorator that adds common project options to a command.

    Adds:
        --project-dir: Path to dbt project directory
        --silver-paths: Override silver layer paths (multiple)
        --gold-paths: Override gold layer paths (multiple)
    """

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
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def require_conceptual_yml(f: F) -> F:
    """Decorator that ensures conceptual.yml exists before running command.

    The decorated function must accept project_dir, silver_paths, and gold_paths
    arguments (typically added via @project_options).

    Injects 'state' and 'config' into the function kwargs if the function
    accepts them.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from rich.console import Console

        console = Console()

        project_dir = kwargs.get("project_dir")
        silver_paths = kwargs.get("silver_paths", ())
        gold_paths = kwargs.get("gold_paths", ())

        try:
            state, config = load_project_state(
                project_dir=project_dir,
                silver_paths=list(silver_paths) if silver_paths else None,
                gold_paths=list(gold_paths) if gold_paths else None,
            )
        except ConceptualFileNotFound as e:
            console.print(f"[red]Error: conceptual.yml not found at {e.path}[/red]")
            console.print("\nRun 'dbt-conceptual init' to create it.")
            raise click.Abort() from None

        # Inject state and config if the function accepts them
        import inspect

        sig = inspect.signature(f)
        if "state" in sig.parameters:
            kwargs["state"] = state
        if "config" in sig.parameters:
            kwargs["config"] = config

        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
