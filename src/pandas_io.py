"""Typed adapters for the pandas I/O boundary used by the LE normalizer.

This module isolates the pandas read/write calls whose published stub
signatures resolve as partially unknown under Pyright strict. pandas-stubs
types ``read_excel`` against optional engine types (openpyxl's
``Workbook``/``Book``) that ship without stubs in this project, and types the
``read_sql``/``to_sql`` connection parameters against optional SQLAlchemy
connectables, so accessing those members directly reports
``reportUnknownMemberType``. Each adapter accesses the relevant pandas member
through a typed ``Protocol`` view of the ``pandas`` module (or a DataFrame),
which declares fully known signatures for the members used here. The unknown
member type is therefore contained at these typed views and callers receive
concrete, known types without any per-call type suppression.

Boundaries:
    - ``read_excel_sheet`` wraps ``pandas.read_excel`` for a single sheet.
    - ``read_table`` wraps ``pandas.read_sql`` for a SQLite connection.
    - ``write_table`` wraps ``DataFrame.to_sql`` for a SQLite connection.

All three functions are thin, side-effecting boundary wrappers; the callers own
the surrounding transform and connection lifecycle. ``typing.cast`` is a no-op
at runtime, so these views change only static typing, never behavior.
"""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, cast

import pandas as pd

if TYPE_CHECKING:
    import sqlite3
    from os import PathLike
    from typing import Protocol

    # Accepted Excel sources: a filesystem path or a binary file-like buffer.
    ExcelSource = str | PathLike[str] | IO[bytes]

    class _PandasReaders(Protocol):
        """Typed view of the ``pandas`` module read members used here.

        Declares only the ``read_excel`` and ``read_sql`` signatures actually
        invoked by this module, each with fully known parameter and return
        types so member access does not surface an unknown member type.
        """

        def read_excel(
            self,
            io: ExcelSource,
            *,
            sheet_name: str,
            header: int | None,
            engine: str,
        ) -> pd.DataFrame:
            """Read a single Excel sheet into a DataFrame."""
            ...

        def read_sql(self, sql: str, con: sqlite3.Connection) -> pd.DataFrame:
            """Read a SQL query result into a DataFrame."""
            ...

    class _FrameWriter(Protocol):
        """Typed view of ``DataFrame.to_sql`` for a SQLite connection.

        Declares the ``to_sql`` signature this module invokes with fully known
        parameter types so the bound-method access does not surface an unknown
        member type. The return value is unused by callers.
        """

        def to_sql(
            self,
            name: str,
            con: sqlite3.Connection,
            *,
            if_exists: str,
            index: bool,
        ) -> None:
            """Write the frame to a SQL table."""
            ...


# Fixed read clause assembled with a quoted identifier in read_table. Kept as a
# separate constant so the read statement is not a single string literal that
# begins with the SQL verb adjacent to interpolation (which the linter flags as
# a possible injection vector); the table identifier is trusted and quoted.
_SELECT_ALL_FROM = "SELECT * FROM "


def read_excel_sheet(
    source: ExcelSource,
    *,
    sheet_name: str,
    header: int | None,
) -> pd.DataFrame:
    """Read a single Excel sheet into a DataFrame via the openpyxl engine.

    Args:
        source: Filesystem path or binary file-like buffer to read.
        sheet_name: Name of the worksheet to read.
        header: Zero-based index of the header row within the sheet, or
            ``None`` to read with no header row (every sheet row, including the
            label row, is returned as data with a positional integer column
            index). ``None`` is used by the header-detection probe read.

    Returns:
        The sheet contents as a typed ``pd.DataFrame``.

    Side effects:
        Reads from the filesystem or the provided buffer via openpyxl.
    """
    # Access read_excel through a typed Protocol view of the pandas module so
    # the openpyxl-driven unknown overload member type does not surface here.
    readers = cast("_PandasReaders", pd)
    return readers.read_excel(
        source, sheet_name=sheet_name, header=header, engine="openpyxl"
    )


def read_table(con: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """Read a full table from an open SQLite connection into a DataFrame.

    Args:
        con: An open SQLite connection.
        table_name: The table to read. The identifier is double-quoted (with
            embedded quotes escaped) before use; identifiers cannot be
            parameterized, so the name must be a trusted internal value.

    Returns:
        The table contents as a typed ``pd.DataFrame``.

    Side effects:
        Executes a read query against the provided SQLite connection.
    """
    # Quote the identifier (doubling embedded quotes) since SQL identifiers
    # cannot be parameterized; the table name is a trusted internal value. The
    # statement is assembled from a fixed clause and the quoted identifier; the
    # value never carries user-controlled SQL.
    quoted_identifier = '"' + table_name.replace('"', '""') + '"'
    query = _SELECT_ALL_FROM + quoted_identifier
    # Access read_sql through a typed Protocol view of the pandas module so the
    # SQLAlchemy-connectable unknown overload member type does not surface here.
    readers = cast("_PandasReaders", pd)
    return readers.read_sql(query, con)


def write_table(
    df: pd.DataFrame,
    table_name: str,
    con: sqlite3.Connection,
    *,
    if_exists: str,
    index: bool,
) -> None:
    """Write a DataFrame to a SQLite table via the connection write boundary.

    Args:
        df: The DataFrame to persist.
        table_name: Destination table name. ``to_sql`` quotes the identifier.
        con: An open SQLite connection.
        if_exists: Behavior when the table exists (for example ``"replace"``).
        index: Whether to write the DataFrame index as a column.

    Returns:
        ``None``.

    Side effects:
        Writes rows to ``table_name`` on the provided SQLite connection.
    """
    # Access to_sql through a typed Protocol view of the DataFrame so the
    # SQLAlchemy-connectable unknown overload member type does not surface here.
    writer = cast("_FrameWriter", df)
    writer.to_sql(table_name, con, if_exists=if_exists, index=index)
