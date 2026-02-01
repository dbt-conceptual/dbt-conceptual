"""Tests for export functionality."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from click.testing import CliRunner

from dbt_conceptual.cli import export


def test_cli_export_without_conceptual_file() -> None:
    """Test export command fails gracefully without conceptual.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create only dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(
            export,
            ["--project-dir", str(tmppath), "--type", "coverage", "--format", "json"],
        )

        assert result.exit_code != 0
        assert "conceptual.yml not found" in result.output


def test_cli_export_coverage_json_to_file() -> None:
    """Test export command writes coverage JSON to file."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml in project root
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create models
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}},
                    ],
                },
                f,
            )

        # Run export command with output file
        output_file = tmppath / "coverage.json"
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "coverage",
                "--format",
                "json",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Exported to" in result.output
        assert output_file.exists()

        # Check file content is valid JSON
        import json

        with open(output_file) as f:
            content = json.load(f)
            assert "summary" in content
            assert "concepts_by_domain" in content


def test_cli_export_bus_matrix_markdown_to_file() -> None:
    """Test export command writes bus matrix markdown to file."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml in project root
        conceptual_data = {
            "version": 1,
            "concepts": {"customer": {"name": "Customer"}, "order": {"name": "Order"}},
            "relationships": [{"verb": "places", "from": "customer", "to": "order"}],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Run export command with output file
        output_file = tmppath / "bus-matrix.md"
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "bus-matrix",
                "--format",
                "markdown",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Exported to" in result.output
        assert output_file.exists()

        # Check file content
        with open(output_file) as f:
            content = f.read()
            assert "Bus Matrix" in content
            assert "places" in content
