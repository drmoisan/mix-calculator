"""Blank-total fill tests for :mod:`src.normalize_le`.

Covers the ``load_source`` blank-total fill behavior (``fill_blank_totals``):
blank ``FY`` and ``Q1``..``Q4`` cells are filled from their monthly components
before collapsing, while populated totals pass through unchanged. The remaining
``load_source`` cases (header/column resolution, blank-customer drop, KEY
overwrite) and the other pure-transform tests live in ``test_normalize_le.py``;
I/O, persistence, and CLI tests live in ``test_normalize_le_io.py``. Shared
in-memory fixtures live in ``le_fixtures.py``; no temporary files are created on
disk.
"""

from __future__ import annotations

from src.normalize_le import load_source
from tests.le_fixtures import (
    build_workbook,
    close,
    make_row,
)

# ---------------------------------------------------------------------------
# load_source — blank-total fill (fill_blank_totals)
# ---------------------------------------------------------------------------


def test_load_source_fills_blank_fy_and_quarters_from_months() -> None:
    """A row with blank FY/quarter cells is filled from its monthly columns.

    Reproduces the source quirk where a deduction-style row leaves FY and the
    quarter totals blank while the monthly columns are populated; load_source
    must fill each blank total from the sum of its constituent months.
    """
    # Arrange: one fabricated row with distinct months so quarter sums differ.
    months = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
    rows = [
        make_row(
            customer="Acme Foods",
            sku=101,
            type_="Deductions",
            ppg="PPG-A",
            months=months,
            blank_totals=True,
        )
    ]
    buffer = build_workbook(rows)

    # Act
    frame = load_source(buffer, "LE-8 + 4")

    # Assert: FY equals all twelve months; each quarter equals its three months.
    row = frame.iloc[0]
    assert close(row["FY"], sum(months))
    assert close(row["Q1"], sum(months[0:3]))
    assert close(row["Q2"], sum(months[3:6]))
    assert close(row["Q3"], sum(months[6:9]))
    assert close(row["Q4"], sum(months[9:12]))


def test_load_source_fills_blank_totals_treating_blank_months_as_zero() -> None:
    """Blank monthly cells count as 0 within the blank-total fill sums.

    A partially-populated row (some months blank) with blank FY/quarter cells
    must fill each total from the sum of only its populated months, since pandas
    sum(axis=1) skips NaN.
    """
    # Arrange: Feb and Nov are blank (None); they contribute 0 to the sums.
    months = [1.0, None, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, None, 12.0]
    rows = [
        make_row(
            customer="Globex Market",
            sku=202,
            type_="Gross Sales",
            ppg="PPG-B",
            months=months,
            blank_totals=True,
        )
    ]
    buffer = build_workbook(rows)

    # Act
    frame = load_source(buffer, "LE-8 + 4")

    # Assert: NaN months count as 0, so FY and Q1/Q4 reflect only populated cells.
    row = frame.iloc[0]
    assert close(row["FY"], 1.0 + 3.0 + 4.0 + 5.0 + 6.0 + 7.0 + 8.0 + 9.0 + 10.0 + 12.0)
    assert close(row["Q1"], 1.0 + 3.0)
    assert close(row["Q4"], 10.0 + 12.0)


def test_load_source_preserves_populated_fy_and_quarters() -> None:
    """A populated FY/quarter value is left unchanged by the blank-total fill.

    The fill is a fillna-style gap fill, not an overwrite; a row that already
    supplies its totals (equal to the month sums, so it stays schema-valid) must
    pass through with those exact values preserved.
    """
    # Arrange: a populated row (blank_totals=False sets each total to its sum).
    months = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0]
    rows = [
        make_row(
            customer="Initech Grocers",
            sku=303,
            type_="Lbs",
            ppg="PPG-C",
            months=months,
            blank_totals=False,
        )
    ]
    buffer = build_workbook(rows)

    # Act
    frame = load_source(buffer, "LE-8 + 4")

    # Assert: the supplied totals are preserved exactly (equal to month sums).
    row = frame.iloc[0]
    assert close(row["FY"], sum(months))
    assert close(row["Q1"], sum(months[0:3]))
    assert close(row["Q2"], sum(months[3:6]))
    assert close(row["Q3"], sum(months[6:9]))
    assert close(row["Q4"], sum(months[9:12]))
