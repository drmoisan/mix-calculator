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

from PySide6.QtWidgets import QApplication

from src.gui._wiring import (
    default_export_runner,
    default_open_chooser,
    default_save_chooser,
)
from src.gui.exporters.csv_exporter import CsvExporter
from src.gui.exporters.excel_exporter import ExcelExporter
from src.gui.exporters.registry import ExporterRegistry
from src.gui.main_window import MainWindow
from src.gui.pipeline_service import ImportSpec, PipelineService
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.gui.runners import RunnerProtocol, ThreadedRunner
from src.gui.services.db_service import DbService
from src.gui.services.workbook_reader import WorkbookReader
from src.gui.widgets.export_dialog import ExportDialog

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui.pipeline_service import PipelineServiceProtocol
    from src.gui.services.workbook_reader import WorkbookReaderProtocol

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


@dataclass
class WiredApplication:
    """The fully-wired GUI components a composition step returns.

    Attributes:
        qt_app: The Qt application (``None`` when the caller supplies one).
        window: The main window.
        registry: The exporter registry holding Excel and CSV exporters. When
            :func:`build_application` is called with an ``exporter_registry``
            keyword, this attribute holds the injected instance instead so
            tests can substitute in-memory or recording exporters.
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
    pipeline_service: PipelineServiceProtocol
    pipeline_presenter: PipelinePresenter
    export_presenter: ExportPresenter
    export_dialog: ExportDialog
    le_presenter: SourceSelectionPresenter
    aop_presenter: SourceSelectionPresenter
    skulu_presenter: SourceSelectionPresenter
    runner: RunnerProtocol


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


def wire_control_signals(
    window: MainWindow,
    pipeline_presenter: PipelinePresenter,
    export_presenter: ExportPresenter,
    export_dialog: ExportDialog,
    *,
    save_path_chooser: Callable[[], str | None],
    open_path_chooser: Callable[[], str | None],
    export_dialog_runner: Callable[[ExportDialog], tuple[str, str] | None],
    runner: RunnerProtocol,
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
        """Dispatch the run task through the injected runner.

        Per spec section 4 / research Q6: the run task is built by the
        presenter and dispatched off the UI thread by the runner; the runner
        routes success/error back to the presenter callbacks.
        """
        if not pipeline_presenter.can_run():
            pipeline_presenter.on_run()
            return
        task = pipeline_presenter.make_run_task()
        runner.run(
            task,
            pipeline_presenter.on_run_success,
            pipeline_presenter.on_run_error,
        )

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

        Uses the working tables (derived after a Run, else imported) so an
        export after a bare import still works. Per v2 Defect 1 fix: the
        checklist is populated BEFORE the dialog runs so the user sees the
        right table set.
        """
        # Defect 1 fix: populate the checklist before the dialog runs.
        tables = pipeline_presenter.working_tables
        export_presenter.set_available_tables(list(tables))
        # Show the modal dialog (or its test fake) and read the format plus
        # destination path. A None return means the user cancelled.
        result = export_dialog_runner(export_dialog)
        if result is None:
            return
        format_name, destination_path = result
        export_presenter.on_export(tables, format_name, destination_path)

    # Connect each control-button signal to its handler closure. The closures
    # bind the presenters and choosers without exposing them on the window.
    window.import_one_requested.connect(_handle_import_one)
    window.import_all_requested.connect(_handle_import_all)
    window.run_requested.connect(_handle_run)
    window.save_requested.connect(_handle_save)
    window.open_db_requested.connect(_handle_open_db)
    window.export_requested.connect(_handle_export)


def build_application(
    qt_app: QApplication | None = None,
    *,
    runner: RunnerProtocol | None = None,
    save_path_chooser: Callable[[], str | None] | None = None,
    open_path_chooser: Callable[[], str | None] | None = None,
    export_dialog_runner: (
        Callable[[ExportDialog], tuple[str, str] | None] | None
    ) = None,
    pipeline_service: PipelineServiceProtocol | None = None,
    workbook_reader: WorkbookReaderProtocol | None = None,
    exporter_registry: ExporterRegistry | None = None,
) -> WiredApplication:
    """Construct and wire every collaborator without entering the event loop.

    Args:
        qt_app: An existing ``QApplication`` to reuse; when ``None`` a new one
            is constructed (tests typically pass the existing application
            managed by ``pytest-qt``).
        runner: Optional :class:`RunnerProtocol`. Defaults to
            :class:`ThreadedRunner` so the production GUI dispatches off the
            UI thread; tests inject a :class:`SynchronousRunner` to make Run
            deterministic.
        save_path_chooser: Optional Save-path chooser. Defaults to the
            production ``QFileDialog``-backed chooser.
        open_path_chooser: Optional Open-path chooser. Defaults to the
            production ``QFileDialog``-backed chooser.
        export_dialog_runner: Optional export-dialog runner. Defaults to
            :func:`default_export_runner` (ExportDialog + Save dialog filter).
        pipeline_service: Optional service seam. Defaults to the production
            :class:`PipelineService` over :class:`DbService`.
        workbook_reader: Optional workbook reader. Defaults to the production
            :class:`WorkbookReader`.
        exporter_registry: Optional :class:`ExporterRegistry`; defaults to
            :func:`_build_registry`. Composition-root test seam so behavioral
            tests can inject a registry whose ``"CSV"`` entry captures writes
            in-memory; production ``main`` does not pass this keyword.

    Returns:
        A :class:`WiredApplication` carrying the assembled components.

    Side effects:
        Constructs Qt widgets and the (Pyside6) ``QApplication`` if none is
        supplied. Does not show the window and does not enter ``exec``.
    """
    application = qt_app
    reader: WorkbookReaderProtocol = (
        workbook_reader if workbook_reader is not None else WorkbookReader()
    )
    pipeline_service_resolved: PipelineServiceProtocol = (
        pipeline_service
        if pipeline_service is not None
        else PipelineService(db_service=DbService())
    )
    runner_resolved: RunnerProtocol = runner if runner is not None else ThreadedRunner()
    # Use the injected registry when supplied (test seam) else build production.
    registry = exporter_registry if exporter_registry is not None else _build_registry()

    # Build the shell and bind one source-selection presenter per input widget;
    # pass the shared preview widget as the preview sink (research Q1 Option A)
    # so each render request renders into the main-window preview.
    window = MainWindow()
    le_presenter = SourceSelectionPresenter(
        window.le_widget, reader, preview_sink=window.preview_widget
    )
    aop_presenter = SourceSelectionPresenter(
        window.aop_widget, reader, preview_sink=window.preview_widget
    )
    skulu_presenter = SourceSelectionPresenter(
        window.skulu_widget, reader, preview_sink=window.preview_widget
    )

    # Wire the per-input file_selected and render_tab_requested signals to
    # their presenters so file selection populates the tab dropdown and
    # render-tab triggers a preview through the shared preview widget.
    window.le_widget.file_selected.connect(le_presenter.on_file_selected)
    window.aop_widget.file_selected.connect(aop_presenter.on_file_selected)
    window.skulu_widget.file_selected.connect(skulu_presenter.on_file_selected)
    window.le_widget.render_tab_requested.connect(le_presenter.on_render_tab)
    window.aop_widget.render_tab_requested.connect(aop_presenter.on_render_tab)
    window.skulu_widget.render_tab_requested.connect(skulu_presenter.on_render_tab)

    # Pipeline presenter over the main window (which satisfies the
    # PipelineViewProtocol surface via the status bar / dialogs).
    pipeline_presenter = PipelinePresenter(
        MainWindowPipelineView(window), pipeline_service_resolved
    )

    # v2 (AC-2/3/4): file selection on each widget reports the new path to
    # the pipeline presenter so the import button re-enables on a fresh pick.
    def _le_path_changed(path: str) -> None:
        pipeline_presenter.on_file_path_changed("LE", path)

    def _aop_path_changed(path: str) -> None:
        pipeline_presenter.on_file_path_changed("aop", path)

    def _skulu_path_changed(path: str) -> None:
        pipeline_presenter.on_file_path_changed("sku_lu", path)

    window.le_widget.file_selected.connect(_le_path_changed)
    window.aop_widget.file_selected.connect(_aop_path_changed)
    window.skulu_widget.file_selected.connect(_skulu_path_changed)

    # v2 (AC-1 preview-clear path): unchecking the Render Tab checkbox on any
    # input clears the shared preview surface.
    def _make_preview_clear(
        checkbox_owner: SourceSelectionPresenter,
    ) -> Callable[[bool], None]:
        def _on_toggled(checked: bool) -> None:
            if not checked:
                checkbox_owner.on_clear_preview()

        return _on_toggled

    window.le_widget.render_checkbox.toggled.connect(_make_preview_clear(le_presenter))
    window.aop_widget.render_checkbox.toggled.connect(
        _make_preview_clear(aop_presenter)
    )
    window.skulu_widget.render_checkbox.toggled.connect(
        _make_preview_clear(skulu_presenter)
    )

    # Export dialog + presenter. v2: dialog has no format combo (Decision 2).
    export_dialog = ExportDialog()
    export_presenter = ExportPresenter(export_dialog, registry)

    # Wire the six main-window control signals using injected (or default)
    # choosers/runner/export-runner so tests can supply fakes without
    # monkeypatching QFileDialog static methods.
    wire_control_signals(
        window,
        pipeline_presenter,
        export_presenter,
        export_dialog,
        save_path_chooser=(
            save_path_chooser if save_path_chooser is not None else default_save_chooser
        ),
        open_path_chooser=(
            open_path_chooser if open_path_chooser is not None else default_open_chooser
        ),
        export_dialog_runner=(
            export_dialog_runner
            if export_dialog_runner is not None
            else default_export_runner
        ),
        runner=runner_resolved,
    )

    return WiredApplication(
        qt_app=application,
        window=window,
        registry=registry,
        pipeline_service=pipeline_service_resolved,
        pipeline_presenter=pipeline_presenter,
        export_presenter=export_presenter,
        export_dialog=export_dialog,
        le_presenter=le_presenter,
        aop_presenter=aop_presenter,
        skulu_presenter=skulu_presenter,
        runner=runner_resolved,
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

    def set_import_button_enabled(self, key: str, enabled: bool) -> None:
        """Route to the matching per-input import button and recompute Import-All.

        Args:
            key: The import key (``"LE"``, ``"aop"``, or ``"sku_lu"``).
            enabled: The new enabled state for the keyed button.

        Returns:
            ``None``.

        Side effects:
            Updates the keyed button's enabled state and recomputes the
            Import-All button as the disjunction over the three per-input
            buttons (per spec section 2 / research Q3).
        """
        # Routing table for the three per-input import buttons. Import-All is
        # set to True iff any of the three per-input buttons is currently
        # enabled. An unknown key is a no-op so the adapter is permissive in
        # the same way the presenter's _import_one_frame KeyError boundary is.
        if key == "LE":
            self._window.import_le_btn.setEnabled(enabled)
        elif key == "aop":
            self._window.import_aop_btn.setEnabled(enabled)
        elif key == "sku_lu":
            self._window.import_skulu_btn.setEnabled(enabled)
        else:
            return
        any_enabled = (
            self._window.import_le_btn.isEnabled()
            or self._window.import_aop_btn.isEnabled()
            or self._window.import_skulu_btn.isEnabled()
        )
        self._window.import_all_btn.setEnabled(any_enabled)

    def set_run_button_enabled(self, enabled: bool) -> None:
        """Set the Run button's enabled state on the wrapped main window."""
        self._window.run_btn.setEnabled(enabled)

    def set_save_button_enabled(self, enabled: bool) -> None:
        """Set the Save button's enabled state on the wrapped main window."""
        self._window.save_btn.setEnabled(enabled)

    def set_export_button_enabled(self, enabled: bool) -> None:
        """Set the Export button's enabled state on the wrapped main window."""
        self._window.export_btn.setEnabled(enabled)


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
