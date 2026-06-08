"""LE column-schema constants and KEY-aware column resolution for the LE loader.

This module holds the LE (Latest Estimate) source/target column-schema constants
and the column-resolution helper used by :mod:`src.normalize_le`. It was extracted
from ``normalize_le.py`` so that file stays under the repository's 500-line cap
while the LE loader gains the example-aware KEY resolver pass-through (issue #52,
AC-7). ``normalize_le`` imports and re-exports these names so existing callers and
tests that import them from ``src.normalize_le`` continue to work unchanged.

Responsibilities:
    - Declare the LE month/quarter/sum/text source and target column constants.
    - ``resolve_le_columns``: a pure helper that locates the optional ``KEY``
      column and each optional-by-name column (``YTD/YTG``, ``Super Category``),
      resolves every required column to its canonical name, and returns the
      actual-to-canonical rename map plus the located KEY column.

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
    "OPTIONAL_BY_NAME",
    "QUARTER_COLUMNS",
    "QUARTER_TO_MONTHS",
    "REQUIRED_COLUMNS",
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

# Must-have source columns: those that contribute to the final output and are
# therefore genuinely required. This is the 23-column set (5 text + 12 months +
# FY + 4 quarters + PPG). It deliberately excludes "KEY" (created/located when
# present), "YTD/YTG" (dropped, never read), and source "Super Category" (the
# output "Super Category" is derived from "PPG", so the source value is ignored).
# A source missing any of these still fails resolution naming the missing column.
REQUIRED_COLUMNS: list[str] = TEXT_COLUMNS + [
    *MONTH_COLUMNS,
    "FY",
    *QUARTER_COLUMNS,
    "PPG",
]

# Columns located by normalized name when present and tolerated when absent. They
# are not required: "YTD/YTG" is dropped at emit and the source "Super Category"
# is overwritten by "PPG" in normalize(). When present they are carried so the
# standard LE-8 + 4 source still drops "YTD/YTG" exactly as before (parity).
OPTIONAL_BY_NAME: list[str] = ["YTD/YTG", "Super Category"]

# The required-only resolution set, matching the AOP module convention where
# EXPECTED_COLUMNS holds only the must-have columns and optional-by-name columns
# (KEY/YTG for AOP; YTD/YTG/Super Category here) are handled separately.
EXPECTED_COLUMNS: list[str] = REQUIRED_COLUMNS

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
    """Resolve LE source columns to canonical names; locate KEY and optionals.

    Performs the column resolution that the LE loader previously inlined in
    ``load_source``, mirroring the AOP ``load_aop`` optional-by-name pattern. It
    locates the optional ``KEY`` column and each :data:`OPTIONAL_BY_NAME` column
    (``YTD/YTG``, ``Super Category``) by normalized name only (no fuzzy match, no
    raise on absence), resolves every :data:`REQUIRED_COLUMNS` entry to its actual
    source name via :func:`resolve_columns`, warns about any extra source columns,
    and returns an actual-to-canonical rename map that also carries the located
    KEY and optional columns through under their canonical names when present.

    Args:
        actual_columns: The source frame's column names rendered as strings, in
            source order.

    Returns:
        A ``(selection, key_actual)`` tuple where ``selection`` maps each actual
        source column name to its canonical name (every required column, plus the
        located KEY column mapped to ``"KEY"`` and each located optional mapped to
        its canonical name, when present), and ``key_actual`` is the located
        source KEY column name or ``None`` when the source has no KEY column.

    Raises:
        ValueError: When a required column cannot be resolved (propagated from
            :func:`resolve_columns`, which names the missing column).

    Side effects:
        Emits a ``logging`` warning naming any extra (unmatched, non-located)
        source columns; they are not included in the returned rename map.
    """
    # Locate the optional KEY column and each optional-by-name column by
    # normalized name only (no fuzzy match), so none of them is treated as a
    # required column or reported as an extra. Absent optionals are simply not
    # located; YTD/YTG and source Super Category are dropped/ignored downstream
    # and are not derived, so tolerating their absence is safe.
    key_actual: str | None = None
    optional_actual: dict[str, str] = {}
    for column in actual_columns:
        normalized = normalize_name(column)
        if normalized == "key":
            key_actual = column
            continue
        # Carry each optional-by-name column under its canonical name when its
        # normalized form matches; the first match per canonical name wins.
        for canonical in OPTIONAL_BY_NAME:
            if (
                normalized == normalize_name(canonical)
                and canonical not in optional_actual
            ):
                optional_actual[canonical] = column

    # Resolve every required column; resolve_columns raises naming any unmatched
    # required column. Exclude the located KEY and optional columns from the
    # resolvable set so they are neither required nor reported as extras.
    located = {key_actual, *optional_actual.values()}
    resolvable = [c for c in actual_columns if c not in located]
    mapping, extras = resolve_columns(resolvable, REQUIRED_COLUMNS)

    # Surface extra source columns as a warning and continue (the caller drops
    # them from the working frame by selecting only the canonical columns).
    if extras:
        logger.warning("Ignoring extra source column(s): %s.", extras)

    # Build the actual-to-canonical rename map from the resolved required columns,
    # then carry the located KEY and optional columns through under their canonical
    # names so the caller can select and rename in one pass. Absent optionals are
    # never added to the selection.
    selection = {mapping[required]: required for required in REQUIRED_COLUMNS}
    if key_actual is not None:
        selection[key_actual] = "KEY"
    for canonical, actual in optional_actual.items():
        selection[actual] = canonical

    return selection, key_actual
