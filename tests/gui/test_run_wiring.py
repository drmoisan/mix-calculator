"""Tests that the Run signal dispatches through the injected runner.

Verifies that :func:`src.gui._run_wiring.wire_run` (wired by
``wire_control_signals``) routes the ``run_requested`` signal through the
injected :class:`~src.gui.runners.RunnerProtocol` when the gate is open, and
routes to the presenter's disabled-Run feedback when the gate is closed. Kept as
a sibling of ``test_app_wiring_dispatch.py`` so neither file exceeds the
repository's 500-line cap. Tests run headless under the pytest-qt fixture with
``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._run_wiring import wire_run
from src.gui.main_window import MainWindow
from src.gui.pipeline_service import ImportSpec
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from tests.gui._wiring_test_doubles import fabricated_imports
from tests.gui.fakes.fake_services import FakePipelineService
from tests.gui.fakes.fake_views import FakePipelineView

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd
    from pytestqt.qtbot import QtBot


class _RecordingRunner:
    """Recording :class:`RunnerProtocol` that captures dispatch without running.

    Purpose:
        Prove that the run handler dispatches through the injected runner's
        ``run`` only when the presenter's gate is open.

    Attributes:
        runs: Each ``run`` invocation's task callable, in call order.
    """

    def __init__(self) -> None:
        """Initialize with no recorded runs."""
        self.runs: list[Callable[[], dict[str, pd.DataFrame]]] = []

    def run(
        self,
        task: Callable[[], dict[str, pd.DataFrame]],
        on_success: Callable[[dict[str, pd.DataFrame]], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Record the task without executing it (proves the dispatch seam)."""
        # Deliberately do not invoke the task so the test can distinguish
        # dispatch-through-runner from any synchronous run path.
        self.runs.append(task)


def _spec() -> ImportSpec:
    """Return a trivial import spec used to seed the presenter's tables."""
    return ImportSpec(
        le_path="le.xlsx",
        le_sheet="Sheet1",
        aop_path="aop.xlsx",
        aop_sheet="AOP1",
        skulu_path="skulu.xlsx",
        skulu_sheet="Sheet1",
    )


def _wired(qtbot: QtBot) -> tuple[MainWindow, PipelinePresenter, _RecordingRunner]:
    """Wire a real presenter and a recording runner through :func:`wire_run`."""
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakePipelineService(import_result=fabricated_imports())
    presenter = PipelinePresenter(FakePipelineView(), service)
    runner = _RecordingRunner()
    wire_run(window, presenter, runner)
    return window, presenter, runner


def test_run_dispatches_through_runner_when_gate_open(qtbot: QtBot) -> None:
    """wire_run dispatches the run task through the runner when can_run is True."""
    # Arrange: seed all imports so the run gate is open.
    window, presenter, runner = _wired(qtbot)
    presenter.record_all_import_result(_spec(), fabricated_imports())

    # Act
    window.run_requested.emit()

    # Assert: exactly one task dispatched (the runner records but never runs it).
    assert len(runner.runs) == 1
    assert presenter.derived_tables == {}


def test_run_routes_to_feedback_when_gate_closed(qtbot: QtBot) -> None:
    """wire_run routes to on_run feedback and never dispatches when gate closed."""
    # Arrange: no imports recorded, so the run gate is closed.
    window, presenter, runner = _wired(qtbot)
    view = presenter.view
    assert isinstance(view, FakePipelineView)

    # Act
    window.run_requested.emit()

    # Assert: no task dispatched; the disabled-Run feedback surfaced an error.
    assert runner.runs == []
    assert view.errors == ["Run is unavailable: import sources first."]
