"""Tests for dbt project scanner."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.scanner import DbtProjectScanner


def test_scanner_finds_schema_files() -> None:
    """Test that scanner finds schema files in gold paths."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create schema files in gold (marts) directory
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)
        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump({"version": 2}, f)

        with open(gold_dir / "models.yml", "w") as f:
            yaml.dump({"version": 2}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_files = list(scanner.find_schema_files())
        assert len(schema_files) == 2
        assert any(f.name == "schema.yml" for f in schema_files)
        assert any(f.name == "models.yml" for f in schema_files)


def test_scanner_extracts_models() -> None:
    """Test that scanner extracts models from schema files."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create schema file with models
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "models": [
                {
                    "name": "dim_customer",
                    "meta": {"concept": "customer"},
                },
                {
                    "name": "fact_orders",
                    "meta": {"concept": "order"},
                },
            ],
        }

        schema_file = gold_dir / "schema.yml"
        with open(schema_file, "w") as f:
            yaml.dump(schema_data, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        models = scanner.extract_models_from_schema(schema_data, schema_file)

        assert len(models) == 2
        assert models[0]["name"] == "dim_customer"
        assert models[0]["meta"]["concept"] == "customer"

        assert models[1]["name"] == "fact_orders"
        assert models[1]["meta"]["concept"] == "order"


def test_scanner_scan_all() -> None:
    """Test full scan of dbt project."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create schema file
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [
                        {"name": "dim_customer", "meta": {"concept": "customer"}},
                        {"name": "fact_orders"},
                    ],
                },
                f,
            )

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)
        all_models = scanner.scan()

        assert len(all_models) == 2
        model_names = [m["name"] for m in all_models]
        assert "dim_customer" in model_names
        assert "fact_orders" in model_names


def test_scanner_handles_invalid_yaml() -> None:
    """Test that scanner handles malformed YAML gracefully."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create invalid YAML
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "bad.yml", "w") as f:
            f.write("invalid: yaml: content: [")

        # Create valid YAML
        with open(gold_dir / "good.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_test", "meta": {"concept": "test"}}],
                },
                f,
            )

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        # Should not crash, should skip bad file
        all_models = scanner.scan()
        assert len(all_models) == 1
        assert all_models[0]["name"] == "dim_test"


def test_scanner_handles_empty_models_list() -> None:
    """Test scanner with schema file that has no models."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create schema file with sources but no models
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "sources": [{"name": "raw", "tables": [{"name": "users"}]}],
        }

        schema_file = gold_dir / "schema.yml"
        with open(schema_file, "w") as f:
            yaml.dump(schema_data, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        models = scanner.extract_models_from_schema(schema_data, schema_file)
        assert len(models) == 0
