"""Unit tests for ``read_worksheet_header_columns`` (issue #62, AC-5/AC-9).

Cover the populated path (the Edit Schema open path reads a worksheet's real
header columns via the same best-header-row logic discovery uses) and the guard
paths (blank/whitespace path or sheet returns ``()`` without calling the reader,
preserving the issue #50 no-file/no-sheet seam; an empty preview returns ``()``).

A per-row-aware fake schema service recognizes a header row only when it carries
a marker token, mirroring the AOP1 layout where the real header is on a later
row. Synthetic headers only; no temp files, no workbook reads, no
``QApplication``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.presenters.source_selection_presenter import (
    read_worksheet_header_columns,
)
from src.schema_matching import MatchResult, MismatchReport
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition, column_ref
from tests.gui.fakes.fake_services import FakeSchemaService, FakeWorkbookReader

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
        Let these tests assert which preview row was selected as the header,
        which the single-result :class:`FakeSchemaService` cannot express.

    Responsibilities:
        Extend :class:`FakeSchemaService` and override :meth:`find_best_match` to
        return a full-coverage match for a row containing the marker token and a
        no-candidate result otherwise.

    Attributes:
        _marker: The token that identifies the real header row.
        _schema: The schema returned for a matching row.
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


def test_header_on_row_zero_returns_those_tokens() -> None:
    """AC-5: a worksheet whose header is on row 0 returns those header tokens."""
    # Arrange: a header on the first row plus a data row.
    preview = [
        ["HEADER", "Customer", "Sales"],
        ["1", "Acme", "10"],
    ]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())

    # Act
    header = read_worksheet_header_columns(reader, service, "le.xlsx", "LE")

    # Assert: the row-0 header tokens are returned as an ordered tuple.
    assert header == ("HEADER", "Customer", "Sales")


def test_stray_leading_rows_return_best_matching_header_row() -> None:
    """AC-5: an AOP1-style preview returns the best-matching (later) header row."""
    # Arrange: stray/blank leading rows with the real header on index 2.
    preview = [
        [],
        ["", ""],
        ["HEADER", "Customer", "Sales"],
    ]
    reader = FakeWorkbookReader(preview_rows=preview)
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())

    # Act
    header = read_worksheet_header_columns(reader, service, "aop.xlsx", "AOP1")

    # Assert: the index-2 header row is selected, not the stray first row.
    assert header == ("HEADER", "Customer", "Sales")


def test_blank_path_returns_empty_and_does_not_call_reader() -> None:
    """AC-9: a blank/whitespace path returns ``()`` with no reader call."""
    # Arrange: a non-empty preview that must never be read for a blank path.
    reader = FakeWorkbookReader(preview_rows=[["HEADER", "Customer"]])
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())

    # Act
    header = read_worksheet_header_columns(reader, service, "   ", "AOP1")

    # Assert: empty header and the reader was never called.
    assert header == ()
    assert reader.preview_calls == []


def test_blank_sheet_returns_empty_and_does_not_call_reader() -> None:
    """AC-9: a blank/whitespace sheet returns ``()`` with no reader call."""
    # Arrange: a non-empty preview that must never be read for a blank sheet.
    reader = FakeWorkbookReader(preview_rows=[["HEADER", "Customer"]])
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())

    # Act
    header = read_worksheet_header_columns(reader, service, "aop.xlsx", "  ")

    # Assert: empty header and the reader was never called.
    assert header == ()
    assert reader.preview_calls == []


def test_empty_preview_returns_empty() -> None:
    """AC-9: an empty preview returns ``()`` (no header row to extract)."""
    # Arrange: a reader that returns no preview rows for the selected sheet.
    reader = FakeWorkbookReader(preview_rows=[])
    service = _PerRowSchemaService(marker="HEADER", schema=_schema())

    # Act
    header = read_worksheet_header_columns(reader, service, "aop.xlsx", "AOP1")

    # Assert: empty header; the reader was called once (then returned nothing).
    assert header == ()
    assert reader.preview_calls == [("aop.xlsx", "AOP1", 5)]
