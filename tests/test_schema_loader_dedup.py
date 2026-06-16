"""Dedup-mode tests for the schema loader: LE explicit path + auto mode (D-3).

Covers the new ``auto`` dedup mode (group by dimension roles, sum measure roles,
no discriminator) and a regression guard that the existing LE explicit
``select_from``/discriminator path is unchanged. Exercises the pure
``collapse_by_key`` phase directly so the dedup behavior is isolated from the
LE/AOP-specific key-rebuild step. All fixture values are synthetic/masked; no
real workbook values or proprietary column names appear.
"""

from __future__ import annotations

import pandas as pd

from src._schema_loader_helpers import collapse_by_key
from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
    SchemaValidationError,
    column_ref,
)


def _le_select_from_schema() -> SchemaDefinition:
    """Build the LE-style explicit collapse schema with a select_from measure.

    Returns:
        A :class:`SchemaDefinition` keyed on ``Customer`` whose ``Picked`` measure
        is selected from the row whose ``Half`` discriminator equals ``"second"``
        and whose ``Added`` measure is additive — the LE explicit dedup shape.
    """
    return SchemaDefinition(
        name="le_dedup_regression",
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


def test_le_explicit_select_from_dedup_unchanged() -> None:
    """AC-8/D-3 regression: the LE explicit dedup output is byte-for-byte unchanged.

    The relaxed ``auto`` invariant must not alter the explicit
    ``select_from``/discriminator path: ``Picked`` comes from the ``"second"`` row
    and ``Added`` is summed, exactly as before the auto mode was added.
    """
    # Arrange: two masked rows sharing one KEY; Picked should come from "second".
    keyed_frame = pd.DataFrame(
        {
            "KEY": ["k1", "k1"],
            "Customer": ["CUST_A", "CUST_A"],
            "Half": ["first", "second"],
            "Picked": [11.0, 22.0],
            "Added": [3.0, 4.0],
        }
    )
    schema = _le_select_from_schema()

    # Act
    out = collapse_by_key(keyed_frame, schema)

    # Assert: one collapsed row; Picked from the "second" row; Added summed.
    assert len(out) == 1
    assert out.loc[0, "Picked"] == 22.0
    assert out.loc[0, "Added"] == 7.0


def _auto_schema() -> SchemaDefinition:
    """Build an auto-mode schema with two dimensions and two measures, no discriminator.

    Returns:
        A :class:`SchemaDefinition` whose dedup is ``auto`` so the loader groups by
        the ``Region``/``Segment`` dimensions and sums the ``Units``/``Sales``
        measures with no explicit discriminator.
    """
    return SchemaDefinition(
        name="auto_dedup",
        version="1",
        columns=(
            ColumnSpec(canonical_name="Region", role="dimension"),
            ColumnSpec(canonical_name="Segment", role="dimension"),
            ColumnSpec(canonical_name="Units", role="measure", numeric=True),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Region",))),
        dedup=DedupPolicy(mode="auto"),
    )


def test_auto_dedup_groups_dimensions_and_sums_measures() -> None:
    """AC-8/D-3: auto mode groups by dimensions and sums measures, no discriminator."""
    # Arrange: four rows over two (Region, Segment) groups; measures to be summed.
    keyed_frame = pd.DataFrame(
        {
            "KEY": ["k1", "k1", "k2", "k2"],
            "Region": ["North", "North", "South", "South"],
            "Segment": ["Retail", "Retail", "Retail", "Retail"],
            "Units": [1.0, 2.0, 4.0, 8.0],
            "Sales": [10.0, 20.0, 40.0, 80.0],
        }
    )
    schema = _auto_schema()

    # Act
    out = (
        collapse_by_key(keyed_frame, schema)
        .sort_values("Region")
        .reset_index(drop=True)
    )

    # Assert: one row per (Region, Segment) group with summed measures.
    assert len(out) == 2
    north = out[out["Region"] == "North"].iloc[0]
    south = out[out["Region"] == "South"].iloc[0]
    assert north["Units"] == 3.0
    assert north["Sales"] == 30.0
    assert south["Units"] == 12.0
    assert south["Sales"] == 120.0


def test_auto_dedup_policy_requires_no_discriminator() -> None:
    """AC-8/D-3: DedupPolicy(mode="auto") constructs with no discriminator."""
    # Arrange / Act
    policy = DedupPolicy(mode="auto")

    # Assert: auto mode constructs cleanly without a discriminator column.
    assert policy.mode == "auto"
    assert policy.discriminator_column is None


def test_aggregate_still_requires_discriminator_after_auto_added() -> None:
    """AC-8/D-3: the relaxed invariant applies to auto only; aggregate is unchanged."""
    # Act / Assert: aggregate without a discriminator still raises.
    try:
        DedupPolicy(mode="aggregate")
    except SchemaValidationError:
        pass
    else:  # pragma: no cover - the construction must raise
        raise AssertionError("aggregate without discriminator should raise")


def test_auto_dedup_single_group_edge_case() -> None:
    """AC-8/D-3: auto mode over a single group sums all rows into one output row."""
    # Arrange: all rows in one (Region, Segment) group.
    keyed_frame = pd.DataFrame(
        {
            "KEY": ["k1", "k1", "k1"],
            "Region": ["North", "North", "North"],
            "Segment": ["Retail", "Retail", "Retail"],
            "Units": [1.0, 2.0, 3.0],
            "Sales": [10.0, 20.0, 30.0],
        }
    )
    schema = _auto_schema()

    # Act
    out = collapse_by_key(keyed_frame, schema)

    # Assert: a single summed row.
    assert len(out) == 1
    assert out.loc[0, "Units"] == 6.0
    assert out.loc[0, "Sales"] == 60.0


def test_auto_dedup_without_measures_raises() -> None:
    """AC-8/D-3: auto dedup with no measure column raises a clear error."""
    # Arrange: a schema whose only columns are dimensions (no measures to sum).
    keyed_frame = pd.DataFrame(
        {"KEY": ["k1"], "Region": ["North"], "Segment": ["Retail"]}
    )
    schema = SchemaDefinition(
        name="auto_no_measure",
        version="1",
        columns=(
            ColumnSpec(canonical_name="Region", role="dimension"),
            ColumnSpec(canonical_name="Segment", role="dimension"),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Region",))),
        dedup=DedupPolicy(mode="auto"),
    )

    # Act / Assert: nothing to aggregate fails fast with a descriptive message.
    try:
        collapse_by_key(keyed_frame, schema)
    except ValueError as error:
        assert "measure" in str(error)
    else:  # pragma: no cover - the call must raise
        raise AssertionError("auto dedup with no measures should raise")


def test_auto_dedup_without_dimensions_returns_reset_frame() -> None:
    """AC-8/D-3: auto dedup with no dimension columns returns a reset-index frame."""
    # Arrange: a schema whose only column is a measure (no dimension groupby key).
    keyed_frame = pd.DataFrame({"KEY": ["k1", "k1"], "Sales": [10.0, 20.0]})
    schema = SchemaDefinition(
        name="auto_no_dim",
        version="1",
        columns=(ColumnSpec(canonical_name="Sales", role="measure", numeric=True),),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Sales",))),
        dedup=DedupPolicy(mode="auto"),
    )

    # Act: no dimension columns means no grouping is possible.
    out = collapse_by_key(keyed_frame, schema)

    # Assert: the rows are returned unchanged with a fresh RangeIndex.
    assert len(out) == 2
    assert list(out.index) == [0, 1]
