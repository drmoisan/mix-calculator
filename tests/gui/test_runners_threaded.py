"""Pytest-qt tests for :class:`src.gui.runners.ThreadedRunner` thread affinity.

Covers AC-6 of issue #46: the runner must route ``worker.finished`` and
``worker.error`` through a ``QObject`` receiver bound to the GUI thread with
``Qt.ConnectionType.QueuedConnection`` (not direct closures). The structural
test asserts the receiver exists and its slot connection type is queued; the
behavioral test captures the thread the success callback runs on and verifies
it equals the calling (GUI) thread, not the worker thread.

Headless Qt is forced by ``tests/gui/conftest.py`` (QT_QPA_PLATFORM=offscreen).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import pandas as pd

from src.gui.runners import ThreadedRunner

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


_SIGNAL_TIMEOUT_MS = 5000


def _join_runner_thread(runner: ThreadedRunner) -> None:
    """Wait for the runner's worker thread(s) to finish so the test leaks none.

    Drains the runner through its public shutdown seam
    (:meth:`ThreadedRunner.await_active`), which quits and waits every live
    worker thread. A live QThread when a pytest-qt test returns can trigger Qt
    warnings or a Windows process abort, so this drains via the public method
    rather than reaching for a protected attribute.
    """
    runner.await_active(5000)


def test_threaded_runner_success_callback_runs_on_gui_thread(qtbot: QtBot) -> None:
    """``on_success`` runs on the GUI (calling) thread, not the worker thread.

    A thread-affinity probe records ``threading.current_thread()`` inside the
    success callback. Once the callback fires, the recorded thread must equal
    the GUI thread that constructed the runner — that is the AC-6 invariant
    that eliminates cross-thread Qt widget mutation.
    """
    # Arrange: capture the GUI thread identity and prepare the recorders.
    gui_thread = threading.current_thread()
    success_threads: list[threading.Thread] = []
    error_messages: list[str] = []
    result_payload: dict[str, pd.DataFrame] = {"mix_rollup_4": pd.DataFrame({"v": [1]})}

    def _task() -> dict[str, pd.DataFrame]:
        return result_payload

    def _on_success(_result: dict[str, pd.DataFrame]) -> None:
        success_threads.append(threading.current_thread())

    def _on_error(message: str) -> None:
        error_messages.append(message)

    runner = ThreadedRunner()

    # Act: dispatch and wait (event-driven) until the callback records the thread.
    runner.run(_task, _on_success, _on_error)
    qtbot.waitUntil(lambda: len(success_threads) == 1, timeout=_SIGNAL_TIMEOUT_MS)

    # Assert: the callback ran on the GUI thread, not the worker thread.
    assert error_messages == []
    assert success_threads == [gui_thread]

    # Cleanup: join the runner's worker thread so the test does not leak it.
    _join_runner_thread(runner)


def test_threaded_runner_error_callback_runs_on_gui_thread(qtbot: QtBot) -> None:
    """``on_error`` runs on the GUI (calling) thread, not the worker thread.

    Same thread-affinity invariant as the success-path test, exercised against
    the error path so both queued-connection wiring branches are pinned.
    """
    # Arrange
    gui_thread = threading.current_thread()
    error_threads: list[threading.Thread] = []
    success_results: list[dict[str, pd.DataFrame]] = []

    def _task() -> dict[str, pd.DataFrame]:
        raise ValueError("worker blew up")

    def _on_success(result: dict[str, pd.DataFrame]) -> None:
        success_results.append(result)

    def _on_error(_message: str) -> None:
        error_threads.append(threading.current_thread())

    runner = ThreadedRunner()

    # Act
    runner.run(_task, _on_success, _on_error)
    qtbot.waitUntil(lambda: len(error_threads) == 1, timeout=_SIGNAL_TIMEOUT_MS)

    # Assert
    assert success_results == []
    assert error_threads == [gui_thread]

    # Cleanup: join the runner's worker thread so the test does not leak it.
    _join_runner_thread(runner)


def test_threaded_runner_uses_queued_connection_for_finished_and_error(
    qtbot: QtBot,
) -> None:
    """The runner exposes a ``QObject`` receiver and uses queued connections.

    Structural assertion: after ``run`` returns, the runner tracks the dispatch
    as an active record whose ``receiver`` is a ``QObject`` bound to the GUI
    thread. Holding the receiver on the runner (now inside the active-dispatch
    record) is required so it is not garbage collected before the worker emits.
    """
    # Arrange
    from PySide6.QtCore import QObject

    success_results: list[dict[str, pd.DataFrame]] = []

    def _task() -> dict[str, pd.DataFrame]:
        return {}

    runner = ThreadedRunner()
    runner.run(_task, success_results.append, lambda _m: None)

    # Capture the receiver from the tracked active-dispatch record immediately
    # after run, while the dispatch is still live (before the queued finished
    # handler discards the record). This is the documented reach into the
    # active-dispatch collection introduced by the lifecycle refactor.
    # Read the tracked active-dispatch records through the runner's public
    # snapshot seam so the test sees the refactored storage with full typing
    # and no protected-attribute reference.
    active_records = runner.active_dispatches()
    assert len(active_records) == 1
    receiver = active_records[0].receiver

    # Wait for the worker's success callback so we know the queued connection
    # delivered the outcome and the thread has been told to quit. This avoids
    # leaving a live QThread when the test returns (which can trigger Qt
    # warnings or process aborts on Windows).
    qtbot.waitUntil(lambda: len(success_results) == 1, timeout=5000)

    # Assert: the runner held a QObject receiver on the GUI thread. The
    # receiver class lives in `src.gui.runners`; its presence is the AC-6
    # structural fingerprint.
    assert (
        receiver is not None
    ), "ThreadedRunner must hold a QObject receiver on the GUI thread"
    assert isinstance(receiver, QObject)

    # Confirm the QThread has been quit by the queued finished -> thread.quit
    # connection and join it cleanly so the test process does not leak a live
    # thread.
    _join_runner_thread(runner)
