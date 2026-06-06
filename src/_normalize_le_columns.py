"""LE column-schema constants and KEY-aware column resolution for the LE loader.

This module holds the LE (Latest Estimate) source/target column-schema constants
and the column-resolution helper used by :mod:`src.normalize_le`. It was extracted
from ``normalize_le.py`` so that file stays under the repository's 500-line cap
while the LE loader gains the example-aware KEY resolver pass-through (issue #52,
AC-7). ``normalize_le`` imports and re-exports these names so existing callers and
tests that import them from ``src.normalize_le`` continue to work unchanged.

Responsibilities:
    - Declare the LE month/quarter/sum/text source and target column constants.
    - ``resolve_le_columns``: a pure helper that locates an optional ``KEY``
      column, resolves every required expected column to its canonical name, and
      returns the actual-to-canonical rename map plus the located KEY column.

Boundaries:
    - This module is pure: it performs no disk, network, or database I/O. It only
      inspects a list of column names and consults the neutral column resolver.
"""

from __future__ import annotations

import logging

from src.etl_columns import normalize_name, resolve_columns

__all__ = [
    "EXPECTED_COLUMNS",
    "MONTH_COLUMNS",
    "QUARTER_COLUMNS",
    "QUARTER_TO_MONTHS",
    "SOURCE_COLUMNS",
    "SUM_COLUMNS",
    "TARGET_COLUMNS",
    "TEXT_COLUMNS",
    "YTG_MONTHS",
    "resolve_le_columns",
]

logger = logging.getLogger(__name__)

# Month columns in calendar order (source columns H..S).
MONTH_COLUMNS: list[str] = list[str](
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
)

# Months contributing to the derived YTG measure (May..Dec under the 8+4 rule).
YTG_MONTHS: list[str] = MONTH_COLUMNS[4:]

# Quarter columns (source columns U..X).
QUARTER_COLUMNS: list[str] = ["Q1", "Q2", "Q3", "Q4"]

# Maps each quarter to its three constituent monthly columns sliced from
# MONTH_COLUMNS in calendar order (Q1->Jan,Feb,Mar ... Q4->Oct,Nov,Dec). Used to
# fill blank FY/quarter cells at the read boundary and to validate per-row
# quarter consistency.
QUARTER_TO_MONTHS: dict[str, list[str]] = {
    quarter: MONTH_COLUMNS[index * 3 : index * 3 + 3]
    for index, quarter in enumerate(QUARTER_COLUMNS)
}

# Numeric columns that are summed when collapsing rows that share a KEY.
SUM_COLUMNS: list[str] = [*MONTH_COLUMNS, "FY", *QUARTER_COLUMNS]

# Text columns taken from the first source row per KEY (the "SKU Descripiton"
# typo is intentional and must be preserved verbatim).
TEXT_COLUMNS: list[str] = list[str](
    "Customer,SKU Descripiton,SKU #,Type,GtN Mapping".split(",")
)

# Source header row, columns A..Z in exact order. The "SKU Descripiton" typo
# and the leading "YTD/YTG" column are intentional and must match the source.
SOURCE_COLUMNS: list[str] = [
    "KEY",
    "YTD/YTG",
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Type",
    "GtN Mapping",
    *MONTH_COLUMNS,
    "FY",
    *QUARTER_COLUMNS,
    "Super Category",
    "PPG",
]

# Required expected columns for resolution: every source column except the
# optional "KEY" (which is resolved by name only and handled separately).
EXPECTED_COLUMNS: list[str] = [c for c in SOURCE_COLUMNS if c != "KEY"]

# Target output header, 26 columns in exact order. "YTD/YTG" is dropped and a
# derived "YTG" column is inserted after "Q4", before "Super Category".
TARGET_COLUMNS: list[str] = [
    "KEY",
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Type",
    "GtN Mapping",
    *MONTH_COLUMNS,
    "FY",
    *QUARTER_COLUMNS,
    "YTG",
    "Super Category",
    "PPG",
]


def resolve_le_columns(
    actual_columns: list[str],
) -> tuple[dict[str, str], str | None]:
    """Resolve LE source columns to canonical names and locate the KEY column.

    Performs the KEY-column lookup and the required-column resolution that the LE
    loader previously inlined in ``load_source``: it finds an optional ``KEY``
    column by normalized name (no fuzzy match), resolves every required expected
    column to its actual source name via :func:`resolve_columns`, warns about any
    extra source columns, and returns an actual-to-canonical rename map that also
    carries the KEY column through under the canonical name ``"KEY"`` when present.

    Args:
        actual_columns: The source frame's column names rendered as strings, in
            source order.

    Returns:
        A ``(selection, key_actual)`` tuple where ``selection`` maps each actual
        source column name to its canonical name (every required expected column,
        plus the located KEY column mapped to ``"KEY"`` when present), and
        ``key_actual`` is the located source KEY column name or ``None`` when the
        source has no KEY column.

    Raises:
        ValueError: When a required expected column cannot be resolved
            (propagated from :func:`resolve_columns`).

    Side effects:
        Emits a ``logging`` warning naming any extra (unmatched, non-KEY) source
        columns; they are not included in the returned rename map.
    """
    # Locate an optional KEY column by normalized name only (no fuzzy match) so
    # it is neither a required expected column nor reported as an extra.
    key_actual: str | None = None
    for column in actual_columns:
        if normalize_name(column) == "key":
            key_actual = column
            break

    # Resolve every required expected column; resolve_columns raises naming any
    # unmatched required column. Extras exclude the located KEY column below.
    resolvable = [c for c in actual_columns if c != key_actual]
    mapping, extras = resolve_columns(resolvable, EXPECTED_COLUMNS)

    # Surface extra source columns as a warning and continue (the caller drops
    # them from the working frame by selecting only the canonical columns).
    if extras:
        logger.warning("Ignoring extra source column(s): %s.", extras)

    # Build the actual-to-canonical rename map from the resolved required columns,
    # then carry the KEY column through under the canonical name when present so
    # the caller can select and rename in one pass.
    selection = {mapping[expected]: expected for expected in EXPECTED_COLUMNS}
    if key_actual is not None:
        selection[key_actual] = "KEY"

    return selection, key_actual
