"""Tests that import-one/import-all dispatch through the injected runner.

Verifies that :func:`src.gui._import_dispatch_wiring.wire_import_dispatch`
(wired by ``wire_control_signals``) routes import requests through the injected
:class:`~src.gui.runners.RunnerProtocol` rather than calling the presenter's
synchronous import path. Kept as a sibling of ``test_app_wiring.py`` so neither
file exceeds the repository's 500-line cap (see
``.claude/rules/general-code-change.md``). Tests run headless under the
pytest-qt fixture with ``QT_QPA_PLATFORM=offscreen`` from
:mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.exporters.registry import ExporterRegistry
from src.gui.main_window import MainWindow
from src.gui.presenters.export_presenter import ExportPresenter
from src.gui.presenters.pipeline_presenter import PipelinePresenter
from src.gui.widgets.export_dialog import ExportDialog
from tests.gui.fakes.fake_views import FakePipelineView

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd
    from pytestqt.qtbot import QtBot


class _RecordingRunner:
    """Recording :class:`RunnerProtocol` that captures dispatch without running.

    Purpose:
        Prove that the import handlers dispatch through the injected runner's
        ``run`` rather than calling the presenter's synchronous import path.

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
        # dispatch-through-runner from the presenter's synchronous import path.
        self.runs.append(task)


def _build_with_recording_runner(
    qtbot: QtBot,
) -> tuple[MainWindow, PipelinePresenter, _RecordingRunner]:
    """Wire a window/presenter through a recording runner for dispatch tests."""
    from src.gui.app import wire_control_signals
    from tests.gui._wiring_test_doubles import (
        fabricated_imports,
        populate_widget_paths,
    )
    from tests.gui.fakes.fake_services import FakePipelineService

    window = MainWindow()
    qtbot.addWidget(window)
    populate_widget_paths(window)
    service = FakePipelineService(import_result=fabricated_imports())
    presenter = PipelinePresenter(FakePipelineView(), service)
    export_dialog = ExportDialog()
    qtbot.addWidget(export_dialog)
    export_presenter = ExportPresenter(export_dialog, ExporterRegistry())
    runner = _RecordingRunner()
    wire_control_signals(
        window,
        presenter,
        export_presenter,
        export_dialog,
        save_path_chooser=lambda: None,
        open_path_chooser=lambda: None,
        export_dialog_runner=lambda _dialog: None,
        runner=runner,
    )
    return window, presenter, runner


def test_import_one_dispatches_through_runner_not_synchronous_path(
    qtbot: QtBot,
) -> None:
    """_handle_import_one calls runner.run, not the presenter's sync import."""
    # Arrange
    window, presenter, runner = _build_with_recording_runner(qtbot)

    # Act
    window.import_one_requested.emit("LE")

    # Assert: the runner recorded exactly one dispatched task and, because the
    # recording runner never runs it, the presenter's tables stay empty.
    assert len(runner.runs) == 1
    assert presenter.imported_tables == {}


def test_import_all_dispatches_through_runner_not_synchronous_path(
    qtbot: QtBot,
) -> None:
    """_handle_import_all calls runner.run, not the presenter's sync import."""
    # Arrange
    window, presenter, runner = _build_with_recording_runner(qtbot)

    # Act
    window.import_all_requested.emit()

    # Assert: the runner recorded exactly one dispatched task; no sync import ran.
    assert len(runner.runs) == 1
    assert presenter.imported_tables == {}
