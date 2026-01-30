"""Tests for git operations module."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest
import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.git import (
    GitNotFoundError,
    NotAGitRepoError,
    RefNotFoundError,
    compute_diff_from_ref,
    load_state_from_git_ref,
)


class TestLoadStateFromGitRef:
    """Tests for load_state_from_git_ref function."""

    def test_raises_git_not_found(self) -> None:
        """Test that GitNotFoundError is raised when git is not installed."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create minimal config
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump({"version": 1}, f)

            config = Config.load(project_dir=tmppath)

            # Mock subprocess.run to raise FileNotFoundError (git not found)
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError("git not found")

                with pytest.raises(GitNotFoundError) as exc_info:
                    load_state_from_git_ref(config, "main")

                assert "git not found" in str(exc_info.value)

    def test_raises_not_a_git_repo(self) -> None:
        """Test that NotAGitRepoError is raised when not in a git repo."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create minimal config
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump({"version": 1}, f)

            config = Config.load(project_dir=tmppath)

            # Mock subprocess.run to fail git rev-parse
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    128, "git", stderr=b"not a git repository"
                )

                with pytest.raises(NotAGitRepoError) as exc_info:
                    load_state_from_git_ref(config, "main")

                assert "Not a git repository" in str(exc_info.value)

    def test_raises_ref_not_found(self) -> None:
        """Test that RefNotFoundError is raised when ref doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create minimal config
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump({"version": 1}, f)

            config = Config.load(project_dir=tmppath)

            def mock_run(*args, **kwargs):  # type: ignore
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(returncode=0)
                elif "show" in cmd:
                    result = MagicMock()
                    result.returncode = 128
                    result.stderr = "fatal: Path 'conceptual.yml' does not exist"
                    return result
                return MagicMock(returncode=0)

            with patch("subprocess.run", side_effect=mock_run):
                with pytest.raises(RefNotFoundError) as exc_info:
                    load_state_from_git_ref(config, "nonexistent-branch")

                assert exc_info.value.ref == "nonexistent-branch"

    def test_loads_state_from_ref(self) -> None:
        """Test successfully loading state from a git ref."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create minimal config
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump({"version": 1}, f)

            config = Config.load(project_dir=tmppath)

            # Mock git output with conceptual model data
            mock_yaml = yaml.dump(
                {
                    "version": 1,
                    "domains": {"party": {"name": "Party", "color": "#E3F2FD"}},
                    "concepts": {
                        "customer": {
                            "name": "Customer",
                            "domain": "party",
                            "owner": "team-a",
                            "definition": "A customer",
                        }
                    },
                    "relationships": [
                        {
                            "verb": "places",
                            "from": "customer",
                            "to": "order",
                            "cardinality": "1:N",
                        }
                    ],
                }
            )

            def mock_run(*args, **kwargs):  # type: ignore
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(returncode=0)
                elif "show" in cmd:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = mock_yaml
                    return result
                return MagicMock(returncode=0)

            with patch("subprocess.run", side_effect=mock_run):
                state = load_state_from_git_ref(config, "main")

                assert "customer" in state.concepts
                assert state.concepts["customer"].name == "Customer"
                assert state.concepts["customer"].domain == "party"
                assert "party" in state.domains
                assert "customer:places:order" in state.relationships


class TestComputeDiffFromRef:
    """Tests for compute_diff_from_ref function."""

    def test_computes_diff(self) -> None:
        """Test computing diff between current and base state."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create dbt_project.yml
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            # Create current conceptual.yml
            current_data = {
                "version": 1,
                "concepts": {
                    "customer": {"name": "Customer", "domain": "party"},
                    "order": {"name": "Order"},  # New concept
                },
                "domains": {"party": {"name": "Party"}},
            }

            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump(current_data, f)

            config = Config.load(project_dir=tmppath)

            # Mock base state with only customer concept
            base_yaml = yaml.dump(
                {
                    "version": 1,
                    "concepts": {"customer": {"name": "Customer", "domain": "party"}},
                    "domains": {"party": {"name": "Party"}},
                }
            )

            def mock_run(*args, **kwargs):  # type: ignore
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(returncode=0)
                elif "show" in cmd:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = base_yaml
                    return result
                return MagicMock(returncode=0)

            with patch("subprocess.run", side_effect=mock_run):
                diff = compute_diff_from_ref(config, "main")

                # Should detect order as added
                assert diff.has_changes
                added_concepts = [
                    c for c in diff.concept_changes if c.change_type == "added"
                ]
                assert len(added_concepts) == 1
                assert added_concepts[0].key == "order"

    def test_no_changes(self) -> None:
        """Test diff when there are no changes."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create dbt_project.yml
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            # Create conceptual.yml
            data = {
                "version": 1,
                "concepts": {"customer": {"name": "Customer"}},
            }

            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump(data, f)

            config = Config.load(project_dir=tmppath)

            # Mock same content in base
            base_yaml = yaml.dump(data)

            def mock_run(*args, **kwargs):  # type: ignore
                cmd = args[0]
                if "rev-parse" in cmd:
                    return MagicMock(returncode=0)
                elif "show" in cmd:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = base_yaml
                    return result
                return MagicMock(returncode=0)

            with patch("subprocess.run", side_effect=mock_run):
                diff = compute_diff_from_ref(config, "main")

                assert not diff.has_changes


class TestExceptionClasses:
    """Tests for git exception classes."""

    def test_git_not_found_error(self) -> None:
        """Test GitNotFoundError exception."""
        exc = GitNotFoundError("git not found")
        assert "git not found" in str(exc)

    def test_not_a_git_repo_error(self) -> None:
        """Test NotAGitRepoError exception."""
        exc = NotAGitRepoError("not a repo")
        assert "not a repo" in str(exc)

    def test_ref_not_found_error(self) -> None:
        """Test RefNotFoundError exception."""
        exc = RefNotFoundError(
            ref="feature-branch",
            file_path="conceptual.yml",
            stderr="fatal: not found",
        )

        assert exc.ref == "feature-branch"
        assert exc.file_path == "conceptual.yml"
        assert exc.stderr == "fatal: not found"
        assert "feature-branch" in str(exc)
