"""SQLite read/write service for the mix-pipeline GUI (SQLite boundary).

This module provides the GUI's SQLite persistence seam used by
:class:`~src.gui.pipeline_service.PipelineService`. It writes every working
frame and reads the known tables back through the typed ``src.pandas_io``
boundary, so it carries no per-call type suppression and follows the same
typed-boundary style as ``src.pandas_io``.

Responsibilities:
    - ``save_tables`` writes each frame with ``if_exists="replace"`` on a single
      connection (equivalent to the CLI ``_persist_all``).
    - ``open_tables`` reads the tables present in a database back into frames.
    - ``list_tables`` enumerates the user tables on an open connection.

Boundaries:
    - All SQLite reads/writes route through ``src.pandas_io.read_table`` /
      ``write_table``. The connection lifecycle is owned here.

Usage:
    Constructed at the composition root and injected into the
    ``PipelineService``; tests exercise it directly with an in-memory connection.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from src.pandas_io import read_table, write_table

if TYPE_CHECKING:
    import pandas as pd

__all__ = ["DbService"]

logger = logging.getLogger(__name__)

# Query that lists user tables (excludes SQLite internal sqlite_* tables).
_LIST_TABLES_SQL = (
    "SELECT name FROM sqlite_master WHERE type='table' "
    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
)


class DbService:
    """SQLite read/write service over the typed pandas I/O boundary.

    Purpose:
        Persist the GUI's working tables to a SQLite database and load them back,
        matching the CLI output sink so databases interoperate between CLI and
        GUI.

    Responsibilities:
        Write each frame with replace semantics on one connection, enumerate the
        tables in a database, and read each table back into a frame. It owns the
        connection lifecycle; it holds no transform logic.

    Usage:
        Injected into ``PipelineService``. ``save_tables`` and ``open_tables``
        each open and close their own connection; ``list_tables`` operates on a
        caller-supplied open connection.

    Key invariants:
        ``save_tables`` replaces existing tables of the same name (matching
        ``_persist_all``); ``open_tables`` returns exactly the user tables found
        in the database, keyed by table name.
    """

    def save_tables(self, tables: dict[str, pd.DataFrame], db_path: str) -> None:
        """Persist every frame to ``db_path`` with replace semantics.

        Args:
            tables: Mapping of destination table name to the frame to persist.
            db_path: Path to the SQLite database file.

        Returns:
            ``None``.

        Side effects:
            Opens a connection at ``db_path``, writes each table with
            ``if_exists="replace"``, commits, and closes the connection.
        """
        logger.info("Persisting %d tables to %r.", len(tables), db_path)
        con = sqlite3.connect(db_path)
        try:
            # Walk the working tables and replace each on the database, matching
            # the CLI _persist_all behavior so a save overwrites prior contents.
            for name, frame in tables.items():
                write_table(frame, name, con, if_exists="replace", index=False)
            con.commit()
        finally:
            con.close()

    def list_tables(self, con: sqlite3.Connection) -> list[str]:
        """Return the user-table names on an open connection.

        Args:
            con: An open SQLite connection.

        Returns:
            The user-table names (SQLite internal tables excluded), sorted.

        Side effects:
            Executes a metadata query on the provided connection.
        """
        return [str(row[0]) for row in con.execute(_LIST_TABLES_SQL).fetchall()]

    def open_tables(self, db_path: str) -> dict[str, pd.DataFrame]:
        """Read every user table from ``db_path`` into frames.

        Args:
            db_path: Path to the SQLite database file.

        Returns:
            A dict keyed by table name of every user table in the database.

        Side effects:
            Opens a connection at ``db_path``, reads each table through the typed
            ``src.pandas_io`` boundary, and closes the connection.
        """
        logger.info("Loading tables from %r.", db_path)
        con = sqlite3.connect(db_path)
        try:
            names = self.list_tables(con)
            # Read each enumerated user table back through the typed boundary so
            # the in-memory set mirrors the persisted database exactly.
            return {name: read_table(con, name) for name in names}
        finally:
            con.close()
