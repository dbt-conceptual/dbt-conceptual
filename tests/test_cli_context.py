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


def _create_test_project(tmppath: Path, conceptual_data: dict[str, Any]) -> None:
    """Helper to create a minimal dbt project with given conceptual data.

    Args:
        tmppath: Path to the temp directory
        conceptual_data: Data for conceptual.yml
    """
    with open(tmppath / "dbt_project.yml", "w") as f:
        yaml.dump({"name": "test", "vars": {"dbt_conceptual": {}}}, f)

    with open(tmppath / "conceptual.yml", "w") as f:
        yaml.dump(conceptual_data, f)

    models_dir = tmppath / "models"
    models_dir.mkdir(exist_ok=True)
    (models_dir / "schema.yml").write_text("version: 2\nmodels: []\n")


def test_context_default_format_is_llm() -> None:
    """Test that the default format is llm when --format is omitted."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "concepts": {
                    "customer": {
                        "name": "Customer",
                        "definition": "A customer entity",
                    }
                }
            },
        )

        # Invoke without --format (should default to llm)
        result = runner.invoke(
            context,
            ["--project-dir", str(tmppath), "--select", "customer"],
        )

        assert result.exit_code == 0
        # LLM format includes "# Concept:" header
        assert "# Concept: Customer" in result.output


def test_context_all_selector() -> None:
    """Test context command with 'all' selector returns all concepts."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "concepts": {
                    "customer": {"name": "Customer"},
                    "order": {"name": "Order"},
                    "product": {"name": "Product"},
                }
            },
        )

        result = runner.invoke(
            context,
            ["--project-dir", str(tmppath), "--select", "all", "--format", "llm"],
        )

        assert result.exit_code == 0
        assert "Customer" in result.output
        assert "Order" in result.output
        assert "Product" in result.output


def test_context_upstream_selector() -> None:
    """Test context command with upstream selector (+concept)."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
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
                    {
                        "from": "order",
                        "to": "payment",
                        "verb": "has",
                        "cardinality": "1:N",
                    },
                ],
            },
        )

        result = runner.invoke(
            context,
            ["--project-dir", str(tmppath), "--select", "+payment", "--format", "llm"],
        )

        assert result.exit_code == 0
        # Upstream from payment should include order and customer
        assert "Payment" in result.output
        assert "Order" in result.output
        assert "Customer" in result.output


def test_context_select_required() -> None:
    """Test that --select flag is required."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(tmppath, {"concepts": {"customer": {"name": "Customer"}}})

        result = runner.invoke(context, ["--project-dir", str(tmppath)])

        # Click should complain about missing --select
        assert result.exit_code != 0
        assert "select" in result.output.lower() or "required" in result.output.lower()


def test_context_markdown_with_relationships() -> None:
    """Test markdown format renders relationships table correctly."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "domains": {"party": {"name": "Party", "display_name": "Party"}},
                "concepts": {
                    "customer": {
                        "name": "Customer",
                        "domain": "party",
                        "owner": "data-team",
                        "definition": "A buyer",
                    },
                    "order": {
                        "name": "Order",
                        "domain": "party",
                        "definition": "A purchase",
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
            },
        )

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
        # Markdown should contain a relationships table
        assert "## Relationships" in result.output
        assert "places" in result.output
        assert "1:N" in result.output
        # Should contain metadata table
        assert "| Property | Value |" in result.output
        assert "| Status |" in result.output
        assert "| Domain | party |" in result.output
        assert "| Owner | data-team |" in result.output


def test_context_markdown_no_definition() -> None:
    """Test markdown format handles missing definition gracefully."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "concepts": {
                    "customer": {"name": "Customer"},
                }
            },
        )

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
        assert "*No definition provided.*" in result.output


def test_context_markdown_with_guidance() -> None:
    """Test markdown format includes guidance section."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "concepts": {
                    "customer": {
                        "name": "Customer",
                        "guidance": {
                            "context": "Business-critical entity",
                            "rules": [
                                {
                                    "name": "pk_rule",
                                    "description": "customer_id is the primary key",
                                }
                            ],
                        },
                    }
                }
            },
        )

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
        assert "## Guidance" in result.output
        assert "Business-critical entity" in result.output
        assert "pk_rule" in result.output
        assert "customer_id is the primary key" in result.output


def test_context_json_contains_expected_keys() -> None:
    """Test that JSON output contains expected concept keys."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "domains": {"party": {"name": "Party", "display_name": "Party"}},
                "concepts": {
                    "customer": {
                        "name": "Customer",
                        "domain": "party",
                        "owner": "data-team",
                        "definition": "A buyer",
                    }
                },
            },
        )

        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "customer",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)

        # Should be a list with one concept
        assert isinstance(data, list)
        assert len(data) == 1

        concept = data[0]
        assert concept["name"] == "Customer"
        assert concept["domain"] == "party"
        assert concept["owner"] == "data-team"
        assert concept["status"] == "draft"  # Has domain but no models
        assert concept["definition"] == "A buyer"


def test_context_llm_json_parity_with_mcp() -> None:
    """Test that CLI llm/json output is identical to MCP handler output.

    This is the critical acceptance criterion: CLI and MCP must produce
    the same output for the same inputs.
    """
    from dbt_conceptual.cli_utils import load_project_state
    from dbt_conceptual.mcp.handlers import handle_get_context

    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "domains": {"party": {"name": "Party", "display_name": "Party"}},
                "concepts": {
                    "customer": {
                        "name": "Customer",
                        "domain": "party",
                        "owner": "data-team",
                        "definition": "A person who buys things",
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
            },
        )

        # Get MCP handler output
        state, config = load_project_state(project_dir=tmppath)
        mcp_llm_output = handle_get_context(
            selector="customer",
            format="llm",
            depth=1,
            project_state=state,
            config=config,
        )
        mcp_json_output = handle_get_context(
            selector="customer",
            format="json",
            depth=1,
            project_state=state,
            config=config,
        )

        # Get CLI output for llm format
        result_llm = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "customer",
                "--format",
                "llm",
                "--depth",
                "1",
            ],
        )
        assert result_llm.exit_code == 0

        # Get CLI output for json format
        result_json = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "customer",
                "--format",
                "json",
                "--depth",
                "1",
            ],
        )
        assert result_json.exit_code == 0

        # CLI output has a trailing newline from click.echo; strip for comparison
        assert result_llm.output.strip() == mcp_llm_output.strip()
        assert result_json.output.strip() == mcp_json_output.strip()


def test_context_depth_out_of_range() -> None:
    """Test that depth values outside 1-3 are rejected."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(tmppath, {"concepts": {"customer": {"name": "Customer"}}})

        # Depth 0 should fail
        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "customer",
                "--depth",
                "0",
            ],
        )
        assert result.exit_code != 0

        # Depth 4 should fail
        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "customer",
                "--depth",
                "4",
            ],
        )
        assert result.exit_code != 0


def test_context_multiple_concepts_json() -> None:
    """Test JSON output with multiple concepts returns a list."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        _create_test_project(
            tmppath,
            {
                "domains": {"party": {"name": "Party", "display_name": "Party"}},
                "concepts": {
                    "customer": {"name": "Customer", "domain": "party"},
                    "order": {"name": "Order", "domain": "party"},
                },
            },
        )

        result = runner.invoke(
            context,
            [
                "--project-dir",
                str(tmppath),
                "--select",
                "domain:party",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2
        names = {c["name"] for c in data}
        assert names == {"Customer", "Order"}
