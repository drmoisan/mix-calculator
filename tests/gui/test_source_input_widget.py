"""Qt tests for :mod:`src.gui.widgets.source_input_widget`.

Runs under ``QT_QPA_PLATFORM=offscreen``. Verifies that ``set_tab_list``
populates the dropdown, ``set_path`` emits ``file_selected``, toggling the
render-tab checkbox emits ``render_tab_requested`` with the current path and
sheet, and ``show_error`` displays the message. Event-driven assertions only;
no banned timing APIs. Fabricated data only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from src.gui.widgets.source_input_widget import SourceInputWidget

if TYPE_CHECKING:
    import pytest
    from pytestqt.qtbot import QtBot


class _SignalBlockerView(Protocol):
    """Typed view of pytest-qt's SignalBlocker.args; see test_pipeline_worker."""

    args: list[object] | None


# Short signal wait budget; widget signals fire synchronously on the main thread.
_SIGNAL_TIMEOUT_MS = 1000


def test_set_tab_list_populates_dropdown(qtbot: QtBot) -> None:
    """set_tab_list replaces the dropdown items with the given names."""
    # Arrange
    widget = SourceInputWidget("LE", default_sheet="LE-8 + 4")
    qtbot.addWidget(widget)

    # Act
    widget.set_tab_list(["AOP1", "LE-8 + 4", "SKU_LU"])

    # Assert: the current sheet is the first replacement item.
    assert widget.current_sheet() == "AOP1"


def test_set_path_emits_file_selected(qtbot: QtBot) -> None:
    """set_path emits file_selected with the chosen path."""
    # Arrange
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)

    # Act / Assert: the signal carries the supplied path.
    with qtbot.waitSignal(widget.file_selected, timeout=_SIGNAL_TIMEOUT_MS) as blocker:
        widget.set_path("workbook.xlsx")
    args = cast("_SignalBlockerView", blocker).args
    assert args is not None
    assert cast("str", args[0]) == "workbook.xlsx"


def test_render_checkbox_emits_render_request_with_path_and_sheet(
    qtbot: QtBot,
) -> None:
    """Checking render emits render_tab_requested with path and current sheet."""
    # Arrange: a populated widget with a path and a selected tab.
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)
    widget.set_path("workbook.xlsx")
    widget.set_tab_list(["AOP1"])

    # Act / Assert: toggling the checkbox emits the request signal.
    with qtbot.waitSignal(
        widget.render_tab_requested, timeout=_SIGNAL_TIMEOUT_MS
    ) as blocker:
        widget.set_render_tab_checked(True)
    args = cast("_SignalBlockerView", blocker).args
    assert args is not None
    assert [cast("str", args[0]), cast("str", args[1])] == ["workbook.xlsx", "AOP1"]


def test_render_without_path_does_not_emit(qtbot: QtBot) -> None:
    """Toggling render with no path does not emit render_tab_requested."""
    # Arrange: a widget with no file selected.
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)
    widget.set_tab_list(["AOP1"])

    # Act: connect a recorder slot and toggle the checkbox; with no path the
    # widget must not emit, so the recorder stays empty.
    received: list[tuple[str, str]] = []

    def _record(path: str, sheet: str) -> None:
        received.append((path, sheet))

    widget.render_tab_requested.connect(_record)
    widget.set_render_tab_checked(True)

    # Assert
    assert received == []


def test_show_error_displays_message(qtbot: QtBot) -> None:
    """show_error sets the error label text."""
    # Arrange
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)

    # Act
    widget.show_error("cannot read workbook")

    # Assert: the error label contains the message.
    assert widget.error_text() == "cannot read workbook"


def test_show_preview_is_a_no_op_for_protocol_completeness(qtbot: QtBot) -> None:
    """show_preview accepts rows and does not draw the grid in this widget."""
    # Arrange
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)

    # Act / Assert: calling show_preview does not raise and does not change the
    # widget's path or sheet state.
    widget.show_preview([["a", "b"], ["c", "d"]])
    assert widget.current_path() == ""


def test_browse_button_uses_file_dialog_result(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Clicking the browse button uses the file dialog's returned path.

    Deterministically exercises the dialog handler by patching the static
    ``QFileDialog.getOpenFileName`` to return a fabricated path with no UI.
    """

    # Arrange: patch the file dialog to return a fixed path and an empty filter.
    def _fake_get_open_file_name(
        parent: object, caption: str, directory: str, filter_: str
    ) -> tuple[str, str]:
        del parent, caption, directory, filter_
        return ("chosen.xlsx", "")

    monkeypatch.setattr(
        "src.gui.widgets.source_input_widget.QFileDialog.getOpenFileName",
        _fake_get_open_file_name,
    )
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)

    # Act / Assert: invoking the handler runs the dialog-returned-path path.
    with qtbot.waitSignal(widget.file_selected, timeout=_SIGNAL_TIMEOUT_MS) as blocker:
        widget.open_file_dialog()
    args = cast("_SignalBlockerView", blocker).args
    assert args is not None
    assert cast("str", args[0]) == "chosen.xlsx"
    assert widget.current_path() == "chosen.xlsx"


def test_browse_button_with_canceled_dialog_does_not_emit(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A canceled file dialog (empty path) does not emit file_selected."""

    # Arrange: simulate the user canceling — QFileDialog returns empty strings.
    def _fake_canceled(
        parent: object, caption: str, directory: str, filter_: str
    ) -> tuple[str, str]:
        del parent, caption, directory, filter_
        return ("", "")

    monkeypatch.setattr(
        "src.gui.widgets.source_input_widget.QFileDialog.getOpenFileName",
        _fake_canceled,
    )
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)
    received: list[str] = []
    widget.file_selected.connect(received.append)

    # Act
    widget.open_file_dialog()

    # Assert: no path is recorded and no signal fires.
    assert received == []
    assert widget.current_path() == ""


# v2 P3-T3: re-render-on-tab-change (AC-1) tests.


def test_tab_change_with_render_checked_re_emits_render_request(qtbot: QtBot) -> None:
    """Changing the worksheet tab while render is checked re-emits the request."""
    # Arrange: widget with a path, two tabs, render checkbox already checked.
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)
    widget.set_path("workbook.xlsx")
    widget.set_tab_list(["AOP1", "LE-8 + 4"])
    widget.set_render_tab_checked(True)
    # Reset the recorder after the initial check-toggle emit so we observe only
    # the tab-change re-emit.
    received: list[tuple[str, str]] = []

    def _record(path: str, sheet: str) -> None:
        received.append((path, sheet))

    widget.render_tab_requested.connect(_record)

    # Act: switch the dropdown to the second tab.
    widget.render_checkbox.setChecked(True)  # confirm checked state stays True
    widget.set_current_sheet("LE-8 + 4")

    # Assert: a re-render request was emitted with the new sheet.
    assert received == [("workbook.xlsx", "LE-8 + 4")]


def test_tab_change_with_render_unchecked_does_not_emit(qtbot: QtBot) -> None:
    """Tab changes with render unchecked do not emit a render request."""
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)
    widget.set_path("workbook.xlsx")
    widget.set_tab_list(["AOP1", "LE-8 + 4"])
    # Leave the render checkbox unchecked.
    received: list[tuple[str, str]] = []

    def _record(path: str, sheet: str) -> None:
        received.append((path, sheet))

    widget.render_tab_requested.connect(_record)

    # Act
    widget.set_current_sheet("LE-8 + 4")

    # Assert
    assert received == []


def test_tab_change_with_no_path_does_not_emit(qtbot: QtBot) -> None:
    """Tab changes with the checkbox checked but no path do not emit."""
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)
    widget.set_tab_list(["AOP1", "LE-8 + 4"])
    # Check the render checkbox before any path is selected.
    widget.set_render_tab_checked(True)
    received: list[tuple[str, str]] = []

    def _record(path: str, sheet: str) -> None:
        received.append((path, sheet))

    widget.render_tab_requested.connect(_record)

    # Act: changing the tab must not fire, because no path is set.
    widget.set_current_sheet("LE-8 + 4")

    # Assert
    assert received == []


def test_render_checkbox_accessor_returns_internal_checkbox(qtbot: QtBot) -> None:
    """The ``render_checkbox`` property returns the underlying QCheckBox."""
    widget = SourceInputWidget("LE")
    qtbot.addWidget(widget)

    cb = widget.render_checkbox
    cb.setChecked(True)

    # The widget's state must reflect the change made through the accessor.
    assert widget.render_checkbox.isChecked() is True
