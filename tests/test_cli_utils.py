"""Tests for CLI utilities."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import click
import pytest
import yaml

from dbt_conceptual.cli_utils import (
    ConceptualFileNotFound,
    load_project_state,
    project_options,
    require_conceptual_yml,
)


class TestLoadProjectState:
    """Tests for load_project_state function."""

    def test_load_basic_state(self) -> None:
        """Test loading a basic project state."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create dbt_project.yml
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            # Create conceptual.yml in project root
            conceptual_data = {
                "version": 1,
                "concepts": {
                    "customer": {"name": "Customer", "domain": "party"},
                },
                "domains": {
                    "party": {"name": "Party"},
                },
            }

            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump(conceptual_data, f)

            state, config = load_project_state(project_dir=tmppath)

            assert "customer" in state.concepts
            assert state.concepts["customer"].name == "Customer"
            assert config.project_dir == tmppath

    def test_raises_when_conceptual_file_missing(self) -> None:
        """Test that ConceptualFileNotFound is raised when file is missing."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create only dbt_project.yml
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            with pytest.raises(ConceptualFileNotFound) as exc_info:
                load_project_state(project_dir=tmppath)

            assert "conceptual.yml not found" in str(exc_info.value)
            assert exc_info.value.path.name == "conceptual.yml"

    def test_with_custom_gold_paths(self) -> None:
        """Test loading with custom gold paths."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create dbt_project.yml
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            # Create conceptual.yml in project root
            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump({"version": 1, "concepts": {}}, f)

            state, config = load_project_state(
                project_dir=tmppath,
                gold_paths=["models/custom_gold"],
            )

            # Verify config has custom paths
            assert "models/custom_gold" in config.gold_paths


class TestProjectOptions:
    """Tests for project_options decorator."""

    def test_adds_options_to_command(self) -> None:
        """Test that project_options adds the expected options."""

        @click.command()
        @project_options
        def test_cmd(
            project_dir: Path | None,
            gold_paths: tuple[str, ...],
        ) -> None:
            pass

        # Check that options exist
        param_names = [p.name for p in test_cmd.params]
        assert "project_dir" in param_names
        assert "gold_paths" in param_names

    def test_options_have_correct_types(self) -> None:
        """Test that options have correct types."""

        @click.command()
        @project_options
        def test_cmd(
            project_dir: Path | None,
            gold_paths: tuple[str, ...],
        ) -> None:
            pass

        params = {p.name: p for p in test_cmd.params}

        # gold_paths should be multiple
        assert params["gold_paths"].multiple is True


class TestRequireConceptualYml:
    """Tests for require_conceptual_yml decorator."""

    def test_injects_state_and_config(self) -> None:
        """Test that decorator injects state and config."""
        captured_state = None
        captured_config = None

        @require_conceptual_yml
        def test_func(
            project_dir: Path | None,
            gold_paths: tuple[str, ...],
            state: object | None = None,
            config: object | None = None,
        ) -> None:
            nonlocal captured_state, captured_config
            captured_state = state
            captured_config = config

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create dbt_project.yml
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            # Create conceptual.yml in project root
            with open(tmppath / "conceptual.yml", "w") as f:
                yaml.dump({"version": 1, "concepts": {}}, f)

            test_func(project_dir=tmppath, gold_paths=())

            assert captured_state is not None
            assert captured_config is not None

    def test_raises_abort_when_file_missing(self) -> None:
        """Test that decorator raises click.Abort when file is missing."""

        @require_conceptual_yml
        def test_func(
            project_dir: Path | None,
            gold_paths: tuple[str, ...],
        ) -> None:
            pass

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create only dbt_project.yml
            with open(tmppath / "dbt_project.yml", "w") as f:
                yaml.dump({"name": "test"}, f)

            with pytest.raises(click.Abort):
                test_func(project_dir=tmppath, gold_paths=())


class TestConceptualFileNotFound:
    """Tests for ConceptualFileNotFound exception."""

    def test_exception_message(self) -> None:
        """Test exception has correct message."""
        path = Path("/some/path/conceptual.yml")
        exc = ConceptualFileNotFound(path)

        assert "conceptual.yml not found at" in str(exc)
        assert str(path) in str(exc)
        assert exc.path == path
