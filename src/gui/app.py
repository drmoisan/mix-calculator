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
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.gui._crash_handler_bootstrap import install_for_main
from src.gui._icon import resolve_icon_path
from src.gui._import_dispatch_wiring import wire_import_dispatch
from src.gui._main_window_view import MainWindowPipelineView
from src.gui._render_exclusivity import wire_render_checkboxes
from src.gui._schema_wiring import wire_schema_builder
from src.gui._velopack_bootstrap import run_velopack_bootstrap
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
from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter
from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.gui.runners import RunnerProtocol, ThreadedRunner
from src.gui.services.db_service import DbService
from src.gui.services.schema_service import build_default_schema_service
from src.gui.services.workbook_reader import WorkbookReader
from src.gui.widgets.export_dialog import ExportDialog
from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui.pipeline_service import PipelineServiceProtocol
    from src.gui.services.schema_service import SchemaServiceProtocol
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
        schema_service: The schema-coordination service seam (Feature D). Wired
            so the "Schema Builder..." action and import-flow discovery share one
            injectable service; tests inject a fake.
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
    schema_service: SchemaServiceProtocol


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

    # Import-one/import-all dispatch is wired in a dedicated helper module so
    # this file stays under the 500-line cap; both signals route through the
    # injected runner there (spec section 4).
    wire_import_dispatch(window, pipeline_presenter, runner, _current_import_spec)

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
    # Import-one/import-all are connected by wire_import_dispatch above.
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
    schema_service: SchemaServiceProtocol | None = None,
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
        schema_service: Optional :class:`SchemaServiceProtocol` (Feature D).
            Defaults to a disk-backed service from
            :func:`~src.gui.services.schema_service.build_default_schema_service`;
            tests inject a fake. Used by the "Schema Builder..." action and
            import-flow schema discovery.

    Returns:
        A :class:`WiredApplication` carrying the assembled components.

    Side effects:
        Constructs Qt widgets and the (Pyside6) ``QApplication`` if none is
        supplied. Does not show the window and does not enter ``exec``.
    """
    # Resolve a QApplication to set the window icon on. Three cases:
    #   1) Caller supplied qt_app (test path or main path) -> reuse it.
    #   2) A QApplication singleton already exists (e.g. pytest-qt
    #      managed instance) -> reuse it; constructing a second would
    #      trigger "Please destroy the QApplication singleton" from
    #      shiboken.
    #   3) No QApplication exists -> construct a fresh one.
    if qt_app is not None:
        application: QApplication = qt_app
    else:
        existing = QCoreApplication.instance()
        if existing is not None:
            application = cast("QApplication", existing)
        else:
            application = QApplication([])

    # Set the window icon on the QApplication so it propagates to the
    # title bar, taskbar, and Alt-Tab preview. ``resolve_icon_path``
    # probes the compiled-mode location first and falls back to the
    # dev-mode location; a missing icon raises FileNotFoundError loudly.
    application.setWindowIcon(QIcon(str(resolve_icon_path())))

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
    # Resolve the schema service (Feature D): use the injected fake when supplied,
    # else build the production disk-backed service from the process environment.
    schema_service_resolved: SchemaServiceProtocol = (
        schema_service
        if schema_service is not None
        else build_default_schema_service(
            env=os.environ, platform=sys.platform, home=Path.home()
        )
    )

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

    # AC1-AC3: wire the three Render-tab checkboxes through the single
    # composition-root entry point. It connects the preview-clear closures
    # (fire only on uncheck so the shared preview clears) and then makes the
    # boxes single-selection, with displaced unchecks emitting no signal so the
    # zero-checked state stays reachable. Rationale and the blockSignals guard
    # live in _render_exclusivity.
    le_box = window.le_widget.render_checkbox
    aop_box = window.aop_widget.render_checkbox
    skulu_box = window.skulu_widget.render_checkbox
    wire_render_checkboxes(
        [le_box, aop_box, skulu_box],
        [
            le_presenter.on_clear_preview,
            aop_presenter.on_clear_preview,
            skulu_presenter.on_clear_preview,
        ],
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

    # Feature D (AC6): connect the "Schema Builder..." action to open the builder
    # dialog driven by a fresh SchemaBuilderPresenter over the resolved service.
    # Fresh dialog/presenter per open so the builder is repeatable.
    wire_schema_builder(
        window,
        schema_service_resolved,
        lambda: SchemaBuilderDialog(),
        lambda dialog, service: SchemaBuilderPresenter(dialog, service),
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
        schema_service=schema_service_resolved,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the GUI: bootstrap Qt, build the wired components, show the window.

    Args:
        argv: Optional argument vector for ``QApplication`` (defaults to
            ``sys.argv``).

    Returns:
        The Qt event loop exit code.

    Side effects:
        Constructs a ``QApplication``, shows the main window, and runs the event
        loop until the user closes the window. Also invokes
        ``velopack.App().run()`` as the very first statement so the Velopack
        installer first-run and uninstall hooks fire correctly.
    """
    # Velopack runtime SDK bootstrap (AC10 of issue #19): MUST be the first
    # call in the entry point. The wrapper (in src.gui._velopack_bootstrap)
    # isolates the untyped Velopack call behind a typed seam.
    run_velopack_bootstrap()

    # Configure logging at the entry point so collaborator info/error messages
    # reach stderr.
    logging.basicConfig(level=logging.WARNING)

    # Crash-visibility installer (issue #46, AC-8): install the four crash
    # hooks BEFORE QApplication is constructed. See ``_crash_handler_bootstrap``.
    install_for_main()

    args = argv if argv is not None else sys.argv
    qt_app = QApplication(args)
    # Set the window icon on the production QApplication so the title
    # bar, taskbar, and Alt-Tab preview pick it up. The independent call
    # in ``build_application`` covers the test/build-only paths.
    qt_app.setWindowIcon(QIcon(str(resolve_icon_path())))
    wired = build_application(qt_app=qt_app)
    wired.window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
