"""Header-detection integration tests for :func:`src.load_aop.load_aop`.

These tests exercise the header-row detection wired into the AOP loader: a flat
workbook whose header is on the first row (index 0) must resolve its columns
without the "Source schema mismatch" error, and must produce the same validated
frame as the equivalent standard header-at-index-2 input for the same data
(parity). All workbooks are built in-memory via ``io.BytesIO`` and openpyxl; no
temporary files are created on disk, per the repository unit-test policy.

The bulk of the AOP load/transform tests live in ``test_load_aop.py`` (494 lines
at baseline); this sibling module holds the header-detection cases so neither
file exceeds the 500-line limit.
"""

from __future__ import annotations

import pandas as pd

from src.load_aop import load_aop
from tests.aop_fixtures import build_aop_workbook, make_aop_row

# A small two-row sample reused for both the flat and standard layouts so the
# only difference between the two loads is the header row position.
_SAMPLE_ROWS = [
    make_aop_row(customer="CustA", sku=9, type_="GS", months=[1.0] * 12),
    make_aop_row(customer="CustB", sku=5, type_="Lbs", months=[2.0] * 12),
]


def test_flat_sheet_header_at_index_zero_resolves_columns() -> None:
    """A flat AOP sheet (header on index 0) loads without a schema mismatch."""
    # Arrange: a flat workbook whose header is on the first row.
    flat_buffer = build_aop_workbook(_SAMPLE_ROWS, leading_rows=0)

    # Act: detection must select index 0 so column resolution succeeds.
    frame = load_aop(flat_buffer, sheet="AOP1")

    # Assert: the canonical columns resolved (Customer present, both rows kept).
    assert "Customer" in frame.columns
    assert len(frame) == 2


def test_flat_sheet_load_equals_standard_header_at_index_two() -> None:
    """A flat (index-0) load equals the standard (index-2) load for same data."""
    # Arrange: identical data written once flat (header index 0) and once in the
    # standard layout (header index 2).
    flat_buffer = build_aop_workbook(_SAMPLE_ROWS, leading_rows=0)
    standard_buffer = build_aop_workbook(_SAMPLE_ROWS, leading_rows=2)

    # Act
    flat_frame = load_aop(flat_buffer, sheet="AOP1")
    standard_frame = load_aop(standard_buffer, sheet="AOP1")

    # Assert: the two loaded frames are identical (parity), so the only change —
    # the header row position — does not alter the loader output.
    pd.testing.assert_frame_equal(
        flat_frame.reset_index(drop=True),
        standard_frame.reset_index(drop=True),
    )
