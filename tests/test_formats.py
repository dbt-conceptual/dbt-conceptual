"""Tests for exporter/formats.py module."""

import json
from io import StringIO
from pathlib import Path

from dbt_conceptual.config import Config
from dbt_conceptual.exporter.formats import (
    export_bus_matrix_json,
    export_bus_matrix_markdown,
    export_coverage_json,
    export_coverage_markdown,
    export_orphans_json,
    export_orphans_markdown,
    export_status_json,
    export_status_markdown,
    export_validation_json,
    export_validation_markdown,
)
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    OrphanModel,
    ProjectState,
    RelationshipState,
)
from dbt_conceptual.validator import Severity, ValidationIssue, Validator


def _create_test_state() -> ProjectState:
    """Create a test ProjectState with sample data for v1.0."""
    return ProjectState(
        domains={
            "party": DomainState(
                name="party", display_name="Party Domain", color="#E3F2FD"
            ),
            "sales": DomainState(name="sales", display_name="Sales Domain"),
        },
        concepts={
            "customer": ConceptState(
                name="Customer",
                domain="party",
                owner="team-a",
                definition="A customer definition",
                models=["dim_customer"],  # v1.0: flat models list
            ),
            "order": ConceptState(
                name="Order",
                domain="sales",
                # No models = draft status
            ),
            "product": ConceptState(
                name="Product",
                # No domain = stub status
            ),
        },
        relationships={
            "customer:places:order": RelationshipState(
                verb="places",
                from_concept="customer",
                to_concept="order",
                cardinality="1:N",
            ),
            "order:contains:product": RelationshipState(
                verb="contains",
                from_concept="order",
                to_concept="product",
            ),
        },
        orphan_models=[
            OrphanModel(name="stg_legacy", path="models/staging"),
            OrphanModel(name="dim_temp"),
        ],
    )


class TestCoverageExporters:
    """Tests for coverage export functions."""

    def test_export_coverage_json_structure(self) -> None:
        """Test export_coverage_json produces valid JSON structure."""
        state = _create_test_state()
        output = StringIO()
        export_coverage_json(state, output)
        result = output.getvalue()
        data = json.loads(result)

        # Check summary structure
        assert "summary" in data
        assert "concepts" in data["summary"]
        assert "coverage" in data["summary"]
        assert "relationships" in data["summary"]
        assert "orphans" in data["summary"]

        # Check concept stats
        assert data["summary"]["concepts"]["total"] == 3
        assert data["summary"]["concepts"]["complete"] == 1  # customer (has models)
        assert data["summary"]["concepts"]["draft"] == 1  # order (domain, no models)
        assert data["summary"]["concepts"]["stub"] == 1  # product (no domain)

        # Check coverage stats (v1.0: models coverage)
        assert data["summary"]["coverage"]["models"]["count"] == 1

        # Check domains and concepts_by_domain
        assert "domains" in data
        assert "party" in data["domains"]
        assert "concepts_by_domain" in data

    def test_export_coverage_json_empty_state(self) -> None:
        """Test export_coverage_json with empty state."""
        state = ProjectState()
        output = StringIO()
        export_coverage_json(state, output)
        result = output.getvalue()
        data = json.loads(result)

        assert data["summary"]["concepts"]["total"] == 0
        assert data["summary"]["concepts"]["completion_percent"] == 0
        assert data["summary"]["coverage"]["models"]["percent"] == 0

    def test_export_coverage_markdown_structure(self) -> None:
        """Test export_coverage_markdown produces valid markdown."""
        state = _create_test_state()
        output = StringIO()
        export_coverage_markdown(state, output)
        result = output.getvalue()

        assert "### Coverage Summary" in result
        assert "| Metric | Value |" in result
        assert "Concept Completion" in result
        assert "Model Coverage" in result

    def test_export_coverage_markdown_attention_items(self) -> None:
        """Test export_coverage_markdown shows attention items for stubs/drafts."""
        state = ProjectState(
            concepts={
                "stub_concept": ConceptState(name="Stub"),  # No domain = stub
                "draft_concept": ConceptState(
                    name="Draft", domain="test"
                ),  # Domain but no models = draft
            }
        )
        output = StringIO()
        export_coverage_markdown(state, output)
        result = output.getvalue()

        assert "#### Attention Needed" in result
        assert "stub concept" in result.lower()
        assert "draft concept" in result.lower()


class TestBusMatrixExporters:
    """Tests for bus matrix export functions."""

    def test_export_bus_matrix_json_structure(self) -> None:
        """Test export_bus_matrix_json produces valid JSON structure."""
        state = _create_test_state()
        output = StringIO()
        export_bus_matrix_json(state, output)
        result = output.getvalue()
        data = json.loads(result)

        # v1.0: Bus matrix shows relationships without realization info
        assert "relationships" in data
        assert "summary" in data

        # Check relationships are present
        assert data["summary"]["total_relationships"] == 2

    def test_export_bus_matrix_json_empty(self) -> None:
        """Test export_bus_matrix_json with no relationships."""
        state = ProjectState(
            concepts={"customer": ConceptState(name="Customer")},
        )
        output = StringIO()
        export_bus_matrix_json(state, output)
        result = output.getvalue()
        data = json.loads(result)

        assert data["relationships"] == []
        assert data["summary"]["total_relationships"] == 0

    def test_export_bus_matrix_markdown_structure(self) -> None:
        """Test export_bus_matrix_markdown produces valid markdown table."""
        state = _create_test_state()
        output = StringIO()
        export_bus_matrix_markdown(state, output)
        result = output.getvalue()

        assert "### Bus Matrix" in result
        assert "| Relationship |" in result
        assert "places" in result
        assert "contains" in result

    def test_export_bus_matrix_markdown_empty(self) -> None:
        """Test export_bus_matrix_markdown with no relationships."""
        state = ProjectState()
        output = StringIO()
        export_bus_matrix_markdown(state, output)
        result = output.getvalue()

        assert "### Bus Matrix" in result
        assert "No relationships defined" in result


class TestStatusExporters:
    """Tests for status export functions."""

    def test_export_status_json_structure(self) -> None:
        """Test export_status_json produces valid JSON structure."""
        state = _create_test_state()
        output = StringIO()
        export_status_json(state, output)
        result = output.getvalue()
        data = json.loads(result)

        assert "summary" in data
        assert "concepts" in data
        assert "relationships" in data

        # Check concepts data
        assert len(data["concepts"]) == 3
        customer = next(c for c in data["concepts"] if c["id"] == "customer")
        assert customer["name"] == "Customer"
        assert customer["domain"] == "party"
        assert customer["model_count"] == 1  # v1.0: flat model count

        # Check relationships data
        assert len(data["relationships"]) == 2

    def test_export_status_markdown_structure(self) -> None:
        """Test export_status_markdown produces valid markdown."""
        state = _create_test_state()
        output = StringIO()
        export_status_markdown(state, output)
        result = output.getvalue()

        assert "### Status Summary" in result
        assert "**Concepts:**" in result
        assert "**Relationships:**" in result
        assert "#### Concepts by Domain" in result

        # Check domain groups shown
        assert "Party Domain" in result
        assert "| Concept | Status | Models |" in result  # v1.0: flat models column


class TestOrphansExporters:
    """Tests for orphans export functions."""

    def test_export_orphans_json_structure(self) -> None:
        """Test export_orphans_json produces valid JSON structure."""
        state = _create_test_state()
        output = StringIO()
        export_orphans_json(state, output)
        result = output.getvalue()
        data = json.loads(result)

        assert "count" in data
        assert "models" in data
        assert data["count"] == 2

        orphan = data["models"][0]
        assert "name" in orphan
        assert "path" in orphan

    def test_export_orphans_json_empty(self) -> None:
        """Test export_orphans_json with no orphans."""
        state = ProjectState()
        output = StringIO()
        export_orphans_json(state, output)
        result = output.getvalue()
        data = json.loads(result)

        assert data["count"] == 0
        assert data["models"] == []

    def test_export_orphans_markdown_with_orphans(self) -> None:
        """Test export_orphans_markdown lists orphan models."""
        state = _create_test_state()
        output = StringIO()
        export_orphans_markdown(state, output)
        result = output.getvalue()

        assert "### Orphan Models" in result
        assert "Found **2 models**" in result
        assert "| Model | Path |" in result
        assert "`stg_legacy`" in result
        assert "`dim_temp`" in result

    def test_export_orphans_markdown_no_orphans(self) -> None:
        """Test export_orphans_markdown with no orphans."""
        state = ProjectState()
        output = StringIO()
        export_orphans_markdown(state, output)
        result = output.getvalue()

        assert "### Orphan Models" in result
        assert "No orphan models found" in result
        assert "All models have" in result


class TestValidationExporters:
    """Tests for validation export functions."""

    def test_export_validation_json_passed(self) -> None:
        """Test export_validation_json with passing validation."""
        state = _create_test_state()
        config = Config(project_dir=Path("/tmp"))
        validator = Validator(config, state)
        issues: list[ValidationIssue] = []

        output = StringIO()
        export_validation_json(validator, issues, output)
        result = output.getvalue()
        data = json.loads(result)

        assert data["passed"] is True
        assert "summary" in data
        assert "issues" in data
        assert data["issues"] == []

    def test_export_validation_json_with_issues(self) -> None:
        """Test export_validation_json with validation issues."""
        state = _create_test_state()
        config = Config(project_dir=Path("/tmp"))
        validator = Validator(config, state)
        issues = [
            ValidationIssue(
                code="E001",
                severity=Severity.ERROR,
                message="Test error",
                context={"concept": "customer"},
            ),
            ValidationIssue(
                code="W001",
                severity=Severity.WARNING,
                message="Test warning",
                context={},
            ),
        ]
        # Add issues to validator for summary
        validator.issues = issues

        output = StringIO()
        export_validation_json(validator, issues, output)
        result = output.getvalue()
        data = json.loads(result)

        assert data["passed"] is False
        assert len(data["issues"]) == 2
        assert data["issues"][0]["code"] == "E001"
        assert data["issues"][0]["severity"] == "error"
        assert data["summary"]["errors"] == 1
        assert data["summary"]["warnings"] == 1

    def test_export_validation_markdown_passed(self) -> None:
        """Test export_validation_markdown with passing validation."""
        state = _create_test_state()
        config = Config(project_dir=Path("/tmp"))
        validator = Validator(config, state)
        issues: list[ValidationIssue] = []

        output = StringIO()
        export_validation_markdown(validator, issues, output)
        result = output.getvalue()

        assert "### " in result  # Has a header
        assert "Validation Passed" in result

    def test_export_validation_markdown_with_errors(self) -> None:
        """Test export_validation_markdown with errors."""
        state = _create_test_state()
        config = Config(project_dir=Path("/tmp"))
        validator = Validator(config, state)
        issues = [
            ValidationIssue(
                code="E001",
                severity=Severity.ERROR,
                message="Test error message",
                context={},
            ),
        ]
        validator.issues = issues

        output = StringIO()
        export_validation_markdown(validator, issues, output)
        result = output.getvalue()

        assert "Validation Failed" in result
        assert "Errors" in result
        assert "| Count |" in result
        assert "**E001**" in result
        assert "Test error message" in result

    def test_export_validation_markdown_with_warnings(self) -> None:
        """Test export_validation_markdown with warnings only."""
        state = _create_test_state()
        config = Config(project_dir=Path("/tmp"))
        validator = Validator(config, state)
        issues = [
            ValidationIssue(
                code="W001",
                severity=Severity.WARNING,
                message="Test warning",
                context={},
            ),
        ]
        validator.issues = issues

        output = StringIO()
        export_validation_markdown(validator, issues, output)
        result = output.getvalue()

        # No errors = passed
        assert "Validation Passed" in result
        assert "Warnings" in result
        assert "**W001**" in result
