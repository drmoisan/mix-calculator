"""Behavioral integration tests for AC-1 (Render Tab preview).

Each test constructs a fully-wired application via
``build_application(runner=SynchronousRunner(), workbook_reader=fake_reader)``
and asserts the preview surface state through direct model inspection. No
polling primitives are used; assertions read ``PreviewWidget.model.rowCount()``
and item text directly after the deterministic synchronous calls.

Fabricated values only; no confidential data appears in this file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.app import build_application
from src.gui.runners import SynchronousRunner
from tests.gui.fakes.fake_services import FakeWorkbookReader

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def _two_tab_preview_rows() -> list[list[str]]:
    """Return fabricated preview rows for the first tab."""
    return [["tab0_a", "tab0_b"], ["tab0_c", "tab0_d"]]


def _alt_preview_rows() -> list[list[str]]:
    """Return fabricated preview rows for the second tab."""
    return [["tab1_x", "tab1_y"], ["tab1_z", "tab1_w"]]


def test_render_checkbox_on_populates_preview_widget(qtbot: QtBot) -> None:
    """Toggling render-on with a path and tab populates the shared preview."""
    # Arrange: fake reader returning two tabs and a specific preview.
    fake_reader = FakeWorkbookReader(
        sheet_names=["AOP1", "LE-8 + 4"], preview_rows=_two_tab_preview_rows()
    )
    wired = build_application(runner=SynchronousRunner(), workbook_reader=fake_reader)
    qtbot.addWidget(wired.window)
    # Seed file path so the render-tab handler has both inputs.
    wired.window.le_widget.set_path("workbook.xlsx")

    # Act: toggle the render checkbox on.
    wired.window.le_widget.render_checkbox.setChecked(True)

    # Assert: the shared preview widget reflects the rows.
    assert wired.window.preview_widget.model.rowCount() == len(_two_tab_preview_rows())


def test_tab_change_re_renders_preview_with_new_rows(qtbot: QtBot) -> None:
    """Changing the worksheet tab with render on re-renders the preview."""
    fake_reader = FakeWorkbookReader(
        sheet_names=["AOP1", "LE-8 + 4"], preview_rows=_two_tab_preview_rows()
    )
    wired = build_application(runner=SynchronousRunner(), workbook_reader=fake_reader)
    qtbot.addWidget(wired.window)
    wired.window.le_widget.set_path("workbook.xlsx")
    wired.window.le_widget.render_checkbox.setChecked(True)

    # Verify initial preview text matches first-tab content.
    item = wired.window.preview_widget.model.item(0, 0)
    assert item is not None
    assert item.text() == "tab0_a"

    # Act: rotate the fake reader's preview rows and switch the dropdown to the
    # second tab; the re-render must pick up the new preview rows.
    fake_reader.preview_rows = _alt_preview_rows()
    wired.window.le_widget.set_current_sheet("LE-8 + 4")

    new_item = wired.window.preview_widget.model.item(0, 0)
    assert new_item is not None
    assert new_item.text() == "tab1_x"


def test_render_checkbox_off_clears_preview(qtbot: QtBot) -> None:
    """Toggling render-off clears the preview surface."""
    fake_reader = FakeWorkbookReader(
        sheet_names=["AOP1"], preview_rows=_two_tab_preview_rows()
    )
    wired = build_application(runner=SynchronousRunner(), workbook_reader=fake_reader)
    qtbot.addWidget(wired.window)
    wired.window.le_widget.set_path("workbook.xlsx")
    wired.window.le_widget.render_checkbox.setChecked(True)
    assert wired.window.preview_widget.model.rowCount() > 0

    # Act
    wired.window.le_widget.render_checkbox.setChecked(False)

    # Assert
    assert wired.window.preview_widget.model.rowCount() == 0


def test_aop_widget_render_cycle(qtbot: QtBot) -> None:
    """The AOP widget exhibits the same toggle-on/tab-change/toggle-off cycle."""
    fake_reader = FakeWorkbookReader(
        sheet_names=["AOP1", "AOP2"], preview_rows=_two_tab_preview_rows()
    )
    wired = build_application(runner=SynchronousRunner(), workbook_reader=fake_reader)
    qtbot.addWidget(wired.window)
    wired.window.aop_widget.set_path("aop.xlsx")

    # Toggle on
    wired.window.aop_widget.render_checkbox.setChecked(True)
    assert wired.window.preview_widget.model.rowCount() > 0
    # Tab change
    fake_reader.preview_rows = _alt_preview_rows()
    wired.window.aop_widget.set_current_sheet("AOP2")
    new_item = wired.window.preview_widget.model.item(0, 0)
    assert new_item is not None and new_item.text() == "tab1_x"
    # Toggle off
    wired.window.aop_widget.render_checkbox.setChecked(False)
    assert wired.window.preview_widget.model.rowCount() == 0


def test_skulu_widget_render_cycle(qtbot: QtBot) -> None:
    """The SKU_LU widget exhibits the same render cycle as LE and AOP."""
    fake_reader = FakeWorkbookReader(
        sheet_names=["SKU_LU", "Aux"], preview_rows=_two_tab_preview_rows()
    )
    wired = build_application(runner=SynchronousRunner(), workbook_reader=fake_reader)
    qtbot.addWidget(wired.window)
    wired.window.skulu_widget.set_path("sku.xlsx")

    wired.window.skulu_widget.render_checkbox.setChecked(True)
    assert wired.window.preview_widget.model.rowCount() > 0

    fake_reader.preview_rows = _alt_preview_rows()
    wired.window.skulu_widget.set_current_sheet("Aux")
    new_item = wired.window.preview_widget.model.item(0, 0)
    assert new_item is not None and new_item.text() == "tab1_x"

    wired.window.skulu_widget.render_checkbox.setChecked(False)
    assert wired.window.preview_widget.model.rowCount() == 0
