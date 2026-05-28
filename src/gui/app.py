"""GUI bootstrap and composition root for the ``mix-pipeline-gui`` console script.

This module wires the real collaborators — :class:`WorkbookReader`,
:class:`PipelineService`, :class:`DbService`, an :class:`ExporterRegistry` with
:class:`ExcelExporter` and :class:`CsvExporter` registered — to the
:class:`MainWindow` and the three presenters, then runs the event loop.

The composition uses constructor injection only; no DI framework is involved.
The build is factored into :func:`build_application` so tests can construct the
wired collaborators without entering the blocking event loop, while
:func:`main` is the production entry point.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication

from src.gui.exporters.csv_exporter import CsvExporter
from src.gui.exporters.excel_exporter import ExcelExporter
from src.gui.exporters.registry import ExporterRegistry
from src.gui.main_window import MainWindow
from src.gui.pipeline_service import PipelineService
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.gui.services.db_service import DbService
from src.gui.services.workbook_reader import WorkbookReader
from src.gui.widgets.export_dialog import ExportDialog

__all__ = ["MainWindowPipelineView", "WiredApplication", "build_application", "main"]


@dataclass
class WiredApplication:
    """The fully-wired GUI components a composition step returns.

    Attributes:
        qt_app: The Qt application (``None`` when the caller supplies one).
        window: The main window.
        registry: The exporter registry holding Excel and CSV exporters.
        pipeline_service: The pipeline service seam.
        pipeline_presenter: The pipeline (import/run/save/open) presenter.
        export_presenter: The export presenter (bound to a fresh ExportDialog).
        export_dialog: The export dialog used by ``export_presenter``.
        le_presenter, aop_presenter, skulu_presenter: The per-input source
            selection presenters, one per input widget.
    """

    qt_app: QApplication | None
    window: MainWindow
    registry: ExporterRegistry
    pipeline_service: PipelineService
    pipeline_presenter: PipelinePresenter
    export_presenter: ExportPresenter
    export_dialog: ExportDialog
    le_presenter: SourceSelectionPresenter
    aop_presenter: SourceSelectionPresenter
    skulu_presenter: SourceSelectionPresenter


def _build_registry() -> ExporterRegistry:
    """Build the exporter registry with Excel and CSV exporters registered."""
    registry = ExporterRegistry()
    registry.register(ExcelExporter())
    registry.register(CsvExporter())
    return registry


def build_application(qt_app: QApplication | None = None) -> WiredApplication:
    """Construct and wire every collaborator without entering the event loop.

    Args:
        qt_app: An existing ``QApplication`` to reuse; when ``None`` a new one is
            constructed (tests typically pass the existing application managed
            by ``pytest-qt``).

    Returns:
        A :class:`WiredApplication` carrying the assembled components.

    Side effects:
        Constructs Qt widgets and the (Pyside6) ``QApplication`` if none is
        supplied. Does not show the window and does not enter ``exec``.
    """
    # Reuse the caller's QApplication when present (the production case
    # constructs one; tests reuse the pytest-qt managed one).
    application = qt_app

    # Real boundary services and the pipeline service seam.
    reader = WorkbookReader()
    db_service = DbService()
    pipeline_service = PipelineService(db_service=db_service)

    # Registry with the two concrete exporters.
    registry = _build_registry()

    # Build the shell and bind one source-selection presenter per input widget.
    window = MainWindow()
    le_presenter = SourceSelectionPresenter(window.le_widget, reader)
    aop_presenter = SourceSelectionPresenter(window.aop_widget, reader)
    skulu_presenter = SourceSelectionPresenter(window.skulu_widget, reader)

    # Wire the per-input file_selected and render_tab_requested signals to their
    # presenters so file selection populates the tab dropdown and render-tab
    # triggers a preview through the shared preview widget on the main window.
    window.le_widget.file_selected.connect(le_presenter.on_file_selected)
    window.aop_widget.file_selected.connect(aop_presenter.on_file_selected)
    window.skulu_widget.file_selected.connect(skulu_presenter.on_file_selected)
    window.le_widget.render_tab_requested.connect(le_presenter.on_render_tab)
    window.aop_widget.render_tab_requested.connect(aop_presenter.on_render_tab)
    window.skulu_widget.render_tab_requested.connect(skulu_presenter.on_render_tab)

    # Pipeline presenter over the main window (which satisfies the
    # PipelineViewProtocol surface via the status bar / dialogs).
    pipeline_presenter = PipelinePresenter(
        MainWindowPipelineView(window), pipeline_service
    )

    # Export dialog + presenter using the registry's formats.
    export_dialog = ExportDialog(registry.available_formats())
    export_presenter = ExportPresenter(export_dialog, registry)

    return WiredApplication(
        qt_app=application,
        window=window,
        registry=registry,
        pipeline_service=pipeline_service,
        pipeline_presenter=pipeline_presenter,
        export_presenter=export_presenter,
        export_dialog=export_dialog,
        le_presenter=le_presenter,
        aop_presenter=aop_presenter,
        skulu_presenter=skulu_presenter,
    )


class MainWindowPipelineView:
    """Thin adapter from :class:`MainWindow` to :class:`PipelineViewProtocol`.

    Purpose:
        Bridge the pipeline presenter's view contract onto the main window's
        status bar and result/error surfaces without modifying ``MainWindow``.

    Responsibilities:
        Implement ``set_running``/``show_result``/``show_error`` by routing to
        the main window's status bar.

    Attributes:
        _window: The wrapped main window.
    """

    def __init__(self, window: MainWindow) -> None:
        """Initialize the adapter with the main window it routes to."""
        self._window = window

    def set_running(self, is_running: bool) -> None:
        """Reflect the running flag in the main window's status bar."""
        self._window.set_status("Working..." if is_running else "")

    def show_result(self, summary: str) -> None:
        """Show a success summary in the main window's status bar."""
        self._window.set_status(summary)

    def show_error(self, message: str) -> None:
        """Show an error message in the main window's status bar."""
        self._window.set_status(f"Error: {message}")


def main(argv: list[str] | None = None) -> int:
    """Run the GUI: bootstrap Qt, build the wired components, show the window.

    Args:
        argv: Optional argument vector for ``QApplication`` (defaults to
            ``sys.argv``).

    Returns:
        The Qt event loop exit code.

    Side effects:
        Constructs a ``QApplication``, shows the main window, and runs the event
        loop until the user closes the window.
    """
    # Configure logging at the entry point so collaborator info/error messages
    # reach stderr.
    logging.basicConfig(level=logging.WARNING)
    args = argv if argv is not None else sys.argv
    qt_app = QApplication(args)
    wired = build_application(qt_app=qt_app)
    wired.window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
