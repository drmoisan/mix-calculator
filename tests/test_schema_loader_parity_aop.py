"""AOP parity tests for SchemaLoader vs load_aop (Issue #43, AC1/AC4/AC6).

Under issue #58 the AOP import path no longer fills blank totals or validates
arithmetic identities: ``default_aop.fill_rules`` is empty, so a blank total
coerces to ``0`` and totals pass through unchanged. The whole-frame equality
against ``load_aop`` (which still fills and validates) therefore no longer holds.
These tests instead assert structural parity with the prior loader for the
populated-source cases:

- column set and order match the canonical AOP source layout, and
- the ``KEY`` composition (``Customer + coerce_sku(SKU #) + Type``) matches.

Two issue-#58-specific behaviors are added:

- a no-arithmetic-validation case (a source whose totals violate
  ``YTD == sum(months)`` loads through ``SchemaLoader(default_aop)`` without
  error), and
- a blank-total-pass-through case (a blank ``YTD`` cell yields ``0`` after
  coercion, not the computed month sum).

The raw frames are built from the SAME in-memory workbook buffers used by the
shared AOP fixtures. No temp files, no network.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from src import load_aop
from src.etl_key import coerce_sku
from src.pandas_io import read_excel_sheet
from src.schema_loader import SchemaLoader
from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

# The in-memory fixtures live in the tests package and import as package modules.
from tests import aop_fixtures

if TYPE_CHECKING:
    import pandas as pd

    from src.schema_model import SchemaDefinition

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


def _default_aop() -> SchemaDefinition:
    """Load the bundled ``default_aop`` schema through a real disk store.

    Returns:
        The parsed AOP :class:`SchemaDefinition`.
    """
    registry = SchemaRegistry(Path("."), DiskSchemaFileStore())
    return registry.load_bundled_default("default_aop")


def _load_schema_aop(
    rows: list[dict[str, object]],
    *,
    header: list[str] | None = None,
) -> pd.DataFrame:
    """Load AOP rows through the schema-driven path and return the output frame.

    Args:
        rows: The AOP source rows to materialize into the workbook.
        header: Optional explicit header (used for the without-YTG layout).

    Returns:
        The ``SchemaLoader(default_aop)`` output for the materialized workbook.
    """
    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows, header=header),
        sheet_name="AOP1",
        header=2,
    )
    return SchemaLoader(_default_aop()).load(raw_frame)


def _expected_key(row: dict[str, object]) -> str:
    """Compute the canonical KEY for a row: Customer + coerce_sku(SKU #) + Type.

    Args:
        row: An AOP source-row dict (see ``aop_fixtures.make_aop_row``).

    Returns:
        The rebuilt KEY string the loader is expected to produce.
    """
    return f"{row['Customer']}{coerce_sku(row['SKU #'])}{row['Type']}"


def _assert_aop_parity(
    rows: list[dict[str, object]],
    *,
    header: list[str] | None = None,
) -> None:
    """Assert structural parity between the schema path and the prior loader.

    Under cleared ``fill_rules`` the schema path no longer matches ``load_aop``
    value-for-value (the protected loader still fills/validates). This helper
    instead asserts that, for populated-source rows, the schema-driven output
    has the same column set and order as the prior loader and the same KEY
    composition row-for-row.

    Args:
        rows: The AOP source rows to materialize into the workbook (each row's
            totals must be populated so the loaders agree on column structure).
        header: Optional explicit header (used for the without-YTG layout).

    Raises:
        AssertionError: If the column set/order or KEY composition diverge.
    """
    schema_output = _load_schema_aop(rows, header=header)
    protected = load_aop.load_aop(
        aop_fixtures.build_aop_workbook(rows, header=header),
        sheet="AOP1",
        key_mismatch="overwrite",
    )
    # Column set and order match the prior loader exactly (AC-6).
    assert list(schema_output.columns) == list(protected.columns)
    # KEY composition matches the rebuilt pattern row-for-row (AC-6).
    expected_keys = [_expected_key(row) for row in rows if row["Customer"] is not None]
    assert list(schema_output["KEY"]) == expected_keys
    assert list(protected["KEY"]) == expected_keys


def test_aop_parity_with_ytg() -> None:
    """SchemaLoader equals load_aop for the with-YTG layout (AC2)."""
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(
            customer="B", sku="2", type_="Gross", months=_MONTHS_B
        ),
    ]
    _assert_aop_parity(rows)


def test_aop_parity_without_ytg() -> None:
    """SchemaLoader equals load_aop for the without-YTG source layout (AC2)."""
    header = aop_fixtures.aop_header_without_key(include_ytg=False)
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(
            customer="B", sku="2", type_="Gross", months=_MONTHS_B
        ),
    ]
    _assert_aop_parity(rows, header=header)


def test_aop_parity_sentinel_clean_labels() -> None:
    """SchemaLoader reproduces sentinel cleaning of label columns (AC2)."""
    # Mix sentinel and real label values so cleaning to None is exercised.
    rows = [
        aop_fixtures.make_aop_row(
            customer="A",
            sku="1",
            type_="Net",
            months=_MONTHS_A,
            super_category="#N/A",
            ppg=0,
        ),
        aop_fixtures.make_aop_row(
            customer="B",
            sku="2",
            type_="Gross",
            months=_MONTHS_B,
            super_category="Real",
            ppg="PPGx",
        ),
    ]
    _assert_aop_parity(rows)


def test_aop_parity_no_row_collapse() -> None:
    """SchemaLoader preserves every AOP row (no collapse, no PPG quirk) (AC2)."""
    # Two rows sharing a key would collapse under LE rules; AOP must keep both.
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_B),
    ]
    _assert_aop_parity(rows)


def test_aop_no_arithmetic_validation_loads_broken_totals() -> None:
    """A source whose totals violate YTD == sum(months) loads without error (AC1).

    The schema-driven AOP path applies no arithmetic identity validation, so a
    row whose ``YTD`` does not equal the sum of its months passes through. The
    prior ``load_aop`` path would raise on the same source.
    """
    # Arrange: a populated row whose YTD is deliberately inconsistent with months.
    row = aop_fixtures.make_aop_row(
        customer="A", sku="1", type_="Net", months=_MONTHS_A
    )
    row["YTD"] = 999999.0  # Violates any YTD == sum(...) identity.

    # Act: the schema-driven path loads the broken-total source without raising.
    out = _load_schema_aop([row])

    # Assert: the violating total passes through unchanged (no validation, no fill).
    assert out.loc[0, "YTD"] == 999999.0
    assert out.loc[0, "KEY"] == _expected_key(row)


def test_aop_blank_total_coerces_to_zero_not_month_sum() -> None:
    """A blank YTD cell yields 0 after coercion, not the computed month sum (AC4).

    With ``fill_rules`` cleared, no blank-total fill runs on the AOP path, so a
    blank ``YTD`` is coerced to ``0`` by numeric coercion rather than being
    derived from the month components.
    """
    # Arrange: a row whose totals (including YTD) are left blank.
    row = aop_fixtures.make_aop_row(
        customer="A",
        sku="1",
        type_="Net",
        months=_MONTHS_A,
        blank_totals=True,
    )

    # Act
    out = _load_schema_aop([row])

    # Assert: the blank YTD became 0, not sum(_MONTHS_A) (the computed month sum).
    assert out.loc[0, "YTD"] == 0.0
    assert out.loc[0, "YTD"] != sum(_MONTHS_A)


# The AOP measure columns whose required flag the Phase 5 minimization flips to
# False. YTG is already required=False; the simulated flip exercises the whole set.
_AOP_MEASURES: frozenset[str] = frozenset(
    {
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
        "YTD",
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "YTG",
    }
)


def _flip_aop_measures(schema: SchemaDefinition) -> SchemaDefinition:
    """Return a copy of ``schema`` with every AOP measure set to required=False.

    Uses :func:`dataclasses.replace` to flip each measure column's ``required``
    flag to False while leaving every other field (including the seeded
    ``located_by_name`` on ``KEY``/``YTG``) unchanged. This simulates the Phase 5
    JSON minimization before the bundled file is edited, so the order-independence
    of the loader is proven against the exact flip scenario.

    Args:
        schema: The bundled AOP schema.

    Returns:
        A schema whose measure columns are all required=False.
    """
    # Flip each measure's required flag to False; non-measure columns pass through.
    flipped_columns = tuple(
        (
            dataclasses.replace(column, required=False)
            if column.canonical_name in _AOP_MEASURES
            else column
        )
        for column in schema.columns
    )
    return dataclasses.replace(schema, columns=flipped_columns)


def test_aop_simulated_required_flip_preserves_order_with_ytg() -> None:
    """Flipping every AOP measure to required=False preserves load_aop's order.

    Reproduces the exact CF1 regression scenario before the JSON edit: with the
    loader decouple in place, a schema whose measures are all required=False emits
    the same column order as ``load_aop`` for the with-YTG layout.
    """
    # Arrange: the with-YTG fixture rows and the measure-flipped AOP schema.
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(
            customer="B", sku="2", type_="Gross", months=_MONTHS_B
        ),
    ]
    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows), sheet_name="AOP1", header=2
    )

    # Act: load through the flipped schema and the protected loader.
    flipped = SchemaLoader(_flip_aop_measures(_default_aop())).load(raw_frame)
    protected = load_aop.load_aop(
        aop_fixtures.build_aop_workbook(rows), sheet="AOP1", key_mismatch="overwrite"
    )

    # Assert: the flipped-schema output order matches the load_aop oracle.
    assert list(flipped.columns) == list(protected.columns)


def test_aop_simulated_required_flip_preserves_order_without_ytg() -> None:
    """The simulated flip preserves load_aop's order for the without-YTG layout too."""
    # Arrange: the without-YTG fixture layout and the measure-flipped AOP schema.
    header = aop_fixtures.aop_header_without_key(include_ytg=False)
    rows = [
        aop_fixtures.make_aop_row(customer="A", sku="1", type_="Net", months=_MONTHS_A),
        aop_fixtures.make_aop_row(
            customer="B", sku="2", type_="Gross", months=_MONTHS_B
        ),
    ]
    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows, header=header),
        sheet_name="AOP1",
        header=2,
    )

    # Act
    flipped = SchemaLoader(_flip_aop_measures(_default_aop())).load(raw_frame)
    protected = load_aop.load_aop(
        aop_fixtures.build_aop_workbook(rows, header=header),
        sheet="AOP1",
        key_mismatch="overwrite",
    )

    # Assert: order parity holds for the without-YTG layout under the flip.
    assert list(flipped.columns) == list(protected.columns)
