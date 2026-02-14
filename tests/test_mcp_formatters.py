"""Tests for MCP output formatters."""

from __future__ import annotations

import json

import pytest

from dbt_conceptual.mcp.context import (
    ColumnInfo,
    ConceptContext,
    ContractContext,
    FullContext,
    InferenceContext,
    ModelContext,
    RelationshipContext,
)
from dbt_conceptual.mcp.formatters import (
    format_context,
    format_json,
    format_llm,
    format_markdown,
)


@pytest.fixture
def minimal_context():
    """Minimal FullContext with one concept."""
    return FullContext(
        concepts=[
            ConceptContext(
                name="customer",
                domain="sales",
                owner="sales-team",
                definition="A person or organization that purchases products.",
                status="complete",
            )
        ]
    )


@pytest.fixture
def full_context():
    """Full FullContext with all layers populated."""
    return FullContext(
        concepts=[
            ConceptContext(
                name="customer",
                domain="sales",
                owner="sales-team",
                definition="A person or organization that purchases products.",
                color="#FF5733",
                guidance_context="Customers are identified by a unique customer_id. All customer data must comply with GDPR.",
                guidance_rules=[
                    {
                        "name": "PII Protection",
                        "description": "Never expose raw email or phone numbers without masking",
                    },
                    {
                        "name": "Deduplication",
                        "description": "Use customer_id as the primary grain; never count by email as customers may have multiple emails",
                    },
                ],
                status="complete",
            )
        ],
        relationships=[
            RelationshipContext(
                verb="places",
                from_concept="customer",
                to_concept="order",
                cardinality="1:N",
                definition="A customer can place multiple orders over time",
                owner="sales-team",
            )
        ],
        models={
            "dim_customer": ModelContext(
                name="dim_customer",
                materialization="table",
                schema="analytics",
                description="Customer dimension with SCD2 tracking",
                path="models/dimensions/dim_customer.sql",
                columns=[
                    ColumnInfo(
                        name="customer_id",
                        type="INTEGER",
                        description="Unique customer identifier",
                        constraints=["not null", "unique"],
                    ),
                    ColumnInfo(
                        name="customer_name",
                        type="VARCHAR",
                        description="Customer full name",
                        constraints=["not null"],
                    ),
                    ColumnInfo(
                        name="email",
                        type="VARCHAR",
                        description="Primary email address",
                        constraints=[],
                    ),
                ],
                constraints=["row count > 0"],
                upstream=[
                    "model.project.stg_customers",
                    "model.project.stg_customer_emails",
                ],
                downstream=["fct_orders", "fct_revenue"],
                row_count=15234,
            )
        },
        contracts={
            "dim_customer": ContractContext(
                enforcement_mode="strict",
                checks=["customer_id is unique", "customer_name is not null"],
                sla_expectations={"freshness": "1 hour"},
            )
        },
        inferences={
            "dim_customer": InferenceContext(
                grain="one row per customer_id",
                grain_columns=["customer_id"],
                risk_level="low",
                risk_message="Well-tested dimension with unique key constraints",
                materialization_guidance="Table materialization is appropriate for frequently-joined dimension",
                data_vault_pattern="hub",
                layer="silver",
                quality_warnings=[
                    "No tests on email column - consider adding format validation"
                ],
            )
        },
    )


@pytest.fixture
def multi_concept_context():
    """Context with multiple concepts."""
    return FullContext(
        concepts=[
            ConceptContext(
                name="customer",
                domain="sales",
                owner="sales-team",
                definition="A person who purchases products",
                status="complete",
            ),
            ConceptContext(
                name="order",
                domain="sales",
                owner="sales-team",
                definition="A customer purchase transaction",
                status="complete",
            ),
        ],
        relationships=[
            RelationshipContext(
                verb="places",
                from_concept="customer",
                to_concept="order",
                cardinality="1:N",
            )
        ],
    )


class TestFormatContext:
    """Tests for format_context entry point."""

    def test_format_context_llm(self, minimal_context):
        """Test format_context with llm format."""
        result = format_context(minimal_context, "llm")
        assert "Concept: customer" in result
        assert "[authored]" in result

    def test_format_context_json(self, minimal_context):
        """Test format_context with json format."""
        result = format_context(minimal_context, "json")
        data = json.loads(result)
        assert "concepts" in data
        assert data["concepts"][0]["name"] == "customer"

    def test_format_context_markdown(self, minimal_context):
        """Test format_context with markdown format."""
        result = format_context(minimal_context, "markdown")
        assert "# Concept: customer" in result
        assert "| Property | Value |" in result

    def test_format_context_invalid_format(self, minimal_context):
        """Test format_context with invalid format raises error."""
        with pytest.raises(ValueError, match="Unsupported format"):
            format_context(minimal_context, "xml")


class TestFormatLLM:
    """Tests for LLM format output."""

    def test_llm_minimal_concept(self, minimal_context):
        """Test LLM format with minimal concept."""
        result = format_llm(minimal_context)

        # Should have concept header
        assert "# Concept: customer" in result

        # Should have status and metadata
        assert "Status: complete [authored]" in result
        assert "Domain: sales [authored]" in result
        assert "Owner: sales-team [authored]" in result

        # Should have definition
        assert "## Definition [authored]" in result
        assert "A person or organization that purchases products" in result

    def test_llm_full_concept(self, full_context):
        """Test LLM format with all layers populated."""
        result = format_llm(full_context)

        # Concept metadata
        assert "# Concept: customer" in result
        assert "Status: complete [authored]" in result

        # Guidance prominently displayed
        assert "## Business Guidance [authored]" in result
        assert "Customers are identified by a unique customer_id" in result
        assert "IMPORTANT RULES:" in result
        assert "**PII Protection**" in result
        assert "**Deduplication**" in result

        # Relationships with grain warnings
        assert "## Relationships [authored]" in result
        assert "This concept places order" in result
        assert "WARNING: This is a 1:N relationship" in result
        assert "DO NOT join to order without accounting for fan-out" in result

        # Model implementation
        assert "## Model Implementations" in result
        assert "### Model: dim_customer [authored]" in result
        assert "This model is materialized as a table in schema analytics" in result

        # Grain inference
        assert "**Grain [inferred]**: one row per customer_id" in result
        assert "Grain columns: customer_id" in result

        # Risk assessment
        assert "**Risk Assessment [inferred]**" in result
        assert "Well-tested dimension" in result

        # Quality warnings
        assert "**Quality Warnings [inferred]**:" in result
        assert "No tests on email column" in result

        # Materialization guidance
        assert "**Materialization Guidance [inferred]**" in result
        assert "Table materialization is appropriate" in result

        # Data Vault pattern
        assert "**Data Vault Pattern [inferred]**: hub" in result

        # Layer
        assert "**Layer [inferred]**: silver" in result

        # Columns
        assert "**Columns [authored]**:" in result
        assert "`customer_id`" in result
        assert "(INTEGER)" in result
        assert "Unique customer identifier" in result
        assert "[Constraints: not null, unique]" in result

        # Table constraints
        assert "**Table Constraints [authored]**:" in result
        assert "row count > 0" in result

        # Dependencies
        assert "**Upstream Dependencies [authored]**" in result
        assert "stg_customers" in result
        assert "**Downstream Consumers [authored]**" in result
        assert "fct_orders" in result
        assert "Changes to this model may impact these downstream models" in result

        # Row count
        assert "**Row Count [authored]**: 15,234" in result

        # Contract
        assert "**Contract Enforcement [authored]**: strict" in result
        assert "customer_id is unique" in result

    def test_llm_multi_concept_xml_tags(self, multi_concept_context):
        """Test LLM format with multiple concepts uses XML tags."""
        result = format_llm(multi_concept_context)

        # Should have concepts wrapper
        assert '<concepts count="2">' in result
        assert "</concepts>" in result

        # Should have individual concept tags
        assert '<concept name="customer">' in result
        assert "</concept>" in result
        assert '<concept name="order">' in result

        # Should have both concept headers
        assert "# Concept: customer" in result
        assert "# Concept: order" in result

    def test_llm_relationship_from_other_side(self):
        """Test relationship display when concept is on the 'to' side."""
        context = FullContext(
            concepts=[
                ConceptContext(
                    name="order",
                    definition="A purchase transaction",
                    status="complete",
                )
            ],
            relationships=[
                RelationshipContext(
                    verb="places",
                    from_concept="customer",
                    to_concept="order",
                    cardinality="1:N",
                )
            ],
        )

        result = format_llm(context)

        assert "## Relationships [authored]" in result
        assert "This concept places customer" in result
        # Should note it's from customer's perspective, not show warning
        assert "Note: This is a 1:N relationship from customer's perspective" in result

    def test_llm_no_guidance(self):
        """Test LLM format when guidance is absent."""
        context = FullContext(
            concepts=[
                ConceptContext(
                    name="test",
                    definition="Test concept",
                    status="stub",
                )
            ]
        )

        result = format_llm(context)

        # Should not have guidance section
        assert "## Business Guidance" not in result
        assert "IMPORTANT RULES:" not in result

    def test_llm_no_models(self):
        """Test LLM format when no models are present."""
        context = FullContext(
            concepts=[
                ConceptContext(
                    name="test",
                    definition="Test concept",
                    status="stub",
                )
            ]
        )

        result = format_llm(context)

        # Should not have model implementations section
        assert "## Model Implementations" not in result


class TestFormatJSON:
    """Tests for JSON format output."""

    def test_json_minimal_concept(self, minimal_context):
        """Test JSON format with minimal concept."""
        result = format_json(minimal_context)
        data = json.loads(result)

        # Validate structure
        assert "concepts" in data
        assert "relationships" in data
        assert "models" in data
        assert "contracts" in data
        assert "inferences" in data

        # Validate concept data
        assert len(data["concepts"]) == 1
        concept = data["concepts"][0]
        assert concept["name"] == "customer"
        assert concept["domain"] == "sales"
        assert concept["owner"] == "sales-team"
        assert (
            concept["definition"] == "A person or organization that purchases products."
        )
        assert concept["status"] == "complete"

    def test_json_full_context(self, full_context):
        """Test JSON format with all layers."""
        result = format_json(full_context)
        data = json.loads(result)

        # Validate concepts
        assert len(data["concepts"]) == 1
        concept = data["concepts"][0]
        assert concept["name"] == "customer"
        assert concept["color"] == "#FF5733"
        assert concept["guidance_context"] is not None
        assert len(concept["guidance_rules"]) == 2
        assert concept["guidance_rules"][0]["name"] == "PII Protection"

        # Validate relationships
        assert len(data["relationships"]) == 1
        rel = data["relationships"][0]
        assert rel["verb"] == "places"
        assert rel["from_concept"] == "customer"
        assert rel["to_concept"] == "order"
        assert rel["cardinality"] == "1:N"

        # Validate models
        assert "dim_customer" in data["models"]
        model = data["models"]["dim_customer"]
        assert model["name"] == "dim_customer"
        assert model["materialization"] == "table"
        assert model["schema"] == "analytics"
        assert len(model["columns"]) == 3
        assert model["columns"][0]["name"] == "customer_id"
        assert model["columns"][0]["type"] == "INTEGER"

        # Validate contracts
        assert "dim_customer" in data["contracts"]
        contract = data["contracts"]["dim_customer"]
        assert contract["enforcement_mode"] == "strict"
        assert len(contract["checks"]) == 2

        # Validate inferences
        assert "dim_customer" in data["inferences"]
        inference = data["inferences"]["dim_customer"]
        assert inference["grain"] == "one row per customer_id"
        assert inference["grain_columns"] == ["customer_id"]
        assert inference["risk_level"] == "low"
        assert inference["data_vault_pattern"] == "hub"
        assert inference["layer"] == "silver"

    def test_json_is_valid_parseable(self, full_context):
        """Test that JSON output is valid and parseable."""
        result = format_json(full_context)

        # Should not raise
        data = json.loads(result)

        # Should be a dict
        assert isinstance(data, dict)

    def test_json_pretty_printed(self, minimal_context):
        """Test that JSON is pretty-printed with indentation."""
        result = format_json(minimal_context)

        # Should have indentation (newlines and spaces)
        assert "\n" in result
        assert "  " in result


class TestFormatMarkdown:
    """Tests for Markdown format output."""

    def test_markdown_minimal_concept(self, minimal_context):
        """Test Markdown format with minimal concept."""
        result = format_markdown(minimal_context)

        # Should have title
        assert "# Concept: customer" in result

        # Should have metadata table
        assert "| Property | Value |" in result
        assert "| **Status** | complete |" in result
        assert "| **Domain** | sales |" in result
        assert "| **Owner** | sales-team |" in result

        # Should have definition section
        assert "### Definition" in result
        assert "A person or organization that purchases products" in result

    def test_markdown_full_context(self, full_context):
        """Test Markdown format with all layers."""
        result = format_markdown(full_context)

        # Title and metadata
        assert "# Concept: customer" in result
        assert "| **Status** | complete |" in result
        assert "| **Color** | #FF5733 |" in result

        # Definition
        assert "### Definition" in result

        # Guidance
        assert "### Business Guidance" in result
        assert "Customers are identified by a unique customer_id" in result
        assert "**Rules:**" in result
        assert "- **PII Protection**" in result
        assert "- **Deduplication**" in result

        # Relationships table
        assert "### Relationships" in result
        assert "| Verb | To/From | Cardinality | Definition |" in result
        assert (
            "| places | to order | 1:N | A customer can place multiple orders over time |"
            in result
        )

        # Models
        assert "### Model Implementations" in result
        assert "#### dim_customer" in result

        # Model metadata table
        assert "| **Materialization** | table |" in result
        assert "| **Schema** | analytics |" in result
        assert "| **Path** | `models/dimensions/dim_customer.sql` |" in result
        assert "| **Row Count** | 15,234 |" in result

        # Inference info in table
        assert (
            "| **Grain** *(inferred)* | one row per customer_id (customer_id) |"
            in result
        )
        assert "| **Risk** *(inferred)* | low |" in result
        assert "| **Data Vault** *(inferred)* | hub |" in result
        assert "| **Layer** *(inferred)* | silver |" in result

        # Description
        assert "**Description:** Customer dimension with SCD2 tracking" in result

        # Columns table
        assert "**Columns:**" in result
        assert "| Name | Type | Description | Constraints |" in result
        assert (
            "| `customer_id` | INTEGER | Unique customer identifier | not null, unique |"
            in result
        )

        # Table constraints
        assert "**Table Constraints:**" in result
        assert "- row count > 0" in result

        # Dependencies
        assert "**Upstream:** stg_customers, stg_customer_emails" in result
        assert "**Downstream:** fct_orders, fct_revenue" in result

        # Quality warnings
        assert "**Quality Warnings:**" in result
        assert "- No tests on email column" in result

        # Contract
        assert "**Contract:** strict" in result

    def test_markdown_multi_concept(self, multi_concept_context):
        """Test Markdown format with multiple concepts."""
        result = format_markdown(multi_concept_context)

        # Should have main title
        assert "# Concepts (2)" in result

        # Should have subsections for each concept
        assert "## customer" in result
        assert "## order" in result

    def test_markdown_standard_formatting(self, full_context):
        """Test that Markdown uses standard formatting."""
        result = format_markdown(full_context)

        # Headers
        assert result.count("# ") >= 1  # At least one h1
        assert result.count("### ") >= 1  # Multiple h3

        # Tables
        assert "|" in result  # Table syntax
        assert "---" in result  # Table header separator

        # Lists
        assert result.count("- ") >= 1  # Bullet lists

        # Code
        assert "`" in result  # Inline code

    def test_markdown_no_models(self):
        """Test Markdown format when no models are present."""
        context = FullContext(
            concepts=[
                ConceptContext(
                    name="test",
                    definition="Test concept",
                    status="stub",
                )
            ]
        )

        result = format_markdown(context)

        # Should not crash
        assert "# Concept: test" in result
        # Should not have model section
        assert "### Model Implementations" not in result


class TestAttributionClarity:
    """Tests for source attribution clarity across formats."""

    def test_llm_attribution_tags(self, full_context):
        """Test LLM format clearly marks authored vs inferred."""
        result = format_llm(full_context)

        # Authored content should be marked
        assert "[authored]" in result

        # Inferred content should be marked
        assert "[inferred]" in result

        # Specific examples
        assert "Status: complete [authored]" in result
        assert "**Grain [inferred]**" in result

    def test_markdown_attribution_italics(self, full_context):
        """Test Markdown format uses italics for inferred content."""
        result = format_markdown(full_context)

        # Inferred fields should be marked with italics
        assert "*(inferred)*" in result

        # Specific examples
        assert "**Grain** *(inferred)*" in result
        assert "**Risk** *(inferred)*" in result

    def test_json_contains_all_data_for_attribution(self, full_context):
        """Test JSON format includes all data needed to determine source."""
        result = format_json(full_context)
        data = json.loads(result)

        # All authored data present
        assert data["concepts"][0]["definition"] is not None
        assert data["models"]["dim_customer"]["columns"] is not None

        # All inferred data present
        assert data["inferences"]["dim_customer"]["grain"] is not None
        assert data["inferences"]["dim_customer"]["grain_columns"] is not None


class TestConsistencyAcrossFormats:
    """Tests that all formats contain the same information."""

    def test_same_concept_info_all_formats(self, full_context):
        """Test concept info appears in all formats."""
        llm = format_llm(full_context)
        json_str = format_json(full_context)
        markdown = format_markdown(full_context)

        # Concept name
        assert "customer" in llm
        assert "customer" in json_str
        assert "customer" in markdown

        # Definition
        assert "A person or organization that purchases products" in llm
        assert "A person or organization that purchases products" in json_str
        assert "A person or organization that purchases products" in markdown

    def test_same_model_info_all_formats(self, full_context):
        """Test model info appears in all formats."""
        llm = format_llm(full_context)
        json_str = format_json(full_context)
        markdown = format_markdown(full_context)

        # Model name
        assert "dim_customer" in llm
        assert "dim_customer" in json_str
        assert "dim_customer" in markdown

        # Materialization
        assert "table" in llm
        assert "table" in json_str
        assert "table" in markdown

    def test_same_inference_info_all_formats(self, full_context):
        """Test inference info appears in all formats."""
        llm = format_llm(full_context)
        json_result = format_json(full_context)
        json_data = json.loads(json_result)
        markdown = format_markdown(full_context)

        # Grain
        assert "one row per customer_id" in llm
        assert (
            json_data["inferences"]["dim_customer"]["grain"]
            == "one row per customer_id"
        )
        assert "one row per customer_id" in markdown

        # Grain columns
        assert "customer_id" in llm
        assert "customer_id" in json_data["inferences"]["dim_customer"]["grain_columns"]
        assert "customer_id" in markdown


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_context(self):
        """Test formatters handle empty context gracefully."""
        context = FullContext()

        llm = format_llm(context)
        json_result = format_json(context)
        markdown = format_markdown(context)

        # Should not crash
        assert isinstance(llm, str)
        assert isinstance(json_result, str)
        assert isinstance(markdown, str)

        # JSON should be valid
        data = json.loads(json_result)
        assert data["concepts"] == []

    def test_concept_without_optional_fields(self):
        """Test formatters handle concepts with minimal fields."""
        context = FullContext(
            concepts=[
                ConceptContext(
                    name="minimal",
                    # All optional fields left as None/default
                )
            ]
        )

        llm = format_llm(context)
        json_result = format_json(context)
        markdown = format_markdown(context)

        # Should not crash
        assert "minimal" in llm
        assert "minimal" in json_result
        assert "minimal" in markdown

    def test_model_without_columns(self):
        """Test formatters handle models with no columns."""
        context = FullContext(
            concepts=[ConceptContext(name="test", status="stub")],
            models={
                "test_model": ModelContext(
                    name="test_model",
                    materialization="view",
                    # No columns
                )
            },
        )

        llm = format_llm(context)
        json_result = format_json(context)
        markdown = format_markdown(context)

        # Should not crash
        assert "test_model" in llm
        assert "test_model" in json_result
        assert "test_model" in markdown

    def test_inference_without_optional_fields(self):
        """Test formatters handle sparse inferences."""
        context = FullContext(
            concepts=[ConceptContext(name="test", status="stub")],
            models={
                "test_model": ModelContext(name="test_model", materialization="view")
            },
            inferences={
                "test_model": InferenceContext(
                    # Only grain set, everything else None/empty
                    grain="one row per id",
                    grain_columns=["id"],
                )
            },
        )

        llm = format_llm(context)
        json_str = format_json(context)
        markdown = format_markdown(context)

        # Should show grain but not crash on missing fields
        assert "one row per id" in llm
        assert "one row per id" in markdown
        # JSON should be valid
        _ = json.loads(json_str)
