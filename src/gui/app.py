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
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QFileDialog

from src.gui.exporters.csv_exporter import CsvExporter
from src.gui.exporters.excel_exporter import ExcelExporter
from src.gui.exporters.registry import ExporterRegistry
from src.gui.main_window import MainWindow
from src.gui.pipeline_service import ImportSpec, PipelineService
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.gui.services.db_service import DbService
from src.gui.services.workbook_reader import WorkbookReader
from src.gui.widgets.export_dialog import ExportDialog

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "MainWindowPipelineView",
    "WiredApplication",
    "build_application",
    "default_export_runner",
    "default_open_chooser",
    "default_save_chooser",
    "main",
    "wire_control_signals",
]

# SQLite filter used by the Save/Open file dialogs so the chooser narrows the
# user's view to ``.db`` files (matching the pipeline's SQLite output format).
_SQLITE_FILTER = "SQLite Databases (*.db)"


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


def _current_import_spec(window: MainWindow) -> ImportSpec:
    """Read the user's per-input file/sheet selection from the main window.

    Args:
        window: The shell exposing the three source input widgets.

    Returns:
        An :class:`ImportSpec` populated from the live widget state.
    """
    # Read each widget's path/sheet directly so the spec always reflects the
    # current user selection at the moment the signal fires.
    return ImportSpec(
        le_path=window.le_widget.current_path(),
        le_sheet=window.le_widget.current_sheet(),
        aop_path=window.aop_widget.current_path(),
        aop_sheet=window.aop_widget.current_sheet(),
        skulu_path=window.skulu_widget.current_path(),
        skulu_sheet=window.skulu_widget.current_sheet(),
    )


def default_save_chooser() -> str | None:
    """Production save-path chooser backed by ``QFileDialog.getSaveFileName``.

    Returns:
        The chosen ``.db`` path, or ``None`` when the user cancels.
    """
    # QFileDialog returns (path, selected_filter); the filter element is not
    # used. An empty path indicates the user cancelled the dialog.
    path, _ = QFileDialog.getSaveFileName(None, "Save Database", "", _SQLITE_FILTER)
    return path or None


def default_open_chooser() -> str | None:
    """Production open-path chooser backed by ``QFileDialog.getOpenFileName``.

    Returns:
        The chosen ``.db`` path, or ``None`` when the user cancels.
    """
    # An empty path indicates the user cancelled the file dialog.
    path, _ = QFileDialog.getOpenFileName(None, "Open Database", "", _SQLITE_FILTER)
    return path or None


def default_export_runner(dialog: ExportDialog) -> tuple[str, str] | None:
    """Production export-dialog runner backed by ``dialog.exec`` + Save dialog.

    Shows the modal export dialog. On accept, reads the chosen format and asks
    the user for a destination path through ``QFileDialog.getSaveFileName``.
    Returns ``None`` when the user cancels either step.

    Args:
        dialog: The export dialog to show modally.

    Returns:
        A ``(format_name, destination_path)`` tuple on accept, or ``None``.
    """
    accepted = dialog.exec()
    # ``exec`` returns truthy on accept and falsy on reject; an explicit truthy
    # check avoids depending on the Qt-specific QDialog.DialogCode integer.
    if not accepted:
        return None
    format_name = dialog.selected_format()
    destination_path, _ = QFileDialog.getSaveFileName(
        dialog, "Export Destination", "", ""
    )
    if not destination_path:
        return None
    return format_name, destination_path


def wire_control_signals(
    window: MainWindow,
    pipeline_presenter: PipelinePresenter,
    export_presenter: ExportPresenter,
    export_dialog: ExportDialog,
    *,
    save_path_chooser: Callable[[], str | None],
    open_path_chooser: Callable[[], str | None],
    export_dialog_runner: Callable[[ExportDialog], tuple[str, str] | None],
) -> None:
    """Connect the six main-window control signals to their presenter handlers.

    The wiring is factored into this helper so tests can inject fake choosers
    and a fake export-dialog runner without monkeypatching ``QFileDialog``
    static methods.

    Args:
        window: The shell whose control signals are being wired.
        pipeline_presenter: Handler for import/run/save/open requests.
        export_presenter: Handler for the export request.
        export_dialog: The modal dialog driven for export.
        save_path_chooser: Returns the chosen ``.db`` path for Save, or
            ``None`` when the user cancels.
        open_path_chooser: Returns the chosen ``.db`` path for Open, or
            ``None`` when the user cancels.
        export_dialog_runner: Shows ``export_dialog`` and returns
            ``(format_name, destination_path)`` on accept, or ``None`` on
            cancel.

    Returns:
        ``None``.

    Side effects:
        Connects Qt signals on ``window`` to closures that route through the
        presenters.
    """

    def _handle_import_one(name: str) -> None:
        """Route a per-input import request through the pipeline presenter."""
        pipeline_presenter.on_import_one(name, _current_import_spec(window))

    def _handle_import_all() -> None:
        """Route the import-all request through the pipeline presenter."""
        pipeline_presenter.on_import_all(_current_import_spec(window))

    def _handle_run() -> None:
        """Route the run request through the pipeline presenter."""
        pipeline_presenter.on_run()

    def _handle_save() -> None:
        """Prompt for a destination path and route the save through the presenter.

        A cancelled file dialog (empty path) is a no-op; no save is attempted.
        """
        path = save_path_chooser()
        # Skip the presenter call when the user cancelled the file dialog so no
        # save is attempted against a missing destination.
        if not path:
            return
        pipeline_presenter.on_save(path)

    def _handle_open_db() -> None:
        """Prompt for a source path and route the open through the presenter.

        A cancelled file dialog (empty path) is a no-op; no open is attempted.
        """
        path = open_path_chooser()
        if not path:
            return
        pipeline_presenter.on_open_db(path)

    def _handle_export() -> None:
        """Drive the export dialog and route the result through the export presenter.

        Uses the derived tables when a run has completed; otherwise the
        imported tables (so an export after a bare import still works). A
        cancelled dialog (runner returns ``None``) is a no-op.
        """
        # Show the modal dialog (or its test fake) and read the chosen format
        # plus destination path. A None return means the user cancelled.
        result = export_dialog_runner(export_dialog)
        if result is None:
            return
        format_name, destination_path = result
        # Prefer the derived tables (they include the rollups) when a run has
        # completed; otherwise fall back to the imports so a save-after-import
        # path is still exportable.
        tables = (
            pipeline_presenter.derived_tables
            if pipeline_presenter.derived_tables
            else pipeline_presenter.imported_tables
        )
        export_presenter.set_available_tables(list(tables))
        export_presenter.on_export(tables, format_name, destination_path)

    # Connect each control-button signal to its handler closure. The closures
    # bind the presenters and choosers without exposing them on the window.
    window.import_one_requested.connect(_handle_import_one)
    window.import_all_requested.connect(_handle_import_all)
    window.run_requested.connect(_handle_run)
    window.save_requested.connect(_handle_save)
    window.open_db_requested.connect(_handle_open_db)
    window.export_requested.connect(_handle_export)


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

    # Wire the six main-window control signals to their presenter handlers,
    # using the production QFileDialog-backed choosers and the production
    # export-dialog runner. Tests build their own application without going
    # through build_application and inject fakes.
    wire_control_signals(
        window,
        pipeline_presenter,
        export_presenter,
        export_dialog,
        save_path_chooser=default_save_chooser,
        open_path_chooser=default_open_chooser,
        export_dialog_runner=default_export_runner,
    )

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
