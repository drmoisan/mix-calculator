"""Unit tests for the pure dtype-coercion check (:mod:`src.dtype_check`).

These tests cover each dtype in the vocabulary across identical, coercible, and
non-coercible inputs, asserting that a non-coercible sample returns the first
failing example. Every fixture value here is synthetic/masked: no real workbook
values or proprietary column names appear, satisfying the confidentiality rule.
"""

from __future__ import annotations

import pytest

from src.dtype_check import check_dtype


@pytest.mark.parametrize(
    ("values", "dtype"),
    [
        (["1", "2", "3"], "integer"),
        ([1, 2, 3], "integer"),
        (["1.5", "2.0"], "float"),
        ([1.5, 2.5], "float"),
        (["2020-01-01", "2021-12-31"], "date"),
        (["true", "FALSE", "Yes"], "bool"),
        ([True, False], "bool"),
        (["alpha", "beta"], "string"),
        ([123, "mixed"], "string"),
    ],
)
def test_coercible_values_pass(values: list[object], dtype: str) -> None:
    """Coercible sample values yield a coercible result with no failing example."""
    # Act
    result = check_dtype(values, dtype)

    # Assert
    assert result.coercible is True
    assert result.failing_example is None


@pytest.mark.parametrize(
    ("values", "dtype", "expected_failing"),
    [
        (["1", "notnum", "3"], "integer", "notnum"),
        (["1.5", "abc"], "float", "abc"),
        (["1.5", "2.5"], "integer", "1.5"),
        (["2020-01-01", "not-a-date"], "date", "not-a-date"),
        (["true", "maybe"], "bool", "maybe"),
    ],
)
def test_non_coercible_values_report_first_failing_example(
    values: list[object], dtype: str, expected_failing: str
) -> None:
    """A non-coercible value yields not-coercible with the first failing example."""
    # Act
    result = check_dtype(values, dtype)

    # Assert
    assert result.coercible is False
    assert result.failing_example == expected_failing


def test_blank_and_null_values_are_skipped() -> None:
    """Blank strings and None values carry no type signal and are skipped."""
    # Arrange: only blanks/None, plus one valid integer.
    values: list[object] = [None, "", "   ", "42"]

    # Act
    result = check_dtype(values, "integer")

    # Assert: the blanks are ignored and the integer passes.
    assert result.coercible is True
    assert result.failing_example is None


def test_empty_sample_is_coercible() -> None:
    """An empty sample (no values to test) is trivially coercible."""
    # Act
    result = check_dtype([], "float")

    # Assert
    assert result.coercible is True
    assert result.failing_example is None


def test_integer_rejects_fractional_value() -> None:
    """The integer dtype rejects a fractional numeric with that value as example."""
    # Act
    result = check_dtype(["10", "3.5"], "integer")

    # Assert
    assert result.coercible is False
    assert result.failing_example == "3.5"


def test_string_dtype_always_coercible() -> None:
    """Any non-blank value is representable as a string, so string always passes."""
    # Act
    result = check_dtype([1, 2.5, "x", True], "string")

    # Assert
    assert result.coercible is True
