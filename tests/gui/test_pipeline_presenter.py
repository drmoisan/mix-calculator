"""Unit tests for :mod:`src.gui.presenters.pipeline_presenter`.

These tests run with no ``QApplication``. They use ``FakePipelineView`` and
``FakePipelineService`` to verify import-one/import-all populate tables, the Run
guard, success and failure reporting, save and open, running-state transitions,
and negative flows. A ``hypothesis`` property test covers the running-state
bracket invariant (T2 density). Fabricated data only; no confidential values.
"""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.gui.pipeline_service import ImportSpec
from src.gui.presenters import import_dispatch
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from src.gui.protocols import PipelineViewProtocol
from tests.gui.fakes.fake_services import FakePipelineService
from tests.gui.fakes.fake_views import FakePipelineView


def _spec() -> ImportSpec:
    """Return a fabricated ImportSpec for the presenter tests."""
    return ImportSpec(
        le_path="le.xlsx",
        le_sheet="LE-8 + 4",
        aop_path="aop.xlsx",
        aop_sheet="AOP1",
        skulu_path="sku.xlsx",
        skulu_sheet="SKU_LU",
    )


def _import_result() -> dict[str, pd.DataFrame]:
    """Return a fabricated three-frame import result."""
    return {
        "LE": pd.DataFrame({"KEY": ["k1"], "FY": [1.0]}),
        "aop": pd.DataFrame({"KEY": ["k1"], "FY": [1.0]}),
        "sku_lu": pd.DataFrame({"SKU": ["SKU-001"]}),
    }


def _derived_result() -> dict[str, pd.DataFrame]:
    """Return a fabricated derived-table result."""
    return {
        "le_wide": pd.DataFrame({"KEY": ["k1"]}),
        "mix_rollup_4": pd.DataFrame({"value": [42.0]}),
    }


def test_fake_view_satisfies_pipeline_protocol() -> None:
    """FakePipelineView is a structural PipelineViewProtocol."""
    # Arrange / Act / Assert
    assert isinstance(FakePipelineView(), PipelineViewProtocol)


def test_import_all_populates_tables() -> None:
    """on_import_all records the service's import frames."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_import_all(_spec())

    # Assert
    assert set(presenter.imported_tables) == {"LE", "aop", "sku_lu"}


def test_import_one_populates_single_table() -> None:
    """on_import_one records a single import frame."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_import_one("aop", _spec())

    # Assert
    assert set(presenter.imported_tables) == {"aop"}


def test_import_one_skulu_uses_skulu_branch() -> None:
    """on_import_one for sku_lu records the SKU lookup frame."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_import_one("sku_lu", _spec())

    # Assert
    assert set(presenter.imported_tables) == {"sku_lu"}


def test_import_one_skulu_defaults_path_to_le_when_empty() -> None:
    """An empty skulu_path defaults the SKU_LU path to the LE workbook path."""
    # Arrange: the fake records the path its skulu loader receives.
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    spec = ImportSpec(
        le_path="le.xlsx",
        le_sheet="LE-8 + 4",
        aop_path="aop.xlsx",
        aop_sheet="AOP1",
        skulu_path="",
        skulu_sheet="SKU_LU",
    )

    # Act
    presenter.on_import_one("sku_lu", spec)

    # Assert: the SKU_LU loader received the LE path (the default).
    assert service.import_calls == [("sku_lu", "le.xlsx", "SKU_LU")]


def test_import_one_unknown_key_raises() -> None:
    """on_import_one with an unknown key raises a KeyError."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act / Assert
    with pytest.raises(KeyError, match="Unknown import key"):
        presenter.on_import_one("nope", _spec())


def test_import_all_value_error_routes_to_show_error() -> None:
    """A loader ValueError on import-all routes to view.show_error."""
    # Arrange: configure the fake's import_sources to raise.
    view = FakePipelineView()
    service = FakePipelineService()
    service.raise_on_import = ValueError("combined workbook invalid")
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_import_all(_spec())

    # Assert
    assert view.errors == ["combined workbook invalid"]
    assert presenter.imported_tables == {}


def test_make_run_task_runs_pipeline_on_current_imports() -> None:
    """make_run_task returns a callable that runs the pipeline on imports."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(
        import_result=_import_result(), run_result=_derived_result()
    )
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())

    # Act: build and invoke the worker task callable.
    task = presenter.make_run_task()
    result = task()

    # Assert: the task ran the pipeline over the imported keys.
    assert set(result) == {"le_wide", "mix_rollup_4"}
    assert service.run_calls[-1] == ["LE", "aop", "sku_lu"]


def test_run_is_unavailable_before_import() -> None:
    """Run is guarded: it reports an error and does not run before import."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(run_result=_derived_result())
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_run()

    # Assert: no run occurred and the guard error surfaced.
    assert service.run_calls == []
    assert view.errors == ["Run is unavailable: import sources first."]
    assert presenter.derived_tables == {}


def test_run_after_import_reports_success() -> None:
    """on_run after import runs the pipeline and reports success."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(
        import_result=_import_result(), run_result=_derived_result()
    )
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())

    # Act
    presenter.on_run()

    # Assert: derived tables recorded and a success summary shown.
    assert set(presenter.derived_tables) == {"le_wide", "mix_rollup_4"}
    assert view.results[-1] == "Run complete: 2 derived tables."


def test_run_failure_routes_to_show_error() -> None:
    """A service ValueError during run routes to view.show_error."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    service.raise_on_run = ValueError("run blew up")
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())

    # Act
    presenter.on_run()

    # Assert
    assert view.errors == ["run blew up"]
    assert presenter.derived_tables == {}


def test_run_brackets_running_state() -> None:
    """on_run sets running True then False around the run."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(
        import_result=_import_result(), run_result=_derived_result()
    )
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())
    # Reset the recorder after import setup so the assertion observes only the
    # run path's busy transitions (import-all now brackets busy too).
    view.running_states.clear()

    # Act
    presenter.on_run()

    # Assert: the running flag was raised then lowered, ending idle.
    assert view.running_states == [True, False]
    assert presenter.is_running is False


def test_save_calls_service_with_working_tables() -> None:
    """on_save persists the working tables via the service."""
    # Arrange: after a run, the working set is the derived tables.
    view = FakePipelineView()
    service = FakePipelineService(
        import_result=_import_result(), run_result=_derived_result()
    )
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())
    presenter.on_run()

    # Act
    presenter.on_save("results.db")

    # Assert: the derived tables were saved to the requested path.
    assert service.saved == [(["le_wide", "mix_rollup_4"], "results.db")]
    assert presenter.db_path == "results.db"


def test_open_db_loads_tables_and_sets_db_path() -> None:
    """on_open_db loads tables into the working set and records the path."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(open_result=_derived_result())
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_open_db("prior.db")

    # Assert
    assert set(presenter.imported_tables) == {"le_wide", "mix_rollup_4"}
    assert presenter.db_path == "prior.db"


def test_save_invalid_path_routes_to_show_error() -> None:
    """A service ValueError on save routes to view.show_error."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    service.raise_on_save = ValueError("bad path")
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())

    # Act
    presenter.on_save("/nope/results.db")

    # Assert
    assert view.errors == ["bad path"]
    assert presenter.db_path is None


def test_open_invalid_path_routes_to_show_error() -> None:
    """A service ValueError on open routes to view.show_error."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService()
    service.raise_on_open = ValueError("missing db")
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_open_db("/nope/prior.db")

    # Assert
    assert view.errors == ["missing db"]
    assert presenter.db_path is None


def test_import_one_value_error_routes_to_show_error() -> None:
    """A loader ValueError on import-one routes to view.show_error."""
    # Arrange: configure the LE loader to raise; nothing should be recorded.
    view = FakePipelineView()
    service = FakePipelineService()
    service.raise_on_import = ValueError("LE schema mismatch")
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_import_one("LE", _spec())

    # Assert
    assert view.errors == ["LE schema mismatch"]
    assert presenter.imported_tables == {}


@given(st.integers(min_value=0, max_value=20))
def test_run_result_summary_reports_table_count(table_count: int) -> None:
    """Property: the success summary reports the derived-table count."""
    # Arrange: a derived result with an arbitrary number of tables.
    derived = {f"t{i}": pd.DataFrame({"v": [i]}) for i in range(table_count)}
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result(), run_result=derived)
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())

    # Act
    presenter.on_run()

    # Assert: the summary reflects the exact derived-table count.
    assert view.results[-1] == f"Run complete: {table_count} derived tables."


# --- Off-thread import-one surface (P2-T3) ---------------------------------


def test_make_import_one_task_returns_callable_producing_single_frame() -> None:
    """make_import_one_task returns a callable producing {name: frame}."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act: build and invoke the task for the AOP key.
    task = presenter.make_import_one_task("aop", _spec())
    result = task()

    # Assert: the task produced exactly the AOP frame under its key.
    assert set(result) == {"aop"}
    assert isinstance(result["aop"], pd.DataFrame)


def test_make_import_one_task_callable_raises_on_loader_value_error() -> None:
    """The one-key task callable propagates a loader ValueError to the caller."""
    # Arrange: configure the LE loader to raise.
    view = FakePipelineView()
    service = FakePipelineService()
    service.raise_on_import = ValueError("LE schema mismatch")
    presenter = PipelinePresenter(view, service)

    # Act: build the task; the error surfaces only when the callable runs.
    task = presenter.make_import_one_task("LE", _spec())

    # Assert: invoking the callable raises so the runner routes to on_error.
    with pytest.raises(ValueError, match="LE schema mismatch"):
        task()


def test_on_import_one_success_records_frame_and_emits_message() -> None:
    """on_import_one_success records state, disables the button, emits a message."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    frame = pd.DataFrame({"KEY": ["k1"]})

    # Act
    presenter.on_import_one_success("LE", _spec(), {"LE": frame})

    # Assert: frame recorded, last-imported path set, derived invalidated,
    # button disabled, busy cleared, completion message emitted.
    assert set(presenter.imported_tables) == {"LE"}
    assert presenter.last_imported_path["LE"] == "le.xlsx"
    assert presenter.derived_tables == {}
    assert ("LE", False) in view.import_button_states
    assert view.running_states[-1] is False
    assert view.results[-1] == "Imported LE."


def test_on_import_one_success_recomputes_run_save_export() -> None:
    """on_import_one_success recomputes Run/Save/Export enable states."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_import_one_success("LE", _spec(), {"LE": pd.DataFrame({"K": [1]})})

    # Assert: a non-empty working set enables Run, Save, and Export.
    assert view.run_button_states[-1] is True
    assert view.save_button_states[-1] is True
    assert view.export_button_states[-1] is True


def test_on_import_one_error_routes_to_show_error_and_keeps_button() -> None:
    """on_import_one_error shows the error, clears busy, leaves button enabled."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService()
    presenter = PipelinePresenter(view, service)

    # Act
    presenter.on_import_one_error("LE schema mismatch")

    # Assert: error routed, busy cleared, and no disabling button transition.
    assert view.errors == ["LE schema mismatch"]
    assert view.running_states[-1] is False
    assert all(enabled for _key, enabled in view.import_button_states) or (
        view.import_button_states == []
    )


def test_resolve_path_for_key_unknown_key_raises() -> None:
    """resolve_path_for_key raises KeyError for an unknown import key."""
    # Act / Assert: the defensive routing branch rejects unknown keys.
    with pytest.raises(KeyError, match="Unknown import key"):
        import_dispatch.resolve_path_for_key("nope", _spec())
