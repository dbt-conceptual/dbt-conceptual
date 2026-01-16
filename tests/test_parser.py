"""Tests for parser and state builder."""

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.parser import ConceptualModelParser, StateBuilder


def test_parse_empty_conceptual_file() -> None:
    """Test parsing an empty conceptual model."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create empty conceptual.yml
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)
        with open(conceptual_dir / "conceptual.yml", "w") as f:
            f.write("")

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert len(state.concepts) == 0
        assert len(state.relationships) == 0
        assert len(state.domains) == 0


def test_parse_conceptual_model_with_domains() -> None:
    """Test parsing conceptual model with domains."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with domains
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "domains": {
                "party": {"name": "Party", "color": "#E3F2FD"},
                "transaction": {"name": "Transaction"},
            },
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "party",
                    "owner": "data_team",
                    "definition": "A customer",
                    "status": "complete",
                }
            },
            "relationships": [
                {
                    "name": "places",
                    "from": "customer",
                    "to": "order",
                    "cardinality": "1:N",
                }
            ],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert len(state.domains) == 2
        assert "party" in state.domains
        assert state.domains["party"].display_name == "Party"
        assert state.domains["party"].color == "#E3F2FD"

        assert len(state.concepts) == 1
        assert "customer" in state.concepts
        assert state.concepts["customer"].domain == "party"
        assert state.concepts["customer"].status == "complete"

        assert len(state.relationships) == 1
        assert "customer:places:order" in state.relationships


def test_parse_conceptual_model_with_groups() -> None:
    """Test parsing conceptual model with relationship groups."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with groups
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
            },
            "relationships": [
                {"name": "places", "from": "customer", "to": "order"},
                {"name": "pays", "from": "customer", "to": "order"},
            ],
            "relationship_groups": {
                "order_flow": ["customer:places:order", "customer:pays:order"]
            },
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        assert "order_flow" in state.groups
        assert len(state.groups["order_flow"]) == 2


def test_state_builder_links_models_to_concepts() -> None:
    """Test that state builder links dbt models to concepts."""
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
            "relationships": [{"name": "places", "from": "customer", "to": "order"}],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create silver model
        silver_dir = tmppath / "models" / "silver"
        silver_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "models": [{"name": "dim_customer_raw", "meta": {"concept": "customer"}}],
        }

        with open(silver_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data, f)

        # Create gold model
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        schema_data_gold = {
            "version": 2,
            "models": [{"name": "dim_customer", "meta": {"concept": "customer"}}],
        }

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data_gold, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Check that models were linked
        assert "customer" in state.concepts
        assert "dim_customer_raw" in state.concepts["customer"].silver_models
        assert "dim_customer" in state.concepts["customer"].gold_models


def test_state_builder_links_realizes() -> None:
    """Test that state builder links realizes to relationships."""
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
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
            },
            "relationships": [{"name": "places", "from": "customer", "to": "order"}],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create fact table
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "models": [
                {
                    "name": "fact_orders",
                    "meta": {"realizes": ["customer:places:order"]},
                }
            ],
        }

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Check that relationship was realized
        assert "customer:places:order" in state.relationships
        assert "fact_orders" in state.relationships["customer:places:order"].realized_by


def test_state_builder_expands_groups() -> None:
    """Test that state builder expands relationship groups."""
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
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
            },
            "relationships": [
                {"name": "places", "from": "customer", "to": "order"},
                {"name": "pays", "from": "customer", "to": "order"},
            ],
            "relationship_groups": {
                "order_flow": ["customer:places:order", "customer:pays:order"]
            },
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create fact table that uses group
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "models": [{"name": "fact_orders", "meta": {"realizes": ["order_flow"]}}],
        }

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Check that both relationships were realized via group
        assert "fact_orders" in state.relationships["customer:places:order"].realized_by
        assert "fact_orders" in state.relationships["customer:pays:order"].realized_by


def test_state_builder_tracks_orphans() -> None:
    """Test that state builder tracks orphan models."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create empty conceptual.yml
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)
        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump({"version": 1}, f)

        # Create model without meta tags
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        schema_data = {"version": 2, "models": [{"name": "dim_orphan"}]}

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Check that orphan was tracked
        orphan_names = [o.name for o in state.orphan_models]
        assert "dim_orphan" in orphan_names
        # Verify orphan has expected attributes
        orphan = state.orphan_models[0]
        assert orphan.layer == "gold"
        assert orphan.path == "models/gold"
