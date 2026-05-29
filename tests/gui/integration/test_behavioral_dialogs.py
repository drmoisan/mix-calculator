"""Behavioral integration tests for AC-7 (Save), AC-8 (Open), AC-9 (Export).

Each test constructs a fully-wired application via ``build_application`` with a
``SynchronousRunner`` and fake choosers/runners. Direct attribute assertions
read the recorded calls on the fake service and exporter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.gui.app import WiredApplication, build_application
from src.gui.pipeline_service import ImportSpec
from src.gui.runners import SynchronousRunner
from tests.gui.fakes.fake_services import FakePipelineService, FakeWorkbookReader

if TYPE_CHECKING:
    from PySide6.QtWidgets import QPushButton
    from pytestqt.qtbot import QtBot

    from src.gui.widgets.export_dialog import ExportDialog


def _click(qtbot: QtBot, button: QPushButton) -> None:
    """Click ``button`` deterministically through the typed QPushButton API."""
    del qtbot
    button.click()


def _fake_imports() -> dict[str, pd.DataFrame]:
    """Return a fabricated three-frame import result for the fake service."""
    return {
        "LE": pd.DataFrame({"KEY": ["k1"]}),
        "aop": pd.DataFrame({"KEY": ["k1"]}),
        "sku_lu": pd.DataFrame({"SKU": ["SKU-001"]}),
    }


def _import_spec() -> ImportSpec:
    """Return a fabricated import spec carrying non-empty paths for all keys."""
    return ImportSpec(
        le_path="le.xlsx",
        le_sheet="LE-8 + 4",
        aop_path="aop.xlsx",
        aop_sheet="AOP1",
        skulu_path="sku_lu.xlsx",
        skulu_sheet="SKU_LU",
    )


def _build_wired(
    qtbot: QtBot,
    *,
    service: FakePipelineService,
    save_path: str | None = None,
    open_path: str | None = None,
    export_result: tuple[str, str] | None = None,
) -> WiredApplication:
    """Build a SynchronousRunner wired app with the given fake choosers."""
    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=service,
        workbook_reader=fake_reader,
        save_path_chooser=lambda: save_path,
        open_path_chooser=lambda: open_path,
        export_dialog_runner=lambda _dialog: export_result,
    )
    qtbot.addWidget(wired.window)
    return wired


# AC-7 Save


def test_save_button_calls_service_with_working_tables(qtbot: QtBot) -> None:
    """AC-7: clicking Save with imports loaded persists the working tables."""
    service = FakePipelineService(import_result=_fake_imports())
    wired = _build_wired(qtbot, service=service, save_path="results.db")
    wired.pipeline_presenter.on_import_all(_import_spec())

    _click(qtbot, wired.window.save_btn)

    assert service.saved == [(["LE", "aop", "sku_lu"], "results.db")]


def test_save_cancel_records_no_call(qtbot: QtBot) -> None:
    """AC-7 cancel: a cancelled save chooser does not call the service."""
    service = FakePipelineService(import_result=_fake_imports())
    wired = _build_wired(qtbot, service=service, save_path=None)
    wired.pipeline_presenter.on_import_all(_import_spec())

    _click(qtbot, wired.window.save_btn)

    assert service.saved == []


# AC-8 Open


def test_open_button_loads_tables_and_disables_imports(qtbot: QtBot) -> None:
    """AC-8: a successful Open loads tables, disables imports, enables Run."""
    service = FakePipelineService(open_result=_fake_imports())
    wired = _build_wired(qtbot, service=service, open_path="prior.db")

    _click(qtbot, wired.window.open_btn)

    assert set(wired.pipeline_presenter.imported_tables) == {"LE", "aop", "sku_lu"}
    assert wired.window.import_le_btn.isEnabled() is False
    assert wired.window.import_aop_btn.isEnabled() is False
    assert wired.window.import_skulu_btn.isEnabled() is False
    assert wired.window.import_all_btn.isEnabled() is False
    assert wired.window.run_btn.isEnabled() is True


def test_open_then_le_path_change_re_enables_le_button(qtbot: QtBot) -> None:
    """AC-8: after Open, a new LE workbook path re-enables only LE/All."""
    service = FakePipelineService(open_result=_fake_imports())
    wired = _build_wired(qtbot, service=service, open_path="prior.db")
    _click(qtbot, wired.window.open_btn)

    wired.window.le_widget.set_path("new.xlsx")

    assert wired.window.import_le_btn.isEnabled() is True
    assert wired.window.import_all_btn.isEnabled() is True
    assert wired.window.import_aop_btn.isEnabled() is False
    assert wired.window.import_skulu_btn.isEnabled() is False


# AC-9 Export


def test_export_populates_checklist_before_dialog(qtbot: QtBot) -> None:
    """AC-9 Defect 1 fix: ``set_available_tables`` is called BEFORE the runner."""
    service = FakePipelineService(import_result=_fake_imports())
    recorded_dialog_table_count: list[int] = []

    def _recording_runner(dialog: ExportDialog) -> tuple[str, str] | None:
        # When the runner is invoked the checklist must already be populated.
        dialog.select_all_tables()
        recorded_dialog_table_count.append(len(dialog.get_selected_names()))
        return None  # cancel after recording

    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=service,
        workbook_reader=fake_reader,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=_recording_runner,
    )
    qtbot.addWidget(wired.window)
    wired.pipeline_presenter.on_import_all(_import_spec())

    _click(qtbot, wired.window.export_btn)

    assert recorded_dialog_table_count == [3]


def test_export_csv_routes_destination_to_csv_exporter(qtbot: QtBot) -> None:
    """AC-9 CSV behavioral path.

    The export click path routes the dialog's CSV format/path through
    ``ExportPresenter`` and the registry to ``CsvExporter``, which writes one
    per-table file via the injected in-memory ``open_writer``. Verifies the
    per-table key set and that each capture is non-empty; the name-mangling
    unit contract is covered by ``tests/gui/test_csv_exporter.py``.
    """
    import io
    import os

    from src.gui.exporters.csv_exporter import CsvExporter
    from src.gui.exporters.excel_exporter import ExcelExporter
    from src.gui.exporters.registry import ExporterRegistry

    # Arrange: in-memory CSV capture seam — the exporter writes into a StringIO
    # per destination path so no file touches disk during the behavioral run.
    # The exporter consumes the sink under a ``with`` block which closes the
    # buffer, so the content snapshot is preserved on close via a subclass.
    captured_writes: dict[str, str] = {}

    class _CapturingStringIO(io.StringIO):
        """StringIO that snapshots its content into ``captured_writes`` on close."""

        def __init__(self, path: str) -> None:
            super().__init__()
            self._path = path

        def close(self) -> None:
            captured_writes[self._path] = self.getvalue()
            super().close()

    def _capture_open_writer(path: str) -> io.StringIO:
        return _CapturingStringIO(path)

    injected_registry = ExporterRegistry()
    injected_registry.register(ExcelExporter())
    injected_registry.register(CsvExporter(open_writer=_capture_open_writer))

    service = FakePipelineService(import_result=_fake_imports())

    def _runner(dialog: ExportDialog) -> tuple[str, str] | None:
        dialog.select_all_tables()
        return "CSV", "C:/tmp/results.csv"

    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=service,
        workbook_reader=fake_reader,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=_runner,
        exporter_registry=injected_registry,
    )
    qtbot.addWidget(wired.window)
    # Drive imports through the production presenter path so _imported_tables
    # is populated by import_sources rather than a removed test-only seam.
    wired.pipeline_presenter.on_import_all(_import_spec())

    _click(qtbot, wired.window.export_btn)

    # Assert: the exporter wrote one per-table file for each fabricated table,
    # routed through the injected in-memory open_writer. Build expected paths
    # via os.path.join so the assertion is OS-independent.
    expected_paths = {
        os.path.join("C:/tmp", "results_LE.csv"),
        os.path.join("C:/tmp", "results_aop.csv"),
        os.path.join("C:/tmp", "results_sku_lu.csv"),
    }
    assert set(captured_writes.keys()) == expected_paths
    # Each capture is non-empty (the exporter actually wrote table content).
    for content in captured_writes.values():
        assert content != ""


def test_export_button_with_no_working_tables_calls_runner_with_empty_list(
    qtbot: QtBot,
) -> None:
    """AC-9: with empty working_tables, the checklist is empty when shown."""
    service = FakePipelineService()
    recorded_table_count: list[int] = []

    def _runner(dialog: ExportDialog) -> tuple[str, str] | None:
        dialog.select_all_tables()
        recorded_table_count.append(len(dialog.get_selected_names()))
        return None

    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=service,
        workbook_reader=fake_reader,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=_runner,
    )
    qtbot.addWidget(wired.window)

    _click(qtbot, wired.window.export_btn)

    assert recorded_table_count == [0]
