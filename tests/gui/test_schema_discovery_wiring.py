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
from tests.gui.fakes.fake_services import FakeSchemaService, FakeWorkbookReader

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


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
