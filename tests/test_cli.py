"""Tests for CLI commands."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from click.testing import CliRunner

from dbt_conceptual.cli import init, main, status, validate


def test_cli_main() -> None:
    """Test main CLI entry point."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "dbt-conceptual" in result.output
    assert "init" in result.output
    assert "status" in result.output
    assert "validate" in result.output


def test_cli_init() -> None:
    """Test init command creates files."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(init, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Initialization complete" in result.output

        # Check files were created
        conceptual_file = tmppath / "models" / "conceptual" / "conceptual.yml"
        layout_file = tmppath / "models" / "conceptual" / "layout.yml"

        assert conceptual_file.exists()
        assert layout_file.exists()


def test_cli_init_already_exists() -> None:
    """Test init command when files already exist."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Run init twice
        runner.invoke(init, ["--project-dir", str(tmppath)])
        result = runner.invoke(init, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "already exists" in result.output


def test_cli_status_no_conceptual_file() -> None:
    """Test status command without conceptual.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(status, ["--project-dir", str(tmppath)])

        assert result.exit_code == 1
        assert "conceptual.yml not found" in result.output


def test_cli_status_with_project() -> None:
    """Test status command with a valid project."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                    "status": "complete",
                }
            },
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create a gold model
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_customer", "meta": {"concept": "customer"}}],
                },
                f,
            )

        result = runner.invoke(status, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Concepts by Domain" in result.output
        assert "Party" in result.output
        assert "customer" in result.output


def test_cli_validate_no_errors() -> None:
    """Test validate command with no errors."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                    "status": "complete",
                }
            },
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create models
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_customer", "meta": {"concept": "customer"}}],
                },
                f,
            )

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        # Should have warnings but no errors
        assert "PASSED" in result.output


def test_cli_validate_with_errors() -> None:
    """Test validate command with validation errors."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationship
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer", "status": "complete"},
                "order": {"name": "Order", "status": "complete"},
            },
            "relationships": [{"name": "places", "from": "customer", "to": "order"}],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create fact that realizes relationship but endpoints aren't implemented
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "fact_orders", "meta": {"realizes": ["customer:places:order"]}}
                    ],
                },
                f,
            )

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        assert result.exit_code == 1
        assert "FAILED" in result.output
        assert "ERRORS" in result.output
