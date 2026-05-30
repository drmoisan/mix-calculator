"""Unit tests for :class:`ColumnMatchingPresenter` (Feature D, AC3).

These tests exercise the manual column-matching presenter with a fake view and a
fake schema service, with no ``QApplication`` and no disk/network. They verify
that the presenter pushes unmatched-required, source-column, and fuzzy-suggestion
state to the view from a :class:`~src.schema_matching.MatchResult`, records
point-and-click assignments and ignores, persists alias additions on
accept-and-save, and rejects an assignment to an absent source column.
"""

from __future__ import annotations

from src.gui.presenters.column_matching_presenter import ColumnMatchingPresenter
from src.schema_matching import (
    CandidateScore,
    MatchResult,
    MismatchReport,
    UnmatchedColumn,
)
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition
from tests.gui.fakes.fake_services import FakeSchemaService
from tests.gui.fakes.fake_views import FakeColumnMatchingView


def _schema_with_sales() -> SchemaDefinition:
    """Return a schema with a required ``Sales`` measure for matching tests.

    Returns:
        A valid :class:`SchemaDefinition` with ``Customer`` and ``Sales``,
        keyed on ``Customer``.
    """
    return SchemaDefinition(
        name="aop_like",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(
                canonical_name="Sales",
                role="measure",
                numeric=True,
                aliases=("Revenue",),
            ),
        ),
        key=KeySpec(columns=("Customer",)),
    )


def _mismatch_result() -> MatchResult:
    """Return a match result whose report has one unmatched required column.

    Returns:
        A :class:`MatchResult` selecting :func:`_schema_with_sales` with ``Sales``
        unmatched and one fuzzy candidate ``"Net Sales"``.
    """
    report = MismatchReport(
        unmatched_required=(
            UnmatchedColumn(
                canonical_name="Sales",
                aliases=("Revenue",),
                candidates=(CandidateScore(actual_name="Net Sales", score=0.62),),
            ),
        ),
        unrecognized_actual=("Net Sales",),
    )
    return MatchResult(schema=_schema_with_sales(), score=0.5, report=report)


def test_present_pushes_unmatched_source_and_suggestions() -> None:
    """present pushes unmatched-required, source, and fuzzy state to the view."""
    # Arrange
    view = FakeColumnMatchingView()
    service = FakeSchemaService()
    presenter = ColumnMatchingPresenter(view, service)

    # Act
    presenter.present(_mismatch_result(), ["Customer", "Net Sales"])

    # Assert: the unmatched required column, source columns, and the report's
    # fuzzy candidate (with its score) all reached the view.
    assert view.unmatched_required[-1] == [("Sales", ("Revenue",))]
    assert view.source_columns[-1] == ["Customer", "Net Sales"]
    assert view.fuzzy_suggestions[-1] == {"Sales": [("Net Sales", 0.62)]}


def test_assign_records_assignment_and_updates_view() -> None:
    """assign records the mapping and reflects it through the view."""
    # Arrange
    view = FakeColumnMatchingView()
    service = FakeSchemaService()
    presenter = ColumnMatchingPresenter(view, service)
    presenter.present(_mismatch_result(), ["Customer", "Net Sales"])

    # Act
    presenter.assign("Sales", "Net Sales")

    # Assert
    assert view.assignments_set[-1] == ("Sales", "Net Sales")


def test_ignore_marks_optional_column() -> None:
    """ignore records the ignore and reflects it through the view."""
    # Arrange
    view = FakeColumnMatchingView()
    service = FakeSchemaService()
    presenter = ColumnMatchingPresenter(view, service)
    presenter.present(_mismatch_result(), ["Customer", "Net Sales"])

    # Act
    presenter.ignore("Sales")

    # Assert
    assert view.ignored[-1] == "Sales"


def test_accept_and_save_persists_alias_addition() -> None:
    """accept_and_save augments the schema with the assigned source as an alias."""
    # Arrange: assign the unmatched Sales column to the actual "Net Sales" header.
    view = FakeColumnMatchingView()
    service = FakeSchemaService()
    presenter = ColumnMatchingPresenter(view, service)
    presenter.present(_mismatch_result(), ["Customer", "Net Sales"])
    presenter.assign("Sales", "Net Sales")

    # Act
    saved = presenter.accept_and_save()

    # Assert: the schema was saved once with "Net Sales" appended to Sales aliases.
    assert saved is True
    assert len(service.saved) == 1
    sales_column = next(
        c for c in service.saved[0].columns if c.canonical_name == "Sales"
    )
    assert "Net Sales" in sales_column.aliases
    assert "Revenue" in sales_column.aliases


def test_accept_and_save_rejects_assignment_to_absent_source() -> None:
    """accept_and_save surfaces an error and persists nothing for a bad source."""
    # Arrange: assign Sales to a source column that is not in the header set.
    view = FakeColumnMatchingView()
    service = FakeSchemaService()
    presenter = ColumnMatchingPresenter(view, service)
    presenter.present(_mismatch_result(), ["Customer", "Net Sales"])
    presenter.assign("Sales", "Nonexistent Column")

    # Act
    saved = presenter.accept_and_save()

    # Assert: rejected before persisting, with an error surfaced.
    assert saved is False
    assert service.saved == []
    assert view.errors


def test_accept_and_save_without_present_surfaces_error() -> None:
    """accept_and_save before present has no schema and surfaces an error."""
    # Arrange: a presenter that was never given a match result.
    view = FakeColumnMatchingView()
    service = FakeSchemaService()
    presenter = ColumnMatchingPresenter(view, service)

    # Act
    saved = presenter.accept_and_save()

    # Assert: nothing persisted, an error surfaced.
    assert saved is False
    assert service.saved == []
    assert view.errors


def test_present_without_schema_raises() -> None:
    """present rejects a match result that selected no candidate schema."""
    # Arrange: a no-candidate match result.
    view = FakeColumnMatchingView()
    service = FakeSchemaService()
    presenter = ColumnMatchingPresenter(view, service)
    empty = MatchResult(
        schema=None,
        score=0.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )

    # Act / Assert
    try:
        presenter.present(empty, ["Customer"])
    except ValueError as error:
        assert "candidate schema" in str(error)
    else:  # pragma: no cover - the call above must raise
        raise AssertionError("present did not raise for a None schema")
