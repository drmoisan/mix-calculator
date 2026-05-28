"""Presenter for per-input source selection, tab discovery, and preview.

This presenter holds the source-selection logic for one pipeline input (LE, AOP,
or SKU_LU). It depends on a :class:`SourceSelectionViewProtocol` and a
:class:`WorkbookReaderProtocol`, both injected via the constructor, and contains
no Qt import so it is fully testable without a ``QApplication``.

Responsibilities:
    - ``on_file_selected`` discovers the worksheet tabs and pushes them to the
      view.
    - ``on_render_tab`` reads a bounded preview and pushes it to the view.
    - ``build_import_spec`` assembles an :class:`ImportSpec` from the per-input
      file/sheet selections.

Loader/reader ``ValueError`` is surfaced via ``view.show_error``; other
exceptions propagate so genuine defects are not hidden.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.pipeline_service import ImportSpec
    from src.gui.protocols import SourceSelectionViewProtocol
    from src.gui.services.workbook_reader import WorkbookReaderProtocol

from src.gui.pipeline_service import ImportSpec as _ImportSpec

__all__ = ["SourceSelectionPresenter"]

logger = logging.getLogger(__name__)

# Default preview row cap, matching the spec preview bound.
_PREVIEW_MAX_ROWS = 200


class SourceSelectionPresenter:
    """Presenter coordinating one input's file/tab selection and preview.

    Purpose:
        Drive a passive source-selection view: discover tabs when a file is
        selected, render a bounded preview on request, and record the selection
        into an :class:`ImportSpec`.

    Responsibilities:
        Translate user actions into reader calls and view updates. It holds no Qt
        code and no transform logic; the workbook reader owns Excel I/O.

    Usage:
        Constructed with a view and a workbook reader at the composition root;
        the widget wires its signals to the presenter's methods.

    Attributes:
        _view: The source-selection view this presenter updates.
        _reader: The workbook reader used for tab discovery and preview.
    """

    def __init__(
        self,
        view: SourceSelectionViewProtocol,
        workbook_reader: WorkbookReaderProtocol,
    ) -> None:
        """Initialize the presenter with its view and workbook reader.

        Args:
            view: The source-selection view to update.
            workbook_reader: The reader used to enumerate tabs and read previews.
        """
        self._view = view
        self._reader = workbook_reader

    def on_file_selected(self, path: str) -> None:
        """Discover the workbook's tabs and push them to the view.

        Args:
            path: The selected workbook path.

        Returns:
            ``None``.

        Side effects:
            Calls the reader and updates the view's tab list, or routes a
            ``ValueError`` to ``view.show_error``.
        """
        logger.info("File selected: %r.", path)
        # A reader ValueError (for example an unreadable/invalid workbook) is a
        # user-facing condition surfaced via the view, not a crash; other
        # exceptions propagate so genuine defects are not masked.
        try:
            tabs = self._reader.get_sheet_names(path)
        except ValueError as error:
            logger.error("Failed to read sheet names from %r: %s", path, error)
            self._view.show_error(str(error))
            return
        self._view.set_tab_list(tabs)

    def on_render_tab(self, path: str, sheet: str) -> None:
        """Read a bounded preview of one tab and push it to the view.

        Args:
            path: The workbook path.
            sheet: The worksheet name to preview.

        Returns:
            ``None``.

        Side effects:
            Calls the reader and updates the view's preview, or routes a
            ``ValueError`` to ``view.show_error``.
        """
        logger.info("Render tab requested: %r on %r.", sheet, path)
        # Same error policy as on_file_selected: a reader ValueError is shown to
        # the user; other exceptions propagate.
        try:
            rows = self._reader.read_sheet_preview(
                path, sheet, max_rows=_PREVIEW_MAX_ROWS
            )
        except ValueError as error:
            logger.error("Failed to preview %r on %r: %s", sheet, path, error)
            self._view.show_error(str(error))
            return
        self._view.show_preview(rows)

    def build_import_spec(
        self,
        *,
        le_path: str,
        le_sheet: str,
        aop_path: str,
        aop_sheet: str,
        skulu_path: str,
        skulu_sheet: str,
    ) -> ImportSpec:
        """Assemble an :class:`ImportSpec` from the per-input selections.

        Args:
            le_path: LE workbook path.
            le_sheet: LE worksheet name.
            aop_path: AOP workbook path.
            aop_sheet: AOP worksheet name.
            skulu_path: SKU_LU workbook path (may be empty for the LE default).
            skulu_sheet: SKU_LU worksheet name.

        Returns:
            A frozen :class:`ImportSpec` carrying the selections.
        """
        return _ImportSpec(
            le_path=le_path,
            le_sheet=le_sheet,
            aop_path=aop_path,
            aop_sheet=aop_sheet,
            skulu_path=skulu_path,
            skulu_sheet=skulu_sheet,
        )
