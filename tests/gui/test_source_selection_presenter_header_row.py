"""Header-row-aware discovery tests for ``SourceSelectionPresenter`` (issue #60).

Covers Defect 3: ``on_schema_discovery`` reads a multi-row preview and selects
the best-matching header row, so a sheet whose real header is on a later row
(AOP1: index 2, with stray/blank leading rows) auto-matches, while LE/SKU_LU
sheets whose header is on row 0 are unchanged. These tests live in their own
module so the sibling ``test_source_selection_presenter.py`` stays under the
repository's 500-line cap.

A ``FakeSchemaService`` returns a single fixed ``MatchResult`` regardless of
input, which cannot distinguish which preview row matched. These tests therefore
use a per-row-aware fake (:class:`_PerRowSchemaService`) that recognizes a header
row only when it contains a marker token, mirroring the AOP1 layout where only
the index-2 row carries the real header. Fabricated data only; no temp files,
no workbook reads, no ``QApplication``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.schema_matching import MatchResult, MismatchReport
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref
from tests.gui.fakes.fake_services import FakeSchemaService, FakeWorkbookReader
from tests.gui.fakes.fake_views import FakeSourceSelectionView

if TYPE_CHECKING:
    from collections.abc import Sequence


def _schema() -> SchemaDefinition:
    """Return a small valid schema used as the matched candidate.

    Returns:
        A :class:`SchemaDefinition` named ``aop_like`` with a Customer/Sales pair.
    """
    return SchemaDefinition(
        name="aop_like",
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(parts=tuple(column_ref(_n) for _n in ("Customer",))),
    )


class _PerRowSchemaService(FakeSchemaService):
    """Fake schema service whose match depends on a marker token in the row.

    Purpose:
        Let the multi-row-header discovery tests assert which preview row was
        selected as the header, which the single-result ``FakeSchemaService``
        cannot express.

    Responsibilities:
        Extend :class:`FakeSchemaService` (so the full
        :class:`SchemaServiceProtocol` surface is satisfied) and override
        :meth:`find_best_match` to return a full-coverage match for a row that
        contains the marker token and a no-candidate result for any other row.
        It records every queried row so the scan order can be asserted.

    Attributes:
        _marker: The token that identifies the real header row.
        _schema: The schema returned for a matching row.
        queried_rows: Each row passed to :meth:`find_best_match`, in call order.
    """

    def __init__(self, marker: str, schema: SchemaDefinition) -> None:
        """Initialize the per-row fake.

        Args:
            marker: The token whose presence in a row marks it as the header.
            schema: The schema returned when a row contains the marker.
        """
        super().__init__(schemas={schema.name: schema})
        self._marker = marker
        self._schema = schema
        self.queried_rows: list[list[str]] = []

    def find_best_match(self, headers: Sequence[str]) -> MatchResult:
        """Return a full match for a marked row, else a no-candidate result.

        Args:
            headers: The candidate header row.

        Returns:
            A full-coverage :class:`MatchResult` selecting the configured schema
            when ``headers`` contains the marker token; otherwise a
            ``schema=None`` result so the row cannot be chosen as the header.
        """
        row = list(headers)
        self.queried_rows.append(row)
        # A row carrying the marker token is the real header and binds the schema;
        # every other (stray/blank) row matches no candidate.
        if self._marker in row:
            return MatchResult(
                schema=self._schema,
                score=1.0,
                report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
            )
        return MatchResult(
            schema=None,
            score=0.0,
            report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
        )


def test_on_schema_discovery_selects_header_on_later_row_aop1_style() -> None:
    """AC-7: an AOP1-style preview (header on index 2) matches the later row.

    The synthetic preview mirrors the AOP1 layout: stray/blank rows at indices
    0-1 and the real header tokens at index 2. Discovery must select the index-2
    row and activate the matched schema rather than reading only the first row.
    """
    # Arrange: a multi-row preview whose only schema-binding row is index 2.
    view = FakeSourceSelectionView()
    preview = [
        [],  # stray/blank first row
        ["", ""],  # stray second row
        ["HEADER", "Customer", "Sales"],  # the real AOP1-style header at index 2
    ]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("aop.xlsx", "AOP1")

    # Assert: the index-2 header bound the schema, which was auto-selected.
    assert view.selected_schemas == ["aop_like"]
    # The reader was asked for the widened multi-row preview window (cap 5).
    assert reader.preview_calls == [("aop.xlsx", "AOP1", 5)]


def test_on_schema_discovery_no_matching_row_falls_back_to_first_row() -> None:
    """AC-7/AC-9: when no preview row matches a schema, discovery uses row 0.

    With a multi-row preview in which no row binds a schema, the best-header-row
    selector falls back to the first row, so classify_activation runs against
    row 0 and the placeholder is set (no usable match) without raising.
    """
    # Arrange: a preview where no row carries the marker, so none bind a schema.
    view = FakeSourceSelectionView()
    preview = [["a", "b"], ["c", "d"], ["e", "f"]]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("aop.xlsx", "AOP1")

    # Assert: no row matched, so the placeholder is set (fallback to row 0, none).
    assert view.selected_schemas == ["<Choose Schema>"]


def test_on_schema_discovery_le_header_on_row_zero_still_selects_row_zero() -> None:
    """AC-8: an LE-style preview (header on index 0) still selects row 0 + LE.

    Regression guard: when the real header is already the first preview row, the
    best-header-row selector returns row 0 and the same schema activates, so LE
    discovery is unchanged by the multi-row widening.
    """
    # Arrange: the header (marker) is on the first row; later rows are data.
    view = FakeSourceSelectionView()
    preview = [
        ["HEADER", "Customer", "Sales"],  # LE-style header on index 0
        ["1", "Acme", "10"],
    ]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("le.xlsx", "LE-8 + 4")

    # Assert: row 0 bound the schema, which was auto-selected (no regression).
    assert view.selected_schemas == ["aop_like"]


def test_on_schema_discovery_skulu_header_on_row_zero_still_selects_row_zero() -> None:
    """AC-8: a SKU_LU-style preview (header on index 0) still selects row 0.

    Regression guard mirroring the LE case for the SKU_LU sheet whose header is
    on the first row.
    """
    # Arrange: the header (marker) is on the first row.
    view = FakeSourceSelectionView()
    preview = [
        ["HEADER", "SKU", "Category"],  # SKU_LU-style header on index 0
        ["A1", "X", "Cat"],
    ]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("sku.xlsx", "SKU_LU")

    # Assert: row 0 bound the schema, which was auto-selected (no regression).
    assert view.selected_schemas == ["aop_like"]


def test_on_schema_discovery_blank_first_row_does_not_raise() -> None:
    """AC-9: a blank first preview row does not raise; discovery completes.

    The first row is empty (a blank leading row) while the real header is on a
    later row. Discovery must not raise on the empty first row and must select
    the later matching header.
    """
    # Arrange: a blank first row and a binding header on index 1.
    view = FakeSourceSelectionView()
    preview = [
        [],  # blank first row (must not raise)
        ["HEADER", "Customer", "Sales"],
    ]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act: this must complete without raising on the blank first row.
    presenter.on_schema_discovery("aop.xlsx", "AOP1")

    # Assert: the later header bound the schema; no error surfaced.
    assert view.selected_schemas == ["aop_like"]
    assert view.errors == []


def test_on_schema_discovery_earliest_row_wins_on_tie() -> None:
    """AC-7: when two rows match equally, the earliest row is selected.

    Two rows carry the marker (equal score). The best-header-row selector uses a
    strict greater-than comparison so the earliest matching row wins the tie.
    """
    # Arrange: a per-row fake that records scan order; two rows carry the marker.
    view = FakeSourceSelectionView()
    preview = [
        ["x"],  # no marker
        ["HEADER", "first"],  # earliest marked row (should win)
        ["HEADER", "second"],  # later marked row (same score)
    ]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("aop.xlsx", "AOP1")

    # Assert: the schema bound (a match occurred). The selector scans all three
    # preview rows, then classify_activation re-queries the *selected* header row;
    # that final re-query carries the earliest marked row ("first"), proving the
    # strict ">" tie-break kept the earlier equal-score row.
    assert view.selected_schemas == ["aop_like"]
    assert service.queried_rows[:3] == [
        ["x"],
        ["HEADER", "first"],
        ["HEADER", "second"],
    ]
    assert service.queried_rows[-1] == ["HEADER", "first"]
