"""Lifecycle regression tests for :class:`src.gui.runners.ThreadedRunner`.

Covers R-AC-7 of issue #48: the threaded runner must perform no cross-thread
``QObject`` destruction. These tests prove four properties of the lifecycle
refactor:

- ``test_worker_deletelater_wired_to_thread_finished`` — the worker is actually
  destroyed (``deleteLater``) on its own thread after ``thread.finished``, not
  merely left for GUI-thread Python GC (R-AC-7 a).
- ``test_second_dispatch_does_not_drop_running_prior_thread`` — a second
  dispatch does not overwrite or drop a still-running prior dispatch; both
  records are tracked concurrently and both drain on shutdown (R-AC-7 b).
- ``test_await_active_quits_and_waits_then_no_running_thread`` — the
  application-shutdown seam quits and waits active threads, leaving none
  running (R-AC-7 c).
- ``test_queued_outcome_still_delivers_on_gui_thread`` — the existing queued
  ``_RunnerReceiver`` delivery (AC-6) still routes success and error callbacks
  onto the GUI thread after the refactor (R-AC-7 d).

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


def test_worker_deletelater_wired_to_thread_finished(qtbot: QtBot) -> None:
    """The worker is destroyed on its own thread after ``thread.finished``.

    R-AC-7 (a): a probe is connected to ``worker.destroyed`` and the test waits
    for that signal after the dispatch completes. A fired ``destroyed`` signal
    proves the worker was actually deleted via the ``thread.finished ->
    worker.deleteLater`` wiring (on the worker thread), not merely GC-deferred.
    """
    # Arrange: a trivial task returning a small dict; capture the live record so
    # we can observe the worker's destroyed signal.
    result_payload: dict[str, pd.DataFrame] = {"mix_rollup_4": pd.DataFrame({"v": [1]})}

    def _task() -> dict[str, pd.DataFrame]:
        return result_payload

    runner = ThreadedRunner()
    runner.run(_task, lambda _r: None, lambda _m: None)

    # Capture the dispatch's worker while the record is still tracked so the
    # destroyed-signal probe can confirm actual deletion after thread.finished.
    active_records = runner.active_dispatches()
    assert len(active_records) == 1
    worker = active_records[0].worker

    # Act + Assert: wait for the worker's destroyed signal, which only fires once
    # deleteLater (scheduled on thread.finished) has run on the worker thread.
    with qtbot.waitSignal(worker.destroyed, timeout=_SIGNAL_TIMEOUT_MS):
        pass

    # Cleanup: drain any remaining thread so the test leaks none.
    runner.await_active(_SIGNAL_TIMEOUT_MS)


def test_second_dispatch_does_not_drop_running_prior_thread(qtbot: QtBot) -> None:
    """A second dispatch does not drop a still-running prior dispatch.

    R-AC-7 (b): both tasks block on a shared event so neither completes before
    both dispatches are registered. The active-dispatch collection must hold two
    records concurrently (no overwrite). Releasing the event lets both finish;
    ``await_active`` then drains them and empties the collection.
    """
    # Arrange: a gate the tasks wait on so both dispatches stay live together.
    gate = threading.Event()

    def _gated_task() -> dict[str, pd.DataFrame]:
        # Block until the test releases the gate so the dispatch stays active
        # while the second dispatch is registered.
        gate.wait(_SIGNAL_TIMEOUT_MS / 1000)
        return {}

    runner = ThreadedRunner()

    # Act: issue two dispatches while the gate holds both workers.
    runner.run(_gated_task, lambda _r: None, lambda _m: None)
    runner.run(_gated_task, lambda _r: None, lambda _m: None)

    # Assert: both dispatches are tracked concurrently; the first was not
    # dropped or overwritten by the second.
    assert len(runner.active_dispatches()) == 2

    # Release the gate so both workers finish, then drain via the public seam.
    gate.set()
    runner.await_active(_SIGNAL_TIMEOUT_MS)

    # Assert: after shutdown the collection is empty (both records removed on
    # their thread.finished) and no thread remains running.
    qtbot.waitUntil(
        lambda: len(runner.active_dispatches()) == 0, timeout=_SIGNAL_TIMEOUT_MS
    )
    assert runner.active_dispatches() == ()


def test_await_active_quits_and_waits_then_no_running_thread(qtbot: QtBot) -> None:
    """Shutdown quits and waits active threads, leaving none running.

    R-AC-7 (c): after one dispatch, ``await_active`` simulates application
    shutdown teardown. Every tracked thread must report ``isRunning() is False``
    afterward (or the collection is empty), so no thread is destroyed while
    running.
    """
    # Arrange: a gated task so the dispatch is reliably live when await_active
    # is called, exercising the quit+wait path rather than an already-finished
    # thread.
    gate = threading.Event()

    def _gated_task() -> dict[str, pd.DataFrame]:
        gate.wait(_SIGNAL_TIMEOUT_MS / 1000)
        return {}

    runner = ThreadedRunner()
    runner.run(_gated_task, lambda _r: None, lambda _m: None)

    # Snapshot the live threads before teardown so we can assert they stop.
    records_before = runner.active_dispatches()
    assert len(records_before) == 1
    threads = [record.thread for record in records_before]

    # Act: release the gate and run the shutdown teardown (quit + wait).
    gate.set()
    runner.await_active(_SIGNAL_TIMEOUT_MS)

    # Assert: every thread that was tracked has stopped running.
    for thread in threads:
        assert thread.isRunning() is False

    # The collection drains as each thread's finished handler removes its record.
    qtbot.waitUntil(
        lambda: len(runner.active_dispatches()) == 0, timeout=_SIGNAL_TIMEOUT_MS
    )


def test_queued_outcome_still_delivers_on_gui_thread(qtbot: QtBot) -> None:
    """Success and error callbacks still run on the GUI thread after the refactor.

    R-AC-7 (d): the existing queued ``_RunnerReceiver`` delivery (AC-6) must be
    preserved. The success path and the error path each record
    ``threading.current_thread()`` and both must equal the GUI thread.
    """
    # Arrange: capture the GUI thread and prepare recorders for both paths.
    gui_thread = threading.current_thread()
    success_threads: list[threading.Thread] = []
    error_threads: list[threading.Thread] = []

    def _ok_task() -> dict[str, pd.DataFrame]:
        return {}

    def _bad_task() -> dict[str, pd.DataFrame]:
        raise ValueError("worker blew up")

    def _on_success(_result: dict[str, pd.DataFrame]) -> None:
        success_threads.append(threading.current_thread())

    def _on_error(_message: str) -> None:
        error_threads.append(threading.current_thread())

    runner = ThreadedRunner()

    # Act: dispatch the success path and wait for delivery on the GUI thread.
    runner.run(_ok_task, _on_success, _on_error)
    qtbot.waitUntil(lambda: len(success_threads) == 1, timeout=_SIGNAL_TIMEOUT_MS)

    # Act: dispatch the error path and wait for delivery on the GUI thread.
    runner.run(_bad_task, _on_success, _on_error)
    qtbot.waitUntil(lambda: len(error_threads) == 1, timeout=_SIGNAL_TIMEOUT_MS)

    # Assert: both callbacks ran on the GUI thread, not a worker thread.
    assert success_threads == [gui_thread]
    assert error_threads == [gui_thread]

    # Cleanup: drain any remaining thread so the test leaks none.
    runner.await_active(_SIGNAL_TIMEOUT_MS)


def test_await_active_drains_repeated_dispatches_without_error(qtbot: QtBot) -> None:
    """Repeated dispatch/drain cycles complete cleanly with an empty collection.

    Exercises the shutdown seam across several sequential dispatches so the
    drain path is run repeatedly. Each cycle must leave the active-dispatch
    collection empty and raise nothing, confirming ``await_active`` is safe to
    call after dispatches have completed.
    """
    # Arrange: a single runner reused across cycles so records accumulate and
    # drain through the public seam.
    runner = ThreadedRunner()

    # Run several dispatch/drain cycles to exercise teardown repeatedly.
    for _ in range(3):
        runner.run(lambda: {}, lambda _r: None, lambda _m: None)
        runner.await_active(_SIGNAL_TIMEOUT_MS)
        qtbot.waitUntil(
            lambda: len(runner.active_dispatches()) == 0, timeout=_SIGNAL_TIMEOUT_MS
        )

    # Assert: after all cycles the collection is empty and teardown never raised.
    assert runner.active_dispatches() == ()
