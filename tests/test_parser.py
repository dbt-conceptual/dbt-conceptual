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
                    # Note: status is no longer stored, it's derived
                }
            },
            "relationships": [
                {
                    "verb": "places",
                    "from": "customer",
                    "to": "order",
                    "cardinality": "1:N",
                    "domains": ["transaction"],  # New: array of domains
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
        # Status is now derived: has domain but no models = "draft"
        assert state.concepts["customer"].status == "draft"

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


def test_validate_and_sync_creates_ghost_concepts() -> None:
    """Test that validate_and_sync creates ghost concepts for missing references."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationship to non-existent concept
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {"customer": {"name": "Customer"}},
            "relationships": [
                {
                    "verb": "places",
                    "from": "customer",
                    "to": "order",
                }  # 'order' doesn't exist
            ],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Check that ghost concept was created
        assert "order" in state.concepts
        assert state.concepts["order"].is_ghost is True
        assert state.concepts["order"].validation_status == "error"

        # Check that error message was generated
        assert validation.error_count >= 1
        error_msgs = [m for m in validation.messages if m.severity == "error"]
        assert any("order" in m.text for m in error_msgs)


def test_validate_and_sync_detects_duplicate_concepts() -> None:
    """Test that validate_and_sync detects duplicate concept names."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with duplicate concept names
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer1": {"name": "Customer"},  # Same name
                "customer2": {"name": "Customer"},  # Same name
            },
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Check that error was detected
        assert validation.error_count >= 1
        error_msgs = [m for m in validation.messages if m.severity == "error"]
        assert any("Duplicate concept name" in m.text for m in error_msgs)


def test_validate_and_sync_handles_relationship_with_both_ghosts() -> None:
    """Test that validate_and_sync creates ghosts for both missing concepts."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml where relationship references two missing concepts
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {},  # No concepts defined
            "relationships": [
                {"verb": "places", "from": "customer", "to": "order"},
            ],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Both concepts should be created as ghosts
        assert "customer" in state.concepts
        assert "order" in state.concepts
        assert state.concepts["customer"].is_ghost is True
        assert state.concepts["order"].is_ghost is True

        # Should have errors for both missing concepts
        assert validation.error_count >= 2


def test_validate_and_sync_counts_messages_correctly() -> None:
    """Test that validate_and_sync counts messages by severity correctly."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with various issues
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "domains": {
                "party": {"name": "Party"},
                "empty": {"name": "Empty"},  # Will be flagged as empty
            },
            "concepts": {
                "customer": {"name": "Customer", "domain": "party"},
            },
            "relationships": [
                {"verb": "places", "from": "customer", "to": "order"},  # Ghost created
            ],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Should have at least: 1 error (missing order), 1 warning (ghost stub + empty domain), 1 info
        assert validation.error_count >= 1
        assert validation.warning_count >= 1
        assert validation.info_count >= 1

        # Total should match sum
        total = (
            validation.error_count + validation.warning_count + validation.info_count
        )
        assert len(validation.messages) == total


def test_validate_and_sync_detects_empty_domains() -> None:
    """Test that validate_and_sync detects domains with no concepts."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with empty domain
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "domains": {
                "party": {"name": "Party"},
                "empty_domain": {"name": "Empty Domain"},  # No concepts use this
            },
            "concepts": {
                "customer": {"name": "Customer", "domain": "party"},
            },
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Check that warning was generated for empty domain
        warning_msgs = [m for m in validation.messages if m.severity == "warning"]
        assert any("empty_domain" in m.text for m in warning_msgs)


def test_validate_and_sync_returns_info_message() -> None:
    """Test that validate_and_sync returns a sync info message."""
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
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Check that info message was generated
        assert validation.info_count >= 1
        info_msgs = [m for m in validation.messages if m.severity == "info"]
        assert any("Synced" in m.text and "concepts" in m.text for m in info_msgs)


def test_validate_and_sync_marks_relationship_invalid() -> None:
    """Test that relationships referencing ghost concepts are marked invalid."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with missing concepts on both ends
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {},  # No concepts defined
            "relationships": [{"verb": "places", "from": "customer", "to": "order"}],
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        builder.validate_and_sync(state)

        # Check that relationship was marked invalid
        rel = state.relationships["customer:places:order"]
        assert rel.validation_status == "error"
        assert len(rel.validation_messages) >= 2  # Both source and target missing


def test_lineage_inference_from_manifest() -> None:
    """Test that lineage inference discovers upstream/downstream models."""
    import json

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
            "concepts": {"customer": {"name": "Customer", "domain": "party"}},
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create silver model with meta.concept (anchor)
        silver_dir = tmppath / "models" / "silver"
        silver_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "models": [{"name": "stg_customer", "meta": {"concept": "customer"}}],
        }

        with open(silver_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data, f)

        # Create gold model without meta.concept (should be inferred)
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        schema_data_gold = {
            "version": 2,
            "models": [{"name": "dim_customer"}],  # No meta.concept
        }

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data_gold, f)

        # Create manifest.json with lineage
        target_dir = tmppath / "target"
        target_dir.mkdir()

        manifest = {
            "nodes": {
                "model.test.stg_customer": {
                    "name": "stg_customer",
                    "original_file_path": "models/silver/stg_customer.sql",
                    "depends_on": {"nodes": ["source.test.raw.customers"]},
                },
                "model.test.dim_customer": {
                    "name": "dim_customer",
                    "original_file_path": "models/gold/dim_customer.sql",
                    "depends_on": {"nodes": ["model.test.stg_customer"]},
                },
            }
        }

        with open(target_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Check that dim_customer was inferred as gold model
        assert "customer" in state.concepts
        customer = state.concepts["customer"]

        # stg_customer should be explicit (has meta.concept)
        assert "stg_customer" in customer.silver_models

        # dim_customer should be inferred from downstream lineage
        assert "dim_customer" in customer.gold_models
        assert "dim_customer" in customer.inferred_models

        # stg_customer should NOT be in inferred (it's explicit)
        assert "stg_customer" not in customer.inferred_models


def test_lineage_inference_respects_explicit_tags() -> None:
    """Test that explicit meta.concept tags take precedence over inference."""
    import json

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with two concepts
        conceptual_dir = tmppath / "models" / "conceptual"
        conceptual_dir.mkdir(parents=True)

        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
            },
        }

        with open(conceptual_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create silver model for customer
        silver_dir = tmppath / "models" / "silver"
        silver_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "models": [{"name": "stg_customer", "meta": {"concept": "customer"}}],
        }

        with open(silver_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data, f)

        # Create gold model explicitly tagged with 'order' concept
        # This should NOT be inferred as 'customer' even though it depends on stg_customer
        gold_dir = tmppath / "models" / "gold"
        gold_dir.mkdir(parents=True)

        schema_data_gold = {
            "version": 2,
            "models": [
                {"name": "fact_orders", "meta": {"concept": "order"}}
            ],  # Explicitly tagged
        }

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data_gold, f)

        # Create manifest.json with lineage
        target_dir = tmppath / "target"
        target_dir.mkdir()

        manifest = {
            "nodes": {
                "model.test.stg_customer": {
                    "name": "stg_customer",
                    "original_file_path": "models/silver/stg_customer.sql",
                    "depends_on": {"nodes": []},
                },
                "model.test.fact_orders": {
                    "name": "fact_orders",
                    "original_file_path": "models/gold/fact_orders.sql",
                    "depends_on": {"nodes": ["model.test.stg_customer"]},
                },
            }
        }

        with open(target_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # fact_orders should belong to 'order' concept (explicit), not 'customer' (inferred)
        assert "fact_orders" in state.concepts["order"].gold_models
        assert "fact_orders" not in state.concepts["customer"].gold_models
        assert "fact_orders" not in state.concepts["customer"].inferred_models
