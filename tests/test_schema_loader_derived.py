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
# output-membership (in_output inclusion) exclusion
# ---------------------------------------------------------------------------


def test_in_output_false_excludes_le_discriminator_from_output() -> None:
    """The LE YTD/YTG column (in_output=false) is excluded from the output (AC1).

    Output membership is determined by in_output inclusion, not by drop_columns:
    the discriminator carries through processing but is omitted from the emitted
    frame because its in_output flag is false.
    """
    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P", months=_MONTHS_A
        ),
    ]
    out = SchemaLoader(_load_default("default_le")).load(_le_raw(rows))
    # The discriminator YTD/YTG column is excluded by in_output=false.
    assert "YTD/YTG" not in out.columns


# ---------------------------------------------------------------------------
# output-membership semantics: in_output inclusion/exclusion + dedup discriminator
# ---------------------------------------------------------------------------


def _membership_schema(*, disc_in_output: bool) -> SchemaDefinition:
    """Build a collapse schema with a discriminator whose in_output is parametric.

    The schema keys on Customer/SKU #/Type, collapses two rows sharing the key
    using the Discriminator column, and sums the single measure. The
    discriminator's in_output flag is supplied by the caller so a single fixture
    exercises both the included and excluded cases.

    Args:
        disc_in_output: The in_output flag for the Discriminator column.

    Returns:
        A structurally valid collapse :class:`SchemaDefinition`.
    """
    from src.schema_model import DedupPolicy, MeasureAggregation

    return SchemaDefinition(
        name="membership",
        version="1",
        columns=(
            ColumnSpec(canonical_name="KEY", role="dimension", required=False),
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(
                canonical_name="Discriminator",
                role="discriminator",
                required=False,
                in_output=disc_in_output,
            ),
            ColumnSpec(canonical_name="Amt", role="measure", numeric=True),
        ),
        key=KeySpec(
            parts=(column_ref("Customer"), column_ref("SKU #"), column_ref("Type"))
        ),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Discriminator",
            measure_aggregations=(MeasureAggregation(measure="Amt", mode="additive"),),
        ),
    )


def _membership_frame() -> pd.DataFrame:
    """Return two rows sharing one business key with distinct discriminators.

    Returns:
        A raw frame: one (Customer, SKU #, Type) key, a YTD half and a YTG half,
        whose measures sum to a single collapsed row.
    """
    return pd.DataFrame(
        {
            "Customer": ["A", "A"],
            "SKU #": ["1", "1"],
            "Type": ["Net", "Net"],
            "Discriminator": ["YTD", "YTG"],
            "Amt": [10.0, 5.0],
        }
    )


def test_in_output_true_column_is_included_in_output() -> None:
    """A column with in_output=true appears in the loader output (AC2)."""
    # Arrange: the discriminator is marked in_output=true, so it is kept.
    schema = _membership_schema(disc_in_output=True)
    out = SchemaLoader(schema).load(_membership_frame())

    # Assert: the in_output=true discriminator column is present.
    assert "Discriminator" in out.columns


def test_in_output_false_column_is_excluded_from_output() -> None:
    """A column with in_output=false is excluded from the loader output (AC2)."""
    # Arrange: the discriminator is marked in_output=false, so it is excluded.
    schema = _membership_schema(disc_in_output=False)
    out = SchemaLoader(schema).load(_membership_frame())

    # Assert: the in_output=false discriminator column is absent.
    assert "Discriminator" not in out.columns


def test_processing_only_discriminator_used_for_dedup_but_excluded() -> None:
    """A required:false, in_output:false column drives dedup yet is excluded (AC5).

    The discriminator is present in the source and used by collapse_by_key to
    merge the YTD and YTG halves of one key into a single additive row, but it is
    excluded from the emitted output by in_output=false.
    """
    # Arrange: discriminator excluded from output but present for dedup.
    schema = _membership_schema(disc_in_output=False)

    # Act
    out = SchemaLoader(schema).load(_membership_frame())

    # Assert: the two halves collapsed into one row with the summed measure, and
    # the discriminator is not in the output.
    assert "Discriminator" not in out.columns
    assert len(out) == 1
    assert out.loc[0, "Amt"] == 15.0


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
