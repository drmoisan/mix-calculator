"""Unit tests for :mod:`src.gui.presenters.export_presenter`.

These tests run with no ``QApplication``. They use ``FakeExportView``,
``FakeExporter``, and a real ``ExporterRegistry`` to verify that available
tables are pushed to the view, select-all triggers the view, export resolves the
format and calls the exporter with the selection and destination, partial vs.
export-all selection, and that an empty selection is rejected before any
exporter call. A ``hypothesis`` property test covers the export-all selection
(T2 density). Fabricated data only; no confidential values.
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.gui.exporters.registry import ExporterRegistry
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.protocols import ExportViewProtocol
from tests.gui.fakes.fake_exporters import FakeExporter
from tests.gui.fakes.fake_views import FakeExportView


def _tables() -> dict[str, pd.DataFrame]:
    """Return a fabricated table set for export tests."""
    return {
        "le_wide": pd.DataFrame({"KEY": ["k1"]}),
        "aop_wide": pd.DataFrame({"KEY": ["k2"]}),
        "mix_rollup_4": pd.DataFrame({"value": [42.0]}),
    }


def _registry_with(exporter: FakeExporter) -> ExporterRegistry:
    """Return a registry with the given exporter registered."""
    registry = ExporterRegistry()
    registry.register(exporter)
    return registry


def test_fake_view_satisfies_export_protocol() -> None:
    """FakeExportView is a structural ExportViewProtocol."""
    # Arrange / Act / Assert
    assert isinstance(FakeExportView(), ExportViewProtocol)


def test_set_available_tables_pushes_names_to_view() -> None:
    """set_available_tables pushes the table names to the view."""
    # Arrange
    view = FakeExportView()
    presenter = ExportPresenter(view, _registry_with(FakeExporter("CSV")))

    # Act
    presenter.set_available_tables(["le_wide", "aop_wide"])

    # Assert
    assert view.table_lists == [["le_wide", "aop_wide"]]


def test_on_select_all_triggers_view_select_all() -> None:
    """on_select_all triggers the view's select-all."""
    # Arrange
    view = FakeExportView()
    presenter = ExportPresenter(view, _registry_with(FakeExporter("CSV")))

    # Act
    presenter.on_select_all()

    # Assert
    assert view.select_all_calls == 1


def test_on_export_resolves_format_and_calls_exporter() -> None:
    """on_export resolves the format and exports the current selection."""
    # Arrange: a partial selection of two of three tables.
    exporter = FakeExporter("CSV")
    view = FakeExportView(selected=["le_wide", "mix_rollup_4"])
    presenter = ExportPresenter(view, _registry_with(exporter))
    tables = _tables()

    # Act
    presenter.on_export(tables, "CSV", "out-dir")

    # Assert: the exporter received the selection and destination.
    assert len(exporter.calls) == 1
    call = exporter.calls[0]
    assert call.selected_names == ["le_wide", "mix_rollup_4"]
    assert call.destination_path == "out-dir"


def test_on_export_all_selection_exports_every_table() -> None:
    """An export-all selection exports every available table name."""
    # Arrange: the view returns all names after select-all.
    exporter = FakeExporter("CSV")
    view = FakeExportView()
    presenter = ExportPresenter(view, _registry_with(exporter))
    tables = _tables()
    presenter.set_available_tables(list(tables))
    presenter.on_select_all()

    # Act
    presenter.on_export(tables, "CSV", "out-dir")

    # Assert
    assert exporter.calls[0].selected_names == list(tables)


def test_on_export_empty_selection_rejected_before_exporter() -> None:
    """Exporting with no selection raises before any exporter call."""
    # Arrange: an empty selection.
    exporter = FakeExporter("CSV")
    view = FakeExportView(selected=[])
    presenter = ExportPresenter(view, _registry_with(exporter))

    # Act / Assert: the guard raises and the exporter is never called.
    with pytest.raises(ValueError, match="No tables selected"):
        presenter.on_export(_tables(), "CSV", "out-dir")
    assert exporter.calls == []


def test_on_export_unknown_format_raises_before_selection() -> None:
    """An unknown format raises a registry KeyError before exporting."""
    # Arrange: a registry without the requested format.
    view = FakeExportView(selected=["le_wide"])
    presenter = ExportPresenter(view, _registry_with(FakeExporter("CSV")))

    # Act / Assert
    with pytest.raises(KeyError, match="No exporter registered"):
        presenter.on_export(_tables(), "Excel", "out-dir")


@given(st.lists(st.text(min_size=1, max_size=12), min_size=1, max_size=10, unique=True))
def test_export_all_selects_exactly_available_names(names: list[str]) -> None:
    """Property: export-all selects exactly the available table names."""
    # Arrange: an exporter and a view; the available names drive select-all.
    exporter = FakeExporter("CSV")
    view = FakeExportView()
    presenter = ExportPresenter(view, _registry_with(exporter))
    tables = {name: pd.DataFrame({"v": [1]}) for name in names}
    presenter.set_available_tables(names)
    presenter.on_select_all()

    # Act
    presenter.on_export(tables, "CSV", "out-dir")

    # Assert: the export selection equals exactly the available names.
    assert exporter.calls[0].selected_names == names
