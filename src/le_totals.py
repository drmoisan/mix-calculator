"""FY/quarter total derivation for the LE ETL read boundary.

The LE source workbook leaves the ``FY`` cell and quarter cells (``Q1``..``Q4``)
blank (NaN) on some rows while the monthly columns (``Jan``..``Dec``) are
populated. Those totals are definitionally the sum of their constituent months,
so a blank is a gap to fill rather than a real zero; left blank they read as 0
downstream and trip the per-row ``FY == sum(months)`` tie-out.

Responsibilities:
    - ``fill_blank_totals``: a pure transform that fills only the blank ``FY``
      and quarter cells from their monthly sums, leaving populated totals
      untouched.
    - ``total_vs_months_violations``: a pure check returning the KEYs whose
      total column diverges from the sum of its monthly components beyond a
      tolerance (used by ``validate_tieouts`` for the FY and quarter checks).

This module holds no I/O; the Excel read boundary in ``normalize_le`` calls
``fill_blank_totals`` after columns are resolved/renamed and blank-``Customer``
rows are dropped, before the ``KEY`` is established.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def fill_blank_totals(
    frame: pd.DataFrame,
    month_columns: list[str],
    quarter_to_months_map: dict[str, list[str]],
) -> pd.DataFrame:
    """Fill only blank ``FY``/quarter cells from their monthly components.

    Fills each blank ``FY`` with ``sum(month_columns)`` and each blank quarter
    with the sum of its three months, leaving any populated total untouched (a
    fillna-style fill, not an overwrite). Months that are themselves NaN count
    as 0 because pandas ``DataFrame.sum(axis=1)`` skips NaN, which is the
    intended 0-fill.

    Args:
        frame: A canonical-named source frame with the ``month_columns``,
            ``FY``, and quarter columns present.
        month_columns: The twelve monthly columns in calendar order.
        quarter_to_months_map: The quarter -> constituent-months grouping
            (``Q1``->``Jan``,``Feb``,``Mar`` ... ``Q4``->``Oct``,``Nov``,``Dec``).

    Returns:
        The same ``frame`` (mutated in place and returned) with blank ``FY`` and
        quarter cells filled from their monthly sums and populated values kept.
    """
    # Fill blank FY from the row-wise sum of all twelve months.
    fy_from_months = frame[month_columns].sum(axis=1)
    frame["FY"] = frame["FY"].fillna(fy_from_months)

    # Fill each blank quarter from the row-wise sum of its three months per the
    # supplied grouping (Q1->Jan..Mar ... Q4->Oct..Dec).
    for quarter, quarter_months in quarter_to_months_map.items():
        quarter_from_months = frame[quarter_months].sum(axis=1)
        frame[quarter] = frame[quarter].fillna(quarter_from_months)

    return frame


def total_vs_months_violations(
    frame: pd.DataFrame,
    total_column: str,
    month_columns: list[str],
    tol: float,
) -> list[object]:
    """Return the KEYs whose total column diverges from its monthly sum.

    A pure per-row consistency check: ``total_column`` must equal the row-wise
    sum of ``month_columns`` within ``tol``. Rows that violate this return their
    ``KEY`` value so the caller can name them in an error.

    Args:
        frame: A frame containing ``KEY``, ``total_column``, and every column in
            ``month_columns``.
        total_column: The total column to validate (for example ``"FY"`` or a
            quarter such as ``"Q1"``).
        month_columns: The monthly columns whose row-wise sum the total must
            match.
        tol: Absolute tolerance for the floating-point comparison.

    Returns:
        A list of the ``KEY`` values of rows where the absolute difference
        exceeds ``tol`` (empty when every row is consistent).
    """
    month_sums = frame[month_columns].sum(axis=1)
    diff = (frame[total_column] - month_sums).abs()
    offending: list[object] = frame.loc[diff > tol, "KEY"].tolist()
    return offending
