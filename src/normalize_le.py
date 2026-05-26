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
import math
import sqlite3
from typing import IO, TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Sequence

# Accepted inputs for the Excel read boundary: a filesystem path or a binary
# file-like buffer (the in-memory test fixtures pass a BytesIO).
ExcelSource = str | IO[bytes]

# Month columns in calendar order (source columns H..S).
MONTH_COLUMNS: list[str] = list[str](
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
)

# Months contributing to the derived YTG measure (May..Dec under the 8+4 rule).
YTG_MONTHS: list[str] = MONTH_COLUMNS[4:]

# Quarter columns (source columns U..X).
QUARTER_COLUMNS: list[str] = ["Q1", "Q2", "Q3", "Q4"]

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


def coerce_sku(val: object) -> str:
    """Render a SKU value the way the source Excel key formula does.

    Excel concatenates the SKU into the KEY without decimal noise: whole-number
    SKUs render as plain integer strings and non-numeric codes are preserved
    verbatim. openpyxl may return an ``int``, a ``float`` (whole or fractional),
    a ``numpy`` scalar, ``NaN`` for an empty cell, or a string code.

    Args:
        val: The raw SKU cell value loaded from the workbook. May be an ``int``,
            ``float``, ``numpy`` integer/float, ``NaN``, ``None``, or ``str``.

    Returns:
        The SKU rendered as a string. ``NaN``/``None`` render as the empty
        string; integral numeric values render with no decimal point; other
        floats render via ``str``; any other value renders via ``str``.
    """
    # Empty cells arrive as None; the Excel formula yields an empty segment.
    if val is None:
        return ""

    # Normalize numpy scalars to their Python equivalents up front so the
    # remaining branches operate only on built-in int/float/str types. The
    # numpy ``.item()`` accessor returns a concrete Python scalar.
    if isinstance(val, np.integer):
        val = int(val.item())
    elif isinstance(val, np.floating):
        val = float(val.item())

    # bool is a subclass of int; treat it as a generic value, not a number.
    if isinstance(val, bool):
        return str(val)

    # Branch ordering matters: integer-typed values render directly, while
    # float values render as an integer only when they have no fractional part
    # (mirroring how Excel concatenates a whole number without a decimal).
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if math.isnan(val):
            return ""
        if val.is_integer():
            return str(int(val))
        return str(val)

    # Non-numeric codes (e.g. "RGFBOWLCB") are preserved exactly as supplied.
    return str(val)


def rebuild_key(customer: str, sku: object, type_: str) -> str:
    """Rebuild the business KEY from its component fields.

    The source workbook stores ``KEY`` as the Excel formula ``=C&E&F``
    (``Customer & SKU # & Type``) with no separator. openpyxl may return the
    formula text, a stale cached value, or ``None``, so the key is always
    rebuilt from components rather than trusting the loaded cell.

    Args:
        customer: The ``Customer`` text segment.
        sku: The raw ``SKU #`` value; rendered via :func:`coerce_sku`.
        type_: The ``Type`` text segment.

    Returns:
        The concatenation ``customer + coerce_sku(sku) + type_`` with no
        separator between segments.
    """
    return f"{customer}{coerce_sku(sku)}{type_}"


def validate_schema(columns: Sequence[str]) -> None:
    """Validate that the loaded source columns match the expected contract.

    Args:
        columns: The column labels read from the source sheet, in order.

    Returns:
        ``None`` when the columns equal :data:`SOURCE_COLUMNS` exactly (same
        names and same order).

    Raises:
        ValueError: When the columns do not match exactly. The message names
            missing columns, extra columns, and (when names match but order
            does not) reports the order mismatch.
    """
    actual = list(columns)
    if actual == SOURCE_COLUMNS:
        return

    expected_set = set(SOURCE_COLUMNS)
    actual_set = set(actual)
    missing = [c for c in SOURCE_COLUMNS if c not in actual_set]
    extra = [c for c in actual if c not in expected_set]

    # Distinguish a name mismatch (missing/extra) from a pure ordering problem:
    # when the same names are present but the sequence differs, report order.
    if missing or extra:
        raise ValueError(
            "Source schema mismatch. "
            f"Missing columns: {missing}. Extra columns: {extra}. "
            f"Expected order: {SOURCE_COLUMNS}."
        )
    raise ValueError(
        "Source schema column order mismatch. "
        f"Got: {actual}. Expected: {SOURCE_COLUMNS}."
    )


def load_source(path: ExcelSource, sheet_name: str) -> pd.DataFrame:
    """Load and clean the source sheet (Excel read boundary).

    Reads the workbook with openpyxl treating Excel row 3 as the header
    (``header=2``), validates the column contract, drops rows with a blank
    ``Customer``, and rebuilds the ``KEY`` column from components so a loaded or
    cached key value is never trusted.

    Args:
        path: Filesystem path or binary file-like buffer accepted by
            ``pd.read_excel`` (see :data:`ExcelSource`).
        sheet_name: Name of the sheet to read (for example ``"LE-8 + 4"``).

    Returns:
        A DataFrame with the validated source columns, blank-``Customer`` rows
        removed, and a freshly rebuilt ``KEY`` column.

    Raises:
        ValueError: When the source schema does not match the contract
            (propagated from :func:`validate_schema`).

    Side effects:
        Reads from the filesystem (or the provided buffer) via openpyxl.
    """
    # pandas-stubs types read_excel's overload against openpyxl Workbook/Book
    # types, but openpyxl ships no stubs, so the overload member resolves as
    # partially unknown under Pyright strict. The result is explicitly typed as
    # pd.DataFrame; the ignore is scoped to this single boundary call.
    frame: pd.DataFrame = pd.read_excel(  # pyright: ignore[reportUnknownMemberType]
        path, sheet_name=sheet_name, header=2, engine="openpyxl"
    )
    validate_schema(list(frame.columns.astype(str)))

    # Drop trailing/interspersed rows with no Customer; these are blank padding
    # rows in the source sheet that carry no business data.
    customer_blank = frame["Customer"].isna() | (
        frame["Customer"].astype(str).str.strip() == ""
    )
    frame = frame.loc[~customer_blank].copy()

    # Always rebuild KEY from components; the loaded cell may hold the formula
    # text, a stale cached value, or None.
    frame["KEY"] = [
        rebuild_key(str(customer), sku, str(type_))
        for customer, sku, type_ in zip(
            frame["Customer"], frame["SKU #"], frame["Type"], strict=True
        )
    ]
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
            source and output beyond ``tol``, or when any output row violates
            ``FY == sum(months)`` beyond ``tol``.
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

    # Every output row's FY must equal the sum of its monthly columns.
    month_sums = output_df[MONTH_COLUMNS].sum(axis=1)
    fy_diff = (output_df["FY"] - month_sums).abs()
    if bool((fy_diff > tol).any()):
        offending = output_df.loc[fy_diff > tol, "KEY"].tolist()
        raise ValueError(
            "Tie-out failure: FY != sum(months) for KEY(s) " f"{offending} (tol={tol})."
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
        # pandas-stubs types to_sql's con parameter against a union that
        # includes an unstubbed connection type, so the member resolves as
        # partially unknown under Pyright strict. sqlite3.Connection is a valid
        # runtime argument; the ignore is scoped to this single boundary call.
        df.to_sql(  # pyright: ignore[reportUnknownMemberType]
            table_name, con, if_exists="replace", index=False
        )
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
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: load, normalize, validate, persist, and summarize.

    Args:
        argv: Optional argument vector (excluding the program name). When
            ``None``, ``argparse`` reads from ``sys.argv``.

    Returns:
        ``0`` on success; ``1`` when a schema or tie-out ``ValueError`` is
        raised. A missing required ``--output`` causes ``argparse`` to raise
        ``SystemExit`` with a non-zero code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Map schema/tie-out validation failures to a non-zero exit while letting
    # the descriptive message reach stderr for the operator.
    try:
        source_df = load_source(args.input, args.source_sheet)
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
