"""Tests for the schema discovery + import-gating composition wiring (Decision 8/9).

Verifies that :func:`wire_schema_discovery_and_gating` connects each source tab's
worksheet-combo activation to the presenter's ``on_schema_discovery`` (Decision 9)
and the widget's ``schema_selected`` to enabling the tab's Import button
(Decision 8). Runs headless under ``QT_QPA_PLATFORM=offscreen``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_discovery_wiring import wire_schema_discovery_and_gating
from src.gui.main_window import MainWindow
from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.schema_matching import MatchResult, MismatchReport
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref
from tests.gui.fakes.fake_services import FakeSchemaService, FakeWorkbookReader

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def _schema() -> SchemaDefinition:
    """Return a small valid schema used as the matched candidate.

    Returns:
        A :class:`SchemaDefinition` named ``le_like`` with a Customer/Sales pair.
    """
    return SchemaDefinition(
        name="le_like",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer",))),
    )


def _full_match() -> MatchResult:
    """Return a full-coverage match result (score 1.0) selecting ``_schema``.

    Returns:
        A :class:`MatchResult` whose score lands at/above the proceed threshold so
        ``classify_activation`` returns the ``"proceed"`` action.
    """
    return MatchResult(
        schema=_schema(),
        score=1.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )


def _no_match() -> MatchResult:
    """Return a no-candidate match result (score 0, no schema).

    Returns:
        A :class:`MatchResult` with no selected schema so discovery classifies
        the activation as a no-match.
    """
    return MatchResult(
        schema=None,
        score=0.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )


def _presenters(
    window: MainWindow, reader: FakeWorkbookReader, service: FakeSchemaService
) -> tuple[
    SourceSelectionPresenter, SourceSelectionPresenter, SourceSelectionPresenter
]:
    """Build one source presenter per input widget over shared fakes.

    Args:
        window: The shell carrying the three source widgets.
        reader: The fake workbook reader injected into each presenter.
        service: The fake schema service injected into each presenter.

    Returns:
        The ``(le, aop, skulu)`` presenter triple.
    """
    return (
        SourceSelectionPresenter(window.le_widget, reader, schema_service=service),
        SourceSelectionPresenter(window.aop_widget, reader, schema_service=service),
        SourceSelectionPresenter(window.skulu_widget, reader, schema_service=service),
    )


def test_tab_activation_triggers_schema_discovery(qtbot: QtBot) -> None:
    """Activating a source tab runs on_schema_discovery (Decision 9)."""
    # Arrange: a reader whose header preview is recorded on read.
    window = MainWindow()
    qtbot.addWidget(window)
    reader = FakeWorkbookReader(preview_rows=[["Customer", "Sales"]])
    service = FakeSchemaService(match_result=_no_match())
    le, aop, skulu = _presenters(window, reader, service)
    window.le_widget.set_path("book.xlsx")
    wire_schema_discovery_and_gating(window, service, le, aop, skulu)

    # Act: change the LE tab combo, which fires currentTextChanged on activation.
    window.le_widget.tab_combo.addItem("Sheet1")
    window.le_widget.tab_combo.setCurrentText("Sheet1")

    # Assert: the presenter read the header to attempt discovery.
    assert any(call[1] == "Sheet1" for call in reader.preview_calls)


def test_tab_activation_no_file_selected_does_not_call_reader(qtbot: QtBot) -> None:
    """B1: activating a tab with NO file selected never calls the reader (issue #50).

    Drives the production activation wiring (the real ``tab_combo.currentTextChanged``
    signal) with no file selected. The guard must short-circuit so the reader is
    never invoked with a blank path/sheet, no exception propagates, the schema
    dropdown stays on the placeholder, and Import stays disabled. This is the
    primary wiring-level integration test for B1.
    """
    # Arrange: wire the real discovery path over a MainWindow and a fake reader,
    # but do NOT select a file (current_path() stays "").
    window = MainWindow()
    qtbot.addWidget(window)
    reader = FakeWorkbookReader(preview_rows=[["Customer", "Sales"]])
    service = FakeSchemaService(match_result=_no_match())
    le, aop, skulu = _presenters(window, reader, service)
    wire_schema_discovery_and_gating(window, service, le, aop, skulu)

    # Act: add and select a tab item, firing the real currentTextChanged signal.
    # No file is selected, so discovery must short-circuit before the reader.
    window.le_widget.tab_combo.addItem("Sheet1")
    window.le_widget.tab_combo.setCurrentText("Sheet1")

    # Assert: the reader was never invoked (no file), so no preview call recorded;
    # the dropdown stays on the placeholder and Import stays disabled. No exception
    # propagated (the test would have errored otherwise).
    assert reader.preview_calls == []
    assert window.le_widget.current_schema() == "<Choose Schema>"
    assert window.import_le_btn.isEnabled() is False


def test_tab_activation_file_but_no_worksheet_never_calls_reader_blank_sheet(
    qtbot: QtBot,
) -> None:
    """B1: a file but NO worksheet selected never calls the reader with a blank sheet.

    Drives the production activation wiring with a file selected but the tab combo
    cleared so the current worksheet text is blank. The guard must short-circuit so
    the reader is never invoked with a blank/whitespace sheet, no exception
    propagates, the dropdown stays on the placeholder, and Import stays disabled.
    This is the wiring-level integration test for B1 (file-selected, no-worksheet
    branch).
    """
    # Arrange: select a file but leave the worksheet selection blank.
    window = MainWindow()
    qtbot.addWidget(window)
    reader = FakeWorkbookReader(preview_rows=[["Customer", "Sales"]])
    service = FakeSchemaService(match_result=_no_match())
    le, aop, skulu = _presenters(window, reader, service)
    window.le_widget.set_path("book.xlsx")
    wire_schema_discovery_and_gating(window, service, le, aop, skulu)

    # Act: populate then clear the combo and set blank current text, firing the
    # real currentTextChanged signal with a blank worksheet selection.
    window.le_widget.tab_combo.addItem("Sheet1")
    window.le_widget.tab_combo.clear()
    window.le_widget.tab_combo.setCurrentText("")

    # Assert: no preview call was ever made with a blank/whitespace sheet; the
    # dropdown stays on the placeholder and Import stays disabled.
    blank_sheet_calls = [call for call in reader.preview_calls if not call[1].strip()]
    assert blank_sheet_calls == []
    assert window.le_widget.current_schema() == "<Choose Schema>"
    assert window.import_le_btn.isEnabled() is False


def test_schema_selection_enables_import_button(qtbot: QtBot) -> None:
    """Selecting a schema enables the tab's Import button via the wiring."""
    # Arrange
    window = MainWindow()
    qtbot.addWidget(window)
    reader = FakeWorkbookReader()
    service = FakeSchemaService()
    le, aop, skulu = _presenters(window, reader, service)
    wire_schema_discovery_and_gating(window, service, le, aop, skulu)
    window.aop_widget.set_schema_list(["aop_v1"])

    # Act
    window.aop_widget.set_selected_schema("aop_v1")

    # Assert: the AOP Import button is enabled.
    assert window.import_aop_btn.isEnabled() is True


def test_ac2_full_match_through_build_application_auto_selects_and_enables(
    qtbot: QtBot,
) -> None:
    """AC-2: with a file AND a worksheet, a full match still auto-selects + enables.

    Re-confirms AC-2 after the cycle-3 guards: driving the production activation
    path through ``build_application`` with a file selected, a real worksheet
    selected, and a service returning a full match auto-selects the matched schema
    in the widget dropdown and enables Import. This proves the blank-path/sheet
    guards do not suppress legitimate activation matching (issue #50 cycle 3).
    """
    # Arrange: build the real composition root with a reader returning a header row
    # and a service whose match is a full proceed for the matched schema.
    from src.gui.app import build_application
    from src.gui.runners import SynchronousRunner

    reader = FakeWorkbookReader(
        sheet_names=["Sheet1"], preview_rows=[["Customer", "Sales"]]
    )
    service = FakeSchemaService(
        schema_names=["le_like"],
        schemas={"le_like": _schema()},
        match_result=_full_match(),
    )
    wired = build_application(
        runner=SynchronousRunner(), workbook_reader=reader, schema_service=service
    )
    qtbot.addWidget(wired.window)
    # Select a file so current_path() is non-blank and the guard does not trip.
    wired.window.le_widget.set_path("book.xlsx")

    # Act: select a real worksheet, firing the production currentTextChanged path.
    wired.window.le_widget.tab_combo.addItem("Sheet1")
    wired.window.le_widget.tab_combo.setCurrentText("Sheet1")

    # Assert: the matched schema is auto-selected and Import is enabled (AC-2 holds).
    assert wired.window.le_widget.current_schema() == "le_like"
    assert wired.window.import_le_btn.isEnabled() is True
