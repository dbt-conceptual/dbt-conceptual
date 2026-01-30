"""Git operations for dbt-conceptual.

Provides utilities for loading project state from git refs and computing diffs.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    ProjectState,
    RelationshipState,
)

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

    # Write base version to temp file and parse
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as temp_file:
        temp_file.write(result.stdout)
        temp_path = Path(temp_file.name)

    try:
        with open(temp_path) as f:
            base_data = yaml.safe_load(f) or {}

        base_state = ProjectState()

        # Populate base state (simplified - no dbt manifest needed for diff)
        for domain_id, domain_data in base_data.get("domains", {}).items():
            base_state.domains[domain_id] = DomainState(
                name=domain_id,
                display_name=domain_data.get("name", domain_id),
                color=domain_data.get("color"),
            )

        for concept_id, concept_data in base_data.get("concepts", {}).items():
            base_state.concepts[concept_id] = ConceptState(
                name=concept_data.get("name", concept_id),
                domain=concept_data.get("domain"),
                owner=concept_data.get("owner"),
                definition=concept_data.get("definition"),
                color=concept_data.get("color"),
                replaced_by=concept_data.get("replaced_by"),
            )

        for rel in base_data.get("relationships", []):
            verb = rel.get("verb", "")
            from_concept = rel.get("from", "")
            to_concept = rel.get("to", "")
            rel_key = f"{from_concept}:{verb}:{to_concept}"

            base_state.relationships[rel_key] = RelationshipState(
                verb=verb,
                from_concept=from_concept,
                to_concept=to_concept,
                cardinality=rel.get("cardinality"),
                definition=rel.get("definition"),
                domains=rel.get("domains", []),
                owner=rel.get("owner"),
                custom_name=rel.get("name"),
            )

        return base_state

    finally:
        # Clean up temp file
        temp_path.unlink()


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
