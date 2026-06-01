"""Behavioral integration tests for AC-6 (Run end-to-end via SynchronousRunner).

Each test constructs ``build_application(runner=SynchronousRunner(), …)`` and
exercises the Run button. Because the synchronous runner returns before the
click handler, the result and Run-button state are observable immediately
after the click. No polling primitives are used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.gui.app import WiredApplication, build_application
from src.gui.pipeline_service import ImportSpec
from src.gui.runners import SynchronousRunner
from tests.gui.fakes.fake_services import FakePipelineService, FakeWorkbookReader

if TYPE_CHECKING:
    import pytest
    from PySide6.QtWidgets import QPushButton
    from pytestqt.qtbot import QtBot


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


def _wired_with(service: FakePipelineService, qtbot: QtBot) -> WiredApplication:
    """Build a SynchronousRunner wired app with the given fake pipeline service."""
    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=service,
        workbook_reader=fake_reader,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=lambda _dialog: None,
    )
    qtbot.addWidget(wired.window)
    return wired


def test_run_with_imports_records_derived_tables(qtbot: QtBot) -> None:
    """AC-6: clicking Run after imports populates ``derived_tables``."""
    # Arrange: fake service returns a derived dict.
    service = FakePipelineService(
        import_result=_fake_imports(),
        run_result={"mix_rollup_4": pd.DataFrame({"value": [42.0]})},
    )
    wired = _wired_with(service, qtbot)
    # Drive imports through the production presenter path so _imported_tables
    # is populated by import_sources rather than a test-only seam.
    wired.pipeline_presenter.on_import_all(_import_spec())
    assert wired.window.run_btn.isEnabled() is True

    # Act
    _click(qtbot, wired.window.run_btn)

    # Assert: derived tables recorded.
    assert set(wired.pipeline_presenter.derived_tables) == {"mix_rollup_4"}


def test_run_failure_surfaces_error_and_preserves_imports(qtbot: QtBot) -> None:
    """AC-6 negative: a run task that raises surfaces the error."""
    service = FakePipelineService(import_result=_fake_imports())
    service.raise_on_run = ValueError("kaboom")
    wired = _wired_with(service, qtbot)
    wired.pipeline_presenter.on_import_all(_import_spec())

    _click(qtbot, wired.window.run_btn)

    # Assert: derived tables stay empty and imports are preserved.
    assert wired.pipeline_presenter.derived_tables == {}
    assert set(wired.pipeline_presenter.imported_tables) == {"LE", "aop", "sku_lu"}


def test_partial_import_failure_shows_modal_run_disabled_no_keyerror(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: a failed AOP import shows the modal, disables Run, no KeyError.

    LE and sku_lu import successfully but the AOP import fails. The modal must
    surface the error, Run must stay disabled (WS3), and clicking Run must never
    reach run_pipeline with a missing "aop" key (no cascading KeyError). Cross-
    checks AC-6 and AC-7.
    """
    # Arrange: record the modal at the view's import location.
    modal_calls: list[tuple[str, str]] = []

    def _record_critical(_parent: object, title: str, message: str) -> None:
        modal_calls.append((title, message))

    monkeypatch.setattr(
        "src.gui._main_window_view.QMessageBox.critical",
        _record_critical,
        raising=True,
    )
    # A service whose run_pipeline raises if reached, and whose AOP import fails.
    service = FakePipelineService(import_result=_fake_imports())
    service.raise_on_run = KeyError("aop")
    wired = _wired_with(service, qtbot)
    # Seed widget paths so the import handlers have something to read.
    wired.window.le_widget.set_path("le.xlsx")
    wired.window.aop_widget.set_path("aop.xlsx")
    wired.window.skulu_widget.set_path("sku.xlsx")

    # Import LE and sku_lu successfully; the AOP import fails.
    wired.pipeline_presenter.on_import_one_success(
        "LE", _import_spec(), {"LE": pd.DataFrame({"KEY": ["k1"]})}
    )
    wired.pipeline_presenter.on_import_one_success(
        "sku_lu", _import_spec(), {"sku_lu": pd.DataFrame({"SKU": ["s1"]})}
    )
    wired.pipeline_presenter.on_import_one_error("AOP import failed")

    # Act: attempt a Run on the partial import.
    _click(qtbot, wired.window.run_btn)

    # Assert: the modal surfaced the error, Run stayed disabled, and run_pipeline
    # was never reached (no KeyError cascade; derived tables stay empty).
    assert modal_calls == [("Error", "AOP import failed")]
    assert wired.window.run_btn.isEnabled() is False
    assert wired.pipeline_presenter.derived_tables == {}
    assert service.run_calls == []
