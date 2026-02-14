"""Tests for constraint_translator module."""

from __future__ import annotations

from dbt_conceptual.constraint_translator import (
    ConstraintTranslator,
    translate_test_to_constraint,
)


class TestCoreTests:
    """Test translation of core dbt tests."""

    def test_not_null_with_column(self) -> None:
        """Test not_null translation with column name."""
        test_node = {
            "test_metadata": {"name": "not_null", "kwargs": {}},
            "column_name": "email",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "email must not be null"

    def test_not_null_without_column(self) -> None:
        """Test not_null translation without column name."""
        test_node = {
            "test_metadata": {"name": "not_null", "kwargs": {}},
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "column must not be null"

    def test_unique_with_column(self) -> None:
        """Test unique translation with column name."""
        test_node = {
            "test_metadata": {"name": "unique", "kwargs": {}},
            "column_name": "customer_id",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "customer_id must be unique"

    def test_unique_without_column(self) -> None:
        """Test unique translation without column name."""
        test_node = {
            "test_metadata": {"name": "unique", "kwargs": {}},
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "column must be unique"

    def test_accepted_values_with_list(self) -> None:
        """Test accepted_values translation with value list."""
        test_node = {
            "test_metadata": {
                "name": "accepted_values",
                "kwargs": {"values": ["active", "churned"]},
            },
            "column_name": "status",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "status must be one of ['active', 'churned']"

    def test_accepted_values_without_values(self) -> None:
        """Test accepted_values translation without values specified."""
        test_node = {
            "test_metadata": {
                "name": "accepted_values",
                "kwargs": {},
            },
            "column_name": "status",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "status must be one of a predefined set of values"

    def test_relationships_with_ref(self) -> None:
        """Test relationships translation with ref() syntax."""
        test_node = {
            "test_metadata": {
                "name": "relationships",
                "kwargs": {"to": "ref('dim_customer')", "field": "customer_id"},
            },
            "column_name": "customer_id",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert (
            result == "customer_id must reference a valid customer_id in dim_customer"
        )

    def test_relationships_with_ref_no_field(self) -> None:
        """Test relationships translation with ref() but no field specified."""
        test_node = {
            "test_metadata": {
                "name": "relationships",
                "kwargs": {"to": "ref('dim_customer')"},
            },
            "column_name": "customer_id",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "customer_id must reference a valid record in dim_customer"

    def test_relationships_fallback(self) -> None:
        """Test relationships translation fallback without ref."""
        test_node = {
            "test_metadata": {
                "name": "relationships",
                "kwargs": {"field": "id"},
            },
            "column_name": "user_id",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "user_id must reference a valid id"

    def test_relationships_minimal_fallback(self) -> None:
        """Test relationships translation with minimal information."""
        test_node = {
            "test_metadata": {
                "name": "relationships",
                "kwargs": {},
            },
            "column_name": "parent_id",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "parent_id must reference a valid foreign key"


class TestDbtUtilsTests:
    """Test translation of dbt_utils test patterns."""

    def test_unique_combination_of_columns(self) -> None:
        """Test unique_combination_of_columns translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.unique_combination_of_columns",
                "kwargs": {"combination_of_columns": ["order_id", "line_number"]},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "combination of (order_id, line_number) must be unique"

    def test_unique_combination_of_columns_empty(self) -> None:
        """Test unique_combination_of_columns with empty column list."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.unique_combination_of_columns",
                "kwargs": {},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "column combination must be unique"

    def test_not_null_proportion(self) -> None:
        """Test not_null_proportion translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.not_null_proportion",
                "kwargs": {"at_least": 0.95},
            },
            "column_name": "phone_number",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "phone_number must be not null in at least 95.0% of rows"

    def test_not_constant(self) -> None:
        """Test not_constant translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.not_constant",
                "kwargs": {},
            },
            "column_name": "color",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert (
            result == "color must not be constant (must have multiple distinct values)"
        )

    def test_cardinality_equality(self) -> None:
        """Test cardinality_equality translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.cardinality_equality",
                "kwargs": {"to": "ref('users')"},
            },
            "column_name": "user_id",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "user_id must have same cardinality as ref('users')"

    def test_at_least_one(self) -> None:
        """Test at_least_one translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.at_least_one",
                "kwargs": {},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "at least one row must exist"

    def test_expression_is_true(self) -> None:
        """Test expression_is_true translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.expression_is_true",
                "kwargs": {"expression": "revenue > 0"},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "expression must be true: revenue > 0"

    def test_unknown_dbt_utils_test(self) -> None:
        """Test fallback for unknown dbt_utils test."""
        test_node = {
            "test_metadata": {
                "name": "dbt_utils.some_custom_test",
                "kwargs": {},
            },
            "column_name": "data",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "dbt_utils.some_custom_test applied to data"


class TestDbtExpectationsTests:
    """Test translation of dbt_expectations test patterns."""

    def test_expect_column_values_to_be_between(self) -> None:
        """Test expect_column_values_to_be_between translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_values_to_be_between",
                "kwargs": {"min_value": 0, "max_value": 100},
            },
            "column_name": "score",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "score must be between 0 and 100"

    def test_expect_column_values_to_be_between_min_only(self) -> None:
        """Test expect_column_values_to_be_between with min only."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_values_to_be_between",
                "kwargs": {"min_value": 0},
            },
            "column_name": "quantity",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "quantity must be >= 0"

    def test_expect_column_values_to_be_between_max_only(self) -> None:
        """Test expect_column_values_to_be_between with max only."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_values_to_be_between",
                "kwargs": {"max_value": 999},
            },
            "column_name": "age",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "age must be <= 999"

    def test_expect_column_values_to_match_regex(self) -> None:
        """Test expect_column_values_to_match_regex translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_values_to_match_regex",
                "kwargs": {"regex": r"^\d{5}$"},
            },
            "column_name": "zip_code",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == r"zip_code must match pattern: ^\d{5}$"

    def test_expect_column_values_to_not_match_regex(self) -> None:
        """Test expect_column_values_to_not_match_regex translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_values_to_not_match_regex",
                "kwargs": {"regex": r"[<>]"},
            },
            "column_name": "description",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == r"description must not match pattern: [<>]"

    def test_expect_column_values_to_be_in_set(self) -> None:
        """Test expect_column_values_to_be_in_set translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_values_to_be_in_set",
                "kwargs": {"value_set": ["USD", "EUR", "GBP"]},
            },
            "column_name": "currency",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "currency must be in set ['USD', 'EUR', 'GBP']"

    def test_expect_column_values_to_be_of_type(self) -> None:
        """Test expect_column_values_to_be_of_type translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_values_to_be_of_type",
                "kwargs": {"column_type": "varchar"},
            },
            "column_name": "name",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "name must be of type varchar"

    def test_expect_column_mean_to_be_between(self) -> None:
        """Test expect_column_mean_to_be_between translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_mean_to_be_between",
                "kwargs": {"min_value": 10.5, "max_value": 15.2},
            },
            "column_name": "price",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "price mean must be between 10.5 and 15.2"

    def test_expect_column_proportion_of_unique_values_to_be_between(self) -> None:
        """Test expect_column_proportion_of_unique_values_to_be_between translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_column_proportion_of_unique_values_to_be_between",
                "kwargs": {"min_value": 0.8, "max_value": 1.0},
            },
            "column_name": "email",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "email uniqueness proportion must be between 0.8 and 1.0"

    def test_expect_table_row_count_to_be_between(self) -> None:
        """Test expect_table_row_count_to_be_between translation."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_table_row_count_to_be_between",
                "kwargs": {"min_value": 1, "max_value": 1000000},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "row count must be between 1 and 1000000"

    def test_unknown_dbt_expectations_test(self) -> None:
        """Test fallback for unknown dbt_expectations test."""
        test_node = {
            "test_metadata": {
                "name": "dbt_expectations.expect_custom_validation",
                "kwargs": {},
            },
            "column_name": "value",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "dbt_expectations.expect_custom_validation applied to value"


class TestCustomAndFallback:
    """Test translation of custom/unknown tests with fallback."""

    def test_custom_test_with_column(self) -> None:
        """Test custom test translation with column name."""
        test_node = {
            "test_metadata": {
                "name": "custom_validation",
                "kwargs": {},
            },
            "column_name": "order_total",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "custom_validation applied to order_total"

    def test_custom_test_without_column(self) -> None:
        """Test custom test translation without column name."""
        test_node = {
            "test_metadata": {
                "name": "data_quality_check",
                "kwargs": {},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "data_quality_check applied to table"

    def test_empty_test_name(self) -> None:
        """Test translation with empty test name."""
        test_node = {
            "test_metadata": {
                "name": "",
                "kwargs": {},
            },
            "column_name": "field",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == " applied to field"


class TestConvenienceFunction:
    """Test the convenience function."""

    def test_translate_test_to_constraint(self) -> None:
        """Test the convenience function wraps ConstraintTranslator correctly."""
        test_node = {
            "test_metadata": {"name": "unique", "kwargs": {}},
            "column_name": "id",
        }
        result = translate_test_to_constraint(test_node)
        assert result == "id must be unique"


class TestColumnNameHandling:
    """Test handling of column names from various sources."""

    def test_column_name_from_test_node(self) -> None:
        """Test column name taken from test_node."""
        test_node = {
            "test_metadata": {"name": "unique", "kwargs": {}},
            "column_name": "user_id",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "user_id must be unique"

    def test_column_name_from_kwargs(self) -> None:
        """Test column name taken from kwargs when not in test_node."""
        test_node = {
            "test_metadata": {
                "name": "unique",
                "kwargs": {"column_name": "product_id"},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "product_id must be unique"

    def test_column_name_from_field_kwarg(self) -> None:
        """Test column name taken from field kwarg for accepted_values."""
        test_node = {
            "test_metadata": {
                "name": "accepted_values",
                "kwargs": {"field": "status", "values": ["pending", "complete"]},
            },
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == "status must be one of ['pending', 'complete']"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_test_metadata(self) -> None:
        """Test handling of empty test_metadata."""
        test_node = {
            "test_metadata": {},
            "column_name": "field",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == " applied to field"

    def test_missing_test_metadata(self) -> None:
        """Test handling of missing test_metadata."""
        test_node = {
            "column_name": "field",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        assert result == " applied to field"

    def test_none_values_in_kwargs(self) -> None:
        """Test handling of None values in kwargs."""
        test_node = {
            "test_metadata": {
                "name": "accepted_values",
                "kwargs": {"values": None},
            },
            "column_name": "type",
        }
        translator = ConstraintTranslator()
        result = translator.translate_test(test_node)
        # Should use fallback when values is None
        assert "type must be one of" in result
