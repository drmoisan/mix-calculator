"""CSV exporter: writes one CSV file per selected table into a directory.

This module implements :class:`~src.gui.exporters.base.ExporterProtocol` for the
``"CSV"`` format. It writes each selected table to ``<destination>/<name>.csv``
via pandas ``to_csv``, wrapping the call in the typed-boundary style of
``src/pandas_io.py`` (a typed ``Protocol`` view plus ``typing.cast``).

To keep the exporter testable without runtime temp files, the per-table text
sink is obtained through an injected ``open_writer`` callable that defaults to
opening a real file. Tests inject a ``StringIO``-backed callable so no file is
created on disk.

Boundaries:
    - The only I/O is obtaining and writing the per-table text sink, which is
      fully behind the injected ``open_writer`` seam.
"""

from __future__ import annotations

import os
from typing import IO, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Protocol

    import pandas as pd

    # A callable that returns a writable text sink for a given destination path.
    OpenWriter = Callable[[str], IO[str]]

    class _FrameCsvWriter(Protocol):
        """Typed view of ``DataFrame.to_csv`` writing to a text buffer.

        Declares the ``to_csv`` signature this module invokes with fully known
        parameter types so the bound-method access does not surface an unknown
        member type.
        """

        def to_csv(self, buf: IO[str], *, index: bool) -> None:
            """Write the frame as CSV to the given text buffer."""
            ...


__all__ = ["CsvExporter"]


def _default_open_writer(path: str) -> IO[str]:
    """Open a real UTF-8 text file for writing (the production sink).

    Args:
        path: The CSV file path to open.

    Returns:
        An open writable text file object.

    Side effects:
        Creates or truncates the file at ``path``.
    """
    return open(path, "w", encoding="utf-8", newline="")


class CsvExporter:
    """Exporter that writes one CSV file per selected table into a directory.

    Purpose:
        Implement the ``"CSV"`` export format for the GUI.

    Responsibilities:
        Write each selected table as ``<destination>/<name>.csv``. Table
        selection is decided by the presenter; this exporter writes only the
        names it is given.

    Usage:
        Registered in the ``ExporterRegistry`` under ``format_name == "CSV"``.
        The per-table text sink is obtained via the injected ``open_writer``
        callable, which defaults to opening a real file; tests inject an
        in-memory sink so no temp files are created.

    Attributes:
        _open_writer: The injected callable that returns a writable text sink for
            a CSV path.
    """

    def __init__(self, open_writer: OpenWriter | None = None) -> None:
        """Initialize the exporter with an optional text-sink factory.

        Args:
            open_writer: Callable returning a writable text sink for a path. When
                ``None``, a real-file opener is used (the production sink).
        """
        # Default to the real-file opener so production needs no extra wiring.
        self._open_writer: OpenWriter = (
            open_writer if open_writer is not None else _default_open_writer
        )

    @property
    def format_name(self) -> str:
        """Return the format identifier ``"CSV"``."""
        return "CSV"

    def export(
        self,
        tables: dict[str, pd.DataFrame],
        selected_names: list[str],
        destination_path: str,
    ) -> None:
        """Write each selected table to its own CSV using the name-mangling rule.

        Per v2 Decision 1 / spec section 7: ``destination_path`` is interpreted
        as a single CSV file path the user selected from the Save dialog. The
        exporter strips a trailing ``.csv`` (case-insensitive) to compute the
        base name, then writes one file per selected table as
        ``<directory>/<base>_<table>.csv``.

        Args:
            tables: All available tables keyed by name.
            selected_names: The subset of table names to export. An empty
                selection produces no output (the caller is responsible for
                empty-selection guards).
            destination_path: The CSV file path the user selected. The base
                name (filename minus a trailing ``.csv``) is used as the
                per-table file's prefix.

        Returns:
            ``None``.

        Raises:
            KeyError: When a name in ``selected_names`` is absent from ``tables``.

        Side effects:
            Writes one CSV per selected table via the injected ``open_writer``.
        """
        # Decompose the destination path into directory + base. The base is the
        # filename portion with a trailing ".csv" (case-insensitive) stripped;
        # an empty directory means the current working directory.
        directory = os.path.dirname(destination_path)
        filename = os.path.basename(destination_path)
        if filename.lower().endswith(".csv"):
            base = filename[: -len(".csv")]
        else:
            base = filename
        # Write each selected table to <directory>/<base>_<table>.csv via the
        # injected text-sink seam so tests can capture output without files.
        for name in selected_names:
            target_name = f"{base}_{name}.csv"
            csv_path = (
                os.path.join(directory, target_name) if directory else target_name
            )
            frame = cast("_FrameCsvWriter", tables[name])
            with self._open_writer(csv_path) as sink:
                frame.to_csv(sink, index=False)
