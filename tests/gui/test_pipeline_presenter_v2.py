"""Unit tests for v2 :mod:`src.gui.presenters.pipeline_presenter` extensions.

Covers v2 P4-T1 behaviors: ``on_file_path_changed`` and the per-key
``last_imported_path`` map, ``working_tables``, derived-table invalidation,
button-state pushes, the ``"db:<path>"`` sentinel on ``on_open_db``, and
``on_run_success``/``on_run_error`` worker callbacks. Sibling to
``test_pipeline_presenter.py``; kept separate so neither file exceeds the
500-line cap (per ``.claude/rules/general-code-change.md``). Fabricated data
only; no confidential values.
"""

from __future__ import annotations

import pandas as pd
from hypothesis import given
from hypothesis import strategies as st

from src.gui.pipeline_service import ImportSpec
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from tests.gui.fakes.fake_services import FakePipelineService
from tests.gui.fakes.fake_views import FakePipelineView


def _spec() -> ImportSpec:
    """Return a fabricated ImportSpec for the v2 presenter tests."""
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


def test_import_one_le_records_last_path_and_disables_button() -> None:
    """on_import_one LE records the path and disables the LE button."""
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    presenter.on_import_one("LE", _spec())

    assert ("LE", False) in view.import_button_states
    assert presenter.last_imported_path["LE"] == "le.xlsx"


def test_file_path_changed_same_path_is_no_op() -> None:
    """on_file_path_changed with the same path does not re-enable the button."""
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    presenter.on_import_one("LE", _spec())
    view.import_button_states.clear()

    presenter.on_file_path_changed("LE", "le.xlsx")

    assert view.import_button_states == []


def test_file_path_changed_different_path_re_enables_button() -> None:
    """on_file_path_changed with a different path re-enables the keyed button."""
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    presenter.on_import_one("LE", _spec())
    view.import_button_states.clear()

    presenter.on_file_path_changed("LE", "different.xlsx")

    assert view.import_button_states == [("LE", True)]


def test_file_path_changed_aop_tracking() -> None:
    """AOP file-path tracking mirrors the LE contract."""
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    presenter.on_import_one("aop", _spec())
    view.import_button_states.clear()

    presenter.on_file_path_changed("aop", "another.xlsx")

    assert view.import_button_states == [("aop", True)]


def test_file_path_changed_sku_lu_tracking() -> None:
    """SKU_LU file-path tracking mirrors the LE contract."""
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    presenter.on_import_one("sku_lu", _spec())
    view.import_button_states.clear()

    presenter.on_file_path_changed("sku_lu", "different-sku.xlsx")

    assert view.import_button_states == [("sku_lu", True)]


def test_import_all_full_success_disables_all_three_keys() -> None:
    """on_import_all full-success disables all three import buttons."""
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    presenter.on_import_all(_spec())

    disabled_keys = [k for (k, e) in view.import_button_states if e is False]
    assert set(disabled_keys) == {"LE", "aop", "sku_lu"}


def test_import_all_records_paths_for_all_three_keys() -> None:
    """on_import_all records the per-key last-imported path for all three keys."""
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    presenter.on_import_all(_spec())

    assert presenter.last_imported_path["LE"] == "le.xlsx"
    assert presenter.last_imported_path["aop"] == "aop.xlsx"
    assert presenter.last_imported_path["sku_lu"] == "sku.xlsx"


def test_derived_tables_are_invalidated_by_subsequent_import() -> None:
    """A successful import after a Run clears _derived_tables to {}."""
    view = FakePipelineView()
    service = FakePipelineService(
        import_result=_import_result(), run_result=_derived_result()
    )
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())
    presenter.on_run()
    assert presenter.derived_tables != {}

    presenter.on_import_one("LE", _spec())

    assert presenter.derived_tables == {}


def test_working_tables_returns_derived_when_present() -> None:
    """working_tables returns derived tables when non-empty, else imports."""
    view = FakePipelineView()
    service = FakePipelineService(
        import_result=_import_result(), run_result=_derived_result()
    )
    presenter = PipelinePresenter(view, service)

    assert presenter.working_tables == {}

    presenter.on_import_all(_spec())
    assert set(presenter.working_tables.keys()) == {"LE", "aop", "sku_lu"}

    presenter.on_run()
    assert set(presenter.working_tables.keys()) == {"le_wide", "mix_rollup_4"}


def test_on_open_db_sets_sentinel_and_pushes_button_state() -> None:
    """on_open_db disables the import buttons for loaded keys and enables Run."""
    view = FakePipelineView()
    service = FakePipelineService(open_result=_import_result())
    presenter = PipelinePresenter(view, service)

    presenter.on_open_db("test.db")

    for key in ("LE", "aop", "sku_lu"):
        assert presenter.last_imported_path[key] == "db:test.db"
    assert ("LE", False) in view.import_button_states
    assert ("aop", False) in view.import_button_states
    assert ("sku_lu", False) in view.import_button_states
    assert True in view.run_button_states


def test_open_db_then_file_path_change_re_enables_only_changed_key() -> None:
    """After Open, a new LE file selection re-enables only the LE button."""
    view = FakePipelineView()
    service = FakePipelineService(open_result=_import_result())
    presenter = PipelinePresenter(view, service)
    presenter.on_open_db("test.db")
    view.import_button_states.clear()

    presenter.on_file_path_changed("LE", "new.xlsx")

    assert view.import_button_states == [("LE", True)]


@given(st.text(min_size=1, max_size=30))
def test_file_path_changed_property_enables_iff_path_differs(path: str) -> None:
    """Property: ``on_file_path_changed`` enables iff ``path != last``."""
    view = FakePipelineView()
    service = FakePipelineService()
    presenter = PipelinePresenter(view, service)
    presenter.set_last_imported_path_for_test("LE", "")

    presenter.on_file_path_changed("LE", path)

    if path != "":
        assert ("LE", True) in view.import_button_states
    else:
        assert view.import_button_states == []


def test_on_run_success_records_derived_and_re_enables_run() -> None:
    """on_run_success records the result and re-enables the Run button."""
    view = FakePipelineView()
    service = FakePipelineService()
    presenter = PipelinePresenter(view, service)

    derived = _derived_result()

    presenter.on_run_success(derived)

    assert presenter.derived_tables == derived
    assert view.run_button_states.count(True) == 1


def test_on_run_error_surfaces_message_and_re_enables_run() -> None:
    """on_run_error surfaces the message, clears running, and re-enables Run."""
    view = FakePipelineView()
    service = FakePipelineService()
    presenter = PipelinePresenter(view, service)

    presenter.on_run_error("boom")

    assert view.errors == ["boom"]
    assert view.running_states[-1] is False
    assert view.run_button_states.count(True) == 1
