"""Tests for export functionality."""

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from click.testing import CliRunner

from dbt_conceptual.cli import export
from dbt_conceptual.config import Config
from dbt_conceptual.parser import StateBuilder


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
            ["--project-dir", str(tmppath), "--type", "coverage", "--format", "html"],
        )

        assert result.exit_code != 0
        assert "conceptual.yml not found" in result.output


def test_export_coverage_basic() -> None:
    """Test basic coverage report HTML export."""
    from dbt_conceptual.exporter import export_coverage

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml in project root
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party", "color": "#E3F2FD"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "team",
                    "definition": "A customer",
                },
                "order": {"name": "Order"},  # stub (no domain)
                "product": {
                    "name": "Product",
                    "domain": "party",
                },  # draft (domain, no models)
            },
            "relationships": [
                {"verb": "places", "from": "customer", "to": "order"},
            ],
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

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Export to string
        output = StringIO()
        export_coverage(state, output)
        result = output.getvalue()

        # Verify HTML structure
        assert "<!DOCTYPE html>" in result
        assert "<title>dbt-conceptual Coverage Report</title>" in result
        assert "Concept Completion" in result
        assert "Model Coverage" in result

        # Verify concepts shown
        assert "Customer" in result
        assert "Order" in result
        assert "Product" in result

        # Verify status indicators
        assert "complete" in result
        assert "stub" in result
        assert "draft" in result


def test_export_coverage_with_attention_items() -> None:
    """Test coverage report shows attention items."""
    from dbt_conceptual.exporter import export_coverage

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},  # stub (no domain)
                "order": {
                    "name": "Order",
                    "domain": "sales",
                },  # draft (domain but no models)
            },
            "relationships": [
                {"verb": "places", "from": "customer", "to": "order"},
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        output = StringIO()
        export_coverage(state, output)
        result = output.getvalue()

        # Verify attention section exists
        assert "Needs Attention" in result
        assert "Stub Concept" in result


def test_cli_export_coverage_to_file() -> None:
    """Test export command writes coverage HTML to file."""
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
        output_file = tmppath / "coverage.html"
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "coverage",
                "--format",
                "html",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Exported to" in result.output
        assert output_file.exists()

        # Check file content is valid HTML
        with open(output_file) as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "Coverage Report" in content


def test_export_bus_matrix_basic() -> None:
    """Test basic bus matrix HTML export."""
    from dbt_conceptual.exporter import export_bus_matrix

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationships
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
                "product": {"name": "Product"},
            },
            "relationships": [
                {"verb": "places", "from": "customer", "to": "order"},
                {"verb": "contains", "from": "order", "to": "product"},
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Export to string
        output = StringIO()
        export_bus_matrix(state, output)
        result = output.getvalue()

        # Verify HTML structure
        assert "<!DOCTYPE html>" in result
        assert "Relationships" in result

        # Verify relationships shown
        assert "places" in result
        assert "contains" in result


def test_export_bus_matrix_empty() -> None:
    """Test bus matrix with no relationships."""
    from dbt_conceptual.exporter import export_bus_matrix

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with no relationships
        conceptual_data = {
            "version": 1,
            "concepts": {"customer": {"name": "Customer"}},
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        output = StringIO()
        export_bus_matrix(state, output)
        result = output.getvalue()

        # Verify empty state message
        assert "No relationships defined" in result


def test_cli_export_bus_matrix_to_file() -> None:
    """Test export command writes bus matrix HTML to file."""
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
        output_file = tmppath / "bus-matrix.html"
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "bus-matrix",
                "--format",
                "html",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Exported to" in result.output
        assert output_file.exists()

        # Check file content is valid HTML
        with open(output_file) as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "Relationships" in content
