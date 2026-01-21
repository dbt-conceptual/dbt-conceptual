"""Tests for demo mode project generator."""

import shutil
from pathlib import Path

import yaml

from dbt_conceptual.demo import create_demo_project


class TestCreateDemoProject:
    """Tests for create_demo_project function."""

    def test_creates_temp_directory(self) -> None:
        """Test that create_demo_project creates a directory."""
        demo_dir = create_demo_project()
        try:
            assert demo_dir.exists()
            assert demo_dir.is_dir()
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_creates_dbt_project_yml(self) -> None:
        """Test that dbt_project.yml is created with correct content."""
        demo_dir = create_demo_project()
        try:
            dbt_project_file = demo_dir / "dbt_project.yml"
            assert dbt_project_file.exists()

            with open(dbt_project_file) as f:
                data = yaml.safe_load(f)

            assert data["name"] == "dbt_conceptual_demo"
            assert "vars" in data
            assert "dbt_conceptual" in data["vars"]
            assert "silver_paths" in data["vars"]["dbt_conceptual"]
            assert "gold_paths" in data["vars"]["dbt_conceptual"]
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_creates_conceptual_yml(self) -> None:
        """Test that conceptual.yml is created with concepts and relationships."""
        demo_dir = create_demo_project()
        try:
            conceptual_file = demo_dir / "conceptual.yml"
            assert conceptual_file.exists()

            with open(conceptual_file) as f:
                data = yaml.safe_load(f)

            # Check domains
            assert "domains" in data
            assert "core" in data["domains"]
            assert "analytics" in data["domains"]
            assert "sales" in data["domains"]

            # Check concepts
            assert "concepts" in data
            assert "customer" in data["concepts"]
            assert "order" in data["concepts"]
            assert "product" in data["concepts"]
            assert "revenue" in data["concepts"]

            # Check relationships
            assert "relationships" in data
            assert len(data["relationships"]) == 4
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_creates_layout_json(self) -> None:
        """Test that conceptual.layout.json is created with positions."""
        demo_dir = create_demo_project()
        try:
            import json

            layout_file = demo_dir / "conceptual.layout.json"
            assert layout_file.exists()

            with open(layout_file) as f:
                data = json.load(f)

            assert "positions" in data
            assert "customer" in data["positions"]
            assert "order" in data["positions"]
            assert "product" in data["positions"]
            assert "revenue" in data["positions"]
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_creates_model_directories(self) -> None:
        """Test that bronze/silver/gold model directories are created."""
        demo_dir = create_demo_project()
        try:
            assert (demo_dir / "models" / "bronze").is_dir()
            assert (demo_dir / "models" / "silver").is_dir()
            assert (demo_dir / "models" / "gold").is_dir()
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_creates_schema_files(self) -> None:
        """Test that _schema.yml files are created in each layer."""
        demo_dir = create_demo_project()
        try:
            bronze_schema = demo_dir / "models" / "bronze" / "_schema.yml"
            silver_schema = demo_dir / "models" / "silver" / "_schema.yml"
            gold_schema = demo_dir / "models" / "gold" / "_schema.yml"

            assert bronze_schema.exists()
            assert silver_schema.exists()
            assert gold_schema.exists()

            # Check silver has concept tags
            with open(silver_schema) as f:
                silver_data = yaml.safe_load(f)
            assert any(
                m.get("meta", {}).get("concept") == "customer"
                for m in silver_data["models"]
            )

            # Check gold has realizes tags
            with open(gold_schema) as f:
                gold_data = yaml.safe_load(f)
            assert any(
                m.get("meta", {}).get("realizes") == "customer"
                for m in gold_data["models"]
            )
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_creates_sql_files(self) -> None:
        """Test that placeholder SQL files are created."""
        demo_dir = create_demo_project()
        try:
            # Bronze models
            assert (demo_dir / "models" / "bronze" / "raw_customers.sql").exists()
            assert (demo_dir / "models" / "bronze" / "raw_orders.sql").exists()
            assert (demo_dir / "models" / "bronze" / "raw_products.sql").exists()

            # Silver models
            assert (demo_dir / "models" / "silver" / "stg_customers.sql").exists()
            assert (demo_dir / "models" / "silver" / "stg_orders.sql").exists()
            assert (demo_dir / "models" / "silver" / "stg_products.sql").exists()

            # Gold models
            assert (demo_dir / "models" / "gold" / "dim_customer.sql").exists()
            assert (demo_dir / "models" / "gold" / "dim_product.sql").exists()
            assert (demo_dir / "models" / "gold" / "fct_orders.sql").exists()
            assert (demo_dir / "models" / "gold" / "fct_revenue.sql").exists()
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_custom_base_dir(self, tmp_path: Path) -> None:
        """Test creating demo project in a custom base directory."""
        demo_dir = create_demo_project(base_dir=tmp_path)
        try:
            assert demo_dir.parent == tmp_path
            assert demo_dir.name == "dbt_conceptual_demo"
            assert (demo_dir / "dbt_project.yml").exists()
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)

    def test_project_is_valid_for_dbt_conceptual(self) -> None:
        """Test that the demo project can be loaded by dbt-conceptual."""
        demo_dir = create_demo_project()
        try:
            from dbt_conceptual.config import Config
            from dbt_conceptual.parser import StateBuilder

            config = Config.load(project_dir=demo_dir)
            builder = StateBuilder(config)
            state = builder.build()

            # Should have 4 concepts
            assert len(state.concepts) == 4
            assert "customer" in state.concepts
            assert "order" in state.concepts
            assert "product" in state.concepts
            assert "revenue" in state.concepts

            # Should have 4 relationships
            assert len(state.relationships) == 4
        finally:
            shutil.rmtree(demo_dir, ignore_errors=True)
