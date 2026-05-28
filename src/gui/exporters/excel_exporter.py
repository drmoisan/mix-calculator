"""Excel exporter: writes one worksheet per selected table.

This module implements :class:`~src.gui.exporters.base.ExporterProtocol` for the
``"Excel"`` format. It writes each selected table as a worksheet in a single
``.xlsx`` workbook via the openpyxl engine, wrapping the pandas ``to_excel`` and
``ExcelWriter`` calls in the typed-boundary style of ``src/pandas_io.py`` (a
typed ``Protocol`` view plus ``typing.cast``) so the openpyxl-driven unknown
member types are contained here with no per-call type suppression.

Boundaries:
    - The only I/O is the workbook write at ``destination_path`` (or to an
      injected binary buffer in tests).
"""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, cast

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType
    from typing import Protocol

    # Accepted Excel write targets: a filesystem path or a binary buffer.
    ExcelTarget = str | IO[bytes]

    class _ExcelWriter(Protocol):
        """Typed view of the ``pandas.ExcelWriter`` context manager.

        Declares the context-manager protocol so the writer can be used in a
        ``with`` block without surfacing the unknown engine-typed members.
        """

        def __enter__(self) -> _ExcelWriter:
            """Enter the writer context, returning the writer."""
            ...

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            """Exit the writer context, finalizing the workbook."""
            ...

    class _FrameExcelWriter(Protocol):
        """Typed view of ``DataFrame.to_excel`` for the openpyxl engine.

        Declares the ``to_excel`` signature this module invokes with fully known
        parameter types so the bound-method access does not surface an unknown
        member type.
        """

        def to_excel(
            self,
            excel_writer: _ExcelWriter,
            *,
            sheet_name: str,
            index: bool,
        ) -> None:
            """Write the frame to a worksheet in the open writer."""
            ...

    # Typed callable view of the ``pandas.ExcelWriter`` factory. Using a callable
    # alias rather than a Protocol with a member named ``ExcelWriter`` avoids
    # the otherwise-required PascalCase method declaration (and the noqa: N802
    # suppression that would carry).
    _ExcelWriterFactory = Callable[..., _ExcelWriter]


__all__ = ["ExcelExporter"]

# Excel worksheet titles are capped at 31 characters by the format; longer table
# names are truncated to stay within the limit.
_MAX_SHEET_NAME = 31


class ExcelExporter:
    """Exporter that writes one worksheet per selected table to one workbook.

    Purpose:
        Implement the ``"Excel"`` export format for the GUI.

    Responsibilities:
        Write each selected table as a worksheet in a single ``.xlsx`` workbook.
        Table selection is decided by the presenter; this exporter only writes
        the names it is given.

    Usage:
        Registered in the ``ExporterRegistry`` under ``format_name == "Excel"``.
        ``export`` accepts a filesystem path or, in tests, a binary buffer.

    Key invariants:
        Only the names in ``selected_names`` are written, each as its own sheet;
        sheet names are truncated to the 31-character Excel limit.
    """

    @property
    def format_name(self) -> str:
        """Return the format identifier ``"Excel"``."""
        return "Excel"

    def export(
        self,
        tables: dict[str, pd.DataFrame],
        selected_names: list[str],
        destination_path: ExcelTarget,
    ) -> None:
        """Write each selected table to its own worksheet in one workbook.

        Args:
            tables: All available tables keyed by name.
            selected_names: The subset of table names to export.
            destination_path: The ``.xlsx`` path, or a binary buffer in tests.

        Returns:
            ``None``.

        Raises:
            KeyError: When a name in ``selected_names`` is absent from ``tables``.

        Side effects:
            Writes one ``.xlsx`` workbook to ``destination_path``.
        """
        # Cast pd.ExcelWriter to a typed callable view so the openpyxl engine's
        # unknown member types do not surface here. The callable alias accepts
        # any positional/keyword arguments, which keeps the ``engine`` keyword
        # typecheck-clean without declaring a PascalCase Protocol member.
        writer_factory = cast("_ExcelWriterFactory", pd.ExcelWriter)
        with writer_factory(destination_path, engine="openpyxl") as writer:
            # Write each selected table as its own worksheet, truncating the
            # sheet name to the Excel 31-character limit.
            for name in selected_names:
                frame = cast("_FrameExcelWriter", tables[name])
                frame.to_excel(writer, sheet_name=name[:_MAX_SHEET_NAME], index=False)
