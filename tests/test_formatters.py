"""Tests for formatters module."""

from __future__ import annotations

import json

from dbt_conceptual.formatters import (
    FullContext,
    ModelContext,
    RelationshipContext,
    format_json,
    format_llm,
    format_markdown,
)
from dbt_conceptual.inference import Confidence, Inference, InferenceType
from dbt_conceptual.state import ConceptState, Guidance, GuidanceRule


class TestFullContextDataclass:
    """Test FullContext dataclass structure."""

    def test_empty_context(self) -> None:
        """Test creating an empty FullContext."""
        ctx = FullContext()
        assert ctx.concepts == []
        assert ctx.relationships == []
        assert ctx.models == []
        assert ctx.inferences == []
        assert ctx.contracts == {}
        assert ctx.catalog == {}

    def test_context_with_data(self) -> None:
        """Test creating FullContext with data."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            owner="team-a",
            definition="A customer entity",
        )

        ctx = FullContext(
            concepts=[concept],
            relationships=[],
            models=[],
            inferences=[],
        )

        assert len(ctx.concepts) == 1
        assert ctx.concepts[0].name == "Customer"


class TestModelContext:
    """Test ModelContext dataclass."""

    def test_minimal_model_context(self) -> None:
        """Test ModelContext with minimal fields."""
        model = ModelContext(name="dim_customer")
        assert model.name == "dim_customer"
        assert model.materialization is None
        assert model.columns == []
        assert model.constraints == []

    def test_full_model_context(self) -> None:
        """Test ModelContext with all fields."""
        model = ModelContext(
            name="dim_customer",
            materialization="table",
            schema="analytics",
            description="Customer dimension",
            columns=[
                {"name": "customer_id", "type": "bigint", "description": "Primary key"}
            ],
            constraints=["customer_id must be unique", "customer_id must not be null"],
            upstream_models=["stg_customers"],
            downstream_models=["fct_orders"],
            path="models/marts/dim_customer.sql",
        )

        assert model.name == "dim_customer"
        assert model.materialization == "table"
        assert len(model.columns) == 1
        assert len(model.constraints) == 2


class TestRelationshipContext:
    """Test RelationshipContext dataclass."""

    def test_authored_relationship(self) -> None:
        """Test authored relationship."""
        rel = RelationshipContext(
            verb="places",
            from_concept="customer",
            to_concept="order",
            cardinality="1:N",
            definition="A customer places orders",
            is_inferred=False,
        )

        assert rel.verb == "places"
        assert rel.from_concept == "customer"
        assert rel.to_concept == "order"
        assert rel.cardinality == "1:N"
        assert rel.is_inferred is False

    def test_inferred_relationship(self) -> None:
        """Test inferred relationship."""
        rel = RelationshipContext(
            verb="references",
            from_concept="order",
            to_concept="customer",
            cardinality="1:1",
            is_inferred=True,
        )

        assert rel.is_inferred is True
        assert rel.definition is None


class TestFormatLLM:
    """Test LLM format output."""

    def test_single_concept_minimal(self) -> None:
        """Test LLM format with single minimal concept."""
        concept = ConceptState(name="Customer")
        ctx = FullContext(concepts=[concept])

        result = format_llm(ctx)

        assert "# Concept: Customer" in result
        assert "STUB (needs enrichment)" in result
        assert "Not assigned (needs domain assignment)" in result
        assert "No definition provided" in result
        assert "Negative Guidance (What NOT to Do)" in result

    def test_single_concept_complete(self) -> None:
        """Test LLM format with complete concept."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            owner="team-a",
            definition="A customer is an entity that purchases products.",
            models=["dim_customer"],
        )

        ctx = FullContext(concepts=[concept])
        result = format_llm(ctx)

        assert "# Concept: Customer" in result
        assert "COMPLETE (has models)" in result
        assert "**Domain:** party" in result
        assert "**Owner:** team-a" in result
        assert "## Definition (Authored)" in result
        assert "A customer is an entity that purchases products." in result

    def test_concept_with_guidance(self) -> None:
        """Test LLM format with guidance."""
        guidance = Guidance(
            context="Customers are critical business entities",
            rules=[
                GuidanceRule(
                    name="grain",
                    description="One row per customer_id",
                ),
                GuidanceRule(
                    name="freshness",
                    description="Updated daily at 3am UTC",
                ),
            ],
        )

        concept = ConceptState(
            name="Customer",
            domain="party",
            definition="A customer entity",
            guidance=guidance,
        )

        ctx = FullContext(concepts=[concept])
        result = format_llm(ctx)

        assert "## Implementation Guidance (Authored)" in result
        assert "**Business Context:**" in result
        assert "Customers are critical business entities" in result
        assert "**Rules:**" in result
        assert "**grain:** One row per customer_id" in result
        assert "**freshness:** Updated daily at 3am UTC" in result

    def test_concept_with_relationships_outbound(self) -> None:
        """Test LLM format with outbound relationships."""
        concept = ConceptState(name="Customer", domain="party")

        rel = RelationshipContext(
            verb="places",
            from_concept="Customer",
            to_concept="Order",
            cardinality="1:N",
            definition="Customers place orders",
            is_inferred=False,
        )

        ctx = FullContext(concepts=[concept], relationships=[rel])
        result = format_llm(ctx)

        assert "## Relationships" in result
        assert "**Outbound (from this concept):**" in result
        assert "places → **Order** [1:N] (AUTHORED)" in result
        assert "Joining may fan out results (1:N relationship)" in result
        assert "*Customers place orders*" in result

    def test_concept_with_relationships_inbound(self) -> None:
        """Test LLM format with inbound relationships."""
        concept = ConceptState(name="Order", domain="sales")

        rel = RelationshipContext(
            verb="places",
            from_concept="Customer",
            to_concept="Order",
            cardinality="1:N",
            is_inferred=True,  # Inferred from lineage
        )

        ctx = FullContext(concepts=[concept], relationships=[rel])
        result = format_llm(ctx)

        assert "## Relationships" in result
        assert "**Inbound (to this concept):**" in result
        assert "Customer → **places** [1:N] (INFERRED)" in result

    def test_concept_with_one_to_one_relationship(self) -> None:
        """Test LLM format with 1:1 relationship (no fan-out warning)."""
        concept = ConceptState(name="Customer", domain="party")

        rel = RelationshipContext(
            verb="has",
            from_concept="Customer",
            to_concept="CustomerProfile",
            cardinality="1:1",
            is_inferred=False,
        )

        ctx = FullContext(concepts=[concept], relationships=[rel])
        result = format_llm(ctx)

        assert "One-to-one relationship (1:1)" in result
        assert "fan out" not in result.lower()  # No fan-out warning for 1:1

    def test_concept_with_model(self) -> None:
        """Test LLM format with model implementation."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            models=["dim_customer"],
        )

        model = ModelContext(
            name="dim_customer",
            materialization="table",
            schema="analytics",
            description="Customer dimension table",
            columns=[
                {"name": "customer_id", "type": "bigint", "description": "Primary key"},
                {"name": "email", "type": "varchar", "description": "Email address"},
            ],
            constraints=[
                "customer_id must be unique",
                "customer_id must not be null",
            ],
            upstream_models=["stg_customers"],
            downstream_models=["fct_orders", "fct_returns"],
            path="models/marts/dim_customer.sql",
        )

        ctx = FullContext(concepts=[concept], models=[model])
        result = format_llm(ctx)

        assert "## Model Implementations" in result
        assert "### Model: dim_customer" in result
        assert "**Materialization:** table" in result
        assert "**Schema:** analytics" in result
        assert "**Path:** models/marts/dim_customer.sql" in result
        assert "**Description:**" in result
        assert "Customer dimension table" in result
        assert "**Constraints (from dbt tests):**" in result
        assert "- customer_id must be unique" in result
        assert "**Columns:**" in result
        assert "- `customer_id` (bigint)" in result
        assert "  Primary key" in result
        assert "**Upstream:** stg_customers" in result
        assert "**Downstream:** fct_orders, fct_returns" in result

    def test_concept_with_grain_inference(self) -> None:
        """Test LLM format with grain inference."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            models=["dim_customer"],
        )

        model = ModelContext(name="dim_customer")

        inference = Inference(
            type=InferenceType.GRAIN,
            message="Grain appears to be one row per customer_id",
            confidence=Confidence.HIGH,
            metadata={
                "model_name": "dim_customer",
                "grain_columns": ["customer_id"],
            },
        )

        ctx = FullContext(concepts=[concept], models=[model], inferences=[inference])
        result = format_llm(ctx)

        assert (
            "**Grain (INFERRED):** Grain appears to be one row per customer_id"
            in result
        )
        assert "*Based on unique test on columns: customer_id*" in result

    def test_concept_without_grain_inference(self) -> None:
        """Test LLM format when no grain inference exists."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            models=["dim_customer"],
        )

        model = ModelContext(name="dim_customer")

        ctx = FullContext(concepts=[concept], models=[model])
        result = format_llm(ctx)

        assert "**Grain:** Not explicitly defined (no unique tests found)" in result

    def test_concept_with_additional_inferences(self) -> None:
        """Test LLM format with non-grain inferences."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            models=["dim_customer"],
        )

        inferences = [
            Inference(
                type=InferenceType.RISK,
                message="High-risk model: 15 downstream dependents",
                confidence=Confidence.HIGH,
                metadata={"concept_name": "Customer"},
            ),
            Inference(
                type=InferenceType.MATERIALIZATION,
                message="Incremental model: remember --full-refresh",
                confidence=Confidence.HIGH,
                metadata={"concept_name": "Customer"},
            ),
        ]

        ctx = FullContext(concepts=[concept], inferences=inferences)
        result = format_llm(ctx)

        assert "## Additional Inferences" in result
        assert "[✓ HIGH] High-risk model: 15 downstream dependents" in result
        assert "[✓ HIGH] Incremental model: remember --full-refresh" in result

    def test_negative_guidance_stub(self) -> None:
        """Test negative guidance for stub concept."""
        concept = ConceptState(name="Customer")  # No domain = stub

        ctx = FullContext(concepts=[concept])
        result = format_llm(ctx)

        assert "## Negative Guidance (What NOT to Do)" in result
        assert (
            "Do NOT use this concept in production queries until it has a domain and definition"
            in result
        )

    def test_negative_guidance_draft(self) -> None:
        """Test negative guidance for draft concept."""
        concept = ConceptState(
            name="Customer", domain="party"
        )  # Domain but no models = draft

        ctx = FullContext(concepts=[concept])
        result = format_llm(ctx)

        assert (
            "Do NOT reference models for this concept yet (no models exist)" in result
        )

    def test_negative_guidance_no_guidance(self) -> None:
        """Test negative guidance when no implementation guidance exists."""
        concept = ConceptState(name="Customer", domain="party", models=["dim_customer"])

        ctx = FullContext(concepts=[concept])
        result = format_llm(ctx)

        assert (
            "Do NOT make assumptions about implementation without consulting the owner"
            in result
        )

    def test_negative_guidance_fan_out_warning(self) -> None:
        """Test negative guidance includes fan-out warning."""
        concept = ConceptState(name="Customer", domain="party")

        rel = RelationshipContext(
            verb="places",
            from_concept="Customer",
            to_concept="Order",
            cardinality="1:N",
        )

        ctx = FullContext(concepts=[concept], relationships=[rel])
        result = format_llm(ctx)

        assert (
            "CAUTION: Joining to Order will fan out your results (1:N relationships)"
            in result
        )

    def test_multiple_concepts_with_wrapper(self) -> None:
        """Test LLM format with multiple concepts includes XML wrapper."""
        concepts = [
            ConceptState(name="Customer", domain="party"),
            ConceptState(name="Order", domain="sales"),
        ]

        ctx = FullContext(concepts=concepts)
        result = format_llm(ctx)

        assert '<concepts count="2">' in result
        assert "</concepts>" in result
        assert "## Summary" in result
        assert "This context includes 2 concepts" in result

    def test_single_concept_no_wrapper(self) -> None:
        """Test LLM format with single concept has no XML wrapper."""
        concept = ConceptState(name="Customer", domain="party")

        ctx = FullContext(concepts=[concept])
        result = format_llm(ctx)

        assert "<concepts" not in result
        assert "</concepts>" not in result
        assert "## Summary" not in result


class TestFormatJSON:
    """Test JSON format output."""

    def test_empty_context(self) -> None:
        """Test JSON format with empty context."""
        ctx = FullContext()
        result = format_json(ctx)
        data = json.loads(result)

        assert data["concepts"] == []
        assert data["relationships"] == []
        assert data["models"] == []
        assert data["inferences"] == []
        assert data["contracts"] == {}
        assert data["catalog"] == {}
        assert data["summary"]["concept_count"] == 0

    def test_single_concept(self) -> None:
        """Test JSON format with single concept."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            owner="team-a",
            definition="A customer entity",
            models=["dim_customer"],
        )

        ctx = FullContext(concepts=[concept])
        result = format_json(ctx)
        data = json.loads(result)

        assert len(data["concepts"]) == 1
        assert data["concepts"][0]["name"] == "Customer"
        assert data["concepts"][0]["domain"] == "party"
        assert data["concepts"][0]["owner"] == "team-a"
        assert data["concepts"][0]["status"] == "complete"
        assert data["concepts"][0]["definition"] == "A customer entity"
        assert data["concepts"][0]["models"] == ["dim_customer"]
        assert data["concepts"][0]["is_ghost"] is False
        assert data["concepts"][0]["validation_status"] == "valid"

    def test_concept_with_guidance(self) -> None:
        """Test JSON format includes guidance structure."""
        guidance = Guidance(
            context="Business context",
            rules=[
                GuidanceRule(name="grain", description="One row per customer_id"),
            ],
        )

        concept = ConceptState(
            name="Customer",
            domain="party",
            guidance=guidance,
        )

        ctx = FullContext(concepts=[concept])
        result = format_json(ctx)
        data = json.loads(result)

        assert data["concepts"][0]["guidance"] is not None
        assert data["concepts"][0]["guidance"]["context"] == "Business context"
        assert len(data["concepts"][0]["guidance"]["rules"]) == 1
        assert data["concepts"][0]["guidance"]["rules"][0]["name"] == "grain"

    def test_concept_without_guidance(self) -> None:
        """Test JSON format with no guidance."""
        concept = ConceptState(name="Customer", domain="party")

        ctx = FullContext(concepts=[concept])
        result = format_json(ctx)
        data = json.loads(result)

        assert data["concepts"][0]["guidance"] is None

    def test_relationships(self) -> None:
        """Test JSON format includes relationships."""
        rel1 = RelationshipContext(
            verb="places",
            from_concept="Customer",
            to_concept="Order",
            cardinality="1:N",
            definition="Customers place orders",
            is_inferred=False,
        )

        rel2 = RelationshipContext(
            verb="references",
            from_concept="Order",
            to_concept="Customer",
            cardinality="1:1",
            is_inferred=True,
        )

        ctx = FullContext(relationships=[rel1, rel2])
        result = format_json(ctx)
        data = json.loads(result)

        assert len(data["relationships"]) == 2
        assert data["relationships"][0]["verb"] == "places"
        assert data["relationships"][0]["from_concept"] == "Customer"
        assert data["relationships"][0]["to_concept"] == "Order"
        assert data["relationships"][0]["cardinality"] == "1:N"
        assert data["relationships"][0]["is_inferred"] is False
        assert data["relationships"][1]["is_inferred"] is True

    def test_models(self) -> None:
        """Test JSON format includes models."""
        model = ModelContext(
            name="dim_customer",
            materialization="table",
            schema="analytics",
            description="Customer dimension",
            columns=[{"name": "customer_id", "type": "bigint"}],
            constraints=["customer_id must be unique"],
            upstream_models=["stg_customers"],
            downstream_models=["fct_orders"],
            path="models/marts/dim_customer.sql",
        )

        ctx = FullContext(models=[model])
        result = format_json(ctx)
        data = json.loads(result)

        assert len(data["models"]) == 1
        assert data["models"][0]["name"] == "dim_customer"
        assert data["models"][0]["materialization"] == "table"
        assert data["models"][0]["schema"] == "analytics"
        assert len(data["models"][0]["columns"]) == 1
        assert len(data["models"][0]["constraints"]) == 1
        assert data["models"][0]["upstream_models"] == ["stg_customers"]

    def test_inferences(self) -> None:
        """Test JSON format includes inferences."""
        inf = Inference(
            type=InferenceType.GRAIN,
            message="Grain appears to be one row per customer_id",
            confidence=Confidence.HIGH,
            metadata={"grain_columns": ["customer_id"]},
        )

        ctx = FullContext(inferences=[inf])
        result = format_json(ctx)
        data = json.loads(result)

        assert len(data["inferences"]) == 1
        assert data["inferences"][0]["type"] == "grain"
        assert data["inferences"][0]["confidence"] == "high"
        assert (
            data["inferences"][0]["message"]
            == "Grain appears to be one row per customer_id"
        )
        assert data["inferences"][0]["metadata"]["grain_columns"] == ["customer_id"]

    def test_summary_counts(self) -> None:
        """Test JSON format summary counts."""
        concepts = [
            ConceptState(name="Customer", domain="party"),
            ConceptState(name="Order", domain="sales"),
        ]

        relationships = [
            RelationshipContext(
                verb="places",
                from_concept="Customer",
                to_concept="Order",
                cardinality="1:N",
            )
        ]

        models = [
            ModelContext(name="dim_customer"),
            ModelContext(name="fct_orders"),
        ]

        inferences = [
            Inference(
                type=InferenceType.GRAIN,
                message="Test",
                confidence=Confidence.HIGH,
            )
        ]

        ctx = FullContext(
            concepts=concepts,
            relationships=relationships,
            models=models,
            inferences=inferences,
        )
        result = format_json(ctx)
        data = json.loads(result)

        assert data["summary"]["concept_count"] == 2
        assert data["summary"]["relationship_count"] == 1
        assert data["summary"]["model_count"] == 2
        assert data["summary"]["inference_count"] == 1

    def test_contracts_and_catalog(self) -> None:
        """Test JSON format includes contracts and catalog."""
        ctx = FullContext(
            contracts={"dim_customer": {"enforced": True}},
            catalog={"dim_customer": {"row_count": 1000}},
        )

        result = format_json(ctx)
        data = json.loads(result)

        assert data["contracts"]["dim_customer"]["enforced"] is True
        assert data["catalog"]["dim_customer"]["row_count"] == 1000


class TestFormatMarkdown:
    """Test Markdown format output."""

    def test_empty_context(self) -> None:
        """Test markdown format with empty context."""
        ctx = FullContext()
        result = format_markdown(ctx)

        # Empty context should produce minimal output
        assert result.strip() == "---"

    def test_single_concept_minimal(self) -> None:
        """Test markdown format with minimal concept."""
        concept = ConceptState(name="Customer")

        ctx = FullContext(concepts=[concept])
        result = format_markdown(ctx)

        assert "# Customer" in result
        assert "| Property | Value |" in result
        assert "| Status | stub |" in result
        assert "| Domain | *Not assigned* |" in result
        assert "## Definition" in result
        assert "*No definition provided.*" in result

    def test_single_concept_complete(self) -> None:
        """Test markdown format with complete concept."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            owner="team-a",
            definition="A customer is an entity that purchases products.",
            models=["dim_customer"],
        )

        ctx = FullContext(concepts=[concept])
        result = format_markdown(ctx)

        assert "# Customer" in result
        assert "| Status | complete |" in result
        assert "| Domain | party |" in result
        assert "| Owner | team-a |" in result
        assert "| Model Count | 1 |" in result
        assert "A customer is an entity that purchases products." in result

    def test_concept_with_guidance(self) -> None:
        """Test markdown format with guidance."""
        guidance = Guidance(
            context="Business context here",
            rules=[
                GuidanceRule(name="grain", description="One row per customer_id"),
                GuidanceRule(name="freshness", description="Daily updates"),
            ],
        )

        concept = ConceptState(
            name="Customer",
            domain="party",
            guidance=guidance,
        )

        ctx = FullContext(concepts=[concept])
        result = format_markdown(ctx)

        assert "## Implementation Guidance" in result
        assert "### Business Context" in result
        assert "Business context here" in result
        assert "### Rules" in result
        assert "**grain**" in result
        assert "One row per customer_id" in result
        assert "**freshness**" in result
        assert "Daily updates" in result

    def test_relationships_table(self) -> None:
        """Test markdown format relationships table."""
        concept = ConceptState(name="Customer", domain="party")

        rels = [
            RelationshipContext(
                verb="places",
                from_concept="Customer",
                to_concept="Order",
                cardinality="1:N",
                is_inferred=False,
            ),
            RelationshipContext(
                verb="belongs_to",
                from_concept="Order",
                to_concept="Customer",
                cardinality="1:1",
                is_inferred=True,
            ),
        ]

        ctx = FullContext(concepts=[concept], relationships=rels)
        result = format_markdown(ctx)

        assert "## Relationships" in result
        assert "| Direction | Verb | Related Concept | Cardinality | Source |" in result
        assert "| → | places | Order | 1:N | Authored |" in result
        assert "| ← | belongs_to | Order | 1:1 | Inferred |" in result

    def test_models_section(self) -> None:
        """Test markdown format models section."""
        concept = ConceptState(
            name="Customer",
            domain="party",
            models=["dim_customer"],
        )

        model = ModelContext(
            name="dim_customer",
            materialization="table",
            schema="analytics",
            description="Customer dimension table",
            columns=[
                {"name": "customer_id", "type": "bigint", "description": "Primary key"},
                {"name": "email", "type": "varchar", "description": "Email"},
            ],
            constraints=["customer_id must be unique"],
            upstream_models=["stg_customers"],
            downstream_models=["fct_orders"],
            path="models/marts/dim_customer.sql",
        )

        ctx = FullContext(concepts=[concept], models=[model])
        result = format_markdown(ctx)

        assert "## Models" in result
        assert "### `dim_customer`" in result
        assert "| Materialization | table |" in result
        assert "| Schema | analytics |" in result
        assert "| Path | `models/marts/dim_customer.sql` |" in result
        assert "**Description:**" in result
        assert "Customer dimension table" in result
        assert "**Constraints:**" in result
        assert "- customer_id must be unique" in result
        assert "**Columns:**" in result
        assert "| Name | Type | Description |" in result
        assert "| `customer_id` | bigint | Primary key |" in result
        assert "| `email` | varchar | Email |" in result
        assert "**Dependencies:**" in result
        assert "- **Upstream:** `stg_customers`" in result
        assert "- **Downstream:** `fct_orders`" in result

    def test_inferences_table(self) -> None:
        """Test markdown format inferences table."""
        concept = ConceptState(name="Customer", domain="party")

        inferences = [
            Inference(
                type=InferenceType.GRAIN,
                message="One row per customer_id",
                confidence=Confidence.HIGH,
                metadata={"concept_name": "Customer"},
            ),
            Inference(
                type=InferenceType.RISK,
                message="High-risk model",
                confidence=Confidence.MEDIUM,
                metadata={"concept_name": "Customer"},
            ),
        ]

        ctx = FullContext(concepts=[concept], inferences=inferences)
        result = format_markdown(ctx)

        assert "## Inferences" in result
        assert "| Type | Confidence | Message |" in result
        assert "| grain | high | One row per customer_id |" in result
        assert "| risk | medium | High-risk model |" in result

    def test_multiple_concepts_summary(self) -> None:
        """Test markdown format includes summary for multiple concepts."""
        concepts = [
            ConceptState(name="Customer", domain="party"),
            ConceptState(name="Order", domain="sales"),
        ]

        ctx = FullContext(concepts=concepts)
        result = format_markdown(ctx)

        assert "# Context Summary" in result
        assert "| Metric | Count |" in result
        assert "| Concepts | 2 |" in result

    def test_single_concept_no_summary(self) -> None:
        """Test markdown format has no summary for single concept."""
        concept = ConceptState(name="Customer", domain="party")

        ctx = FullContext(concepts=[concept])
        result = format_markdown(ctx)

        assert "# Context Summary" not in result
