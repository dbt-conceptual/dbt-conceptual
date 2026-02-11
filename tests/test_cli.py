"""Tests for CLI commands."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml
from click.testing import CliRunner

from dbt_conceptual.cli import init, main, status, sync, validate


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
    """Test init command creates both conceptual.yml and adds vars to dbt_project.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(init, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Initialization complete" in result.output

        # Check conceptual.yml was created (clean, no config section)
        conceptual_file = tmppath / "conceptual.yml"
        assert conceptual_file.exists()
        content = conceptual_file.read_text()
        assert "config:" not in content
        assert "domains:" in content
        assert "concepts:" in content
        assert "relationships:" in content

        # Check dbt_project.yml now has vars.dbt_conceptual
        with open(tmppath / "dbt_project.yml") as f:
            dbt_data = yaml.safe_load(f)
        assert "vars" in dbt_data
        assert "dbt_conceptual" in dbt_data["vars"]
        assert "scan" in dbt_data["vars"]["dbt_conceptual"]
        assert "validation" in dbt_data["vars"]["dbt_conceptual"]


def test_cli_init_already_exists() -> None:
    """Test init command when conceptual.yml already exists."""
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


def test_cli_init_force_overwrites() -> None:
    """Test init --force overwrites existing conceptual.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create existing conceptual.yml with custom content
        conceptual_file = tmppath / "conceptual.yml"
        conceptual_file.write_text("custom: content\n")

        result = runner.invoke(init, ["--project-dir", str(tmppath), "--force"])

        assert result.exit_code == 0
        assert "Overwrote" in result.output

        # Content should be the new template
        content = conceptual_file.read_text()
        assert "domains:" in content
        assert "custom: content" not in content


def test_cli_init_merges_existing_vars() -> None:
    """Test init merges with existing vars in dbt_project.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml with existing vars
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"other_tool": {"enabled": True}}}, f)

        result = runner.invoke(init, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Added vars.dbt_conceptual" in result.output

        # Both vars should exist
        with open(tmppath / "dbt_project.yml") as f:
            dbt_data = yaml.safe_load(f)
        assert "other_tool" in dbt_data["vars"]
        assert "dbt_conceptual" in dbt_data["vars"]


def test_cli_init_skips_existing_dbt_conceptual_vars() -> None:
    """Test init skips if vars.dbt_conceptual already exists."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml with existing dbt_conceptual vars
        existing_config = {"scan": {"gold": ["custom/**/*.yml"]}}
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test", "vars": {"dbt_conceptual": existing_config}}, f)

        result = runner.invoke(init, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "already exists in dbt_project.yml" in result.output

        # Should NOT overwrite the existing config
        with open(tmppath / "dbt_project.yml") as f:
            dbt_data = yaml.safe_load(f)
        assert dbt_data["vars"]["dbt_conceptual"]["scan"]["gold"] == ["custom/**/*.yml"]


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

        # Create conceptual.yml in project root
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

        # Create a gold model
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

        # Create conceptual.yml in project root
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

        # Create models
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

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        # Should pass
        assert "PASSED" in result.output


def test_cli_validate_with_errors() -> None:
    """Test validate command with validation errors."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationship referencing unknown concept
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
            },
            "relationships": [
                {"verb": "places", "from": "customer", "to": "unknown_concept"}
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        # Should fail with E002 (unknown reference)
        assert result.exit_code == 1
        assert "FAILED" in result.output
        assert "E002" in result.output


def test_cli_status_with_orphans() -> None:
    """Test status command displays orphan models."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create minimal conceptual.yml in project root
        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump({"version": 1}, f)

        # Create orphan model
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)
        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump({"version": 2, "models": [{"name": "dim_orphan"}]}, f)

        result = runner.invoke(status, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Orphan Models" in result.output
        assert "dim_orphan" in result.output


def test_cli_status_with_relationships() -> None:
    """Test status command displays relationships."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationships
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                },
                "order": {
                    "name": "Order",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "An order",
                },
            },
            "relationships": [{"verb": "places", "from": "customer", "to": "order"}],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create models for both concepts
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}},
                        {"name": "fact_orders", "meta": {"concept": "order"}},
                    ],
                },
                f,
            )

        result = runner.invoke(status, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Relationships" in result.output
        assert "places" in result.output


def test_cli_status_with_stub_concept() -> None:
    """Test status command shows stub concepts with missing fields."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with stub (missing domain)
        conceptual_data = {
            "version": 1,
            "concepts": {"payment": {"name": "Payment"}},
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(status, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "payment" in result.output
        # Stub concepts show warning icon and missing attributes
        assert "missing" in result.output


def test_cli_validate_with_warnings_only() -> None:
    """Test validate command with warnings but no errors."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with a concept that has domain/owner/definition
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

        # Create gold model
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

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        # Should pass (warnings are not errors)
        assert "customer" in result.output


def test_cli_init_without_dbt_project() -> None:
    """Test init command fails without dbt_project.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        result = runner.invoke(init, ["--project-dir", str(tmppath)])

        assert result.exit_code == 1
        assert "dbt_project.yml not found" in result.output


def test_cli_validate_without_conceptual_file() -> None:
    """Test validate command fails without conceptual.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml only
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        assert result.exit_code == 1
        assert "conceptual.yml not found" in result.output


def test_cli_validate_with_relationship() -> None:
    """Test validate shows relationships."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationship
        conceptual_data = {
            "version": 1,
            "domains": {
                "party": {"name": "Party"},
                "transaction": {"name": "Transaction"},
            },
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                },
                "order": {
                    "name": "Order",
                    "domain": "transaction",
                    "owner": "data_team",
                    "definition": "An order",
                },
            },
            "relationships": [{"verb": "places", "from": "customer", "to": "order"}],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create models for both concepts
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}},
                        {"name": "fact_orders", "meta": {"concept": "order"}},
                    ],
                },
                f,
            )

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "places" in result.output


def test_cli_validate_with_info_messages() -> None:
    """Test validate command displays info messages."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with stub concept (missing domain generates stub)
        conceptual_data = {
            "version": 1,
            "concepts": {"payment": {"name": "Payment"}},
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "INFO" in result.output


def test_cli_status_with_draft_concept_missing_attrs() -> None:
    """Test status shows missing attributes for draft concepts."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with draft concept missing owner
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "definition": "A customer",
                    # owner is missing
                }
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(status, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "customer" in result.output
        assert "missing: owner" in result.output
        assert "Concepts Needing Attention" in result.output


def test_cli_sync_no_orphans() -> None:
    """Test sync command with no orphan models."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with concept
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

        # Create gold model with concept tag
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

        result = runner.invoke(sync, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "No orphan models found" in result.output


def test_cli_sync_with_orphans() -> None:
    """Test sync command creates stubs for orphan models."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create minimal conceptual.yml
        conceptual_file = tmppath / "conceptual.yml"
        with open(conceptual_file, "w") as f:
            yaml.dump({"version": 1}, f)

        # Create orphan model
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)
        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump({"version": 2, "models": [{"name": "dim_product"}]}, f)

        result = runner.invoke(sync, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Found 1 orphan model" in result.output
        assert "dim_product" in result.output
        assert "Created 1 stub concept" in result.output
        assert "product" in result.output

        # Verify stub was created in file
        with open(conceptual_file) as f:
            data = yaml.safe_load(f)
            assert "product" in data["concepts"]


def test_cli_sync_create_stubs() -> None:
    """Test sync command creates stub concepts."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create minimal conceptual.yml
        conceptual_file = tmppath / "conceptual.yml"
        with open(conceptual_file, "w") as f:
            yaml.dump({"version": 1}, f)

        # Create orphan models
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)
        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_product"}, {"name": "fact_sales"}],
                },
                f,
            )

        result = runner.invoke(sync, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "Created 2 stub concept" in result.output
        assert "product" in result.output
        assert "sales" in result.output

        # Verify stubs were created in file
        with open(conceptual_file) as f:
            data = yaml.safe_load(f)
            assert "product" in data["concepts"]
            assert "sales" in data["concepts"]


def test_cli_sync_specific_model() -> None:
    """Test sync command with --model flag."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create minimal conceptual.yml
        conceptual_file = tmppath / "conceptual.yml"
        with open(conceptual_file, "w") as f:
            yaml.dump({"version": 1}, f)

        # Create multiple orphan models
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)
        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_product"},
                        {"name": "dim_customer"},
                    ],
                },
                f,
            )

        result = runner.invoke(
            sync,
            [
                "--project-dir",
                str(tmppath),
                "--model",
                "dim_product",
            ],
        )

        assert result.exit_code == 0
        assert "Created 1 stub concept" in result.output
        assert "product" in result.output

        # Verify only one stub was created
        with open(conceptual_file) as f:
            data = yaml.safe_load(f)
            assert "product" in data["concepts"]
            assert "customer" not in data["concepts"]


def test_cli_sync_without_conceptual_file() -> None:
    """Test sync command fails without conceptual.yml."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml only
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        result = runner.invoke(sync, ["--project-dir", str(tmppath)])

        assert result.exit_code == 1
        assert "conceptual.yml not found" in result.output


def test_cli_validate_exit_code_on_success() -> None:
    """Test validate command returns exit code 0 on success."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with complete concept
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

        # Create models
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

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        assert result.exit_code == 0
        assert "PASSED" in result.output


def test_cli_validate_exit_code_on_failure() -> None:
    """Test validate command returns exit code 1 on validation errors."""
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationship referencing unknown concept
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
            },
            "relationships": [
                {"verb": "places", "from": "customer", "to": "unknown_concept"}
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        result = runner.invoke(validate, ["--project-dir", str(tmppath)])

        assert result.exit_code == 1
        assert "FAILED" in result.output
        assert "E002" in result.output
