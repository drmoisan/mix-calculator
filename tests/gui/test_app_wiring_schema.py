"""Tests for the Feature D schema wiring in the composition root (AC6, AC2).

Verifies that ``build_application(schema_service=FakeSchemaService(...))`` wires
the "Schema Builder..." action to open the builder (AC6), and that the
import-flow discovery helper proceeds on a suitable match but surfaces the
rendered mismatch and offers the resolve path on a no-match (AC2). Runs headless
under ``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_wiring import discover_schema, wire_schema_builder
from src.gui.app import build_application
from src.gui.main_window import MainWindow
from src.gui.runners import SynchronousRunner
from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog
from src.schema_matching import (
    CandidateScore,
    MatchResult,
    MismatchReport,
    UnmatchedColumn,
)
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition
from tests.gui.fakes.fake_services import FakeSchemaService

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def _schema() -> SchemaDefinition:
    """Return a small valid schema used as the matched candidate.

    Returns:
        A :class:`SchemaDefinition` with ``Customer`` and ``Sales``.
    """
    return SchemaDefinition(
        name="aop_like",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(columns=("Customer",)),
    )


def _full_match() -> MatchResult:
    """Return a full-coverage match result (score 1.0).

    Returns:
        A :class:`MatchResult` selecting :func:`_schema` with an empty report.
    """
    return MatchResult(
        schema=_schema(),
        score=1.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )


def _no_match() -> MatchResult:
    """Return a low-coverage match result with an unmatched required column.

    Returns:
        A :class:`MatchResult` whose score is below threshold and whose report
        names the unmatched ``Sales`` column.
    """
    report = MismatchReport(
        unmatched_required=(
            UnmatchedColumn(
                canonical_name="Sales",
                aliases=(),
                candidates=(CandidateScore(actual_name="Net Sales", score=0.4),),
            ),
        ),
        unrecognized_actual=("Net Sales",),
    )
    return MatchResult(schema=_schema(), score=0.0, report=report)


def test_build_application_wires_schema_builder_action(qtbot: QtBot) -> None:
    """The "Schema Builder..." action opens the builder via an injected service."""
    # Arrange: build the app with an injected fake schema service.
    service = FakeSchemaService(
        schema_names=["aop_like"], schemas={"aop_like": _schema()}
    )
    wired = build_application(
        runner=SynchronousRunner(),
        schema_service=service,
    )
    qtbot.addWidget(wired.window)

    # Act: trigger the menu action exactly as the user would.
    wired.window.schema_builder_action.trigger()

    # Assert: a builder presenter was retained on the window (the dialog opened).
    assert wired.window.schema_builder_presenter is not None
    assert wired.schema_service is service


def test_discover_schema_proceeds_on_suitable_match() -> None:
    """discover_schema returns a proceed decision for a full-coverage match."""
    # Arrange
    service = FakeSchemaService(match_result=_full_match())

    # Act
    decision = discover_schema(service, ["Customer", "Sales"])

    # Assert
    assert decision.action == "proceed"
    assert decision.explanation == ""


def test_discover_schema_resolves_on_no_match() -> None:
    """discover_schema surfaces the mismatch and asks to resolve on a no-match."""
    # Arrange
    service = FakeSchemaService(match_result=_no_match())

    # Act
    decision = discover_schema(service, ["Customer", "Net Sales"])

    # Assert: the resolve path carries the rendered mismatch explanation (AC2).
    assert decision.action == "resolve"
    assert "Sales" in decision.explanation


def test_wire_schema_builder_uses_injected_factories(qtbot: QtBot) -> None:
    """wire_schema_builder opens a dialog and retains the presenter (AC6)."""
    # Arrange: recording factories so the test asserts the open path directly.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    opened: list[SchemaBuilderDialog] = []

    def dialog_factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        opened.append(dialog)
        return dialog

    sentinel = object()

    wire_schema_builder(
        window,
        service,
        dialog_factory,
        lambda _dialog, _service: sentinel,
    )

    # Act
    window.schema_builder_requested.emit()

    # Assert: one dialog opened and the presenter was retained on the window.
    assert len(opened) == 1
    assert window.schema_builder_presenter is sentinel
