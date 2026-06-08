"""Header-detection integration tests for :func:`src.normalize_le.load_source`.

These tests exercise the header-row detection wired into the LE loader: a flat
workbook whose header is on the first row (index 0) must resolve its columns
without the "Source schema mismatch" error, and must produce the same loaded
frame as the equivalent standard header-at-index-2 input for the same data
(parity). All workbooks are built in-memory via ``io.BytesIO`` and openpyxl; no
temporary files are created on disk, per the repository unit-test policy.

The bulk of the LE pure-transform and load tests live in ``test_normalize_le.py``;
this sibling module holds the header-detection cases so that file stays under the
500-line limit.
"""

from __future__ import annotations

import pandas as pd

from src.normalize_le import TARGET_COLUMNS, load_source, normalize
from tests.le_fixtures import build_workbook, make_row, source_header_without_key

# A small two-row sample reused for both the flat and standard layouts so the
# only difference between the two loads is the header row position.
_SAMPLE_ROWS = [
    make_row(customer="CustA", sku=9, type_="GS", ppg="PX", months=[1.0] * 12),
    make_row(customer="CustB", sku=5, type_="Lbs", ppg="PY", months=[2.0] * 12),
]


def test_flat_sheet_header_at_index_zero_resolves_columns() -> None:
    """A flat LE sheet (header on index 0) loads without a schema mismatch."""
    # Arrange: a flat workbook whose header is on the first row.
    flat_buffer = build_workbook(_SAMPLE_ROWS, leading_rows=0)

    # Act: detection must select index 0 so column resolution succeeds.
    frame = load_source(flat_buffer, "LE-8 + 4")

    # Assert: the canonical columns resolved (Customer present, both rows kept).
    assert "Customer" in frame.columns
    assert len(frame) == 2


def test_flat_sheet_load_equals_standard_header_at_index_two() -> None:
    """A flat (index-0) load equals the standard (index-2) load for same data."""
    # Arrange: identical data written once flat (header index 0) and once in the
    # standard layout (header index 2).
    flat_buffer = build_workbook(_SAMPLE_ROWS, leading_rows=0)
    standard_buffer = build_workbook(_SAMPLE_ROWS, leading_rows=2)

    # Act
    flat_frame = load_source(flat_buffer, "LE-8 + 4")
    standard_frame = load_source(standard_buffer, "LE-8 + 4")

    # Assert: the two loaded frames are identical (parity), so the only change —
    # the header row position — does not alter the loader output.
    pd.testing.assert_frame_equal(
        flat_frame.reset_index(drop=True),
        standard_frame.reset_index(drop=True),
    )


def test_flat_le84data_style_sheet_imports_to_target_columns() -> None:
    """A flat LE84Data sheet (index 0, no YTD/YTG, no KEY) imports to TARGET_COLUMNS."""
    # Arrange: a flat workbook whose header is on index 0 and omits both the
    # optional YTD/YTG column and the KEY column (the LE84Data-style layout).
    header = [c for c in source_header_without_key() if c != "YTD/YTG"]
    flat_buffer = build_workbook(_SAMPLE_ROWS, header=header, leading_rows=0)

    # Act: load (detection selects index 0) then normalize the loaded frame.
    out = normalize(load_source(flat_buffer, "LE-8 + 4"))

    # Assert: the full 26-column target schema is produced from the must-have set.
    assert set(out.columns) == set(TARGET_COLUMNS)
