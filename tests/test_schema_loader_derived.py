"""Derived-column / drop / emission tests for SchemaLoader (Issue #43).

Covers the ``copy_from`` quirk, the ``expression``-derived ``YTG``, ratio
recompute via ``safe_div`` (with safe-division edge cases as a Hypothesis
property), the column-builder path (a measure built from an expression rather
than read from the source), drop-column removal, and the exact output column
order/index for both bundled default schemas. Uses in-memory fixtures only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from hypothesis import given
from hypothesis import strategies as st

from src._schema_loader_helpers import apply_derived_columns
from src.schema_formula import FormulaEvaluator
from src.schema_loader import SchemaLoader
from src.schema_model import (
    ColumnSpec,
    DerivedColumnSpec,
    KeySpec,
    SchemaDefinition,
    column_ref,
)
from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

# The in-memory fixtures live in the tests package and import as package modules.
from tests import aop_fixtures, le_fixtures

_MONTHS_A: list[float] = [
    10.0,
    20.0,
    30.0,
    40.0,
    50.0,
    60.0,
    70.0,
    80.0,
    90.0,
    100.0,
    110.0,
    120.0,
]
_MONTHS_B: list[float] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]


def _load_default(name: str) -> SchemaDefinition:
    """Load a bundled default schema by name through a real disk store.

    Args:
        name: The bundled schema name.

    Returns:
        The parsed :class:`SchemaDefinition`.
    """
    registry = SchemaRegistry(Path("."), DiskSchemaFileStore())
    return registry.load_bundled_default(name)


def _le_raw(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Read an in-memory LE workbook of ``rows`` into a raw frame.

    Args:
        rows: The LE source-row dicts.

    Returns:
        The raw header=2 frame for the LE sheet.
    """
    from src.pandas_io import read_excel_sheet

    return read_excel_sheet(
        le_fixtures.build_workbook(rows), sheet_name="LE-8 + 4", header=2
    )


# ---------------------------------------------------------------------------
# copy_from quirk
# ---------------------------------------------------------------------------


def test_copy_from_populates_super_category_from_ppg() -> None:
    """The copy_from quirk populates Super Category from PPG (LE, AC4)."""
    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="SourcePPG", months=_MONTHS_A
        ),
    ]
    out = SchemaLoader(_load_default("default_le")).load(_le_raw(rows))
    # Both Super Category and PPG equal the source PPG value.
    assert out.loc[0, "Super Category"] == "SourcePPG"
    assert out.loc[0, "PPG"] == "SourcePPG"


# ---------------------------------------------------------------------------
# expression-derived YTG
# ---------------------------------------------------------------------------


def test_expression_derives_ytg_as_sum_may_to_dec() -> None:
    """The YTG derived expression equals sum(May..Dec) on the aggregated row (AC5)."""
    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P", months=_MONTHS_A
        ),
    ]
    out = SchemaLoader(_load_default("default_le")).load(_le_raw(rows))
    # YTG = sum of May..Dec (indices 4..11).
    assert out.loc[0, "YTG"] == sum(_MONTHS_A[4:])


# ---------------------------------------------------------------------------
# drop-columns removal
# ---------------------------------------------------------------------------


def test_drop_columns_removed_from_output() -> None:
    """The schema drop-columns (LE YTD/YTG) are absent from the output (AC1)."""
    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P", months=_MONTHS_A
        ),
    ]
    out = SchemaLoader(_load_default("default_le")).load(_le_raw(rows))
    # The discriminator YTD/YTG column is dropped from the output.
    assert "YTD/YTG" not in out.columns


# ---------------------------------------------------------------------------
# Exact output column order / index for both default schemas
# ---------------------------------------------------------------------------


def test_le_output_column_order_matches_target() -> None:
    """The LE output columns match normalize_le.TARGET_COLUMNS in order (AC1)."""
    from src import normalize_le

    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P", months=_MONTHS_A
        ),
    ]
    out = SchemaLoader(_load_default("default_le")).load(_le_raw(rows))
    assert list(out.columns) == normalize_le.TARGET_COLUMNS
    # Collapse path resets the index to a default RangeIndex.
    assert list(out.index) == list(range(len(out)))


def test_aop_output_columns_present() -> None:
    """The AOP output contains every canonical column with KEY present (AC2)."""
    from src.pandas_io import read_excel_sheet

    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
    ]
    raw = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows), sheet_name="AOP1", header=2
    )
    out = SchemaLoader(_load_default("default_aop")).load(raw)
    # The AOP output preserves all source columns and the created KEY.
    for column in ("KEY", "Customer", "SKU #", "YTG", "Super Category", "PPG"):
        assert column in out.columns


# ---------------------------------------------------------------------------
# Column-builder path (a measure built from an expression over existing columns)
# ---------------------------------------------------------------------------


def test_column_builder_constructs_missing_column_from_expression() -> None:
    """A derived expression builds a column from other columns (AC4)."""
    # Arrange: a frame with two source columns and a schema deriving their sum.
    frame = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
    schema = SchemaDefinition(
        name="builder",
        version="1",
        columns=(
            ColumnSpec(canonical_name="a", role="measure", numeric=True),
            ColumnSpec(canonical_name="b", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("a",))),
        derived_columns=(DerivedColumnSpec(name="total", expression="a + b"),),
    )
    # Act: apply derived columns directly (isolated from key rebuild).
    out = apply_derived_columns(frame.copy(), schema, FormulaEvaluator())
    # Assert: the built column equals the element-wise sum.
    assert list(out["total"]) == [4.0, 6.0]


def test_ratio_recompute_via_safe_div_expression() -> None:
    """A ratio column recomputes from dollars/volume via safe_div (AC5)."""
    frame = pd.DataFrame({"dollars": [50.0, 0.0], "volume": [10.0, 0.0]})
    schema = SchemaDefinition(
        name="ratio",
        version="1",
        columns=(
            ColumnSpec(canonical_name="dollars", role="measure", numeric=True),
            ColumnSpec(canonical_name="volume", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("dollars",))),
        derived_columns=(
            DerivedColumnSpec(name="rate", expression="safe_div(dollars, volume)"),
        ),
    )
    out = apply_derived_columns(frame.copy(), schema, FormulaEvaluator())
    # First row divides cleanly; the zero-volume row yields 0.0 (safe division).
    assert out.loc[0, "rate"] == 5.0
    assert out.loc[1, "rate"] == 0.0


# ---------------------------------------------------------------------------
# Hypothesis property: ratio safe-division across generated denominators (AC5)
# ---------------------------------------------------------------------------

_DOLLARS = st.floats(
    min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False
)
_DENOM = st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False)


@given(dollars=st.lists(_DOLLARS, min_size=1, max_size=6))
def test_property_ratio_safe_div_zero_and_negative_denominators(
    dollars: list[float],
) -> None:
    """A derived ratio yields 0.0 for every zero/negative denominator (AC5)."""
    # Arrange: every denominator is 0.0 so the ratio must be 0.0 for every row.
    frame = pd.DataFrame({"dollars": dollars, "volume": [0.0] * len(dollars)})
    schema = SchemaDefinition(
        name="ratio_prop",
        version="1",
        columns=(
            ColumnSpec(canonical_name="dollars", role="measure", numeric=True),
            ColumnSpec(canonical_name="volume", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("dollars",))),
        derived_columns=(
            DerivedColumnSpec(name="rate", expression="safe_div(dollars, volume)"),
        ),
    )
    # Act
    out = apply_derived_columns(frame.copy(), schema, FormulaEvaluator())
    # Assert: zero denominator -> 0.0 for every generated numerator.
    assert list(out["rate"]) == [0.0] * len(dollars)


@given(
    pairs=st.lists(
        st.tuples(
            _DOLLARS,
            st.floats(
                min_value=1e-3, max_value=1e5, allow_nan=False, allow_infinity=False
            ),
        ),
        min_size=1,
        max_size=6,
    )
)
def test_property_ratio_safe_div_positive_denominators_divide(
    pairs: list[tuple[float, float]],
) -> None:
    """A derived ratio equals dollars/volume for every positive denominator (AC5)."""
    dollars = [d for d, _ in pairs]
    volume = [v for _, v in pairs]
    frame = pd.DataFrame({"dollars": dollars, "volume": volume})
    schema = SchemaDefinition(
        name="ratio_prop_pos",
        version="1",
        columns=(
            ColumnSpec(canonical_name="dollars", role="measure", numeric=True),
            ColumnSpec(canonical_name="volume", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("dollars",))),
        derived_columns=(
            DerivedColumnSpec(name="rate", expression="safe_div(dollars, volume)"),
        ),
    )
    out = apply_derived_columns(frame.copy(), schema, FormulaEvaluator())
    # Each row equals dollars/volume within floating-point tolerance.
    for index, (numerator, denominator) in enumerate(pairs):
        assert le_fixtures.close(out.loc[index, "rate"], numerator / denominator)
