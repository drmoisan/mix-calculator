"""LE parity tests for SchemaLoader vs normalize_le (Issue #43, AC1).

Proves ``SchemaLoader(default_le).load(raw_le_frame)`` equals
``normalize_le.normalize(load_source(<same workbook>))`` via
``pandas.testing.assert_frame_equal``. The raw frame and the protected-path
output are built from the SAME in-memory workbook buffers (the shared LE
fixtures), so the comparison is exact. Covers multi-row collapse, the blank-
totals fill quirk, and the PPG copy quirk. No temp files, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pandas.testing import assert_frame_equal

from src import normalize_le
from src.pandas_io import read_excel_sheet
from src.schema_loader import SchemaLoader
from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

if TYPE_CHECKING:
    from src.schema_model import SchemaDefinition

sys.path.insert(0, str(Path(__file__).resolve().parent))

import le_fixtures  # noqa: E402

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


def _default_le() -> SchemaDefinition:
    """Load the bundled ``default_le`` schema through a real disk store.

    Returns:
        The parsed LE :class:`SchemaDefinition`.
    """
    registry = SchemaRegistry(Path("."), DiskSchemaFileStore())
    return registry.load_bundled_default("default_le")


def _assert_le_parity(rows: list[dict[str, object]]) -> None:
    """Assert SchemaLoader and normalize_le agree on the same LE workbook.

    Builds the raw frame and the protected-path output from the SAME workbook
    contents (two independent buffers with identical rows) and compares the
    SchemaLoader output to the protected output with ``assert_frame_equal``.

    Args:
        rows: The LE source rows to materialize into the workbook.

    Raises:
        AssertionError: If the two outputs differ in columns, order, dtypes, or
            values.
    """
    # Read the raw frame from one buffer; the protected path consumes a second
    # buffer with identical contents (load_source reads at header=2 internally).
    raw_frame = read_excel_sheet(
        le_fixtures.build_workbook(rows), sheet_name="LE-8 + 4", header=2
    )
    protected = normalize_le.normalize(
        normalize_le.load_source(
            le_fixtures.build_workbook(rows), "LE-8 + 4", key_mismatch="overwrite"
        )
    )
    loader_output = SchemaLoader(_default_le()).load(raw_frame)
    assert_frame_equal(loader_output, protected, check_dtype=True, check_like=False)


def test_le_parity_multi_row_collapse() -> None:
    """SchemaLoader equals normalize for multi-row collapse per KEY (AC1)."""
    rows = [
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P1", months=_MONTHS_A
        ),
        le_fixtures.make_row(
            customer="A", sku="1", type_="Net", ppg="P1", months=_MONTHS_B
        ),
        le_fixtures.make_row(
            customer="B", sku="2", type_="Gross", ppg="P2", months=_MONTHS_A
        ),
        le_fixtures.make_row(
            customer="B", sku="2", type_="Gross", ppg="P2", months=_MONTHS_B
        ),
    ]
    _assert_le_parity(rows)


def test_le_parity_blank_totals_fill() -> None:
    """SchemaLoader equals normalize when source totals are blank (fill quirk, AC1)."""
    rows = [
        le_fixtures.make_row(
            customer="A",
            sku="1",
            type_="Net",
            ppg="P1",
            months=_MONTHS_A,
            blank_totals=True,
        ),
        le_fixtures.make_row(
            customer="A",
            sku="1",
            type_="Net",
            ppg="P1",
            months=_MONTHS_B,
            blank_totals=True,
        ),
    ]
    _assert_le_parity(rows)


def test_le_parity_ppg_quirk() -> None:
    """SchemaLoader reproduces the Super Category <- PPG copy quirk (AC1)."""
    # The source Super Category must be ignored; both output label columns equal
    # the source PPG. The fixture's default super_category is a sentinel string.
    rows = [
        le_fixtures.make_row(
            customer="C", sku="3", type_="Net", ppg="QuirkPPG", months=_MONTHS_A
        ),
        le_fixtures.make_row(
            customer="C", sku="3", type_="Net", ppg="QuirkPPG", months=_MONTHS_B
        ),
    ]
    _assert_le_parity(rows)


@pytest.mark.parametrize(
    "ppg_values",
    [
        ("P1", "P2", "P3"),
        ("Alpha", "Beta", "Gamma"),
    ],
)
def test_le_parity_multiple_keys(ppg_values: tuple[str, str, str]) -> None:
    """SchemaLoader equals normalize across several distinct keys (AC1)."""
    rows: list[dict[str, object]] = []
    # Two rows per key (YTD and YTG halves) across three distinct customers.
    for index, ppg in enumerate(ppg_values):
        customer = f"Cust{index}"
        sku = str(100 + index)
        rows.append(
            le_fixtures.make_row(
                customer=customer, sku=sku, type_="Net", ppg=ppg, months=_MONTHS_A
            )
        )
        rows.append(
            le_fixtures.make_row(
                customer=customer, sku=sku, type_="Net", ppg=ppg, months=_MONTHS_B
            )
        )
    _assert_le_parity(rows)
