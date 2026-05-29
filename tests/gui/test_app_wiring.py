"""Unit tests for :func:`src.gui.app.wire_control_signals` signal routing.

Verifies that each of the six :class:`MainWindow` control-button signals routes
to the correct presenter handler, that the file-dialog choosers are consulted
only when the user actually triggers Save/Open/Export, and that a cancelled
chooser/dialog produces a no-op. Tests run headless under the pytest-qt fixture
with ``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.

Companion module :mod:`tests.gui.test_app_wiring_defaults` covers the default
chooser/runner factories that ship with the wiring helper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.app import MainWindowPipelineView, wire_control_signals
from src.gui.exporters.registry import ExporterRegistry
from src.gui.main_window import MainWindow
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from src.gui.runners import SynchronousRunner
from src.gui.widgets.export_dialog import ExportDialog
from tests.gui._wiring_test_doubles import (
    build_wired,
    populate_widget_paths,
    seed_import_spec,
)
from tests.gui.fakes.fake_services import FakePipelineService
from tests.gui.fakes.fake_views import FakePipelineView

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_import_one_signal_routes_to_presenter_with_live_spec(qtbot: QtBot) -> None:
    """Emitting import_one_requested imports the named table via the presenter."""
    # Arrange
    window, presenter, _service, *_rest = build_wired(qtbot)

    # Act: emit the signal exactly as the LE button does.
    window.import_one_requested.emit("LE")

    # Assert: the presenter recorded the import under the expected key.
    assert "LE" in presenter.imported_tables


def test_import_all_signal_routes_to_presenter(qtbot: QtBot) -> None:
    """Emitting import_all_requested loads every import key via the presenter."""
    # Arrange
    window, presenter, *_rest = build_wired(qtbot)

    # Act
    window.import_all_requested.emit()

    # Assert: all three keys land on the presenter's imported tables.
    assert set(presenter.imported_tables) == {"LE", "aop", "sku_lu"}


def test_run_signal_with_no_imports_surfaces_guard_error(qtbot: QtBot) -> None:
    """Emitting run_requested before any import shows the unavailable message."""
    # Arrange: build a wiring with a presenter whose view records errors so the
    # Run-guard message can be asserted directly.
    window = MainWindow()
    qtbot.addWidget(window)
    populate_widget_paths(window)
    fake_view = FakePipelineView()
    presenter = PipelinePresenter(fake_view, FakePipelineService())
    registry = ExporterRegistry()
    dialog = ExportDialog()
    qtbot.addWidget(dialog)
    export_presenter = ExportPresenter(dialog, registry)
    wire_control_signals(
        window,
        presenter,
        export_presenter,
        dialog,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=lambda _d: None,
        runner=SynchronousRunner(),
    )

    # Act
    window.run_requested.emit()

    # Assert: the presenter's view received the Run-guard error.
    assert fake_view.errors == ["Run is unavailable: import sources first."]


def test_run_signal_routes_to_presenter_when_imports_present(qtbot: QtBot) -> None:
    """Emitting run_requested after imports runs the pipeline via the presenter."""
    # Arrange: import first so the Run guard is satisfied.
    window, presenter, service, *_rest = build_wired(qtbot)
    window.import_all_requested.emit()

    # Act
    window.run_requested.emit()

    # Assert: the fake service's run_pipeline was called and derived tables set.
    assert service.run_calls == [["LE", "aop", "sku_lu"]]
    assert set(presenter.derived_tables) == {"mix_rollup_4"}


def test_save_signal_routes_to_presenter_with_chosen_path(qtbot: QtBot) -> None:
    """Emitting save_requested calls the chooser and persists the DB path."""
    # Arrange: import first so on_save has working tables (the FakePipelineService
    # records the save call without performing any DB I/O).
    window, presenter, service, *_rest = build_wired(qtbot, save_path="results.db")
    window.import_all_requested.emit()

    # Act
    window.save_requested.emit()

    # Assert: the fake service recorded a save at the chosen path.
    assert service.saved == [(["LE", "aop", "sku_lu"], "results.db")]
    assert presenter.db_path == "results.db"


def test_save_signal_skips_presenter_when_chooser_cancels(qtbot: QtBot) -> None:
    """A cancelled save dialog (None path) does not invoke the presenter."""
    # Arrange
    window, presenter, service, *_rest = build_wired(qtbot, save_path=None)
    window.import_all_requested.emit()

    # Act
    window.save_requested.emit()

    # Assert: no save was recorded on the fake service.
    assert service.saved == []
    assert presenter.db_path is None


def test_open_db_signal_routes_to_presenter_and_records_path(qtbot: QtBot) -> None:
    """Emitting open_db_requested calls the chooser and loads the DB."""
    # Arrange
    window, presenter, *_rest = build_wired(qtbot, open_path="existing.db")

    # Act
    window.open_db_requested.emit()

    # Assert: the presenter loaded the fake's open_result and recorded the path.
    assert set(presenter.imported_tables) == {"LE", "aop", "sku_lu"}
    assert presenter.db_path == "existing.db"


def test_open_db_signal_skips_presenter_when_chooser_cancels(qtbot: QtBot) -> None:
    """A cancelled open dialog (None path) does not invoke the presenter."""
    # Arrange
    window, presenter, *_rest = build_wired(qtbot, open_path=None)

    # Act
    window.open_db_requested.emit()

    # Assert: no tables were loaded and no DB path recorded.
    assert presenter.imported_tables == {}
    assert presenter.db_path is None


def test_export_signal_invokes_exporter_on_full_selection(qtbot: QtBot) -> None:
    """Export success path: dialog accept + selection drives exporter.export.

    Uses the derived (post-run) tables since they take precedence over imports.
    """
    # Arrange: import + run so derived tables are populated, with auto-check-all
    # wiring so the dialog selection is non-empty when on_export runs.
    window, presenter, _service, exporter, *_rest = build_wired(
        qtbot,
        export_result=("Fake", "out.xlsx"),
        auto_check_all_on_set=True,
    )
    window.import_all_requested.emit()
    window.run_requested.emit()

    # Act
    window.export_requested.emit()

    # Assert: exporter received the derived tables and the destination path.
    assert len(exporter.calls) == 1
    call = exporter.calls[0]
    assert call.destination_path == "out.xlsx"
    assert set(call.selected_names) == set(presenter.derived_tables)


def test_export_signal_uses_imported_tables_when_no_run(qtbot: QtBot) -> None:
    """Without a completed run, export falls back to the imported tables."""
    # Arrange: import only (no run).
    window, _presenter, _service, exporter, *_rest = build_wired(
        qtbot,
        export_result=("Fake", "out.xlsx"),
        auto_check_all_on_set=True,
    )
    window.import_all_requested.emit()

    # Act
    window.export_requested.emit()

    # Assert: exporter called with the import keys.
    assert len(exporter.calls) == 1
    assert set(exporter.calls[0].selected_names) == {"LE", "aop", "sku_lu"}


def test_export_signal_skips_exporter_when_dialog_cancels(qtbot: QtBot) -> None:
    """A cancelled export dialog (None runner result) skips exporter.export."""
    # Arrange
    window, _presenter, _service, exporter, *_rest = build_wired(
        qtbot, export_result=None
    )
    window.import_all_requested.emit()
    window.run_requested.emit()

    # Act
    window.export_requested.emit()

    # Assert: no exporter call was made.
    assert exporter.calls == []


def test_wire_helper_reads_live_widget_state_into_spec(qtbot: QtBot) -> None:
    """The import handler reads the current widget paths into the ImportSpec.

    Verifies the live-state read path: changing the widget paths between
    construction and signal emission must change the spec the presenter sees.
    """
    # Arrange
    window, _presenter, service, *_rest = build_wired(qtbot)
    # Mutate widget state after wiring so the spec must be read at emit time.
    window.le_widget.set_path("custom-le.xlsx")
    window.aop_widget.set_path("custom-aop.xlsx")

    # Act
    window.import_all_requested.emit()

    # Assert: the FakePipelineService recorded the sku_lu call (which receives
    # the resolved skulu path); the spec carried widget state at emit time.
    # The FakePipelineService import_sources path does not record the spec, so
    # use import_one to exercise the live-state read deterministically.
    service.import_calls.clear()
    window.import_one_requested.emit("sku_lu")
    assert service.import_calls == [("sku_lu", "sku.xlsx", "SKU_LU")]
    # And re-emit after another widget mutation confirms the spec is live.
    window.skulu_widget.set_path("alt-sku.xlsx")
    window.import_one_requested.emit("sku_lu")
    assert service.import_calls[-1] == ("sku_lu", "alt-sku.xlsx", "SKU_LU")
    # Reference the canonical spec helper to keep its public surface exercised.
    assert seed_import_spec().le_path == "le.xlsx"


# v2 P2-T4: MainWindowPipelineView routing tests for the four new button methods.


def test_adapter_set_import_button_enabled_le_routes_to_le_button(
    qtbot: QtBot,
) -> None:
    """``set_import_button_enabled('LE', False)`` disables the LE import button."""
    # Arrange
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    # Act
    adapter.set_import_button_enabled("LE", False)

    # Assert
    assert window.import_le_btn.isEnabled() is False


def test_adapter_set_import_button_enabled_le_re_enable(qtbot: QtBot) -> None:
    """``set_import_button_enabled('LE', True)`` re-enables the LE button."""
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    adapter.set_import_button_enabled("LE", False)
    adapter.set_import_button_enabled("LE", True)

    assert window.import_le_btn.isEnabled() is True


def test_adapter_set_import_button_enabled_aop_routes_to_aop_button(
    qtbot: QtBot,
) -> None:
    """``set_import_button_enabled('aop', False)`` disables the AOP button."""
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    adapter.set_import_button_enabled("aop", False)

    assert window.import_aop_btn.isEnabled() is False


def test_adapter_set_import_button_enabled_sku_lu_routes_to_skulu_button(
    qtbot: QtBot,
) -> None:
    """``set_import_button_enabled('sku_lu', False)`` disables the SKU_LU button."""
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    adapter.set_import_button_enabled("sku_lu", False)

    assert window.import_skulu_btn.isEnabled() is False


def test_adapter_set_import_button_unknown_key_is_no_op(qtbot: QtBot) -> None:
    """An unknown import key leaves all four import buttons unchanged."""
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    adapter.set_import_button_enabled("unknown", False)

    assert window.import_le_btn.isEnabled() is True
    assert window.import_aop_btn.isEnabled() is True
    assert window.import_skulu_btn.isEnabled() is True
    assert window.import_all_btn.isEnabled() is True


def test_adapter_import_all_recomputes_as_disjunction(qtbot: QtBot) -> None:
    """Import-All is enabled iff any of LE/AOP/SKU_LU is enabled."""
    # Arrange
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    # Act + Assert: disabling all three drives Import-All to False.
    adapter.set_import_button_enabled("LE", False)
    adapter.set_import_button_enabled("aop", False)
    adapter.set_import_button_enabled("sku_lu", False)
    assert window.import_all_btn.isEnabled() is False

    # Re-enabling one of them drives Import-All back to True.
    adapter.set_import_button_enabled("aop", True)
    assert window.import_all_btn.isEnabled() is True


def test_adapter_set_run_button_enabled_routes_to_run_btn(qtbot: QtBot) -> None:
    """``set_run_button_enabled(False)`` disables the Run button."""
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    adapter.set_run_button_enabled(False)
    assert window.run_btn.isEnabled() is False

    adapter.set_run_button_enabled(True)
    assert window.run_btn.isEnabled() is True


def test_adapter_set_save_button_enabled_routes_to_save_btn(qtbot: QtBot) -> None:
    """``set_save_button_enabled(False)`` disables the Save button."""
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    adapter.set_save_button_enabled(False)
    assert window.save_btn.isEnabled() is False


def test_adapter_set_export_button_enabled_routes_to_export_btn(qtbot: QtBot) -> None:
    """``set_export_button_enabled(False)`` disables the Export button."""
    window = MainWindow()
    qtbot.addWidget(window)
    adapter = MainWindowPipelineView(window)

    adapter.set_export_button_enabled(False)
    assert window.export_btn.isEnabled() is False


# v2 P7-T2: build_application runner/chooser/service injection tests.


def test_build_application_injects_synchronous_runner(qtbot: QtBot) -> None:
    """``build_application(runner=SynchronousRunner())`` exposes that runner."""
    from src.gui.app import build_application

    runner = SynchronousRunner()
    wired = build_application(runner=runner)
    qtbot.addWidget(wired.window)

    assert wired.runner is runner


def test_build_application_defaults_to_threaded_runner(qtbot: QtBot) -> None:
    """With ``runner=None`` the default is a ThreadedRunner."""
    from src.gui.app import build_application
    from src.gui.runners import ThreadedRunner

    wired = build_application()
    qtbot.addWidget(wired.window)

    assert isinstance(wired.runner, ThreadedRunner)


def test_build_application_wires_preview_sink_to_main_window_preview(
    qtbot: QtBot,
) -> None:
    """Each source-selection presenter is wired to the shared PreviewWidget."""
    from src.gui.app import build_application

    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)

    # The presenter's preview_sink should reference the same widget the main
    # window exposes as the shared preview.
    assert wired.le_presenter.preview_sink is wired.window.preview_widget
    assert wired.aop_presenter.preview_sink is wired.window.preview_widget
    assert wired.skulu_presenter.preview_sink is wired.window.preview_widget


def test_build_application_file_selected_triggers_on_file_path_changed(
    qtbot: QtBot,
) -> None:
    """``le_widget.file_selected`` re-enables the LE import button on new path."""
    from src.gui.app import build_application
    from tests.gui.fakes.fake_services import FakeWorkbookReader

    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(runner=SynchronousRunner(), workbook_reader=fake_reader)
    qtbot.addWidget(wired.window)

    # Seed the presenter's last-imported LE path so any new selection differs.
    wired.pipeline_presenter.set_last_imported_path_for_test("LE", "old.xlsx")
    # Disable the button first so the re-enable transition is observable.
    wired.window.import_le_btn.setEnabled(False)

    wired.window.le_widget.set_path("new.xlsx")

    assert wired.window.import_le_btn.isEnabled() is True


def test_build_application_unchecking_render_clears_preview(qtbot: QtBot) -> None:
    """Toggling the LE render checkbox off pushes an empty preview to the sink."""
    from src.gui.app import build_application

    wired = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired.window)

    # Populate the preview directly so we can observe the clear.
    wired.window.preview_widget.show_preview([["a", "b"]])
    assert wired.window.preview_widget.model.rowCount() > 0

    # Act: toggle on then off to drive the clear branch.
    wired.window.le_widget.render_checkbox.setChecked(True)
    wired.window.le_widget.render_checkbox.setChecked(False)

    assert wired.window.preview_widget.model.rowCount() == 0


def test_build_application_injects_pipeline_service_and_workbook_reader(
    qtbot: QtBot,
) -> None:
    """``pipeline_service`` and ``workbook_reader`` are used when injected."""
    from src.gui.app import build_application
    from tests.gui.fakes.fake_services import FakePipelineService, FakeWorkbookReader

    fake_service = FakePipelineService()
    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])

    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=fake_service,
        workbook_reader=fake_reader,
    )
    qtbot.addWidget(wired.window)

    # Assert: the wired pipeline service is the injected fake, and the
    # workbook reader is the one the presenters were constructed with.
    assert wired.pipeline_service is fake_service
    assert wired.le_presenter.reader is fake_reader


def test_build_application_uses_injected_exporter_registry(qtbot: QtBot) -> None:
    """Cycle-1 seam: injected ``exporter_registry`` honored; default kept otherwise."""
    from io import StringIO

    from src.gui.app import build_application
    from src.gui.exporters.csv_exporter import CsvExporter
    from src.gui.exporters.excel_exporter import ExcelExporter

    injected = ExporterRegistry()
    injected.register(ExcelExporter())
    injected.register(CsvExporter(open_writer=lambda _path: StringIO()))
    wired = build_application(runner=SynchronousRunner(), exporter_registry=injected)
    qtbot.addWidget(wired.window)
    assert wired.registry is injected
    assert wired.registry.get("CSV") is injected.get("CSV")

    wired_default = build_application(runner=SynchronousRunner())
    qtbot.addWidget(wired_default.window)
    assert wired_default.registry.available_formats() == ["Excel", "CSV"]
