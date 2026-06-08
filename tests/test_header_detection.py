"""Unit tests for :func:`src._header_detection.detect_header_row`.

All workbooks are built in-memory via ``io.BytesIO`` and openpyxl; no temporary
files are created on disk and no network is touched, per the repository
unit-test policy. Each test follows Arrange-Act-Assert and asserts a single
behavior.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pytest
from openpyxl import Workbook

from src._header_detection import detect_header_row
from src.etl_columns import normalize_name

if TYPE_CHECKING:
    from collections.abc import Sequence

# A small, realistic set of expected canonical column labels. Normalized tokens
# are used as the expected-token set the detector scores rows against.
_EXPECTED_LABELS = [
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Type",
    "GtN Mapping",
    "Super Category",
    "PPG",
]
_EXPECTED_TOKENS = frozenset(normalize_name(label) for label in _EXPECTED_LABELS)

# A run of data-row values whose normalized tokens do not coincide with any
# expected token, used to pad non-header rows.
_DATA_ROW = ["Able Sales Company", "Nuggets 20oz", "33105", "GS", 0, 0, 0]


def _build_sheet(
    rows: Sequence[Sequence[object]], *, sheet_name: str = "Sheet1"
) -> io.BytesIO:
    """Build an in-memory ``.xlsx`` whose rows are written verbatim.

    Args:
        rows: The cell rows to append, in order (row 0 first).
        sheet_name: Name of the worksheet to create.

    Returns:
        A ``BytesIO`` positioned at offset 0 containing the workbook bytes.
    """
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = sheet_name
    # Append each supplied row verbatim so the caller controls the exact layout;
    # materialize each row as a list because openpyxl's append expects a list or
    # tuple, not an arbitrary Sequence.
    for row in rows:
        worksheet.append(list(row))
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def test_detects_header_at_index_zero() -> None:
    """A header on the first row resolves to index 0."""
    # Arrange: header row first, then two data rows.
    buffer = _build_sheet([_EXPECTED_LABELS, _DATA_ROW, _DATA_ROW], sheet_name="Flat")

    # Act
    detected = detect_header_row(buffer, "Flat", _EXPECTED_TOKENS, min_match=5)

    # Assert
    assert detected == 0


def test_detects_header_at_index_two() -> None:
    """A header on Excel row 3 (index 2) resolves to index 2 (parity layout)."""
    # Arrange: two leading note rows precede the header, matching the standard
    # pipeline-sheet layout the loaders previously hardcoded as header=2.
    buffer = _build_sheet(
        [
            ["leading note row 1"],
            ["leading note row 2"],
            _EXPECTED_LABELS,
            _DATA_ROW,
        ],
        sheet_name="Standard",
    )

    # Act
    detected = detect_header_row(buffer, "Standard", _EXPECTED_TOKENS, min_match=5)

    # Assert
    assert detected == 2


def test_detects_header_at_index_three() -> None:
    """A workbook with three leading rows resolves the header to index 3."""
    # Arrange: three leading non-header rows precede the header.
    buffer = _build_sheet(
        [
            ["title banner"],
            ["subtitle"],
            ["generated 2026-06-06"],
            _EXPECTED_LABELS,
            _DATA_ROW,
        ],
        sheet_name="Padded",
    )

    # Act
    detected = detect_header_row(buffer, "Padded", _EXPECTED_TOKENS, min_match=5)

    # Assert
    assert detected == 3


def test_no_qualifying_row_raises_value_error_naming_sheet_and_columns() -> None:
    """No row reaching ``min_match`` raises ValueError naming sheet and columns."""
    # Arrange: a workbook of only data rows (no label row in the scan window).
    buffer = _build_sheet([_DATA_ROW, _DATA_ROW, _DATA_ROW], sheet_name="NoHeader")

    # Act / Assert: the error names the sheet and the expected columns.
    with pytest.raises(ValueError) as excinfo:
        detect_header_row(buffer, "NoHeader", _EXPECTED_TOKENS, min_match=5)
    message = str(excinfo.value)
    assert "NoHeader" in message
    assert normalize_name("Customer") in message


def test_data_row_with_few_coincidental_tokens_below_threshold_not_selected() -> None:
    """A data row with a few coincidental expected tokens is rejected by the floor."""
    # Arrange: a single row contains exactly two expected tokens ("Type" and
    # "PPG") plus unrelated data; with min_match=5 it must not be accepted.
    coincidental_row = ["Type", "PPG", "Able Sales Company", 33105, 0]
    buffer = _build_sheet([coincidental_row, _DATA_ROW], sheet_name="Coincidental")

    # Act / Assert: the row's score (2) is below the floor (5), so no row
    # qualifies and detection fails rather than selecting the data row.
    with pytest.raises(ValueError):
        detect_header_row(buffer, "Coincidental", _EXPECTED_TOKENS, min_match=5)


def test_bytesio_rewind_makes_repeated_calls_deterministic() -> None:
    """Calling detection twice on the same buffer returns the same index."""
    # Arrange: a header-at-index-2 workbook reused across two calls.
    buffer = _build_sheet(
        [
            ["leading note row 1"],
            ["leading note row 2"],
            _EXPECTED_LABELS,
            _DATA_ROW,
        ],
        sheet_name="Repeat",
    )

    # Act: the second call relies on the detector rewinding the shared buffer.
    first = detect_header_row(buffer, "Repeat", _EXPECTED_TOKENS, min_match=5)
    second = detect_header_row(buffer, "Repeat", _EXPECTED_TOKENS, min_match=5)

    # Assert
    assert first == 2
    assert second == 2
