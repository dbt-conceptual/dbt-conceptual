"""Translator for dbt test definitions into natural language constraints.

Converts dbt manifest test nodes into human-readable constraint descriptions
for agent consumption. Supports core dbt tests, dbt_utils, and dbt_expectations.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConstraintTranslator:
    """Translates dbt test definitions into natural language constraints."""

    def translate_test(self, test_node: dict[str, Any]) -> str:
        """Translate a dbt test node into a natural language constraint.

        Args:
            test_node: A test node from the dbt manifest (dict with test metadata)

        Returns:
            Natural language constraint description

        Example test_node structure:
            {
                "test_metadata": {
                    "name": "unique",
                    "kwargs": {"column_name": "customer_id"}
                },
                "column_name": "customer_id",
                "attached_node": "model.project.dim_customer"
            }
        """
        # Extract test metadata
        test_metadata = test_node.get("test_metadata", {})
        test_name = test_metadata.get("name", "")
        kwargs = test_metadata.get("kwargs", {})
        column_name = test_node.get("column_name") or kwargs.get("column_name")

        # Try core dbt tests first
        if test_name == "not_null":
            return self._translate_not_null(column_name)
        elif test_name == "unique":
            return self._translate_unique(column_name)
        elif test_name == "accepted_values":
            return self._translate_accepted_values(column_name, kwargs)
        elif test_name == "relationships":
            return self._translate_relationships(column_name, kwargs, test_node)

        # Try dbt_utils patterns
        if test_name.startswith("dbt_utils."):
            return self._translate_dbt_utils(test_name, column_name, kwargs)

        # Try dbt_expectations patterns
        if test_name.startswith("dbt_expectations."):
            return self._translate_dbt_expectations(test_name, column_name, kwargs)

        # Fallback for custom/unknown tests
        return self._translate_fallback(test_name, column_name)

    def _translate_not_null(self, column_name: str | None) -> str:
        """Translate not_null test."""
        if column_name:
            return f"{column_name} must not be null"
        return "column must not be null"

    def _translate_unique(self, column_name: str | None) -> str:
        """Translate unique test."""
        if column_name:
            return f"{column_name} must be unique"
        return "column must be unique"

    def _translate_accepted_values(
        self, column_name: str | None, kwargs: dict[str, Any]
    ) -> str:
        """Translate accepted_values test."""
        values = kwargs.get("values", [])
        column = column_name or kwargs.get("field", "column")

        if values:
            # Format the values list for readability
            values_str = str(values)
            return f"{column} must be one of {values_str}"

        return f"{column} must be one of a predefined set of values"

    def _translate_relationships(
        self,
        column_name: str | None,
        kwargs: dict[str, Any],
        test_node: dict[str, Any],
    ) -> str:
        """Translate relationships test."""
        # Extract target model and field
        to_ref = kwargs.get("to", "")
        field = kwargs.get("field", "")
        column = column_name or kwargs.get("column_name", "column")

        # Parse the ref() expression if present
        # Example: "ref('dim_customer')" -> "dim_customer"
        if to_ref and "ref(" in to_ref:
            # Extract model name from ref()
            start = to_ref.find("ref(") + 4
            end = to_ref.find(")", start)
            if end > start:
                # Remove quotes
                model_name = to_ref[start:end].strip("'\"")
                if field:
                    return f"{column} must reference a valid {field} in {model_name}"
                return f"{column} must reference a valid record in {model_name}"

        # Fallback if ref parsing fails
        if field:
            return f"{column} must reference a valid {field}"
        return f"{column} must reference a valid foreign key"

    def _translate_dbt_utils(
        self, test_name: str, column_name: str | None, kwargs: dict[str, Any]
    ) -> str:
        """Translate dbt_utils test patterns."""
        # Remove the dbt_utils. prefix
        short_name = test_name.replace("dbt_utils.", "")
        column = column_name or kwargs.get("column_name", "column")

        # Common dbt_utils tests
        if short_name == "unique_combination_of_columns":
            columns = kwargs.get("combination_of_columns", [])
            if columns:
                cols_str = ", ".join(columns)
                return f"combination of ({cols_str}) must be unique"
            return "column combination must be unique"

        elif short_name == "not_null_proportion":
            at_least = kwargs.get("at_least", 1.0)
            return f"{column} must be not null in at least {at_least * 100}% of rows"

        elif short_name == "not_constant":
            return f"{column} must not be constant (must have multiple distinct values)"

        elif short_name == "cardinality_equality":
            to_ref = kwargs.get("to", "")
            if to_ref:
                return f"{column} must have same cardinality as {to_ref}"
            return f"{column} must match cardinality with reference table"

        elif short_name == "at_least_one":
            return "at least one row must exist"

        elif short_name == "expression_is_true":
            expression = kwargs.get("expression", "")
            if expression:
                return f"expression must be true: {expression}"
            return "custom expression must be true"

        # Fallback for other dbt_utils tests
        return f"{test_name} applied to {column}"

    def _translate_dbt_expectations(
        self, test_name: str, column_name: str | None, kwargs: dict[str, Any]
    ) -> str:
        """Translate dbt_expectations test patterns."""
        # Remove the dbt_expectations. prefix
        short_name = test_name.replace("dbt_expectations.", "")
        column = column_name or kwargs.get("column_name", "column")

        # Common dbt_expectations tests
        if short_name == "expect_column_values_to_be_between":
            min_val = kwargs.get("min_value")
            max_val = kwargs.get("max_value")
            if min_val is not None and max_val is not None:
                return f"{column} must be between {min_val} and {max_val}"
            elif min_val is not None:
                return f"{column} must be >= {min_val}"
            elif max_val is not None:
                return f"{column} must be <= {max_val}"
            return f"{column} must be within a valid range"

        elif short_name == "expect_column_values_to_match_regex":
            regex = kwargs.get("regex", "")
            if regex:
                return f"{column} must match pattern: {regex}"
            return f"{column} must match a regex pattern"

        elif short_name == "expect_column_values_to_not_match_regex":
            regex = kwargs.get("regex", "")
            if regex:
                return f"{column} must not match pattern: {regex}"
            return f"{column} must not match a regex pattern"

        elif short_name == "expect_column_values_to_be_in_set":
            value_set = kwargs.get("value_set", [])
            if value_set:
                values_str = str(value_set)
                return f"{column} must be in set {values_str}"
            return f"{column} must be in a predefined set"

        elif short_name == "expect_column_values_to_be_of_type":
            type_name = kwargs.get("column_type", "")
            if type_name:
                return f"{column} must be of type {type_name}"
            return f"{column} must be of a specific type"

        elif short_name == "expect_column_mean_to_be_between":
            min_val = kwargs.get("min_value")
            max_val = kwargs.get("max_value")
            if min_val is not None and max_val is not None:
                return f"{column} mean must be between {min_val} and {max_val}"
            return f"{column} mean must be within a valid range"

        elif short_name == "expect_column_proportion_of_unique_values_to_be_between":
            min_val = kwargs.get("min_value", 0)
            max_val = kwargs.get("max_value", 1)
            return f"{column} uniqueness proportion must be between {min_val} and {max_val}"

        elif short_name == "expect_table_row_count_to_be_between":
            min_val = kwargs.get("min_value")
            max_val = kwargs.get("max_value")
            if min_val is not None and max_val is not None:
                return f"row count must be between {min_val} and {max_val}"
            return "row count must be within a valid range"

        # Fallback for other dbt_expectations tests
        return f"{test_name} applied to {column}"

    def _translate_fallback(self, test_name: str, column_name: str | None) -> str:
        """Fallback translation for unknown/custom tests."""
        if column_name:
            return f"{test_name} applied to {column_name}"
        return f"{test_name} applied to table"


def translate_test_to_constraint(test_node: dict[str, Any]) -> str:
    """Convenience function to translate a single test node.

    Args:
        test_node: A test node from the dbt manifest

    Returns:
        Natural language constraint description
    """
    translator = ConstraintTranslator()
    return translator.translate_test(test_node)
