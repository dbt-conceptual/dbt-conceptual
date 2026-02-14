"""Tests for MCP context resolution engine."""

import json
import tempfile
from pathlib import Path

import pytest

from dbt_conceptual.mcp.context import (
    ColumnInfo,
    ConceptContext,
    ContextResolver,
    ContractContext,
    FullContext,
    InferenceContext,
    ModelContext,
    RelationshipContext,
)
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    Guidance,
    GuidanceRule,
    ProjectState,
    RelationshipState,
)


@pytest.fixture
def sample_state() -> ProjectState:
    """Fixture for a sample project state.

    Contains:
    - 2 domains: party, transaction
    - 3 concepts: customer (draft), order (complete), payment (complete)
    - 1 relationship: customer -> order
    """
    state = ProjectState()

    # Domains
    state.domains["party"] = DomainState(
        name="party", display_name="Party", owner="data-team"
    )
    state.domains["transaction"] = DomainState(
        name="transaction", display_name="Transaction", owner="finance-team"
    )

    # Customer concept (draft - no models)
    state.concepts["customer"] = ConceptState(
        name="customer",
        domain="party",
        definition="A person or organization that purchases goods or services",
        guidance=Guidance(
            context="Critical entity for revenue tracking",
            rules=[
                GuidanceRule(
                    name="uniqueness",
                    description="customer_id must be globally unique",
                )
            ],
        ),
    )

    # Order concept (complete - has models)
    state.concepts["order"] = ConceptState(
        name="order",
        domain="transaction",
        owner="finance-team",
        definition="A customer purchase transaction",
        models=["fct_orders", "stg_orders"],
    )

    # Payment concept (complete - has models)
    state.concepts["payment"] = ConceptState(
        name="payment",
        domain="transaction",
        definition="Payment for an order",
        models=["fct_payments"],
    )

    # Relationship
    state.relationships["customer:places:order"] = RelationshipState(
        verb="places",
        from_concept="customer",
        to_concept="order",
        cardinality="1:N",
        definition="A customer can place many orders",
    )

    return state


@pytest.fixture
def sample_manifest() -> dict:
    """Fixture for a minimal dbt manifest.json."""
    return {
        "nodes": {
            "model.project.fct_orders": {
                "unique_id": "model.project.fct_orders",
                "resource_type": "model",
                "name": "fct_orders",
                "schema": "analytics",
                "description": "Order facts table",
                "original_file_path": "models/marts/fct_orders.sql",
                "config": {"materialized": "table"},
                "columns": {
                    "order_id": {
                        "name": "order_id",
                        "description": "Unique order identifier",
                    },
                    "customer_id": {
                        "name": "customer_id",
                        "description": "Foreign key to customer",
                    },
                    "order_date": {
                        "name": "order_date",
                        "description": "Date order was placed",
                    },
                },
                "depends_on": {"nodes": ["model.project.stg_orders"]},
            },
            "model.project.stg_orders": {
                "unique_id": "model.project.stg_orders",
                "resource_type": "model",
                "name": "stg_orders",
                "schema": "staging",
                "description": "Staging orders",
                "original_file_path": "models/staging/stg_orders.sql",
                "config": {"materialized": "view"},
                "columns": {
                    "order_id": {"name": "order_id", "description": "Order ID"},
                },
                "depends_on": {"nodes": []},
            },
            "model.project.fct_payments": {
                "unique_id": "model.project.fct_payments",
                "resource_type": "model",
                "name": "fct_payments",
                "schema": "analytics",
                "description": "Payment facts",
                "original_file_path": "models/marts/fct_payments.sql",
                "config": {"materialized": "incremental"},
                "columns": {
                    "payment_id": {"name": "payment_id", "description": "Payment ID"},
                },
                "depends_on": {"nodes": ["model.project.fct_orders"]},
            },
            "test.project.unique_order_id": {
                "unique_id": "test.project.unique_order_id",
                "resource_type": "test",
                "name": "unique_order_id",
                "attached_node": "model.project.fct_orders",
                "column_name": "order_id",
                "test_metadata": {
                    "name": "unique",
                    "kwargs": {"column_name": "order_id"},
                },
            },
            "test.project.not_null_order_id": {
                "unique_id": "test.project.not_null_order_id",
                "resource_type": "test",
                "name": "not_null_order_id",
                "attached_node": "model.project.fct_orders",
                "column_name": "order_id",
                "test_metadata": {
                    "name": "not_null",
                    "kwargs": {"column_name": "order_id"},
                },
            },
            "test.project.relationships_customer_id": {
                "unique_id": "test.project.relationships_customer_id",
                "resource_type": "test",
                "name": "relationships_customer_id",
                "attached_node": "model.project.fct_orders",
                "column_name": "customer_id",
                "test_metadata": {
                    "name": "relationships",
                    "kwargs": {
                        "column_name": "customer_id",
                        "to": "ref('dim_customer')",
                        "field": "customer_id",
                    },
                },
            },
        }
    }


@pytest.fixture
def sample_catalog() -> dict:
    """Fixture for a minimal dbt catalog.json."""
    return {
        "nodes": {
            "model.project.fct_orders": {
                "metadata": {"name": "fct_orders", "type": "table"},
                "columns": {
                    "order_id": {"name": "order_id", "type": "INTEGER"},
                    "customer_id": {"name": "customer_id", "type": "INTEGER"},
                    "order_date": {"name": "order_date", "type": "DATE"},
                },
                "stats": {"row_count": {"value": 1000}},
            },
            "model.project.fct_payments": {
                "metadata": {"name": "fct_payments", "type": "table"},
                "columns": {
                    "payment_id": {"name": "payment_id", "type": "INTEGER"},
                },
                "stats": {"row_count": {"value": 500}},
            },
        }
    }


@pytest.fixture
def temp_project_dir(sample_manifest, sample_catalog):
    """Create a temporary dbt project directory with manifest and catalog."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        target_dir = project_dir / "target"
        target_dir.mkdir()

        # Write manifest.json
        with open(target_dir / "manifest.json", "w") as f:
            json.dump(sample_manifest, f)

        # Write catalog.json
        with open(target_dir / "catalog.json", "w") as f:
            json.dump(sample_catalog, f)

        yield project_dir


def test_context_resolver_initialization(sample_state, temp_project_dir):
    """Test ContextResolver initializes correctly."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)

    assert resolver.state == sample_state
    assert resolver.project_dir == temp_project_dir
    assert resolver.manifest is not None
    assert resolver.catalog is not None
    assert resolver.inference_engine is not None


def test_context_resolver_missing_manifest(sample_state):
    """Test ContextResolver fails gracefully when manifest is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        with pytest.raises(FileNotFoundError, match="manifest.json not found"):
            ContextResolver(state=sample_state, project_dir=project_dir)


def test_context_resolver_missing_catalog(sample_state, sample_manifest):
    """Test ContextResolver handles missing catalog gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        target_dir = project_dir / "target"
        target_dir.mkdir()

        # Write only manifest, no catalog
        with open(target_dir / "manifest.json", "w") as f:
            json.dump(sample_manifest, f)

        resolver = ContextResolver(state=sample_state, project_dir=project_dir)

        assert resolver.manifest is not None
        assert resolver.catalog is None  # Gracefully missing


def test_resolve_full_context_single_concept(sample_state, temp_project_dir):
    """Test resolving full context for a single concept."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    # Layer 1: Conceptual context
    assert len(context.concepts) == 1
    concept = context.concepts[0]
    assert concept.name == "order"
    assert concept.domain == "transaction"
    assert concept.owner == "finance-team"
    assert concept.definition == "A customer purchase transaction"
    assert concept.status == "complete"

    # Relationships involving 'order'
    assert len(context.relationships) == 1
    rel = context.relationships[0]
    assert rel.verb == "places"
    assert rel.from_concept == "customer"
    assert rel.to_concept == "order"

    # Models for 'order' concept
    assert "fct_orders" in context.models
    assert "stg_orders" in context.models


def test_resolve_full_context_multiple_concepts(sample_state, temp_project_dir):
    """Test resolving full context for multiple concepts."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order", "payment"})

    # Should have 2 concepts
    assert len(context.concepts) == 2
    concept_names = {c.name for c in context.concepts}
    assert concept_names == {"order", "payment"}

    # Should have models from both concepts
    assert "fct_orders" in context.models
    assert "stg_orders" in context.models
    assert "fct_payments" in context.models


def test_resolve_concept_owner_inheritance(sample_state, temp_project_dir):
    """Test that concept inherits owner from domain if not set."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"customer"})

    # Customer concept doesn't have owner, should inherit from 'party' domain
    concept = context.concepts[0]
    assert concept.owner == "data-team"  # From party domain


def test_resolve_concept_guidance(sample_state, temp_project_dir):
    """Test that guidance is resolved correctly."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"customer"})

    concept = context.concepts[0]
    assert concept.guidance_context == "Critical entity for revenue tracking"
    assert len(concept.guidance_rules) == 1
    rule = concept.guidance_rules[0]
    assert rule["name"] == "uniqueness"
    assert rule["description"] == "customer_id must be globally unique"


def test_resolve_model_context_basic(sample_state, temp_project_dir):
    """Test resolving model context with basic metadata."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    model = context.models["fct_orders"]
    assert model.name == "fct_orders"
    assert model.materialization == "table"
    assert model.schema == "analytics"
    assert model.description == "Order facts table"
    assert model.path == "models/marts/fct_orders.sql"


def test_resolve_model_columns(sample_state, temp_project_dir):
    """Test resolving model columns with types and descriptions."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    model = context.models["fct_orders"]
    assert len(model.columns) == 3

    # Check column metadata
    order_id_col = next(c for c in model.columns if c.name == "order_id")
    assert order_id_col.description == "Unique order identifier"
    assert order_id_col.type == "INTEGER"  # From catalog


def test_resolve_model_dependencies(sample_state, temp_project_dir):
    """Test resolving upstream and downstream dependencies."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    fct_orders = context.models["fct_orders"]
    assert "model.project.stg_orders" in fct_orders.upstream
    assert "fct_payments" in fct_orders.downstream

    stg_orders = context.models["stg_orders"]
    assert len(stg_orders.upstream) == 0
    assert "fct_orders" in stg_orders.downstream


def test_resolve_model_constraints(sample_state, temp_project_dir):
    """Test translating tests to constraints."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    model = context.models["fct_orders"]

    # Column constraints
    order_id_col = next(c for c in model.columns if c.name == "order_id")
    assert "order_id must be unique" in order_id_col.constraints
    assert "order_id must not be null" in order_id_col.constraints

    customer_id_col = next(c for c in model.columns if c.name == "customer_id")
    assert any(
        "must reference a valid customer_id" in c for c in customer_id_col.constraints
    )


def test_resolve_catalog_row_count(sample_state, temp_project_dir):
    """Test resolving row count from catalog."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    model = context.models["fct_orders"]
    assert model.row_count == 1000


def test_resolve_inference_grain(sample_state, temp_project_dir):
    """Test grain inference from unique tests."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    inference = context.inferences["fct_orders"]
    assert inference.grain is not None
    assert "order_id" in inference.grain
    assert "order_id" in inference.grain_columns


def test_resolve_inference_risk(sample_state, temp_project_dir):
    """Test risk inference from downstream count."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    # fct_orders has 1 downstream (fct_payments)
    inference = context.inferences["fct_orders"]
    # Should not trigger risk (needs >= 5 downstream)
    assert inference.risk_level is None


def test_resolve_inference_materialization(sample_state, temp_project_dir):
    """Test materialization guidance inference."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"payment"})

    # fct_payments is incremental
    inference = context.inferences["fct_payments"]
    assert inference.materialization_guidance is not None
    assert "incremental" in inference.materialization_guidance.lower()


def test_resolve_contract_context(sample_state, temp_project_dir):
    """Test contract context is initialized (stub)."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"order"})

    # Contract context should exist but be empty (stub)
    assert "fct_orders" in context.contracts
    contract = context.contracts["fct_orders"]
    assert contract.enforcement_mode is None
    assert len(contract.checks) == 0


def test_resolve_unknown_concept(sample_state, temp_project_dir):
    """Test resolving unknown concept is handled gracefully."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"nonexistent"})

    # Should return empty context
    assert len(context.concepts) == 0
    assert len(context.models) == 0


def test_resolve_concept_with_no_models(sample_state, temp_project_dir):
    """Test resolving concept that has no models (draft status)."""
    resolver = ContextResolver(state=sample_state, project_dir=temp_project_dir)
    context = resolver.resolve_full_context({"customer"})

    # Should have concept but no models
    assert len(context.concepts) == 1
    assert context.concepts[0].status == "draft"
    assert len(context.models) == 0


def test_dataclass_initialization():
    """Test all dataclass types can be initialized."""
    # ConceptContext
    concept = ConceptContext(
        name="test", domain="test_domain", owner="test_owner", status="complete"
    )
    assert concept.name == "test"

    # RelationshipContext
    rel = RelationshipContext(
        verb="has", from_concept="a", to_concept="b", cardinality="1:N"
    )
    assert rel.verb == "has"

    # ColumnInfo
    col = ColumnInfo(name="col1", type="INTEGER", description="A column")
    assert col.name == "col1"
    assert len(col.constraints) == 0

    # ModelContext
    model = ModelContext(name="model1", materialization="table")
    assert model.name == "model1"
    assert len(model.columns) == 0

    # ContractContext
    contract = ContractContext(enforcement_mode="strict")
    assert contract.enforcement_mode == "strict"

    # InferenceContext
    inference = InferenceContext(grain="one row per id", risk_level="high")
    assert inference.grain == "one row per id"

    # FullContext
    full = FullContext()
    assert len(full.concepts) == 0
    assert len(full.relationships) == 0
    assert len(full.models) == 0
