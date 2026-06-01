"""Behavioral integration tests for AC-2, AC-3, AC-4, AC-5 (import buttons).

Each test constructs a fully-wired application via ``build_application`` with
a ``SynchronousRunner`` and a ``FakePipelineService`` injected so the loader
paths are deterministic. ``qtbot.mouseClick`` drives the four import buttons
and the file-selected re-enable contract is verified. Fabricated data only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.gui.app import WiredApplication, build_application
from src.gui.runners import SynchronousRunner
from tests.gui.fakes.fake_services import FakePipelineService, FakeWorkbookReader

if TYPE_CHECKING:
    import pytest
    from PySide6.QtWidgets import QPushButton
    from pytestqt.qtbot import QtBot


def _click(qtbot: QtBot, button: QPushButton) -> None:
    """Click ``button`` deterministically.

    Uses :meth:`QPushButton.click` (typed by the PySide6 stubs) rather than
    ``qtbot.mouseClick`` whose stubs lose argument types under strict Pyright.
    The two approaches are behaviorally equivalent for our synchronous flow
    because the SynchronousRunner returns before this function does.
    """
    del qtbot  # parameter retained for call-site symmetry
    button.click()


def _fake_imports() -> dict[str, pd.DataFrame]:
    """Return a fabricated three-frame import result for the fake service."""
    return {
        "LE": pd.DataFrame({"KEY": ["k1"], "FY": [1.0]}),
        "aop": pd.DataFrame({"KEY": ["k1"], "FY": [1.0]}),
        "sku_lu": pd.DataFrame({"SKU": ["SKU-001"]}),
    }


def _wired(
    qtbot: QtBot, *, service: FakePipelineService | None = None
) -> WiredApplication:
    """Build a SynchronousRunner-wired application with fake collaborators."""
    fake_service = (
        service
        if service is not None
        else FakePipelineService(import_result=_fake_imports())
    )
    fake_reader = FakeWorkbookReader(sheet_names=["AOP1"])
    wired = build_application(
        runner=SynchronousRunner(),
        pipeline_service=fake_service,
        workbook_reader=fake_reader,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=lambda _dialog: None,
    )
    qtbot.addWidget(wired.window)
    # Seed the three widget paths so the import handler has something to read.
    wired.window.le_widget.set_path("le.xlsx")
    wired.window.aop_widget.set_path("aop.xlsx")
    wired.window.skulu_widget.set_path("sku.xlsx")
    return wired


def test_import_le_disables_button_on_success(qtbot: QtBot) -> None:
    """AC-2: clicking Import LE on a successful load disables the LE button."""
    wired = _wired(qtbot)

    _click(qtbot, wired.window.import_le_btn)

    assert wired.window.import_le_btn.isEnabled() is False
    assert "LE" in wired.pipeline_presenter.imported_tables


def test_le_same_path_keeps_button_disabled(qtbot: QtBot) -> None:
    """AC-2: a fresh file_selected with the same path leaves LE disabled."""
    wired = _wired(qtbot)
    _click(qtbot, wired.window.import_le_btn)
    assert wired.window.import_le_btn.isEnabled() is False

    # Re-emit the same path; the path-tracking guard keeps the button disabled.
    wired.window.le_widget.set_path("le.xlsx")

    assert wired.window.import_le_btn.isEnabled() is False


def test_le_different_path_re_enables_button(qtbot: QtBot) -> None:
    """AC-2: a different path on the LE widget re-enables the LE button."""
    wired = _wired(qtbot)
    _click(qtbot, wired.window.import_le_btn)

    wired.window.le_widget.set_path("different.xlsx")

    assert wired.window.import_le_btn.isEnabled() is True


def test_import_aop_disables_button_on_success(qtbot: QtBot) -> None:
    """AC-3: Import AOP success disables the AOP button."""
    wired = _wired(qtbot)

    _click(qtbot, wired.window.import_aop_btn)

    assert wired.window.import_aop_btn.isEnabled() is False


def test_aop_different_path_re_enables_button(qtbot: QtBot) -> None:
    """AC-3: a different AOP path re-enables the AOP button."""
    wired = _wired(qtbot)
    _click(qtbot, wired.window.import_aop_btn)

    wired.window.aop_widget.set_path("different_aop.xlsx")

    assert wired.window.import_aop_btn.isEnabled() is True


def test_import_sku_lu_disables_button_on_success(qtbot: QtBot) -> None:
    """AC-4: Import SKU_LU success disables the SKU_LU button."""
    wired = _wired(qtbot)

    _click(qtbot, wired.window.import_skulu_btn)

    assert wired.window.import_skulu_btn.isEnabled() is False


def test_sku_lu_different_path_re_enables_button(qtbot: QtBot) -> None:
    """AC-4: a different SKU_LU path re-enables the SKU_LU button."""
    wired = _wired(qtbot)
    _click(qtbot, wired.window.import_skulu_btn)

    wired.window.skulu_widget.set_path("different_sku.xlsx")

    assert wired.window.import_skulu_btn.isEnabled() is True


def test_le_failure_leaves_button_enabled(qtbot: QtBot) -> None:
    """AC-2 negative: a loader ValueError leaves the LE button enabled."""
    service = FakePipelineService(import_result=_fake_imports())
    service.raise_on_import = ValueError("bad LE")
    wired = _wired(qtbot, service=service)

    _click(qtbot, wired.window.import_le_btn)

    assert wired.window.import_le_btn.isEnabled() is True


def test_import_all_full_success_disables_all_four_buttons(qtbot: QtBot) -> None:
    """AC-5: Import-All full-success disables all four import buttons."""
    wired = _wired(qtbot)

    _click(qtbot, wired.window.import_all_btn)

    assert wired.window.import_le_btn.isEnabled() is False
    assert wired.window.import_aop_btn.isEnabled() is False
    assert wired.window.import_skulu_btn.isEnabled() is False
    assert wired.window.import_all_btn.isEnabled() is False


def test_import_all_then_le_path_change_re_enables_le_and_all(qtbot: QtBot) -> None:
    """AC-5: after Import-All, changing LE re-enables LE and Import-All."""
    wired = _wired(qtbot)
    _click(qtbot, wired.window.import_all_btn)

    wired.window.le_widget.set_path("new_le.xlsx")

    assert wired.window.import_le_btn.isEnabled() is True
    assert wired.window.import_all_btn.isEnabled() is True
    # AOP and SKU_LU remain disabled.
    assert wired.window.import_aop_btn.isEnabled() is False
    assert wired.window.import_skulu_btn.isEnabled() is False


# --- Off-thread dispatch behavior: error routing, busy, messages (P3-T3) ----


def test_le_failure_routes_message_to_status_bar(qtbot: QtBot) -> None:
    """AC-6: a loader ValueError routes the message to the status bar."""
    # Arrange: the LE loader raises so the error path runs.
    service = FakePipelineService(import_result=_fake_imports())
    service.raise_on_import = ValueError("bad LE")
    wired = _wired(qtbot, service=service)

    # Act
    _click(qtbot, wired.window.import_le_btn)

    # Assert: the status bar shows the error (the adapter prefixes "Error: ").
    assert wired.window.statusBar().currentMessage() == "Error: bad LE"


def test_import_one_clears_busy_after_completion(qtbot: QtBot) -> None:
    """AC-8: the busy state is cleared once an import-one completes."""
    # Arrange
    wired = _wired(qtbot)

    # Act
    _click(qtbot, wired.window.import_le_btn)

    # Assert: the presenter is idle after the synchronous dispatch completes.
    assert wired.pipeline_presenter.is_running is False


def test_import_all_failure_clears_busy_and_leaves_buttons_enabled(
    qtbot: QtBot,
) -> None:
    """AC-6/AC-8: a bulk ValueError clears busy and re-enables the buttons."""
    # Arrange: the bulk loader raises.
    service = FakePipelineService(import_result=_fake_imports())
    service.raise_on_import = ValueError("combined invalid")
    wired = _wired(qtbot, service=service)

    # Act
    _click(qtbot, wired.window.import_all_btn)

    # Assert: error routed, busy cleared, and the buttons re-enabled for retry.
    assert wired.window.statusBar().currentMessage() == "Error: combined invalid"
    assert wired.pipeline_presenter.is_running is False
    assert wired.window.import_all_btn.isEnabled() is True
    assert wired.window.import_le_btn.isEnabled() is True
    assert wired.window.import_aop_btn.isEnabled() is True
    assert wired.window.import_skulu_btn.isEnabled() is True


def test_import_one_success_shows_completion_message(qtbot: QtBot) -> None:
    """AC-9: a successful import-one shows the completion message in the status bar."""
    # Arrange
    wired = _wired(qtbot)

    # Act
    _click(qtbot, wired.window.import_le_btn)

    # Assert: the import-one completion message reaches the status bar.
    assert wired.window.statusBar().currentMessage() == "Imported LE."


def test_import_all_success_shows_completion_message(qtbot: QtBot) -> None:
    """AC-10: a successful import-all shows the completion message in the status bar."""
    # Arrange
    wired = _wired(qtbot)

    # Act
    _click(qtbot, wired.window.import_all_btn)

    # Assert: the import-all completion message reaches the status bar.
    assert wired.window.statusBar().currentMessage() == "Imported all 3 sources."


def test_import_failure_shows_modal_and_leaves_run_disabled(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-7: an import failure shows the modal AND leaves Run disabled (WS4).

    Records ``QMessageBox.critical`` to prove the full diagnostic reaches the
    modal surface, and asserts the Run button stays disabled because the failed
    import left the working set incomplete (WS3 gate).
    """
    # Arrange: record the modal at the view's import location (overrides the
    # conftest no-op stub, whose patch runs before this test-body patch).
    modal_calls: list[tuple[str, str]] = []

    def _record_critical(_parent: object, title: str, message: str) -> None:
        modal_calls.append((title, message))

    monkeypatch.setattr(
        "src.gui._main_window_view.QMessageBox.critical",
        _record_critical,
        raising=True,
    )
    service = FakePipelineService(import_result=_fake_imports())
    service.raise_on_import = ValueError("bad LE")
    wired = _wired(qtbot, service=service)

    # Act: the LE import fails.
    _click(qtbot, wired.window.import_le_btn)

    # Assert: the modal carried the full diagnostic and Run stays disabled.
    assert modal_calls == [("Error", "bad LE")]
    assert wired.window.run_btn.isEnabled() is False
