"""Tests for the sandboxed schema formula engine (Issue #43, Feature C).

Covers the whitelisted helpers (``safe_div``, ``col``/alias resolution), valid
expression evaluation (arithmetic, ``sum``, special-char columns), and the
descriptive rejection of invalid/unsafe/unknown-reference expressions, plus
Hypothesis property tests for the T1 pure functions.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.schema_formula import (
    FormulaError,
    FormulaEvaluator,
    alias_for,
    build_alias_map,
    safe_div,
)

# ---------------------------------------------------------------------------
# safe_div unit tests
# ---------------------------------------------------------------------------


def test_safe_div_positive_denominator_divides() -> None:
    """safe_div returns the quotient for a positive finite denominator."""
    # Arrange / Act
    result = safe_div(10.0, 4.0)
    # Assert
    assert result == 2.5


def test_safe_div_zero_denominator_returns_zero() -> None:
    """safe_div returns 0.0 when the denominator is zero."""
    assert safe_div(10.0, 0.0) == 0.0


def test_safe_div_negative_denominator_returns_zero() -> None:
    """safe_div returns 0.0 when the denominator is negative."""
    assert safe_div(10.0, -3.0) == 0.0


def test_safe_div_none_denominator_returns_zero() -> None:
    """safe_div returns 0.0 when the denominator is None."""
    assert safe_div(10.0, None) == 0.0


def test_safe_div_nan_denominator_returns_zero() -> None:
    """safe_div returns 0.0 when the denominator is NaN."""
    assert safe_div(10.0, float("nan")) == 0.0


# ---------------------------------------------------------------------------
# alias unit tests
# ---------------------------------------------------------------------------


def test_alias_for_replaces_special_chars() -> None:
    """alias_for produces a valid identifier for a special-char column name."""
    # Arrange / Act
    alias = alias_for("Off Invoice $")
    # Assert
    assert alias.isidentifier()


def test_alias_for_leading_digit_is_prefixed() -> None:
    """alias_for prefixes a leading-digit name so the alias is a valid identifier."""
    alias = alias_for("3M Sales")
    assert alias.isidentifier()
    assert alias.startswith("c_")


def test_alias_for_empty_name_falls_back() -> None:
    """alias_for returns a valid identifier even for an empty name."""
    assert alias_for("").isidentifier()


def test_build_alias_map_chained_collision_suffixes() -> None:
    """build_alias_map suffixes a third colliding column with an incremented index."""
    # Three distinct names all sanitize to the same base identifier.
    columns = ["SKU #", "SKU $", "SKU %"]
    alias_map = build_alias_map(columns)
    assert len(alias_map) == 3
    assert set(alias_map.values()) == set(columns)


def test_build_alias_map_disambiguates_collisions() -> None:
    """build_alias_map assigns distinct aliases to columns that sanitize alike."""
    # Arrange: two distinct names that both sanitize to "SKU__"
    columns = ["SKU #", "SKU $"]
    # Act
    alias_map = build_alias_map(columns)
    # Assert: two aliases, each mapping back to a distinct source column
    assert len(alias_map) == 2
    assert set(alias_map.values()) == {"SKU #", "SKU $"}


# ---------------------------------------------------------------------------
# FormulaEvaluator.evaluate unit tests
# ---------------------------------------------------------------------------


def test_evaluate_arithmetic_expression() -> None:
    """A valid arithmetic expression over known columns evaluates correctly."""
    # Arrange
    evaluator = FormulaEvaluator()
    context = {"Jan": 2.0, "Feb": 3.0}
    # Act
    result = evaluator.evaluate("Jan + Feb * 2", context)
    # Assert
    assert result == 8.0


def test_evaluate_sum_call() -> None:
    """The whitelisted sum() over an explicit list of column refs evaluates."""
    evaluator = FormulaEvaluator()
    context = {"May": 1.0, "Jun": 2.0, "Jul": 4.0}
    result = evaluator.evaluate("sum([May, Jun, Jul])", context)
    assert result == 7.0


def test_evaluate_special_char_columns_via_alias() -> None:
    """Special-char columns are reachable via their identifier alias (AC6)."""
    # Arrange
    evaluator = FormulaEvaluator()
    context = {"SKU #": 5.0, "Off Invoice $": 10.0}
    sku_alias = build_alias_map(["SKU #", "Off Invoice $"])
    # Build the expression from the actual aliases to avoid hard-coding them.
    inverse = {v: k for k, v in sku_alias.items()}
    expr = f"{inverse['SKU #']} + {inverse['Off Invoice $']}"
    # Act
    result = evaluator.evaluate(expr, context)
    # Assert
    assert result == 15.0


def test_evaluate_special_char_columns_via_col_callable() -> None:
    """The col() accessor resolves exact special-char column names (AC6)."""
    evaluator = FormulaEvaluator()
    context = {"Off Invoice $": 12.0}
    result = evaluator.evaluate('col("Off Invoice $") * 2', context)
    assert result == 24.0


def test_evaluate_ratio_recompute_via_safe_div() -> None:
    """A ratio expression using safe_div recomputes from summed dollars/volume."""
    evaluator = FormulaEvaluator()
    context = {"dollars": 50.0, "volume": 10.0}
    result = evaluator.evaluate("safe_div(dollars, volume)", context)
    assert result == 5.0


def test_evaluate_ratio_safe_div_zero_denominator() -> None:
    """A ratio with a zero denominator yields 0.0 through safe_div."""
    evaluator = FormulaEvaluator()
    context = {"dollars": 50.0, "volume": 0.0}
    result = evaluator.evaluate("safe_div(dollars, volume)", context)
    assert result == 0.0


# ---------------------------------------------------------------------------
# FormulaEvaluator.validate rejection unit tests
# ---------------------------------------------------------------------------


def test_validate_accepts_valid_expression() -> None:
    """validate returns None for a safe expression over known columns."""
    evaluator = FormulaEvaluator()
    # Act / Assert: no exception
    evaluator.validate("Jan + Feb", ["Jan", "Feb"])


def test_validate_rejects_syntax_error() -> None:
    """validate raises FormulaError naming a syntax problem for malformed input."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="invalid formula syntax"):
        evaluator.validate("Jan +", ["Jan"])


def test_validate_rejects_import() -> None:
    """validate rejects an import construct with a descriptive message."""
    evaluator = FormulaEvaluator()
    # An import is not even a valid eval-mode expression; it is reported as syntax.
    with pytest.raises(FormulaError):
        evaluator.validate("__import__('os')", ["Jan"])


def test_validate_rejects_dunder_attribute_access() -> None:
    """validate rejects attribute access (dunder escape) with a descriptive message."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="attribute access"):
        evaluator.validate("Jan.__class__", ["Jan"])


def test_validate_rejects_subscript() -> None:
    """validate rejects subscripting with a descriptive message."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="subscripting"):
        evaluator.validate("Jan[0]", ["Jan"])


def test_validate_rejects_lambda() -> None:
    """validate rejects a lambda construct with a descriptive message."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="lambda"):
        evaluator.validate("Jan + (lambda: 1)", ["Jan"])


def test_validate_rejects_called_lambda() -> None:
    """validate rejects an immediately-invoked lambda (call to a non-name callee)."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError):
        evaluator.validate("(lambda: 1)()", ["Jan"])


def test_validate_rejects_comprehension() -> None:
    """validate rejects a comprehension with a descriptive message."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="comprehension"):
        evaluator.validate("[x for x in Jan]", ["Jan"])


def test_validate_rejects_non_whitelisted_call() -> None:
    """validate rejects a call to a non-whitelisted function, naming it."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="non-whitelisted function"):
        evaluator.validate("eval('1')", ["Jan"])


def test_validate_rejects_unknown_column() -> None:
    """validate rejects a reference to an unknown column/name (AC6)."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="unknown column or name"):
        evaluator.validate("Mar + Jan", ["Jan", "Feb"])


def test_evaluate_col_unknown_column_raises() -> None:
    """col() raises FormulaError when its argument is not in the context."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError, match="col\\(\\) references unknown column"):
        evaluator.evaluate('col("Missing")', {"Jan": 1.0})


def test_evaluate_column_named_col_round_trips_via_col_callable() -> None:
    """A column literally named ``col`` round-trips via col("col") without shadowing.

    Regression for C1: when a column's identifier alias collides with a
    whitelisted callable name (``col``/``sum``/``safe_div``), the alias binding
    must not overwrite the callable in the symbol table. The col() accessor must
    remain callable and return the exact-name column value for the colliding name.
    """
    # Arrange: a context whose column names collide with whitelisted callables.
    evaluator = FormulaEvaluator()
    context = {"col": 7.0, "sum": 3.0, "safe_div": 11.0}
    # Act: resolve each colliding column by its exact name through col().
    col_value = evaluator.evaluate('col("col")', context)
    sum_value = evaluator.evaluate('col("sum")', context)
    safe_div_value = evaluator.evaluate('col("safe_div")', context)
    # Assert: each colliding column returns its stored value; the helper is not
    # shadowed by the column value.
    assert col_value == 7.0
    assert sum_value == 3.0
    assert safe_div_value == 11.0


# ---------------------------------------------------------------------------
# Hypothesis property tests (T1: >= 1 property test per pure function)
# ---------------------------------------------------------------------------

# Bound float magnitude so sums/quotients stay finite and comparisons are
# meaningful (per the repo's float-magnitude property-test guidance).
_FINITE = st.floats(
    min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False
)
_POSITIVE = st.floats(
    min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False
)
_NON_POSITIVE = st.floats(max_value=0.0, allow_nan=False, allow_infinity=False)


@given(num=_FINITE, den=_POSITIVE)
def test_property_safe_div_positive_matches_division(num: float, den: float) -> None:
    """safe_div equals num/den for any positive finite denominator."""
    assert safe_div(num, den) == num / den


@given(num=_FINITE, den=_NON_POSITIVE)
def test_property_safe_div_non_positive_is_zero(num: float, den: float) -> None:
    """safe_div returns 0.0 for any zero/negative denominator."""
    assert safe_div(num, den) == 0.0


@given(num=_FINITE)
def test_property_safe_div_none_and_nan_are_zero(num: float) -> None:
    """safe_div returns 0.0 for None and NaN denominators."""
    assert safe_div(num, None) == 0.0
    assert safe_div(num, float("nan")) == 0.0


# Column-name strategy: arbitrary non-empty text, including special characters.
_COLUMN_NAME = st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != "")


@given(name=_COLUMN_NAME)
def test_property_alias_for_is_valid_identifier(name: str) -> None:
    """alias_for always produces a valid Python identifier for any column name."""
    assert alias_for(name).isidentifier()


@given(columns=st.lists(_COLUMN_NAME, min_size=1, max_size=8, unique=True))
def test_property_alias_map_round_trips(columns: list[str]) -> None:
    """build_alias_map yields a unique alias per column that round-trips to it."""
    alias_map = build_alias_map(columns)
    # Every source column appears exactly once as a mapped value.
    assert sorted(alias_map.values()) == sorted(columns)
    # Aliases are unique (one alias never names two different columns).
    assert len(alias_map) == len(columns)


@given(
    values=st.dictionaries(keys=_COLUMN_NAME, values=_FINITE, min_size=1, max_size=6)
)
def test_property_col_round_trips_values(values: dict[str, float]) -> None:
    """col(name) round-trips arbitrary column-name -> value bindings through eval."""
    evaluator = FormulaEvaluator()
    # For each column, col("<name>") must return exactly the stored value.
    for name, expected in values.items():
        result = evaluator.evaluate("col(name)", {**values, "name": name})
        # The 'name' helper key collides only if a column is literally "name";
        # guard that degenerate case out of the assertion.
        if name != "name":
            assert result == expected


# Unsafe-construct corpus: each must be rejected by the validator.
_UNSAFE_EXPRESSIONS = st.sampled_from(
    [
        "Jan.__class__",
        "Jan[0]",
        "(lambda: 1)()",
        "[x for x in Jan]",
        "{x for x in Jan}",
        "eval('1')",
        "open('f')",
        "Unknown + 1",
    ]
)


@given(expr=_UNSAFE_EXPRESSIONS)
def test_property_validator_rejects_unsafe_corpus(expr: str) -> None:
    """The validator rejects every member of the unsafe-construct corpus."""
    evaluator = FormulaEvaluator()
    with pytest.raises(FormulaError):
        evaluator.validate(expr, ["Jan", "Feb"])


# Safe-expression corpus: arithmetic over two known columns must validate.
_SAFE_OPERATORS = st.sampled_from(["+", "-", "*"])


@given(op=_SAFE_OPERATORS)
def test_property_validator_accepts_safe_arithmetic(op: str) -> None:
    """The validator accepts safe arithmetic over known columns."""
    evaluator = FormulaEvaluator()
    # Act / Assert: no exception for arithmetic over declared columns.
    evaluator.validate(f"Jan {op} Feb", ["Jan", "Feb"])


def test_safe_div_nan_numerator_with_valid_denominator_propagates() -> None:
    """A NaN numerator with a valid denominator yields NaN (no silent masking)."""
    result = safe_div(float("nan"), 2.0)
    assert isinstance(result, float)
    assert math.isnan(result)
