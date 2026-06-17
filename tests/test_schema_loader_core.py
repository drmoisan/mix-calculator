"""Core-phase tests for :class:`src.schema_loader.SchemaLoader` (Issue #43).

Covers the resolve/rename/extra-warn/blank-drop, key establishment, fill rules,
numeric coercion + sentinel cleaning, and dedup phases (none-preserving,
collapse-additive, collapse-select_from), plus Hypothesis property tests for the
pure dedup-aggregation behavior. Uses the in-memory LE/AOP fixtures; no temp
files, no network.
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src._schema_loader_helpers import collapse_by_key, resolve_and_rename
from src.schema_loader import SchemaLoader
from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
    column_ref,
)

# The in-memory fixtures live in the tests package and import as package modules.
from tests import aop_fixtures, le_fixtures

# The monthly vectors and the bundled-default loader are shared with the seam
# test module; they live in a dedicated underscore-prefixed fixtures module so
# the two cohesive modules reuse identical fixtures without duplication.
from tests._schema_loader_fixtures import _MONTHS_A, _MONTHS_B, _load_default

# ---------------------------------------------------------------------------
# Resolve / rename / blank-drop
# ---------------------------------------------------------------------------


def test_resolve_renames_and_drops_blank_customer_rows() -> None:
    """The loader resolves to canonical names and drops blank-Customer rows (AOP)."""
    # Arrange: two real rows plus a blank-Customer padding row.
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(
            customer=None, sku="2", type_="Net", months=_MONTHS_B
        ),
        aop_fixtures.make_aop_row(
            customer="B", sku="3", type_="Gross", months=_MONTHS_B
        ),
    ]
    raw = aop_fixtures.build_aop_workbook(rows)
    from src.pandas_io import read_excel_sheet

    raw_frame = read_excel_sheet(raw, sheet_name="AOP1", header=2)
    schema = _load_default("default_aop")
    # Act
    out = SchemaLoader(schema).load(raw_frame)
    # Assert: blank-Customer row removed; canonical KEY column present.
    assert len(out) == 2
    assert "KEY" in out.columns
    assert set(out["Customer"]) == {"A", "B"}


# ---------------------------------------------------------------------------
# Key establishment
# ---------------------------------------------------------------------------


def test_key_is_rebuilt_from_customer_sku_type() -> None:
    """The loader establishes KEY as Customer + coerced SKU + Type (LE)."""
    rows = [
        le_fixtures.make_row(
            customer="A", sku="100", type_="Net", ppg="P", months=_MONTHS_A
        ),
    ]
    from src.pandas_io import read_excel_sheet

    raw_frame = read_excel_sheet(
        le_fixtures.build_workbook(rows), sheet_name="LE-8 + 4", header=2
    )
    out = SchemaLoader(_load_default("default_le")).load(raw_frame)
    # The rebuilt key concatenates the three key dimensions.
    assert out.loc[0, "KEY"] == "A100Net"


# ---------------------------------------------------------------------------
# Fill rules
# ---------------------------------------------------------------------------


def test_fill_rules_populate_blank_totals() -> None:
    """Blank FY/quarter totals are filled from their monthly components (LE)."""
    rows = [
        le_fixtures.make_row(
            customer="A",
            sku="1",
            type_="Net",
            ppg="P",
            months=_MONTHS_A,
            blank_totals=True,
        ),
        le_fixtures.make_row(
            customer="A",
            sku="1",
            type_="Net",
            ppg="P",
            months=_MONTHS_B,
            blank_totals=True,
        ),
    ]
    from src.pandas_io import read_excel_sheet

    raw_frame = read_excel_sheet(
        le_fixtures.build_workbook(rows), sheet_name="LE-8 + 4", header=2
    )
    out = SchemaLoader(_load_default("default_le")).load(raw_frame)
    # FY for the collapsed row equals the sum of both rows' monthly totals.
    expected_fy = sum(_MONTHS_A) + sum(_MONTHS_B)
    assert out.loc[0, "FY"] == expected_fy


# ---------------------------------------------------------------------------
# Numeric coercion + sentinel cleaning (AOP)
# ---------------------------------------------------------------------------


def test_sentinel_cleaning_replaces_label_sentinels_with_none() -> None:
    """Sentinel label values (#N/A, 0) are cleaned to None for AOP label columns."""
    rows = [
        aop_fixtures.make_aop_row(
            customer="A",
            sku="1",
            type_="Net",
            months=_MONTHS_A,
            super_category="#N/A",
            ppg=0,
        ),
    ]
    from src.pandas_io import read_excel_sheet

    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows), sheet_name="AOP1", header=2
    )
    out = SchemaLoader(_load_default("default_aop")).load(raw_frame)
    # Both sentinel label cells become None after cleaning.
    assert out.loc[0, "Super Category"] is None
    assert out.loc[0, "PPG"] is None


# ---------------------------------------------------------------------------
# Minimal schema: no fill rules, no numeric/sentinel columns
# ---------------------------------------------------------------------------


def test_load_minimal_schema_without_fill_or_numeric_columns() -> None:
    """A schema with no fill rules and no numeric/sentinel columns loads cleanly.

    Exercises the loader's fill-skip and coerce/clean-skip branches (the schema
    declares neither fill rules nor numeric/sentinel columns), so the optional
    phases are correctly bypassed.
    """
    # Arrange: a frame with only key dimensions and a text column; no totals.
    raw_frame = pd.DataFrame(
        {
            "Customer": ["A", "B"],
            "SKU #": ["1", "2"],
            "Type": ["Net", "Gross"],
            "Label": ["x", "y"],
        }
    )
    schema = SchemaDefinition(
        name="minimal",
        version="1",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(canonical_name="Label", role="dimension"),
        ),
        key=KeySpec(
            parts=tuple(column_ref(_n) for _n in ("Customer", "SKU #", "Type"))
        ),
        dedup=DedupPolicy(mode="none"),
    )
    # Act
    out = SchemaLoader(schema).load(raw_frame)
    # Assert: both rows preserved, KEY created, no fill/coerce phase needed.
    assert list(out["Customer"]) == ["A", "B"]
    assert "KEY" in out.columns


# ---------------------------------------------------------------------------
# Required-output semantics: resolve gate (Issue #74)
# ---------------------------------------------------------------------------

# The six output-identity dimensions that remain required for default_le under
# the 3.0 required-output semantics; a source supplying these resolves even when
# every month/quarter/FY measure is absent.
_LE_IDENTITY_DIMENSIONS = (
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Type",
    "GtN Mapping",
    "PPG",
)


def test_default_le_resolves_when_only_months_are_absent() -> None:
    """The default_le resolve path succeeds when only month/quarter/FY are absent.

    Under 3.0 the month/quarter/FY measures are required=False, so a source that
    supplies the six output-identity dimensions but none of the measures must
    resolve without raising a required-column ValueError.
    """
    # Arrange: a source frame with only the required-output dimensions present.
    raw_frame = pd.DataFrame({name: ["A", "B"] for name in _LE_IDENTITY_DIMENSIONS})
    schema = _load_default("default_le")

    # Act: exercise the resolve phase directly (the phase that gates required
    # columns); it previously raised when months were required.
    resolved = resolve_and_rename(raw_frame, schema)

    # Assert: resolution succeeds and the identity dimensions are present.
    for name in _LE_IDENTITY_DIMENSIONS:
        assert name in resolved.columns
    assert list(resolved["Customer"]) == ["A", "B"]


def test_default_le_resolve_raises_when_required_dimension_absent() -> None:
    """The default_le resolve path still raises when a required dimension is absent.

    A source missing the required-output dimension ``Customer`` must still fail
    resolution with a ValueError, confirming required-output dimensions remain
    gated.
    """
    # Arrange: drop the required Customer dimension; keep the rest present.
    present = [name for name in _LE_IDENTITY_DIMENSIONS if name != "Customer"]
    raw_frame = pd.DataFrame({name: ["A", "B"] for name in present})
    schema = _load_default("default_le")

    # Act / Assert: the missing required dimension raises from resolve_columns.
    with pytest.raises(ValueError):
        resolve_and_rename(raw_frame, schema)


# ---------------------------------------------------------------------------
# Dedup: none (row-preserving)
# ---------------------------------------------------------------------------


def test_dedup_none_preserves_all_rows() -> None:
    """Dedup mode 'none' preserves every row in first-appearance order (AOP, AC3)."""
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(
            customer="B", sku="2", type_="Gross", months=_MONTHS_B
        ),
    ]
    from src.pandas_io import read_excel_sheet

    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows), sheet_name="AOP1", header=2
    )
    out = SchemaLoader(_load_default("default_aop")).load(raw_frame)
    # No collapse: both rows survive, in order.
    assert list(out["Customer"]) == ["A", "B"]


# ---------------------------------------------------------------------------
# Dedup: collapse additive (sum property)
# ---------------------------------------------------------------------------


def test_dedup_collapse_sums_additive_measures() -> None:
    """Dedup mode 'collapse' sums additive measures across same-key rows (AC3)."""
    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P", months=_MONTHS_A
        ),
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P", months=_MONTHS_B
        ),
    ]
    from src.pandas_io import read_excel_sheet

    raw_frame = read_excel_sheet(
        le_fixtures.build_workbook(rows), sheet_name="LE-8 + 4", header=2
    )
    out = SchemaLoader(_load_default("default_le")).load(raw_frame)
    # One collapsed row; Jan equals the sum of both rows' Jan values.
    assert len(out) == 1
    assert out.loc[0, "Jan"] == _MONTHS_A[0] + _MONTHS_B[0]


# ---------------------------------------------------------------------------
# Dedup: collapse select_from
# ---------------------------------------------------------------------------


def _select_from_schema() -> SchemaDefinition:
    """Build a small collapse schema with a select_from measure for testing.

    Returns:
        A :class:`SchemaDefinition` keyed on ``Customer`` whose ``Picked`` measure
        is selected from the row whose ``Half`` discriminator equals ``"second"``,
        and whose ``Added`` measure is additive.
    """
    return SchemaDefinition(
        name="select_test",
        version="1",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Half", role="discriminator"),
            ColumnSpec(canonical_name="Picked", role="measure", numeric=True),
            ColumnSpec(canonical_name="Added", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer",))),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Half",
            measure_aggregations=(
                MeasureAggregation(
                    measure="Picked", mode="select_from", select_values=("second",)
                ),
                MeasureAggregation(measure="Added", mode="additive"),
            ),
        ),
    )


def test_dedup_collapse_select_from_picks_discriminator_row() -> None:
    """Dedup select_from picks the measure from the discriminator-matched row (AC3).

    Exercises the pure ``collapse_by_key`` phase directly so the dedup behavior is
    isolated from the LE/AOP-specific key-rebuild step in the full pipeline.
    """
    # Arrange: two rows sharing one KEY; Picked should come from the "second" row.
    keyed_frame = pd.DataFrame(
        {
            "KEY": ["k1", "k1"],
            "Customer": ["A", "A"],
            "Half": ["first", "second"],
            "Picked": [11.0, 22.0],
            "Added": [3.0, 4.0],
        }
    )
    schema = _select_from_schema()
    # Act
    out = collapse_by_key(keyed_frame, schema)
    # Assert: Picked is the "second"-row value; Added is the sum.
    assert len(out) == 1
    assert out.loc[0, "Picked"] == 22.0
    assert out.loc[0, "Added"] == 7.0


# ---------------------------------------------------------------------------
# Hypothesis property tests (dedup-aggregation sum property)
# ---------------------------------------------------------------------------

_GROUP_VALUES = st.lists(
    st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
    min_size=1,
    max_size=8,
)


@given(values=_GROUP_VALUES)
def test_property_collapse_additive_equals_group_sum(values: list[float]) -> None:
    """A collapsed additive measure equals the arithmetic sum of the group's rows."""
    # Arrange: N rows sharing one key, each with a single additive measure value.
    schema = SchemaDefinition(
        name="sum_prop",
        version="1",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Amount", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer",))),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Customer",
            measure_aggregations=(
                MeasureAggregation(measure="Amount", mode="additive"),
            ),
        ),
    )
    keyed_frame = pd.DataFrame(
        {
            "KEY": ["k"] * len(values),
            "Customer": ["A"] * len(values),
            "Amount": values,
        }
    )
    # Act: exercise the pure collapse phase directly (isolated from key rebuild).
    out = collapse_by_key(keyed_frame, schema)
    # Assert: the single collapsed Amount equals the sum of the group's values.
    assert len(out) == 1
    assert le_fixtures.close(out.loc[0, "Amount"], sum(values))
