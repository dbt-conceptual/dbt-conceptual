"""Tests for parser and state builder.

v1.0: Simplified model - conceptual.yml in project root, flat models list.
"""

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

        # Create empty conceptual.yml in project root
        with open(tmppath / "conceptual.yml", "w") as f:
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

        # Create conceptual.yml in project root
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
                }
            },
            "relationships": [
                {
                    "verb": "places",
                    "from": "customer",
                    "to": "order",
                    "cardinality": "1:N",
                }
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
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
        # Status is derived: has domain but no models = "draft"
        assert state.concepts["customer"].status == "draft"

        assert len(state.relationships) == 1
        assert "customer:places:order" in state.relationships


def test_state_builder_links_models_to_concepts() -> None:
    """Test that state builder links dbt models to concepts."""
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

        # Create gold model
        gold_dir = tmppath / "models" / "marts"
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
        assert "dim_customer" in state.concepts["customer"].models
        # With models + domain, status should be "complete"
        assert state.concepts["customer"].status == "complete"


def test_state_builder_tracks_orphans() -> None:
    """Test that state builder tracks orphan models."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create empty conceptual.yml in project root
        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump({"version": 1}, f)

        # Create model without meta tags
        gold_dir = tmppath / "models" / "marts"
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


def test_validate_and_sync_creates_ghost_concepts() -> None:
    """Test that validate_and_sync creates ghost concepts for missing references."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with relationship to non-existent concept
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

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Check that ghost concept was created
        assert "order" in state.concepts
        assert state.concepts["order"].is_ghost is True

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
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer1": {"name": "Customer"},  # Same name
                "customer2": {"name": "Customer"},  # Same name
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
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
        conceptual_data = {
            "version": 1,
            "concepts": {},  # No concepts defined
            "relationships": [
                {"verb": "places", "from": "customer", "to": "order"},
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
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

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Should have at least: 1 error (missing order), 1 warning (empty domain), 1 info
        assert validation.error_count >= 1
        assert validation.warning_count >= 1

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

        with open(tmppath / "conceptual.yml", "w") as f:
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

        # Create conceptual.yml in project root
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()
        validation = builder.validate_and_sync(state)

        # Check that info message was generated
        assert validation.info_count >= 1
        info_msgs = [m for m in validation.messages if m.severity == "info"]
        assert any("Synced" in m.text and "concepts" in m.text for m in info_msgs)


def test_status_derived_from_domain_and_models() -> None:
    """Test that concept status is correctly derived from domain and models."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with various concepts
        conceptual_data = {
            "version": 1,
            "domains": {"party": {"name": "Party"}},
            "concepts": {
                "stub_concept": {"name": "Stub"},  # No domain = stub
                "draft_concept": {
                    "name": "Draft",
                    "domain": "party",
                },  # Domain but no models = draft
                "complete_concept": {
                    "name": "Complete",
                    "domain": "party",
                },  # Will have models = complete
            },
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create model for complete_concept
        gold_dir = tmppath / "models" / "marts"
        gold_dir.mkdir(parents=True)

        schema_data = {
            "version": 2,
            "models": [
                {"name": "dim_complete", "meta": {"concept": "complete_concept"}}
            ],
        }

        with open(gold_dir / "schema.yml", "w") as f:
            yaml.dump(schema_data, f)

        config = Config.load(project_dir=tmppath)
        builder = StateBuilder(config)
        state = builder.build()

        # Verify statuses
        assert state.concepts["stub_concept"].status == "stub"
        assert state.concepts["draft_concept"].status == "draft"
        assert state.concepts["complete_concept"].status == "complete"


def test_relationship_cardinality_validation() -> None:
    """Test that only 1:1 and 1:N cardinalities are allowed."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create dbt_project.yml
        with open(tmppath / "dbt_project.yml", "w") as f:
            yaml.dump({"name": "test"}, f)

        # Create conceptual.yml with various cardinalities
        conceptual_data = {
            "version": 1,
            "concepts": {
                "customer": {"name": "Customer"},
                "order": {"name": "Order"},
                "address": {"name": "Address"},
            },
            "relationships": [
                {
                    "verb": "places",
                    "from": "customer",
                    "to": "order",
                    "cardinality": "1:N",
                },
                {
                    "verb": "has",
                    "from": "customer",
                    "to": "address",
                    "cardinality": "1:1",
                },
                {
                    "verb": "invalid",
                    "from": "order",
                    "to": "address",
                    "cardinality": "N:M",
                },  # Invalid
            ],
        }

        with open(tmppath / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        config = Config.load(project_dir=tmppath)
        parser = ConceptualModelParser(config)
        state = parser.parse()

        # Check valid cardinalities preserved
        assert state.relationships["customer:places:order"].cardinality == "1:N"
        assert state.relationships["customer:has:address"].cardinality == "1:1"
        # Invalid cardinality should default to 1:N
        assert state.relationships["order:invalid:address"].cardinality == "1:N"
