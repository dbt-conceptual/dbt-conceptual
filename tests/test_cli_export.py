"""Tests for CLI export, diff, and serve commands."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from dbt_conceptual.cli import diff, export, main, serve


def test_cli_export_coverage_html() -> None:
    """Test export command with coverage type and html format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create a model directory structure
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}}
                    ],
                },
                f,
            )

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
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<html" in content.lower()


def test_cli_export_coverage_markdown() -> None:
    """Test export command with coverage type and markdown format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create a model directory structure
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}}
                    ],
                },
                f,
            )

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "coverage",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert (
            "Coverage Summary" in result.output or "coverage" in result.output.lower()
        )


def test_cli_export_coverage_json() -> None:
    """Test export command with coverage type and json format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create a model directory structure
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}}
                    ],
                },
                f,
            )

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "coverage",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "summary" in data or "concepts" in data


def test_cli_export_status_markdown() -> None:
    """Test export command with status type and markdown format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "status",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert "Status Summary" in result.output or "Concepts:" in result.output


def test_cli_export_status_json() -> None:
    """Test export command with status type and json format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "status",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)


def test_cli_export_orphans_markdown() -> None:
    """Test export command with orphans type and markdown format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create minimal conceptual.yml
        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump({"version": 1}, f)

        # Create orphan model
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)
        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump({"version": 2, "models": [{"name": "dim_product"}]}, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "orphans",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert "dim_product" in result.output or "orphan" in result.output.lower()


def test_cli_export_orphans_json() -> None:
    """Test export command with orphans type and json format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create minimal conceptual.yml
        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump({"version": 1}, f)

        # Create orphan model
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)
        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump({"version": 2, "models": [{"name": "dim_product"}]}, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "orphans",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)


def test_cli_export_validation_markdown() -> None:
    """Test export command with validation type and markdown format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with incomplete concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    # Missing owner and definition
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "validation",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert "customer" in result.output or "validation" in result.output.lower()


def test_cli_export_validation_json() -> None:
    """Test export command with validation type and json format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with incomplete concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    # Missing owner and definition
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "validation",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)


def test_cli_export_bus_matrix_html() -> None:
    """Test export command with bus-matrix type and html format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create a model directory structure
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}}
                    ],
                },
                f,
            )

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "bus-matrix",
                "--format",
                "html",
            ],
        )

        assert result.exit_code == 0
        assert "<html" in result.output.lower() or "customer" in result.output


def test_cli_export_bus_matrix_markdown() -> None:
    """Test export command with bus-matrix type and markdown format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create a model directory structure
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}}
                    ],
                },
                f,
            )

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "bus-matrix",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0


def test_cli_export_bus_matrix_json() -> None:
    """Test export command with bus-matrix type and json format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create a model directory structure
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}}
                    ],
                },
                f,
            )

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "bus-matrix",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)


def test_cli_export_diagram_svg() -> None:
    """Test export command with diagram type and svg format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        output_file = tmppath / "diagram.svg"
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "diagram",
                "--format",
                "svg",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<svg" in content.lower()


def test_cli_export_diff_without_base() -> None:
    """Test export command with diff type but missing --base."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump({"version": 1}, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "diff",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 1
        assert "--base is required" in result.output


def test_cli_export_invalid_combination() -> None:
    """Test export command with invalid type/format combination."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump({"version": 1}, f)

        # diagram only supports svg, not json
        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "diagram",
                "--format",
                "json",
            ],
        )

        # Should fail with validation error
        assert result.exit_code != 0


def test_cli_export_without_conceptual_file() -> None:
    """Test export command without conceptual.yml file."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml only
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(
            export,
            [
                "--project-dir",
                str(tmppath),
                "--type",
                "status",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 1
        assert "conceptual.yml not found" in result.output


def test_cli_diff_command() -> None:
    """Test diff command with git base."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Initialize git repo
        import subprocess

        subprocess.run(["git", "init"], cwd=tmppath, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmppath,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=tmppath,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=tmppath, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmppath,
            capture_output=True,
        )

        # Make a change
        conceptual_data["concepts"]["product"] = {
            "name": "Product",
            "domain": "party",
            "owner": "data_team",
            "definition": "A product",
        }
        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(
            diff,
            [
                "--project-dir",
                str(tmppath),
                "--base",
                "HEAD",
                "--format",
                "human",
            ],
        )

        # Should succeed (exit 0 even if there are changes)
        assert result.exit_code == 0


def test_cli_diff_command_github_format() -> None:
    """Test diff command with GitHub format."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Initialize git repo
        import subprocess

        subprocess.run(["git", "init"], cwd=tmppath, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmppath,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=tmppath,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=tmppath, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmppath,
            capture_output=True,
        )

        result = runner.invoke(
            diff,
            [
                "--project-dir",
                str(tmppath),
                "--base",
                "HEAD",
                "--format",
                "github",
            ],
        )

        assert result.exit_code == 0


def test_cli_serve_command() -> None:
    """Test serve command (basic invocation check)."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Mock run_server function to prevent actual server startup
        with patch("dbt_conceptual.server.run_server") as mock_run_server:
            _ = runner.invoke(
                serve,
                [
                    "--project-dir",
                    str(tmppath),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8080",
                ],
            )

            # Check that run_server was called
            assert mock_run_server.called


def test_cli_serve_command_demo_mode() -> None:
    """Test serve command in demo mode."""
    runner = CliRunner()

    with TemporaryDirectory() as _tmpdir:

        # No need to create files for demo mode

        # Mock run_server function to prevent actual server startup
        with patch("dbt_conceptual.server.run_server") as mock_run_server:
            _ = runner.invoke(
                serve,
                [
                    "--demo",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8080",
                ],
            )

            # Check that run_server was called
            assert mock_run_server.called


def test_cli_main_verbose_flag() -> None:
    """Test main CLI with verbose flag."""
    runner = CliRunner()
    result = runner.invoke(main, ["-v", "--help"])
    assert result.exit_code == 0
    assert "dbt-conceptual" in result.output


def test_cli_main_very_verbose_flag() -> None:
    """Test main CLI with very verbose flag."""
    runner = CliRunner()
    result = runner.invoke(main, ["-vv", "--help"])
    assert result.exit_code == 0
    assert "dbt-conceptual" in result.output


def test_cli_main_quiet_flag() -> None:
    """Test main CLI with quiet flag."""
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "--help"])
    assert result.exit_code == 0
    assert "dbt-conceptual" in result.output
