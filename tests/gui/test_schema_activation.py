"""Unit tests for activation-time schema matching (Decision 6).

These tests exercise :func:`classify_activation` with a fake schema service and a
controlled :class:`~src.schema_matching.MatchResult`, with no ``QApplication`` and
no disk. They verify the three-way classification: a full-coverage match proceeds
and auto-selects the schema; a partial-band score offers the closest existing
schema as a new-from-template seed; and a low score yields no usable match.
"""

from __future__ import annotations

from src.gui._schema_activation import classify_activation
from src.schema_matching import MatchResult, MismatchReport
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref
from tests.gui.fakes.fake_services import FakeSchemaService


def _schema(name: str) -> SchemaDefinition:
    """Return a small valid schema under ``name``.

    Args:
        name: The schema name.

    Returns:
        A :class:`SchemaDefinition` with one dimension and one measure column.
    """
    return SchemaDefinition(
        name=name,
        version="2.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension", aliases=("cust",)),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer",))),
    )


def _result(score: float, *, has_schema: bool = True) -> MatchResult:
    """Return a match result with the given score.

    Args:
        score: The coverage score to report.
        has_schema: Whether a candidate schema is selected.

    Returns:
        A :class:`MatchResult` selecting ``_schema("existing")`` (or ``None``).
    """
    return MatchResult(
        schema=_schema("existing") if has_schema else None,
        score=score,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )


def test_full_match_proceeds_and_selects_schema() -> None:
    """A full-coverage score proceeds and names the matched schema."""
    # Arrange
    service = FakeSchemaService(match_result=_result(1.0))

    # Act
    decision = classify_activation(service, ["cust", "Sales"])

    # Assert
    assert decision.action == "proceed"
    assert decision.schema_name == "existing"


def test_partial_match_selects_closest_template() -> None:
    """A partial-band score selects the highest-scoring schema as the template."""
    # Arrange: a score below the full threshold but within the partial band.
    service = FakeSchemaService(match_result=_result(0.6))

    # Act
    decision = classify_activation(service, ["cust", "Net Sales"])

    # Assert: the closest existing schema is offered for new-from-template.
    assert decision.action == "partial"
    assert decision.schema_name == "existing"


def test_low_score_yields_no_usable_match() -> None:
    """A score below the partial band yields no usable match (placeholder)."""
    # Arrange
    service = FakeSchemaService(match_result=_result(0.1))

    # Act
    decision = classify_activation(service, ["zzz"])

    # Assert
    assert decision.action == "none"
    assert decision.schema_name is None


def test_no_candidate_yields_no_usable_match() -> None:
    """An empty registry (no candidate) yields no usable match."""
    # Arrange
    service = FakeSchemaService(match_result=_result(0.0, has_schema=False))

    # Act
    decision = classify_activation(service, ["Customer"])

    # Assert
    assert decision.action == "none"
    assert decision.schema_name is None
