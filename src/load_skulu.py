"""Load and clean the ``SKU_LU`` lookup sheet into a SQLite table.

This module is the SkuLu sibling of :mod:`src.load_aop`. It reads the ``SKU_LU``
sheet into a pandas DataFrame, resolves the documented schema
position-independently, renames ``International`` to ``Country``, casts the four
columns to text, maps the ``Country`` codes ``"0"`` -> ``"US"`` and ``"1"`` ->
``"Canada"``, and persists the result to SQLite.

Confidentiality:
    ``SKU Description`` and ``Category`` values are confidential and must never
    appear in fixtures, tests, or docs; only the schema column names appear in
    this module. The ``Country`` values ``"US"`` and ``"Canada"`` are not
    secret.

Boundaries:
    - ``load_skulu`` reads via ``src.pandas_io.read_excel_sheet`` (openpyxl).
    - ``persist_skulu`` writes via ``src.pandas_io.write_table`` (SQLite).
    - The rename, casts, and country mapping are pure transforms with no I/O.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import IO, TYPE_CHECKING

from src.etl_columns import resolve_columns
from src.pandas_io import read_excel_sheet, write_table

if TYPE_CHECKING:
    import pandas as pd

__all__ = [
    "EXPECTED_COLUMNS",
    "load_skulu",
    "persist_skulu",
]

logger = logging.getLogger(__name__)

# Accepted inputs for the Excel read boundary: a filesystem path or a binary
# file-like buffer (the in-memory test fixtures pass a BytesIO).
ExcelSource = str | IO[bytes]

# Source header for the SKU_LU sheet, in canonical order. ``International`` is
# renamed to ``Country`` after resolution. These are schema labels, not secrets.
EXPECTED_COLUMNS: list[str] = ["SKU", "SKU Description", "Category", "International"]

# Country code mapping applied after the rename: the source encodes country as a
# numeric code (rendered as text), which is mapped to the readable label. The
# US/Canada values are not confidential.
_COUNTRY_CODE_MAP: dict[str, str] = {"0": "US", "1": "Canada"}

# Columns cast to text after resolution and rename.
_TEXT_COLUMNS: list[str] = ["SKU", "SKU Description", "Category", "Country"]


def load_skulu(source: ExcelSource, *, sheet: str = "SKU_LU") -> pd.DataFrame:
    """Load, clean, and return the ``SKU_LU`` sheet as a DataFrame.

    Reads the sheet treating Excel row 1 as the header (``header=0``), resolves
    the source columns to the canonical names position-independently, renames
    ``International`` to ``Country``, casts the four columns to text, and maps the
    ``Country`` codes ``"0"`` -> ``"US"`` and ``"1"`` -> ``"Canada"``. Country
    codes outside the known map are left unchanged.

    Args:
        source: Filesystem path or binary file-like buffer accepted by
            ``read_excel_sheet`` (see :data:`ExcelSource`).
        sheet: Name of the worksheet to read (default ``"SKU_LU"``).

    Returns:
        A DataFrame with columns ``SKU``, ``SKU Description``, ``Category``, and
        ``Country``, all of text dtype, with the country codes mapped.

    Raises:
        ValueError: When a required column cannot be resolved (propagated from
            :func:`src.etl_columns.resolve_columns`).

    Side effects:
        Reads from the filesystem (or buffer) via openpyxl and emits a
        ``logging`` warning for any extra source columns.
    """
    # Route the read through the typed pandas_io boundary, which contains the
    # openpyxl-driven unknown member type so it does not surface here.
    frame: pd.DataFrame = read_excel_sheet(source, sheet_name=sheet, header=0)
    actual_columns = list(frame.columns.astype(str))

    # Resolve every required column position-independently; resolve_columns
    # raises naming any unmatched required column.
    mapping, extras = resolve_columns(actual_columns, EXPECTED_COLUMNS)
    if extras:
        logger.warning("Ignoring extra source column(s): %s.", extras)

    # Select and rename to canonical names so downstream logic is order-agnostic.
    selection = {mapping[expected]: expected for expected in EXPECTED_COLUMNS}
    columns_to_keep = [mapping[expected] for expected in EXPECTED_COLUMNS]
    frame = frame[columns_to_keep].rename(columns=selection).copy()

    # Rename International to Country, then cast each lookup column to text so the
    # SKU join key and the country-code mapping operate on strings.
    frame = frame.rename(columns={"International": "Country"})
    for column in _TEXT_COLUMNS:
        frame[column] = frame[column].astype(str)

    # Map the numeric country codes (now text) to readable labels; unknown codes
    # pass through unchanged.
    frame["Country"] = frame["Country"].replace(_COUNTRY_CODE_MAP)
    return frame


def persist_skulu(
    df: pd.DataFrame,
    db_path: str,
    table: str = "sku_lu",
    if_exists: str = "replace",
) -> None:
    """Persist the SKU lookup DataFrame to SQLite.

    Writes the frame through the typed ``write_table`` boundary without an index.

    Args:
        df: The cleaned SKU lookup DataFrame to persist.
        db_path: Path to the SQLite database file.
        table: Destination table name (default ``"sku_lu"``).
        if_exists: Behavior when the table exists (``"replace"``, ``"append"``,
            or ``"fail"``); forwarded unchanged to the write boundary.

    Returns:
        ``None``.

    Side effects:
        Opens a SQLite connection at ``db_path``, writes ``table``, commits, and
        closes the connection.
    """
    con = sqlite3.connect(db_path)
    try:
        # Route the write through the typed pandas_io boundary so the
        # SQLAlchemy-connectable unknown member type does not surface here.
        write_table(df, table, con, if_exists=if_exists, index=False)
        con.commit()
    finally:
        con.close()
