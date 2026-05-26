"""AOP-specific constants and pure helpers for :mod:`src.load_aop`.

This module holds the AOP schema constants and the pure (I/O-free) helpers used
by the AOP loader so that ``src.load_aop`` stays under the 500-line file limit.
It contains the module constants (months, quarters, source/expected/target
column lists, the snake_case rename map, and index-column list) and the pure
transform/validation/summary helpers.

Responsibilities:
    - ``clean_label_sentinels``: normalize label-column sentinels to ``None``.
    - ``coerce_numeric``: coerce the numeric AOP columns to float.
    - ``validate_aop``: per-row total-identity validation (raises on failure).
    - ``safe_index_name``: build a SQL-safe lowercase index name.
    - ``print_summary``: write the CLI run summary and confirmation to stdout.
    - ``build_parser``: build the load-aop argparse parser.

The only impurity here is ``print_summary`` (writes to stdout) and the WARNING
logging inside ``validate_aop``; neither touches disk, network, or a database.
The SQLite/Excel boundaries live in ``src.load_aop`` and ``src.pandas_io``.
"""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from src.etl_totals import total_vs_months_violations

logger = logging.getLogger(__name__)

# Absolute tolerance for the per-row total identity checks.
TIEOUT_TOL: float = 1e-6

# Month columns in calendar order (source columns G..R).
MONTHS: list[str] = list[str]("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())

# Months contributing to the source YTG measure (May..Dec under the 8+4 rule).
YTG_MONTHS: list[str] = MONTHS[4:]

# Quarter columns (source columns T..W).
QUARTER_COLUMNS: list[str] = ["Q1", "Q2", "Q3", "Q4"]

# Maps each quarter to its three constituent monthly columns sliced from MONTHS
# in calendar order (Q1->Jan,Feb,Mar ... Q4->Oct,Nov,Dec). Used to fill blank
# quarter cells at the read boundary and to validate per-row quarter identity.
QUARTER_TO_MONTHS: dict[str, list[str]] = {
    quarter: MONTHS[index * 3 : index * 3 + 3]
    for index, quarter in enumerate(QUARTER_COLUMNS)
}

# Numeric columns coerced to float before validation (months plus every total).
NUMERIC_COLS: list[str] = [*MONTHS, "YTD", *QUARTER_COLUMNS, "YTG"]

# Source header row, columns A..Z in exact order. The "SKU Descripiton" typo and
# the optional leading "KEY" column are intentional and must match the source.
SOURCE_COLUMNS: list[str] = [
    "KEY",
    "Customer",
    "SKU Descripiton",
    "SKU #",
    "Customer Master",
    "Type",
    *MONTHS,
    "YTD",
    *QUARTER_COLUMNS,
    "YTG",
    "Super Category",
    "PPG",
]

# Required expected columns for resolution: every source column except the
# optional "KEY" (which is resolved by name only and handled separately).
EXPECTED_COLUMNS: list[str] = [c for c in SOURCE_COLUMNS if c != "KEY"]

# Target output header; AOP preserves the full source layout (no column dropped
# and no derived column added), so the target equals the source header.
TARGET_COLUMNS: list[str] = SOURCE_COLUMNS

# Label columns whose sentinel values are cleaned to None after coercion.
LABEL_COLUMNS: list[str] = ["Super Category", "PPG"]

# Snake-case rename map applied before writing when --snake-case is requested.
# The original headers (including the "SKU Descripiton" typo) are preserved by
# default; this map normalizes them to lowercase snake_case identifiers.
SNAKE_CASE_RENAMES: dict[str, str] = {
    "KEY": "key",
    "Customer": "customer",
    "SKU Descripiton": "sku_description",
    "SKU #": "sku_num",
    "Customer Master": "customer_master",
    "Type": "type",
    "YTD": "ytd",
    "YTG": "ytg",
    "Super Category": "super_category",
    "PPG": "ppg",
    "Q1": "q1",
    "Q2": "q2",
    "Q3": "q3",
    "Q4": "q4",
    **{month: month.lower() for month in MONTHS},
}

# Columns that receive a quoted lookup index on the persisted table.
INDEX_COLUMNS: list[str] = ["KEY", "Customer", "SKU #", "Type"]


def clean_label_sentinels(
    frame: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Replace sentinel placeholders with ``None`` in the named label columns.

    The AOP source encodes "no label" several ways in the ``Super Category`` and
    ``PPG`` text columns: the numeric ``0``, the string ``"0"``, the string
    ``"#N/A"``, and a blank (``NaN``) cell. This helper normalizes all of those
    to ``None`` so downstream consumers see a single missing-value marker. Unlike
    the LE normalizer, AOP does not copy ``PPG`` into ``Super Category``; each
    label column is cleaned independently and otherwise left intact.

    Args:
        frame: The working frame (mutated in place and returned).
        columns: The label columns to clean (for example
            ``["Super Category", "PPG"]``).

    Returns:
        The same ``frame`` with each listed column's sentinel values replaced by
        ``None`` and all other values preserved.
    """
    # The sentinel set spans both numeric and string encodings of "no label";
    # NaN is handled separately because it is not equal to itself.
    sentinels: set[object] = {0, "0", "#N/A"}

    # Clean each requested label column independently; a value matching any
    # sentinel (or NaN) becomes None, every other value is kept as-is. The
    # cleaned column is assigned as an object-dtype Series so the None markers
    # survive: assigning a plain list of mixed None/number values would let
    # pandas infer a float column and silently re-coerce None back to NaN.
    for column in columns:
        cleaned = [
            None if (value in sentinels or pd.isna(value)) else value
            for value in frame[column]
        ]
        frame[column] = pd.Series(cleaned, index=frame.index, dtype=object)

    return frame


def coerce_numeric(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce every numeric AOP column to float, filling blanks with ``0.0``.

    Args:
        frame: The working frame with the canonical numeric columns present.

    Returns:
        The same ``frame`` with each :data:`NUMERIC_COLS` column converted via
        ``pd.to_numeric(..., errors="coerce").fillna(0.0)``.
    """
    # Coerce each numeric column to float; non-numeric cells become NaN and are
    # then filled with 0.0 so validation arithmetic never sees text or blanks.
    for column in NUMERIC_COLS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return frame


def validate_aop(frame: pd.DataFrame) -> None:
    """Validate AOP per-row total identities, raising on any failure.

    Runs after numeric coercion and before any transform. Collects every failure
    and raises a single ``ValueError`` listing them all. Duplicate KEYs are a
    warning only and never cause a failure.

    Checks:
        - At least one data row remains.
        - ``YTD == sum(Jan..Dec)`` within :data:`TIEOUT_TOL`.
        - Each ``Q1..Q4`` equals the sum of its three months.
        - ``YTG == sum(May..Dec)``.

    Args:
        frame: The coerced working frame with an established ``KEY`` column.

    Returns:
        ``None`` when every check passes.

    Raises:
        ValueError: When the frame is empty or any per-row total identity is
            violated; the message lists all failures.

    Side effects:
        Emits a ``logging`` warning when duplicate KEYs are present.
    """
    failures: list[str] = []

    # Row-count guard: an empty frame after the blank-Customer drop means the
    # source carried no AOP data rows and cannot be validated or persisted.
    if len(frame) < 1:
        failures.append("no data rows remain after dropping blank-Customer rows")

    # Per-row identity checks: the grand total, each quarter, and the year-to-go
    # measure must each equal the row-wise sum of their constituent months.
    per_row_checks: dict[str, list[str]] = {
        "YTD": MONTHS,
        **QUARTER_TO_MONTHS,
        "YTG": YTG_MONTHS,
    }
    # Only run identity checks when rows exist; on an empty frame the row-count
    # failure above already explains the problem and the column math is moot.
    if len(frame) >= 1:
        for total_column, months in per_row_checks.items():
            offending = total_vs_months_violations(
                frame, total_column, months, TIEOUT_TOL
            )
            if offending:
                failures.append(
                    f"{total_column} != sum(months) for KEY(s) {offending} "
                    f"(tol={TIEOUT_TOL})"
                )

        # Duplicate KEYs are reported but tolerated: AOP preserves rows and does
        # not require KEY uniqueness, so this is a warning rather than a failure.
        duplicate_mask = frame["KEY"].duplicated(keep=False)
        if bool(duplicate_mask.any()):
            duplicate_keys = sorted(
                {str(key) for key in frame.loc[duplicate_mask, "KEY"]}
            )
            logger.warning(
                "Duplicate KEY value(s) present (not a failure): %s.",
                duplicate_keys,
            )

    # Aggregate every failure into a single error so the operator can correct the
    # source in one pass rather than discovering issues one run at a time.
    if failures:
        raise ValueError("AOP validation failed: " + "; ".join(failures) + ".")


def safe_index_name(table: str, column: str) -> str:
    """Build a SQL-safe lowercase index name from a table and column.

    Args:
        table: The destination table name.
        column: The column the index covers.

    Returns:
        A lowercase index name of the form ``ix_<table>_<column>`` with each
        space replaced by ``_`` and each ``#`` replaced by ``num``.
    """
    # Replace the two characters that appear in AOP headers but are awkward in a
    # bare identifier, then lowercase so the index name is stable and quoted-safe.
    safe_column = column.replace(" ", "_").replace("#", "num").lower()
    safe_table = table.replace(" ", "_").replace("#", "num").lower()
    return f"ix_{safe_table}_{safe_column}"


def print_summary(
    df: pd.DataFrame,
    db_path: str,
    table: str,
) -> None:
    """Print the AOP run summary and persistence confirmation to stdout.

    The summary is intentionally written via ``print`` (not ``logging``) because
    it is CLI tool output for the operator; warnings remain on ``logging``.

    Args:
        df: The validated/persisted AOP DataFrame.
        db_path: The SQLite database path the frame was written to.
        table: The destination table name.

    Returns:
        ``None``. Emits the summary and the persistence confirmation to stdout.
    """
    row_count = len(df)
    unique_keys = int(df["KEY"].nunique())
    customers = int(df["Customer"].nunique())
    sku_count = int(df["SKU #"].nunique())
    types = sorted({str(value) for value in df["Type"]})
    ytd_total = float(df["YTD"].sum())

    print("Loaded sheet 'AOP1':")
    print(f"  Rows:           {row_count}")
    print(f"  Unique KEYs:    {unique_keys}")
    print(f"  Customers:      {customers}")
    print(f"  SKU #s:         {sku_count}")
    print(f"  Types:          {types}")
    print(f"  YTD total:      {ytd_total}")
    print("  Validation:     OK")
    print(f"Persisted {row_count} rows to {db_path} (table='{table}')")


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the load-aop CLI.

    Returns:
        A configured ``ArgumentParser`` with the positional input path, the
        required ``--output``, and the ``--source-sheet``, ``--table-name``,
        ``--key-mismatch``, ``--if-exists``, and ``--snake-case`` options.
    """
    parser = argparse.ArgumentParser(
        prog="load-aop",
        description="Load and validate the AOP1 Excel sheet into a SQLite table.",
    )
    parser.add_argument("input", help="Path to the source .xlsx workbook.")
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the SQLite database file to write (required).",
    )
    parser.add_argument(
        "--source-sheet",
        default="AOP1",
        help='Source sheet name (default: "AOP1").',
    )
    parser.add_argument(
        "--table-name",
        default="aop",
        help='Destination SQLite table name (default: "aop").',
    )
    parser.add_argument(
        "--key-mismatch",
        choices=("prompt", "trust", "overwrite"),
        default="prompt",
        help=(
            "How to resolve a present KEY column that diverges from the rebuilt "
            "pattern (default: prompt)."
        ),
    )
    parser.add_argument(
        "--if-exists",
        choices=("replace", "append", "fail"),
        default="replace",
        help="Behavior when the destination table exists (default: replace).",
    )
    parser.add_argument(
        "--snake-case",
        action="store_true",
        help="Rename columns to lowercase snake_case before writing.",
    )
    return parser
