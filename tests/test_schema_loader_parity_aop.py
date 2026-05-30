"""AOP parity tests for SchemaLoader vs load_aop (Issue #43, AC2).

Proves ``SchemaLoader(default_aop).load(raw_aop_frame)`` equals
``load_aop(<same workbook>)`` (the validated frame) via
``pandas.testing.assert_frame_equal``. The raw frame and the protected-path
output are built from the SAME in-memory workbook buffers (the shared AOP
fixtures). Covers the with-YTG and without-YTG source layouts and the
sentinel-clean label columns. No temp files, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pandas.testing import assert_frame_equal

from src import load_aop
from src.pandas_io import read_excel_sheet
from src.schema_loader import SchemaLoader
from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

if TYPE_CHECKING:
    from src.schema_model import SchemaDefinition

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aop_fixtures  # noqa: E402

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


def _assert_aop_parity(
    rows: list[dict[str, object]],
    *,
    header: list[str] | None = None,
) -> None:
    """Assert SchemaLoader and load_aop agree on the same AOP workbook.

    Args:
        rows: The AOP source rows to materialize into the workbook.
        header: Optional explicit header (used for the without-YTG layout).

    Raises:
        AssertionError: If the two outputs differ in columns, order, dtypes, or
            values.
    """
    raw_frame = read_excel_sheet(
        aop_fixtures.build_aop_workbook(rows, header=header),
        sheet_name="AOP1",
        header=2,
    )
    protected = load_aop.load_aop(
        aop_fixtures.build_aop_workbook(rows, header=header),
        sheet="AOP1",
        key_mismatch="overwrite",
    )
    loader_output = SchemaLoader(_default_aop()).load(raw_frame)
    assert_frame_equal(loader_output, protected, check_dtype=True, check_like=False)


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
