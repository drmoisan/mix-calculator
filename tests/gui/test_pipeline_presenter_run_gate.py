"""Run-gate (WS3) tests for :class:`PipelinePresenter` and the gate predicate.

Split out of ``test_pipeline_presenter.py`` so neither file exceeds the
repository's 500-line cap. Covers ``can_run`` delegation to
:func:`import_dispatch.required_keys_present`, the WS3 all-three-keys gate, the
partial-import cascade guard (no ``KeyError: 'aop'``), and the derived-set
re-run branch (issue #48 / WS3; AC-5, AC-6). These presenter tests need no
``QApplication``; they assert on what the presenter pushed to a fake view.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.gui.pipeline_service import ImportSpec
from src.gui.presenters import import_dispatch
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from tests.gui.fakes.fake_services import FakePipelineService
from tests.gui.fakes.fake_views import FakePipelineView


def _spec() -> ImportSpec:
    """Return a fabricated ImportSpec for the run-gate tests."""
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


def test_can_run_delegates_to_required_keys_present() -> None:
    """can_run forwards the presenter's working state to the gate predicate.

    This proves the gate logic lives in import_dispatch.required_keys_present and
    that can_run only forwards the presenter's current state.
    """
    # Arrange: a fresh presenter has no imports/derived and is not running.
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act / Assert: empty working set -> predicate (and can_run) report False,
    # matching required_keys_present called with the same state.
    assert presenter.can_run() is False
    assert (
        import_dispatch.required_keys_present(
            presenter.imported_tables, presenter.derived_tables, presenter.is_running
        )
        is False
    )


def test_can_run_false_after_single_import_ws3() -> None:
    """A single imported key leaves Run disabled under the WS3 gate (AC-5/AC-6).

    Under WS3 the gate requires all three import keys (or a derived set); a
    partial import (one key) must leave Run disabled so the run path cannot
    cascade into a KeyError.
    """
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act: import a single key only (a partial import).
    presenter.on_import_one("aop", _spec())

    # Assert: WS3 — one key is not enough; Run stays disabled.
    assert presenter.can_run() is False


def test_can_run_true_with_all_three_keys_ws3() -> None:
    """All three import keys present (and not running) opens the gate (AC-5)."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act: a complete import populates all three keys.
    presenter.on_import_all(_spec())

    # Assert: the WS3 gate opens only when every required key is present.
    assert set(presenter.imported_tables) == {"LE", "aop", "sku_lu"}
    assert presenter.can_run() is True


def test_can_run_false_while_running() -> None:
    """The gate is closed while a job is in flight even with all keys present."""
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    presenter.on_import_all(_spec())

    # Act: raise the busy flag through the public setter.
    presenter.set_busy(True)

    # Assert: a running job closes the gate.
    assert presenter.can_run() is False


@pytest.mark.parametrize(
    "keys",
    [
        ("LE",),
        ("aop",),
        ("sku_lu",),
        ("LE", "aop"),
        ("LE", "sku_lu"),
        ("aop", "sku_lu"),
    ],
)
def test_required_keys_present_false_for_partial_imports(keys: tuple[str, ...]) -> None:
    """Each single-key and two-key partial import keeps the gate closed (AC-5)."""
    # Arrange: only the named subset of keys is imported.
    imported = {key: pd.DataFrame({"col": [1.0]}) for key in keys}

    # Act / Assert: a partial import never opens the gate.
    assert import_dispatch.required_keys_present(imported, {}, False) is False


def test_required_keys_present_true_for_all_keys() -> None:
    """All three keys present (not running) opens the gate (AC-5)."""
    # Arrange
    imported = {key: pd.DataFrame({"col": [1.0]}) for key in ("LE", "aop", "sku_lu")}

    # Act / Assert
    assert import_dispatch.required_keys_present(imported, {}, False) is True


def test_required_keys_present_true_for_derived_set() -> None:
    """A non-empty derived set opens the gate even with no fresh imports (AC-5)."""
    # Arrange: no imports, but a prior run produced a derived table.
    derived = {"mix_rollup_4": pd.DataFrame({"value": [42.0]})}

    # Act / Assert: the derived-set branch preserves re-run after a prior run.
    assert import_dispatch.required_keys_present({}, derived, False) is True


def test_required_keys_present_false_when_running_with_all_keys() -> None:
    """A running job closes the gate even when all keys are present (AC-5)."""
    # Arrange
    imported = {key: pd.DataFrame({"col": [1.0]}) for key in ("LE", "aop", "sku_lu")}

    # Act / Assert
    assert import_dispatch.required_keys_present(imported, {}, True) is False


def test_partial_import_failure_disables_run_no_keyerror() -> None:
    """LE + sku_lu imported but AOP failed leaves Run disabled (AC-6).

    Simulates a partial import where the AOP source failed: only LE and sku_lu
    are recorded. The WS3 gate must keep Run disabled so the run path is never
    dispatched, and make_run_task therefore never captures a tables dict missing
    the "aop" key — eliminating the cascading KeyError: 'aop' on run_pipeline.
    """
    # Arrange
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)

    # Act: record only LE and sku_lu successes (AOP import failed and recorded an
    # error, which does not populate the "aop" key).
    presenter.on_import_one_success(
        "LE", _spec(), {"LE": pd.DataFrame({"KEY": ["k1"]})}
    )
    presenter.on_import_one_success(
        "sku_lu", _spec(), {"sku_lu": pd.DataFrame({"SKU": ["s1"]})}
    )
    presenter.on_import_one_error("AOP import failed")

    # Assert: the "aop" key is absent and the WS3 gate keeps Run disabled.
    assert "aop" not in presenter.imported_tables
    assert presenter.can_run() is False
    # The last Run-button push (from the import successes) is disabled, so the
    # run task is never dispatched and run_pipeline is never reached.
    assert view.run_button_states[-1] is False


def test_on_run_with_partial_import_does_not_call_service() -> None:
    """on_run with a partial import surfaces feedback and never runs the pipeline.

    Proves the in-presenter run guard short-circuits before run_pipeline so a
    missing "aop" key cannot cascade into a KeyError (AC-6).
    """
    # Arrange: only LE and sku_lu imported; AOP is missing.
    view = FakePipelineView()
    service = FakePipelineService(import_result=_import_result())
    presenter = PipelinePresenter(view, service)
    presenter.on_import_one_success(
        "LE", _spec(), {"LE": pd.DataFrame({"KEY": ["k1"]})}
    )
    presenter.on_import_one_success(
        "sku_lu", _spec(), {"sku_lu": pd.DataFrame({"SKU": ["s1"]})}
    )

    # Act: a Run request on the partial import.
    presenter.on_run()

    # Assert: the run guard surfaced feedback and never called run_pipeline, so
    # no KeyError: 'aop' path is reachable.
    assert service.run_calls == []
    assert view.errors[-1] == "Run is unavailable: import sources first."
