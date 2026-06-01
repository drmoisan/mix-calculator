"""Unit tests for :mod:`src.gui.presenters.source_selection_presenter`.

These tests run with no ``QApplication``. They use ``FakeSourceSelectionView``
and ``FakeWorkbookReader`` to verify that file selection populates the tab list,
render-tab produces a bounded preview, building an ``ImportSpec`` records the
selection, and that reader ``ValueError`` routes to ``view.show_error``. A
``hypothesis`` property test covers the pure tab-list pass-through (T2 density).
Fabricated data only; no confidential values.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
from src.gui.protocols import SourceSelectionViewProtocol
from src.schema_matching import MatchResult, MismatchReport, UnmatchedColumn
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition
from tests.gui.fakes.fake_services import FakeSchemaService, FakeWorkbookReader
from tests.gui.fakes.fake_views import FakeSourceSelectionView


def _schema() -> SchemaDefinition:
    """Return a small valid schema used as the matched candidate."""
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
    """Return a full-coverage match result (score 1.0) selecting ``_schema``."""
    return MatchResult(
        schema=_schema(),
        score=1.0,
        report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
    )


def _no_match() -> MatchResult:
    """Return a below-threshold match result with an unmatched required column."""
    report = MismatchReport(
        unmatched_required=(
            UnmatchedColumn(canonical_name="Sales", aliases=(), candidates=()),
        ),
        unrecognized_actual=("Net Sales",),
    )
    return MatchResult(schema=_schema(), score=0.0, report=report)


def test_fake_view_satisfies_source_selection_protocol() -> None:
    """FakeSourceSelectionView is a structural SourceSelectionViewProtocol."""
    # Arrange / Act
    view = FakeSourceSelectionView()

    # Assert: the runtime-checkable Protocol confirms structural compatibility.
    assert isinstance(view, SourceSelectionViewProtocol)


def test_source_selection_protocol_declares_schema_view_methods() -> None:
    """The protocol declares the WS2 schema-view methods and the fake records them."""
    # Arrange: the protocol now carries the schema list/select contract.
    assert hasattr(SourceSelectionViewProtocol, "set_schema_list")
    assert hasattr(SourceSelectionViewProtocol, "set_selected_schema")
    view = FakeSourceSelectionView()

    # Act: drive the two schema-view methods on the fake.
    view.set_schema_list(["aop_v1", "le_v1"])
    view.set_selected_schema("aop_v1")

    # Assert: the fake records both calls.
    assert view.schema_lists == [["aop_v1", "le_v1"]]
    assert view.selected_schemas == ["aop_v1"]


def test_file_selection_populates_tab_list() -> None:
    """on_file_selected pushes the reader's sheet names to the view."""
    # Arrange
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(sheet_names=["AOP1", "LE-8 + 4", "SKU_LU"])
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_file_selected("workbook.xlsx")

    # Assert
    assert view.tab_lists == [["AOP1", "LE-8 + 4", "SKU_LU"]]


def test_single_tab_workbook_populates_one_name() -> None:
    """A single-tab workbook yields a one-element tab list."""
    # Arrange
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(sheet_names=["OnlyTab"])
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_file_selected("workbook.xlsx")

    # Assert
    assert view.tab_lists == [["OnlyTab"]]


def test_duplicate_tab_names_are_passed_through() -> None:
    """Duplicate tab names from the reader are passed to the view unchanged."""
    # Arrange: the presenter does not deduplicate; it forwards what it is given.
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(sheet_names=["Tab", "Tab1"])
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_file_selected("workbook.xlsx")

    # Assert
    assert view.tab_lists == [["Tab", "Tab1"]]


def test_render_tab_produces_bounded_preview() -> None:
    """on_render_tab requests a max_rows-bounded preview and pushes it."""
    # Arrange: the reader caps the preview at max_rows (here 200).
    rows = [[f"r{i}", "x"] for i in range(10)]
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(preview_rows=rows)
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_render_tab("workbook.xlsx", "AOP1")

    # Assert: the preview was pushed and the reader received the 200-row cap.
    assert view.previews == [rows]
    assert reader.preview_calls == [("workbook.xlsx", "AOP1", 200)]


def test_build_import_spec_records_selection() -> None:
    """build_import_spec records the per-input file/sheet selection."""
    # Arrange
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader()
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    spec = presenter.build_import_spec(
        le_path="le.xlsx",
        le_sheet="LE-8 + 4",
        aop_path="aop.xlsx",
        aop_sheet="AOP1",
        skulu_path="sku.xlsx",
        skulu_sheet="SKU_LU",
    )

    # Assert
    assert spec.le_path == "le.xlsx"
    assert spec.aop_sheet == "AOP1"
    assert spec.skulu_path == "sku.xlsx"


def test_unreadable_workbook_routes_to_show_error() -> None:
    """A reader ValueError on tab discovery routes to view.show_error."""
    # Arrange
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader()
    reader.raise_on_get = ValueError("cannot read workbook")
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_file_selected("bad.xlsx")

    # Assert: the error surfaced and no tab list was pushed.
    assert view.errors == ["cannot read workbook"]
    assert view.tab_lists == []


def test_preview_value_error_routes_to_show_error() -> None:
    """A reader ValueError during preview routes to view.show_error."""
    # Arrange
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader()
    reader.raise_on_preview = ValueError("no usable tab")
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_render_tab("bad.xlsx", "Missing")

    # Assert
    assert view.errors == ["no usable tab"]
    assert view.previews == []


@given(st.lists(st.text(max_size=20), max_size=25))
def test_tab_list_equals_reader_output_for_any_names(names: list[str]) -> None:
    """Property: the tab list pushed to the view equals the reader output."""
    # Arrange: a reader returning an arbitrary list of names.
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(sheet_names=names)
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_file_selected("workbook.xlsx")

    # Assert: the presenter forwards exactly the reader's names, unchanged.
    assert view.tab_lists == [list(names)]


# v2 P3-T4: preview_sink (AC-1) tests.


def test_render_tab_with_preview_sink_pushes_rows_to_both() -> None:
    """on_render_tab pushes the preview rows to the view and the wired sink."""
    # Arrange
    view = FakeSourceSelectionView()
    sink = FakeSourceSelectionView()
    rows = [["a", "b"], ["c", "d"]]
    reader = FakeWorkbookReader(preview_rows=rows)
    presenter = SourceSelectionPresenter(view, reader, preview_sink=sink)

    # Act
    presenter.on_render_tab("workbook.xlsx", "AOP1")

    # Assert: both the primary view and the sink received the same rows once.
    assert view.previews == [rows]
    assert sink.previews == [rows]


def test_on_clear_preview_clears_both_view_and_sink() -> None:
    """on_clear_preview pushes ``[]`` to the view and the wired sink."""
    # Arrange
    view = FakeSourceSelectionView()
    sink = FakeSourceSelectionView()
    reader = FakeWorkbookReader()
    presenter = SourceSelectionPresenter(view, reader, preview_sink=sink)

    # Act
    presenter.on_clear_preview()

    # Assert
    assert view.previews == [[]]
    assert sink.previews == [[]]


def test_render_tab_without_preview_sink_only_pushes_to_view() -> None:
    """With ``preview_sink=None``, on_render_tab leaves the sink untouched."""
    # Arrange
    view = FakeSourceSelectionView()
    rows = [["x"]]
    reader = FakeWorkbookReader(preview_rows=rows)
    presenter = SourceSelectionPresenter(view, reader)  # preview_sink defaults to None

    # Act
    presenter.on_render_tab("workbook.xlsx", "AOP1")

    # Assert: only the primary view received the preview.
    assert view.previews == [rows]


def test_on_clear_preview_without_sink_only_clears_view() -> None:
    """on_clear_preview with no sink only pushes ``[]`` to the primary view."""
    # Arrange
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader()
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_clear_preview()

    # Assert
    assert view.previews == [[]]


def test_on_schema_discovery_proceed_selects_matched_schema() -> None:
    """WS2: a suitable match auto-selects the matched schema name (AC-11)."""
    # Arrange: a reader returning a header row and a service that proceeds.
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(preview_rows=[["Customer", "Sales"]])
    service = FakeSchemaService(match_result=_full_match())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("workbook.xlsx", "AOP1")

    # Assert: the matched schema name was auto-selected in the view.
    assert view.selected_schemas == ["aop_like"]


def test_on_schema_discovery_resolve_leaves_placeholder() -> None:
    """WS2: a no-match leaves the placeholder and does not auto-select (AC-12)."""
    # Arrange: a reader returning a header row and a service that resolves.
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(preview_rows=[["Customer", "Net Sales"]])
    service = FakeSchemaService(match_result=_no_match())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("workbook.xlsx", "AOP1")

    # Assert: no schema was auto-selected; the placeholder remains.
    assert view.selected_schemas == []


def test_on_schema_discovery_no_service_is_noop() -> None:
    """WS2: without an injected schema service, discovery is a no-op."""
    # Arrange: no schema service injected.
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(preview_rows=[["Customer", "Sales"]])
    presenter = SourceSelectionPresenter(view, reader)

    # Act
    presenter.on_schema_discovery("workbook.xlsx", "AOP1")

    # Assert: nothing was selected and no error surfaced.
    assert view.selected_schemas == []
    assert view.errors == []


def test_on_schema_discovery_empty_header_leaves_placeholder() -> None:
    """WS2: an empty header preview leaves the placeholder (no match attempted)."""
    # Arrange: a reader returning no rows.
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader(preview_rows=[])
    service = FakeSchemaService(match_result=_full_match())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("workbook.xlsx", "AOP1")

    # Assert: no schema selected because there was no header to match.
    assert view.selected_schemas == []


def test_on_schema_discovery_reader_value_error_routes_to_show_error() -> None:
    """WS2: a reader ValueError during discovery routes to show_error, no select."""
    # Arrange: a reader that raises on preview, and a service that would proceed.
    view = FakeSourceSelectionView()
    reader = FakeWorkbookReader()
    reader.raise_on_preview = ValueError("unreadable header")
    service = FakeSchemaService(match_result=_full_match())
    presenter = SourceSelectionPresenter(view, reader, schema_service=service)

    # Act
    presenter.on_schema_discovery("workbook.xlsx", "AOP1")

    # Assert: the error surfaced and no schema was auto-selected.
    assert view.errors == ["unreadable header"]
    assert view.selected_schemas == []
