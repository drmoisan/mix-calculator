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
from tests.gui.fakes.fake_services import FakeWorkbookReader
from tests.gui.fakes.fake_views import FakeSourceSelectionView


def test_fake_view_satisfies_source_selection_protocol() -> None:
    """FakeSourceSelectionView is a structural SourceSelectionViewProtocol."""
    # Arrange / Act
    view = FakeSourceSelectionView()

    # Assert: the runtime-checkable Protocol confirms structural compatibility.
    assert isinstance(view, SourceSelectionViewProtocol)


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
