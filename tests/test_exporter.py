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

        result = runner.invoke(export, ["--project-dir", str(tmppath)])

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

        # Create conceptual.yml with various states
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party", "color": "#E3F2FD"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "team",
                    "definition": "A customer",
                    "status": "complete",
                },
                "order": {"name": "Order", "status": "stub"},
                "product": {"name": "Product", "status": "draft"},
            },
            "relationships": [
                {"name": "places", "from": "customer", "to": "order"},
            ],
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
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}},
                        {
                            "name": "fact_orders",
                            "meta": {"realizes": ["customer:places:order"]},
                        },
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
        assert "Silver Coverage" in result
        assert "Gold Coverage" in result
        assert "Relationships Realized" in result

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
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer", "status": "stub"},
                "order": {
                    "name": "Order",
                    "status": "draft",
                },  # Missing owner, definition, domain
            },
            "relationships": [
                {"name": "places", "from": "customer", "to": "order"},
            ],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
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
        assert "Missing Attributes" in result
        assert "Unrealized Relationship" in result


def test_cli_export_coverage_to_file() -> None:
    """Test export command writes coverage HTML to file."""
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
            "concepts": {"customer": {"name": "Customer", "status": "complete"}},
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Run export command with output file
        output_file = tmppath / "coverage.html"
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--format",
                "coverage",
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
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
                "product": {"name": "Product"},
            },
            "relationships": [
                {"name": "places", "from": "customer", "to": "order"},
                {"name": "contains", "from": "order", "to": "product"},
            ],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create fact models
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {
                            "name": "fact_orders",
                            "meta": {"realizes": ["customer:places:order"]},
                        },
                        {
                            "name": "fact_order_lines",
                            "meta": {
                                "realizes": [
                                    "customer:places:order",
                                    "order:contains:product",
                                ]
                            },
                        },
                    ],
                },
                f,
            )

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Export to string
        output = StringIO()
        export_bus_matrix(state, output)
        result = output.getvalue()

        # Verify HTML structure
        assert "<!DOCTYPE html>" in result
        assert "<title>dbt-conceptual Bus Matrix</title>" in result
        assert "Bus Matrix" in result

        # Verify fact tables shown
        assert "fact_orders" in result
        assert "fact_order_lines" in result

        # Verify relationships shown
        assert "customer:places:order" in result
        assert "order:contains:product" in result

        # Verify checkmarks present (facts realize relationships)
        assert "✓" in result


def test_export_bus_matrix_empty() -> None:
    """Test bus matrix with no fact tables."""
    from dbt_conceptual.exporter import export_bus_matrix

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with no realized relationships
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {"customer": {"name": "Customer"}},
            "relationships": [{"name": "places", "from": "customer", "to": "order"}],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        output = StringIO()
        export_bus_matrix(state, output)
        result = output.getvalue()

        # Verify empty state message
        assert "No fact tables found" in result
        assert "meta.realizes" in result


def test_cli_export_bus_matrix_to_file() -> None:
    """Test export command writes bus matrix HTML to file."""
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
            "concepts": {"customer": {"name": "Customer"}, "order": {"name": "Order"}},
            "relationships": [{"name": "places", "from": "customer", "to": "order"}],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create fact model
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {
                            "name": "fact_orders",
                            "meta": {"realizes": ["customer:places:order"]},
                        }
                    ],
                },
                f,
            )

        # Run export command with output file
        output_file = tmppath / "bus-matrix.html"
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--format",
                "bus-matrix",
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
            assert "Bus Matrix" in content
            assert "fact_orders" in content
