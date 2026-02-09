"""Git operations for dbt-conceptual.

Provides utilities for loading project state from git refs and computing diffs.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from dbt_conceptual.state import ProjectState

if TYPE_CHECKING:
    from dbt_conceptual.config import Config
    from dbt_conceptual.differ import ConceptualDiff


class GitError(Exception):
    """Error during git operations."""

    pass


class GitNotFoundError(GitError):
    """Git executable not found."""

    pass


class NotAGitRepoError(GitError):
    """Not a git repository."""

    pass


class RefNotFoundError(GitError):
    """Git ref or file not found."""

    def __init__(self, ref: str, file_path: str, stderr: str = ""):
        self.ref = ref
        self.file_path = file_path
        self.stderr = stderr
        super().__init__(f"Could not find {file_path} at ref '{ref}'")


def load_state_from_git_ref(config: "Config", base_ref: str) -> ProjectState:
    """Load ProjectState from a git ref.

    Args:
        config: Project configuration
        base_ref: Git ref to load from (e.g., 'main', 'origin/main', 'HEAD~1')

    Returns:
        ProjectState loaded from the git ref

    Raises:
        GitNotFoundError: If git is not installed
        NotAGitRepoError: If not in a git repository
        RefNotFoundError: If the ref or file doesn't exist
    """
    from dbt_conceptual.parser import StateBuilder

    project_dir = config.project_dir

    # Check if we're in a git repo
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise NotAGitRepoError("Not a git repository") from e
    except FileNotFoundError as e:
        raise GitNotFoundError("git not found. This command requires git.") from e

    # Get the conceptual.yml content from base ref
    conceptual_rel_path = config.conceptual_file.relative_to(project_dir)
    result = subprocess.run(
        ["git", "show", f"{base_ref}:{conceptual_rel_path}"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RefNotFoundError(
            ref=base_ref,
            file_path=str(conceptual_rel_path),
            stderr=result.stderr.strip(),
        )

    # Write base version to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as temp_file:
        temp_file.write(result.stdout)
        temp_path = Path(temp_file.name)

    try:
        # Create a temporary config that points to the temp file
        # StateBuilder will handle parsing the YAML and building the state
        temp_config = type(config)(
            project_dir=temp_path.parent,
            gold_paths=config.gold_paths,
            validation=config.validation,
        )

        # Override the conceptual_file property to point to our temp file
        # We do this by replacing the project_dir to make the relative path work
        temp_config.project_dir = temp_path.parent

        # Temporarily rename temp file to match expected name
        expected_path = temp_path.parent / "conceptual.yml"
        temp_path.rename(expected_path)
        temp_path = expected_path

        # Use StateBuilder to parse YAML into domain objects
        # Note: This will not scan dbt models, only load conceptual.yml structure
        builder = StateBuilder(temp_config)
        base_state = builder._parse_conceptual_yml(temp_path)

        return base_state

    finally:
        # Clean up temp file
        temp_path.unlink(missing_ok=True)


def compute_diff_from_ref(config: "Config", base_ref: str) -> "ConceptualDiff":
    """Compute diff between current state and base git ref.

    Args:
        config: Project configuration
        base_ref: Base git ref to compare against

    Returns:
        ConceptualDiff object with changes

    Raises:
        GitNotFoundError: If git is not installed
        NotAGitRepoError: If not in a git repository
        RefNotFoundError: If the ref or file doesn't exist
    """
    from dbt_conceptual.differ import compute_diff
    from dbt_conceptual.parser import StateBuilder

    # Load current state
    builder = StateBuilder(config)
    current_state = builder.build()

    # Load base state from git ref
    base_state = load_state_from_git_ref(config, base_ref)

    # Compute and return diff
    return compute_diff(base_state, current_state)
