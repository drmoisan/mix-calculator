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
    from src.gui.protocols import PreviewSinkProtocol, SourceSelectionViewProtocol
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.gui.services.workbook_reader import WorkbookReaderProtocol

from src.gui.pipeline_service import ImportSpec as _ImportSpec

__all__ = ["SourceSelectionPresenter"]

logger = logging.getLogger(__name__)

# Default preview row cap, matching the spec preview bound.
_PREVIEW_MAX_ROWS = 200

# Rows read to extract the header for schema discovery (the first/header row).
_HEADER_PREVIEW_ROWS = 1


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
        _schema_service: Optional schema service used for import-schema discovery
            (WS2 / issue #48). When ``None``, schema discovery is unavailable and
            :meth:`on_schema_discovery` is a no-op.
    """

    def __init__(
        self,
        view: SourceSelectionViewProtocol,
        workbook_reader: WorkbookReaderProtocol,
        *,
        preview_sink: PreviewSinkProtocol | None = None,
        schema_service: SchemaServiceProtocol | None = None,
    ) -> None:
        """Initialize the presenter with its view, reader, and optional sinks.

        Args:
            view: The source-selection view to update.
            workbook_reader: The reader used to enumerate tabs and read previews.
            preview_sink: Optional second view that also receives preview rows
                via ``show_preview`` (per spec section 1 / research Q1 Option A:
                the composition root passes the shared ``PreviewWidget`` here so
                a render request renders into the main-window preview as well
                as into the per-input widget's no-op sink). Defaults to
                ``None`` (single-view behavior, the v1 contract).
            schema_service: Optional schema service used by
                :meth:`on_schema_discovery` to match a header preview against the
                registry (WS2). The composition root injects the production
                service; tests inject a fake. Defaults to ``None`` (discovery
                unavailable).
        """
        self._view = view
        self._reader = workbook_reader
        self._preview_sink = preview_sink
        self._schema_service = schema_service

    @property
    def preview_sink(self) -> PreviewSinkProtocol | None:
        """Return the wired preview sink (or ``None`` when not wired)."""
        return self._preview_sink

    @property
    def reader(self) -> WorkbookReaderProtocol:
        """Return the workbook reader the presenter was constructed with."""
        return self._reader

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
        # When a preview sink is wired (the composition root passes the main
        # window's shared PreviewWidget), forward the same rows so the shared
        # preview surface renders the request.
        if self._preview_sink is not None:
            self._preview_sink.show_preview(rows)

    def on_clear_preview(self) -> None:
        """Clear the preview on both the primary view and any wired sink.

        Spec section 1: when the user unchecks the Render Tab checkbox, the
        composition root invokes this path so the shared preview surface
        returns to an empty state.

        Returns:
            ``None``.

        Side effects:
            Calls ``show_preview([])`` on the primary view and, when set, on
            the preview sink.
        """
        self._view.show_preview([])
        if self._preview_sink is not None:
            self._preview_sink.show_preview([])

    def on_schema_discovery(self, path: str, sheet: str) -> None:
        """Auto-select a matching import schema for a source tab (WS2).

        Reads the header row of ``sheet``, matches it against the registry via
        the injected schema service, and applies the discovery decision:

        - ``action == "proceed"`` (a suitable match): select the matched schema
          name in the view's dropdown (AC-11).
        - ``action == "resolve"`` (no suitable match): leave the
          ``<Choose Schema>`` placeholder selected; do not auto-select (AC-12).

        A no-op when no schema service was injected or when the header preview is
        empty (no header to match).

        Args:
            path: The workbook path of the activated source tab.
            sheet: The worksheet name whose header is matched.

        Returns:
            ``None``.

        Side effects:
            May call ``view.set_selected_schema`` on a proceed decision; routes a
            reader ``ValueError`` to ``view.show_error``.
        """
        # Discovery is only available when a schema service was injected; without
        # one the per-tab dropdown stays at the placeholder.
        if self._schema_service is None:
            return
        logger.info("Schema discovery requested: %r on %r.", sheet, path)
        # Read just the header row; a reader ValueError is user-facing and shown
        # via the view, matching the on_render_tab/on_file_selected policy.
        try:
            rows = self._reader.read_sheet_preview(
                path, sheet, max_rows=_HEADER_PREVIEW_ROWS
            )
        except ValueError as error:
            logger.error("Failed to read header for %r on %r: %s", sheet, path, error)
            self._view.show_error(str(error))
            return
        # An empty preview carries no header to match, so leave the placeholder.
        if not rows:
            return
        headers = rows[0]
        # Import the discovery decision locally so the presenter module does not
        # depend on the wiring module at import time.
        from src.gui._schema_wiring import discover_schema

        decision = discover_schema(self._schema_service, headers)
        # Decision routing: a proceed selects the matched schema name; a resolve
        # leaves the <Choose Schema> placeholder so the user picks manually.
        if decision.action == "proceed" and decision.result.schema is not None:
            self._view.set_selected_schema(decision.result.schema.name)

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
