"""Loader-helper tests for the located-by-name decouple (issue #74, CF2).

Covers the flag-independent keep-set and ordering behavior of
:mod:`src._schema_loader_helpers` and :mod:`src._schema_loader_keepset`:

- a ``required`` source column absent from the frame still raises,
- a ``located_by_name`` column absent loads without error and is not emitted,
- a present ``located_by_name`` column is located and emitted in its trailing slot,
- the ``none``-path emitted column order is independent of the ``required`` flag.

All schemas and frames are fabricated in memory; no temp files, no network.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src._schema_loader_helpers import resolve_and_rename
from src._schema_loader_keepset import referenced_columns
from src.schema_loader import SchemaLoader
from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    FillRule,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
    column_ref,
)
from tests._schema_loader_fixtures import _load_default

# The seven AOP output-identity dimensions that remain required after the Phase 5
# minimization. Until the bundled JSON flips the measures, the AOP required-output
# set also includes the measures; the post-flip assertion (P5-T3) narrows the
# expected set to exactly these dimensions.
_AOP_REQUIRED_DIMENSIONS = (
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Customer Master",
    "Type",
    "Super Category",
    "PPG",
)


def _none_dedup_schema(columns: tuple[ColumnSpec, ...]) -> SchemaDefinition:
    """Build a ``none``-dedup schema keyed on Customer/SKU #/Type.

    Args:
        columns: The declared columns, in the order they should be considered.

    Returns:
        A :class:`SchemaDefinition` with dedup mode ``none`` and a three-part key.
    """
    return SchemaDefinition(
        name="fabricated",
        version="3.0",
        columns=columns,
        key=KeySpec(
            parts=tuple(column_ref(name) for name in ("Customer", "SKU #", "Type"))
        ),
        dedup=DedupPolicy(mode="none"),
    )


# ---------------------------------------------------------------------------
# required still gates presence (P2-T4)
# ---------------------------------------------------------------------------


def test_required_column_absent_raises() -> None:
    """A required source column absent from the raw frame raises ValueError.

    The keep-set decouple must not weaken the required-presence gate: a column
    declared ``required=True`` whose name is absent from the source still fails
    resolution.
    """
    # Arrange: a schema requiring a Customer Master column the frame omits.
    schema = _none_dedup_schema(
        (
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(canonical_name="Customer Master", role="dimension"),
        )
    )
    raw_frame = pd.DataFrame({"Customer": ["A"], "SKU #": ["1"], "Type": ["Net"]})

    # Act / Assert: the absent required column raises from resolve_columns.
    with pytest.raises(ValueError):
        resolve_and_rename(raw_frame, schema)


# ---------------------------------------------------------------------------
# located_by_name tolerates absence and emits a trailing slot (P2-T5)
# ---------------------------------------------------------------------------


def test_located_by_name_absent_loads_without_error() -> None:
    """A located_by_name column absent from the frame loads and is not emitted."""
    # Arrange: an optional located-by-name column the source omits entirely.
    schema = _none_dedup_schema(
        (
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(
                canonical_name="YTG",
                role="measure",
                required=False,
                located_by_name=True,
            ),
        )
    )
    raw_frame = pd.DataFrame({"Customer": ["A"], "SKU #": ["1"], "Type": ["Net"]})

    # Act: loading does not raise even though the located column is absent.
    out = SchemaLoader(schema).load(raw_frame)

    # Assert: the absent located column is simply not emitted.
    assert "YTG" not in out.columns
    assert list(out["Customer"]) == ["A"]


def test_located_by_name_present_emitted_in_trailing_slot() -> None:
    """A present located_by_name column is located and emitted after the others."""
    # Arrange: the located-by-name YTG is present in the source frame.
    schema = _none_dedup_schema(
        (
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(
                canonical_name="YTG",
                role="measure",
                required=False,
                located_by_name=True,
            ),
        )
    )
    raw_frame = pd.DataFrame(
        {"Customer": ["A"], "SKU #": ["1"], "Type": ["Net"], "YTG": [5.0]}
    )

    # Act
    out = SchemaLoader(schema).load(raw_frame)

    # Assert: YTG is emitted and trails the non-located columns; KEY is created
    # last by the key phase, so YTG precedes KEY in the emitted order.
    assert "YTG" in out.columns
    columns = list(out.columns)
    assert columns.index("YTG") > columns.index("Type")
    assert columns.index("YTG") < columns.index("KEY")


# ---------------------------------------------------------------------------
# Order is independent of the required flag (P3-T1, the CF1-finding reproduction)
# ---------------------------------------------------------------------------


def test_none_path_order_is_independent_of_required_flag() -> None:
    """The none-path emitted order follows resolution order, not the required flag.

    Reproduces the CF1 finding made GREEN: measures declared
    ``required=False, in_output=True`` interleaved with required dimensions, plus a
    trailing ``located_by_name`` optional, must emit in declared/resolution order
    (dimensions and measures in declared order) followed by the located optional
    last. A flipped ``required`` flag must not move the measures.
    """
    # Arrange: required dimensions interleaved with required=False, in_output
    # measures, then a trailing located-by-name optional.
    schema = _none_dedup_schema(
        (
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(
                canonical_name="Jan", role="measure", required=False, in_output=True
            ),
            ColumnSpec(
                canonical_name="Feb", role="measure", required=False, in_output=True
            ),
            ColumnSpec(canonical_name="Super Category", role="dimension"),
            ColumnSpec(
                canonical_name="YTG",
                role="measure",
                required=False,
                located_by_name=True,
            ),
        )
    )
    raw_frame = pd.DataFrame(
        {
            "Customer": ["A"],
            "SKU #": ["1"],
            "Type": ["Net"],
            "Jan": [1.0],
            "Feb": [2.0],
            "Super Category": ["X"],
            "YTG": [9.0],
        }
    )

    # Act
    out = SchemaLoader(schema).load(raw_frame)

    # Assert: the non-located columns keep their declared/resolution order; the
    # located-by-name YTG trails them; KEY (created last) closes the frame. The
    # required=False measures sit in their declared slots, not relocated.
    assert list(out.columns) == [
        "Customer",
        "SKU #",
        "Type",
        "Jan",
        "Feb",
        "Super Category",
        "YTG",
        "KEY",
    ]


# ---------------------------------------------------------------------------
# default_aop required-output accessor (P3-T3; narrowed post-flip in P5-T3)
# ---------------------------------------------------------------------------


def test_aop_required_output_columns_match_expected_set() -> None:
    """AOP required-output columns are exactly the seven identity dimensions.

    After the Phase 5 minimization the bundled AOP measures are required=False, so
    the required-output set is exactly the seven dimensions in declared order and
    excludes every measure (``Jan``..``Dec``, ``YTD``, ``Q1``..``Q4``, ``YTG``).
    The test reads only the public ``required_output_columns()`` accessor.
    """
    # Arrange / Act
    schema = _load_default("default_aop")
    required = schema.required_output_columns()

    # Assert: the required-output set is exactly the seven dimensions, in order,
    # with no measure present.
    assert required == _AOP_REQUIRED_DIMENSIONS


# ---------------------------------------------------------------------------
# referenced_columns gathers every processing-spec reference
# ---------------------------------------------------------------------------


def test_referenced_columns_gathers_all_spec_references() -> None:
    """referenced_columns collects discriminator, aggregations, fills, and copy_from.

    A column referenced only by a key/dedup/fill/derived spec must be carried
    through resolve/rename even when it is neither required nor emitted; this test
    exercises every reference source so the keep-set helper reports the full set.
    """
    # Arrange: a schema whose specs reference columns through every supported path.
    schema = SchemaDefinition(
        name="referenced",
        version="3.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(canonical_name="Disc", role="discriminator", required=False),
            ColumnSpec(canonical_name="Total", role="measure", required=False),
            ColumnSpec(canonical_name="Part", role="measure", required=False),
            ColumnSpec(canonical_name="PPG", role="dimension"),
        ),
        key=KeySpec(
            parts=tuple(column_ref(name) for name in ("Customer", "SKU #", "Type"))
        ),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Disc",
            measure_aggregations=(
                MeasureAggregation(measure="Total", mode="additive"),
            ),
        ),
        derived_columns=(DerivedColumnSpec(name="Super Category", copy_from="PPG"),),
        fill_rules=(FillRule(total="Total", components=("Part",)),),
    )

    # Act
    referenced = referenced_columns(schema)

    # Assert: each reference source contributes its named column(s).
    assert referenced == {"Disc", "Total", "Part", "PPG"}
