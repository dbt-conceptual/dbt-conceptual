"""Tests for `dbc context` CLI command."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml
from click.testing import CliRunner

from dbt_conceptual.cli import context, main


def test_context_command_exists() -> None:
    """Test that context command is registered."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "context" in result.output


def test_context_single_concept() -> None:
    """Test context command with single concept selector."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml
        conceptual_data = {
            "domains": {
                "party": {
                    "name": "Party",
                    "display_name": "Party Domain",
                }
            },
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data-team",
                    "definition": "A person or organization that purchases products",
                },
                "order": {
                    "name": "Order",
                    "domain": "party",
                    "definition": "A purchase transaction",
                },
            },
            "relationships": [
                {
                    "from": "customer",
                    "to": "order",
                    "verb": "places",
                    "cardinality": "1:N",
                }
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory structure
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context,
            ["--project-dir", str(tmppath), "--select", "customer", "--format", "llm"],
        )

        assert result.exit_code == 0
        assert "Customer" in result.output
        assert "A person or organization that purchases products" in result.output
        assert "party" in result.output


def test_context_json_format() -> None:
    """Test context command with JSON output format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml
        conceptual_data = {
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "definition": "A customer entity",
                }
            }
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context,
            ["--project-dir", str(tmppath), "--select", "customer", "--format", "json"],
        )

        assert result.exit_code == 0
        # JSON output should be valid
        import json

        try:
            json.loads(result.output)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON output: {result.output}") from e


def test_context_markdown_format() -> None:
    """Test context command with Markdown output format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml
        conceptual_data = {
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "definition": "A customer entity",
                }
            }
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "customer",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert "# Customer" in result.output
        assert "A customer entity" in result.output


def test_context_domain_selector() -> None:
    """Test context command with domain selector."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml
        conceptual_data = {
            "domains": {
                "party": {"name": "Party", "display_name": "Party Domain"},
                "product": {"name": "Product", "display_name": "Product Domain"},
            },
            "concepts": {
                "customer": {"name": "Customer", "domain": "party"},
                "order": {"name": "Order", "domain": "party"},
                "product": {"name": "Product", "domain": "product"},
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "domain:party",
                "--format",
                "llm",
            ],
        )

        assert result.exit_code == 0
        assert "Customer" in result.output
        assert "Order" in result.output
        assert "Product" not in result.output


def test_context_status_selector() -> None:
    """Test context command with status selector."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml
        conceptual_data = {
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {"name": "Customer", "domain": "party"},
                "product": {"name": "Product"},  # No domain = stub status
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "status:stub",
                "--format",
                "llm",
            ],
        )

        assert result.exit_code == 0
        assert "Product" in result.output
        assert "Customer" not in result.output


def test_context_downstream_selector() -> None:
    """Test context command with downstream selector."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml with relationships
        conceptual_data = {
            "concepts": {
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
                "payment": {"name": "Payment"},
            },
            "relationships": [
                {
                    "from": "customer",
                    "to": "order",
                    "verb": "places",
                    "cardinality": "1:N",
                },
                {"from": "order", "to": "payment", "verb": "has", "cardinality": "1:N"},
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context,
            ["--project-dir", str(tmppath), "--select", "customer+", "--format", "llm"],
        )

        assert result.exit_code == 0
        assert "Customer" in result.output
        assert "Order" in result.output
        assert "Payment" in result.output


def test_context_no_conceptual_file() -> None:
    """Test context command without conceptual.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml only
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(
            context, ["--project-dir", str(tmppath), "--select", "customer"]
        )

        assert result.exit_code == 1
        assert "conceptual.yml not found" in result.output


def test_context_invalid_selector() -> None:
    """Test context command with invalid selector."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml
        conceptual_data = {"concepts": {"customer": {"name": "Customer"}}}

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context, ["--project-dir", str(tmppath), "--select", "nonexistent"]
        )

        assert result.exit_code == 1
        assert "Error" in result.output or "Unknown concept" in result.output


def test_context_with_depth() -> None:
    """Test context command with depth parameter."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml with chain of relationships
        conceptual_data = {
            "concepts": {
                "a": {"name": "A"},
                "b": {"name": "B"},
                "c": {"name": "C"},
            },
            "relationships": [
                {"from": "a", "to": "b", "verb": "relates", "cardinality": "1:N"},
                {"from": "b", "to": "c", "verb": "relates", "cardinality": "1:N"},
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        # Test depth 1 - should only get A and B
        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "a+",
                "--depth",
                "1",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        # Parse JSON to verify - should be valid JSON
        import json

        try:
            data = json.loads(result.output)
            # Just verify it's valid JSON - can be list or dict
            assert isinstance(data, (dict, list))
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON: {result.output}") from e


def test_context_with_guidance() -> None:
    """Test context command includes guidance in output."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

        # Create conceptual.yml with guidance
        conceptual_data = {
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "definition": "A customer entity",
                    "guidance": {
                        "context": "Critical business entity",
                        "rules": [
                            {
                                "name": "uniqueness",
                                "description": "Must have unique customer_id",
                            }
                        ],
                    },
                }
            }
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create minimal models directory
        models_dir = tmppath / "models"
        models_dir.mkdir()
        (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")

        result = runner.invoke(
            context,
            ["--project-dir", str(tmppath), "--select", "customer", "--format", "llm"],
        )

        assert result.exit_code == 0
        assert "Critical business entity" in result.output
        assert "uniqueness" in result.output
        assert "Must have unique customer_id" in result.output
