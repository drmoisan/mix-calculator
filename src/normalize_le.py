"""Normalize an LE (Latest Estimate) topline Excel sheet into a SQLite table.

This module reproduces an as-built Excel normalization for the ``LE-8 + 4``
planning sheet. Each ``(Customer, SKU #, Type)`` business key appears in the
source twice (a year-to-date ``YTD`` half and a year-to-go ``YTG`` half). The
transform collapses every source row sharing a rebuilt ``KEY`` into a single
output row: text columns are taken from the first matching source row, while
month, ``FY``, and quarter columns are summed. A derived ``YTG`` measure equal
to ``sum(May..Dec)`` is added, the source ``YTD/YTG`` column is dropped, and a
deliberate as-built quirk is preserved in which both the ``Super Category`` and
``PPG`` output columns are populated from the source ``PPG`` column.

The only output sink is SQLite. The normalized DataFrame is read from Excel,
transformed entirely in pandas, and persisted with
``to_sql(table, conn, if_exists="replace", index=False)``.

Boundaries:
    - ``load_source`` is the Excel read boundary (openpyxl engine).
    - ``write_sqlite`` is the SQLite write boundary.
    - All other functions are pure transforms with no I/O.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from typing import IO, TYPE_CHECKING

import pandas as pd

from src._normalize_le_columns import (
    EXPECTED_COLUMNS,
    MONTH_COLUMNS,
    QUARTER_COLUMNS,
    QUARTER_TO_MONTHS,
    SOURCE_COLUMNS,
    SUM_COLUMNS,
    TARGET_COLUMNS,
    TEXT_COLUMNS,
    YTG_MONTHS,
    resolve_le_columns,
)
from src.etl_columns import resolve_columns
from src.etl_key import coerce_sku, decide_key_action, rebuild_key, resolve_key
from src.etl_totals import fill_blank_totals, total_vs_months_violations
from src.pandas_io import read_excel_sheet, write_table

if TYPE_CHECKING:
    from collections.abc import Callable

# Re-export the column resolver, KEY helpers, and the extracted LE column-schema
# constants and resolver so callers and tests can import them from this module as
# well as from their home modules. The neutral resolver lives in
# ``src.etl_columns``, the KEY helpers in ``src.etl_key``, and the LE column
# schema/resolution in ``src._normalize_le_columns`` so this file stays under the
# 500-line limit.
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
    "coerce_sku",
    "compute_ytg",
    "decide_key_action",
    "load_source",
    "main",
    "normalize",
    "print_summary",
    "rebuild_key",
    "resolve_columns",
    "resolve_key",
    "resolve_le_columns",
    "validate_tieouts",
    "write_sqlite",
]

logger = logging.getLogger(__name__)

# Accepted inputs for the Excel read boundary: a filesystem path or a binary
# file-like buffer (the in-memory test fixtures pass a BytesIO).
ExcelSource = str | IO[bytes]


def load_source(
    path: ExcelSource,
    sheet_name: str,
    *,
    key_mismatch: str = "prompt",
    is_tty: Callable[[], bool] = sys.stdin.isatty,
    prompt: Callable[[str], str] = input,
    resolver: Callable[[list[tuple[str, str]]], str] | None = None,
) -> pd.DataFrame:
    """Load and clean the source sheet (Excel read boundary).

    Reads the workbook with openpyxl treating Excel row 3 as the header
    (``header=2``), resolves the source columns to the canonical expected names
    (position pass then fuzzy pass via :func:`resolve_columns`), renames the
    frame to those canonical names, drops rows with a blank ``Customer``, and
    establishes the ``KEY`` column per :func:`resolve_key`.

    Args:
        path: Filesystem path or binary file-like buffer accepted by
            ``pd.read_excel`` (see :data:`ExcelSource`).
        sheet_name: Name of the sheet to read (for example ``"LE-8 + 4"``).
        key_mismatch: The ``--key-mismatch`` policy applied when a present
            ``KEY`` column diverges from the rebuilt pattern.
        is_tty: Callable returning whether stdin is interactive (injectable for
            tests; defaults to ``sys.stdin.isatty``).
        prompt: Callable used to ask the user on the interactive prompt path
            (injectable for tests; defaults to the built-in ``input``).
        resolver: Optional example-aware KEY-mismatch resolver forwarded to
            :func:`resolve_key`. When supplied (the GUI path) it is invoked only
            on a genuine divergence with up to three ``(existing, rebuilt)``
            example pairs and returns ``"trust"`` or ``"overwrite"``. When
            ``None`` (the default and the CLI path), divergence is resolved via
            ``key_mismatch``/``is_tty``/``prompt`` exactly as before (issue #52,
            AC-5/AC-6).

    Returns:
        A DataFrame with the canonical expected columns plus an established
        ``KEY`` column, with blank-``Customer`` rows removed.

    Raises:
        ValueError: When a required expected column cannot be resolved
            (propagated from :func:`resolve_columns`), or when a diverging
            ``KEY`` cannot be resolved (propagated from :func:`resolve_key`).

    Side effects:
        Reads from the filesystem (or the provided buffer) via openpyxl and
        emits ``logging`` warnings for extra source columns and for
        ``trust``/``overwrite`` KEY resolution.
    """
    # Route the read through the typed pandas_io boundary, which contains the
    # openpyxl-driven unknown member type so it does not surface here.
    frame: pd.DataFrame = read_excel_sheet(path, sheet_name=sheet_name, header=2)
    actual_columns = list(frame.columns.astype(str))

    # Resolve the source columns to canonical names and locate the optional KEY
    # column in one pass (extracted to src._normalize_le_columns so this file
    # stays under the 500-line cap). The returned selection maps each actual
    # source column to its canonical name, carrying KEY through when present.
    selection, key_actual = resolve_le_columns(actual_columns)

    # Select and rename to canonical expected names so all downstream logic uses
    # canonical names regardless of source order. Build the keep-list in canonical
    # expected order with the KEY column appended last, matching the prior
    # in-place behavior; invert the selection map to find each canonical column's
    # source name.
    canonical_to_actual = {canonical: actual for actual, canonical in selection.items()}
    columns_to_keep = [canonical_to_actual[expected] for expected in EXPECTED_COLUMNS]
    if key_actual is not None:
        columns_to_keep.append(key_actual)
    frame = frame[columns_to_keep].rename(columns=selection).copy()

    # Drop trailing/interspersed rows with no Customer; these are blank padding
    # rows in the source sheet that carry no business data.
    customer_blank = frame["Customer"].isna() | (
        frame["Customer"].astype(str).str.strip() == ""
    )
    frame = frame.loc[~customer_blank].copy()

    # Fill only the blank FY/quarter totals from their monthly components: the
    # source omits these totals on some rows even though they are definitionally
    # the sum of their months, and left blank they read as 0 and trip the tie-out.
    frame = fill_blank_totals(frame, {"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS})

    # Establish KEY per the documented branches (create/trust/resolve).
    frame = resolve_key(
        frame,
        key_mismatch,
        has_key_column=key_actual is not None,
        is_tty=is_tty,
        prompt=prompt,
        resolver=resolver,
    )
    return frame


def compute_ytg(df: pd.DataFrame) -> pd.Series[float]:
    """Compute the derived YTG measure as the row-wise sum of May..Dec.

    Under the "8 + 4" convention the year-to-go projection is the sum of the
    May through December monthly columns.

    Args:
        df: A DataFrame containing the :data:`YTG_MONTHS` columns.

    Returns:
        A ``pd.Series`` of the row-wise sum of the May..Dec columns, aligned to
        ``df``'s index.
    """
    result: pd.Series[float] = df[YTG_MONTHS].sum(axis=1)
    return result


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse source rows sharing a KEY into one normalized output row.

    Text columns are taken from the first source row per KEY; month, ``FY``, and
    quarter columns are summed (NaN treated as 0). A derived ``YTG`` column is
    added, the ``YTD/YTG`` column is dropped, and both ``Super Category`` and
    ``PPG`` output columns are populated from the source ``PPG`` column (the
    as-built quirk). Output rows preserve first-appearance order and numeric
    precision is preserved (no rounding).

    Args:
        df: A validated source DataFrame with a rebuilt ``KEY`` column.

    Returns:
        A DataFrame with exactly the 26 :data:`TARGET_COLUMNS` in order, one row
        per unique KEY, in first-appearance order.
    """
    # First row per KEY supplies all text fields and the source PPG value.
    first_rows = df.drop_duplicates(subset="KEY", keep="first").set_index("KEY")

    # Sum numeric columns across every row sharing a KEY; sort=False preserves
    # first-appearance order and the default min_count=0 fills all-NaN as 0.
    sums = df.groupby("KEY", sort=False)[SUM_COLUMNS].sum()

    output = pd.DataFrame(index=sums.index)
    output.index.name = "KEY"

    # Carry text columns from the first matching source row per KEY.
    for column in TEXT_COLUMNS:
        output[column] = first_rows[column]

    # Carry summed numeric columns.
    for column in SUM_COLUMNS:
        output[column] = sums[column]

    # Derive YTG from the summed output rows, then apply the as-built quirk that
    # populates both Super Category and PPG from the source PPG column.
    output["YTG"] = compute_ytg(output)
    output["Super Category"] = first_rows["PPG"]
    output["PPG"] = first_rows["PPG"]

    output = output.reset_index()
    return output[TARGET_COLUMNS]


def validate_tieouts(
    source_df: pd.DataFrame,
    output_df: pd.DataFrame,
    tol: float = 1e-6,
) -> None:
    """Validate that the normalized output ties out to the source.

    Args:
        source_df: The validated source DataFrame (with rebuilt ``KEY``).
        output_df: The normalized output DataFrame.
        tol: Absolute tolerance for floating-point column tie-outs.

    Returns:
        ``None`` when every check passes.

    Raises:
        ValueError: When the output row count differs from the number of unique
            KEYs, when any month/``FY``/quarter column total differs between
            source and output beyond ``tol``, when any output row violates
            ``FY == sum(months)`` beyond ``tol``, or when any output row violates
            ``Qn == sum(its months)`` beyond ``tol``.
    """
    unique_keys = source_df["KEY"].nunique()
    if len(output_df) != unique_keys:
        raise ValueError(
            "Tie-out failure: output row count "
            f"{len(output_df)} != unique KEY count {unique_keys}."
        )

    # Each summed column must preserve its grand total from source to output.
    for column in SUM_COLUMNS:
        source_total = float(source_df[column].sum())
        output_total = float(output_df[column].sum())
        if abs(source_total - output_total) > tol:
            raise ValueError(
                f"Tie-out failure on column '{column}': source total "
                f"{source_total} != output total {output_total} (tol={tol})."
            )

    # Every output row's FY and each quarter must equal the sum of their months;
    # FY covers Jan..Dec and each quarter covers its three-month group. These
    # per-row checks confirm the load-time blank-total fill stayed consistent.
    per_row_checks = {"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS}
    for total_column, months in per_row_checks.items():
        offending = total_vs_months_violations(output_df, total_column, months, tol)
        if offending:
            raise ValueError(
                f"Tie-out failure: {total_column} != sum(months) for KEY(s) "
                f"{offending} (tol={tol})."
            )


def write_sqlite(df: pd.DataFrame, db_path: str, table_name: str) -> None:
    """Persist the normalized DataFrame to SQLite (SQLite write boundary).

    Drops and rewrites any existing table of the same name and does not persist
    the DataFrame index.

    Args:
        df: The normalized DataFrame to persist.
        db_path: Path to the SQLite database file.
        table_name: Destination table name (from the trusted ``--table-name``
            CLI argument; ``to_sql`` quotes the identifier).

    Returns:
        ``None``.

    Side effects:
        Opens a SQLite connection at ``db_path``, replaces ``table_name``, and
        closes the connection.
    """
    con = sqlite3.connect(db_path)
    try:
        # Route the write through the typed pandas_io boundary so the
        # SQLAlchemy-connectable unknown member type does not surface here.
        write_table(df, table_name, con, if_exists="replace", index=False)
    finally:
        con.close()


def print_summary(
    source_df: pd.DataFrame,
    output_df: pd.DataFrame,
) -> None:
    """Print a validation/tie-out summary to stdout for spot-checking.

    Args:
        source_df: The validated source DataFrame.
        output_df: The normalized output DataFrame.

    Returns:
        ``None``. Emits summary lines to stdout (this is CLI tool output, not
        library logging).
    """
    source_rows = len(source_df)
    unique_keys = int(source_df["KEY"].nunique())
    output_rows = len(output_df)

    print(f"Source rows: {source_rows}")
    print(f"Unique keys: {unique_keys}")
    print(f"Output rows: {output_rows}")

    # Report per-column source/output totals so a reviewer can confirm the
    # transform conserved every monthly, FY, and quarter measure.
    print("Tie-outs (source total -> output total):")
    for column in SUM_COLUMNS:
        source_total = float(source_df[column].sum())
        output_total = float(output_df[column].sum())
        print(f"  {column}: {source_total} -> {output_total}")

    # Show first/middle/last output rows as a lightweight spot-check sample.
    if output_rows:
        middle_index = output_rows // 2
        print("First output row:")
        print(output_df.iloc[0].to_dict())
        print("Middle output row:")
        print(output_df.iloc[middle_index].to_dict())
        print("Last output row:")
        print(output_df.iloc[-1].to_dict())


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the normalize-le CLI.

    Returns:
        A configured ``ArgumentParser`` with the positional input path and the
        ``--output`` (required), ``--source-sheet``, and ``--table-name``
        options.
    """
    parser = argparse.ArgumentParser(
        prog="normalize-le",
        description="Normalize an LE topline Excel sheet into a SQLite table.",
    )
    parser.add_argument("input", help="Path to the source .xlsx workbook.")
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the SQLite database file to write (required).",
    )
    parser.add_argument(
        "--source-sheet",
        default="LE-8 + 4",
        help='Source sheet name (default: "LE-8 + 4").',
    )
    parser.add_argument(
        "--table-name",
        default="LE",
        help='Destination SQLite table name (default: "LE").',
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
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: load, normalize, validate, persist, and summarize.

    Args:
        argv: Optional argument vector (excluding the program name). When
            ``None``, ``argparse`` reads from ``sys.argv``.

    Returns:
        ``0`` on success; ``1`` when a column-resolution, KEY-resolution, or
        tie-out ``ValueError`` is raised. A missing required ``--output`` causes
        ``argparse`` to raise ``SystemExit`` with a non-zero code.

    Side effects:
        Configures the stdlib ``logging`` module to emit WARNING-level messages
        to stderr for extra source columns and KEY resolution.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Configure logging once at the entry point so warnings (extra columns, KEY
    # resolution) reach stderr without library code touching global config.
    logging.basicConfig(level=logging.WARNING)

    # Map column-resolution, KEY-resolution, and tie-out failures to a non-zero
    # exit while letting the descriptive message reach the operator on stdout.
    try:
        source_df = load_source(
            args.input, args.source_sheet, key_mismatch=args.key_mismatch
        )
        output_df = normalize(source_df)
        validate_tieouts(source_df, output_df)
    except ValueError as error:
        print(f"ERROR: {error}")
        return 1

    write_sqlite(output_df, args.output, args.table_name)
    print_summary(source_df, output_df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
