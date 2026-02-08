"""Tests for dbt project scanner."""

import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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


# ---- Edge case tests below ----


def test_find_schema_files_yaml_extension() -> None:
    """Test that scanner finds .yaml files (not just .yml) in directories."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Configure a direct directory path (no glob) so the is_dir branch runs
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yaml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_yaml_model"}],
                },
                f,
            )

        with open(gold_dir / "other.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_yml_model"}],
                },
                f,
            )

        # Use direct directory path (not glob) to trigger the is_dir branch
        config = Config(
            project_dir=tmppath,
            gold_paths=["models/marts"],
        )
        scanner = DbtProjectScanner(config)

        schema_files = list(scanner.find_schema_files())
        filenames = [f.name for f in schema_files]
        assert "schema.yaml" in filenames
        assert "other.yml" in filenames
        assert len(schema_files) == 2


def test_find_schema_files_direct_file_path() -> None:
    """Test that scanner handles a direct file path (not dir, not glob)."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        schema_file = gold_dir / "specific.yml"
        with open(schema_file, "w") as f:
            yaml.dump({"version": 2, "models": [{"name": "dim_specific"}]}, f)

        # Point gold_paths to a specific file
        config = Config(
            project_dir=tmppath,
            gold_paths=["models/marts/specific.yml"],
        )
        scanner = DbtProjectScanner(config)

        schema_files = list(scanner.find_schema_files())
        assert len(schema_files) == 1
        assert schema_files[0].name == "specific.yml"


def test_find_schema_files_nonexistent_path() -> None:
    """Test that scanner yields nothing for a path that doesn't exist."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config(
            project_dir=tmppath,
            gold_paths=["models/nonexistent"],
        )
        scanner = DbtProjectScanner(config)

        schema_files = list(scanner.find_schema_files())
        assert len(schema_files) == 0


def test_scan_dedup_overlapping_glob_patterns() -> None:
    """Test that overlapping glob patterns do not produce duplicate models."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_customer", "meta": {"concept": "c"}}],
                },
                f,
            )

        # Two overlapping patterns that both match the same file
        config = Config(
            project_dir=tmppath,
            gold_paths=[
                "models/marts/**/*.yml",
                "models/**/*.yml",
            ],
        )
        scanner = DbtProjectScanner(config)

        all_models = scanner.scan()
        # Should have only 1 model, not 2 (dedup)
        assert len(all_models) == 1
        assert all_models[0]["name"] == "dim_customer"


def test_scan_empty_directory() -> None:
    """Test that scanner handles an empty directory gracefully."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create the gold directory but put no files in it
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        all_models = scanner.scan()
        assert len(all_models) == 0


def test_extract_models_non_dict_entry() -> None:
    """Test that non-dict entries in models list are skipped."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_data = {
            "version": 2,
            "models": [
                "just_a_string",
                42,
                {"name": "dim_valid", "meta": {"concept": "valid"}},
            ],
        }
        file_path = tmppath / "models" / "marts" / "schema.yml"

        models = scanner.extract_models_from_schema(schema_data, file_path)
        assert len(models) == 1
        assert models[0]["name"] == "dim_valid"


def test_extract_models_missing_name() -> None:
    """Test that model dicts without a name key are skipped."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_data = {
            "version": 2,
            "models": [
                {"meta": {"concept": "no_name"}},
                {"name": "", "meta": {"concept": "empty_name"}},
                {"name": "dim_with_name", "meta": {"concept": "valid"}},
            ],
        }
        file_path = tmppath / "models" / "marts" / "schema.yml"

        models = scanner.extract_models_from_schema(schema_data, file_path)
        # Only the model with a truthy name should be included
        assert len(models) == 1
        assert models[0]["name"] == "dim_with_name"


def test_extract_models_tags_not_list() -> None:
    """Test that non-list tags are replaced with empty list."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_data = {
            "version": 2,
            "models": [
                {
                    "name": "dim_bad_tags",
                    "tags": "not_a_list",
                },
            ],
        }
        file_path = tmppath / "models" / "marts" / "schema.yml"

        models = scanner.extract_models_from_schema(schema_data, file_path)
        assert len(models) == 1
        assert models[0]["tags"] == []


def test_extract_models_databricks_tags_not_dict() -> None:
    """Test that non-dict databricks_tags are replaced with empty dict."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_data = {
            "version": 2,
            "models": [
                {
                    "name": "dim_bad_db_tags",
                    "config": {"databricks_tags": "not_a_dict"},
                },
            ],
        }
        file_path = tmppath / "models" / "marts" / "schema.yml"

        models = scanner.extract_models_from_schema(schema_data, file_path)
        assert len(models) == 1
        assert models[0]["databricks_tags"] == {}


def test_extract_models_file_outside_project_dir() -> None:
    """Test relative path fallback when file is outside project_dir."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_data = {
            "version": 2,
            "models": [
                {"name": "dim_outside", "meta": {"concept": "outside"}},
            ],
        }
        # Use a path outside the project directory
        outside_path = Path("/tmp/totally-different-dir/schema.yml")

        models = scanner.extract_models_from_schema(schema_data, outside_path)
        assert len(models) == 1
        # Path should fall back to the full file_path since relative_to fails
        assert models[0]["path"] == str(outside_path)


def test_scan_handles_oserror(caplog: "logging.LogRecord") -> None:
    """Test that scan handles OSError when reading files."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        schema_file = gold_dir / "schema.yml"
        with open(schema_file, "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_test"}],
                },
                f,
            )

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        # Patch load_schema_file to raise OSError
        with patch.object(
            scanner, "load_schema_file", side_effect=OSError("Permission denied")
        ):
            with caplog.at_level(logging.WARNING, logger="dbt_conceptual.scanner"):
                all_models = scanner.scan()

        assert len(all_models) == 0
        assert "Failed to read" in caplog.text


def test_scan_handles_type_error(caplog: "logging.LogRecord") -> None:
    """Test that scan handles TypeError/ValueError from malformed schema data."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        schema_file = gold_dir / "schema.yml"
        with open(schema_file, "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_test"}],
                },
                f,
            )

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        # Patch extract_models_from_schema to raise TypeError
        with patch.object(
            scanner,
            "extract_models_from_schema",
            side_effect=TypeError("unexpected type"),
        ):
            with caplog.at_level(logging.WARNING, logger="dbt_conceptual.scanner"):
                all_models = scanner.scan()

        assert len(all_models) == 0
        assert "Malformed schema" in caplog.text


def test_load_schema_file_empty_content() -> None:
    """Test that load_schema_file returns empty dict for empty YAML."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        empty_file = tmppath / "empty.yml"
        with open(empty_file, "w") as f:
            f.write("")

        result = scanner.load_schema_file(empty_file)
        assert result == {}


def test_scan_yaml_extension_integration() -> None:
    """Test full scan with .yaml files using directory path config."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        # Only create .yaml files
        with open(gold_dir / "schema.yaml", "w") as f:
            yaml.dump(
                {
                    "version": 2,
                    "models": [{"name": "dim_yaml_only", "meta": {"concept": "y"}}],
                },
                f,
            )

        # Use directory path so both .yml and .yaml are discovered
        config = Config(
            project_dir=tmppath,
            gold_paths=["models/marts"],
        )
        scanner = DbtProjectScanner(config)

        all_models = scanner.scan()
        assert len(all_models) == 1
        assert all_models[0]["name"] == "dim_yaml_only"


def test_extract_models_tags_from_config() -> None:
    """Test that tags are extracted from config block when not at top level."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_data = {
            "version": 2,
            "models": [
                {
                    "name": "dim_config_tags",
                    "config": {
                        "tags": ["gold", "production"],
                        "databricks_tags": {"env": "prod"},
                    },
                },
            ],
        }
        file_path = tmppath / "models" / "marts" / "schema.yml"

        models = scanner.extract_models_from_schema(schema_data, file_path)
        assert len(models) == 1
        assert models[0]["tags"] == ["gold", "production"]
        assert models[0]["databricks_tags"] == {"env": "prod"}


def test_extract_models_description_field() -> None:
    """Test that description is properly extracted (including None)."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        config = Config.load(project_dir=tmppath)
        scanner = DbtProjectScanner(config)

        schema_data = {
            "version": 2,
            "models": [
                {"name": "dim_with_desc", "description": "A dimension table"},
                {"name": "dim_no_desc"},
            ],
        }
        file_path = tmppath / "models" / "marts" / "schema.yml"

        models = scanner.extract_models_from_schema(schema_data, file_path)
        assert len(models) == 2
        assert models[0]["description"] == "A dimension table"
        assert models[1]["description"] is None
