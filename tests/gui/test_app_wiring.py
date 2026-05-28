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

from src.gui.app import wire_control_signals
from src.gui.exporters.registry import ExporterRegistry
from src.gui.main_window import MainWindow
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.presenters.pipeline_presenter import PipelinePresenter
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
    dialog = ExportDialog([])
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
