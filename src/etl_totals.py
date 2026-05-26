"""Total-column derivation for the ETL read boundary.

ETL source workbooks leave some total cells (for example ``FY``/``YTD``,
``YTG``, and the quarter cells ``Q1``..``Q4``) blank (NaN) on some rows while
the monthly columns (``Jan``..``Dec``) are populated. Those totals are
definitionally the sum of their constituent months, so a blank is a gap to fill
rather than a real zero; left blank they read as 0 downstream and trip the
per-row ``total == sum(months)`` tie-out.

Responsibilities:
    - ``fill_blank_totals``: a pure transform that fills only blank total cells
      from the row-wise sum of their constituent months per a supplied mapping,
      leaving populated totals untouched.
    - ``total_vs_months_violations``: a pure check returning the KEYs whose
      total column diverges from the sum of its monthly components beyond a
      tolerance (used by the loaders' per-row validation checks).

This module holds no I/O and is consumed by both the LE and AOP loaders; each
loader calls ``fill_blank_totals`` after columns are resolved/renamed and
blank-``Customer`` rows are dropped, before the ``KEY`` is established.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def fill_blank_totals(
    frame: pd.DataFrame,
    totals_to_months: dict[str, list[str]],
) -> pd.DataFrame:
    """Fill only blank total cells from the sum of their constituent months.

    For each ``(total_column, month_columns)`` entry in ``totals_to_months``,
    fills each blank/NaN cell of ``total_column`` with the row-wise sum of its
    ``month_columns``, leaving any populated total untouched (a fillna-style
    fill, not an overwrite). Months that are themselves NaN count as 0 because
    pandas ``DataFrame.sum(axis=1)`` skips NaN, which is the intended 0-fill.

    The mapping is the contract for which totals to fill and from which months:
    callers pass, for example, ``{"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS}``
    (LE) or ``{"YTD": MONTHS, **QUARTER_TO_MONTHS, "YTG": YTG_MONTHS}`` (AOP).
    No total-column name is hardcoded here.

    Args:
        frame: A canonical-named source frame containing every total column and
            every month column referenced by ``totals_to_months``.
        totals_to_months: A mapping from each total column to the ordered list
            of month columns whose row-wise sum fills that total's blank cells.

    Returns:
        The same ``frame`` (mutated in place and returned) with each mapped
        total's blank cells filled from its monthly sum and populated values
        kept.
    """
    # Fill each blank total from the row-wise sum of its constituent months per
    # the supplied mapping; populated totals are preserved by the fillna fill.
    for total_column, month_columns in totals_to_months.items():
        total_from_months = frame[month_columns].sum(axis=1)
        frame[total_column] = frame[total_column].fillna(total_from_months)

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
