"""Qt tests for :mod:`src.gui.workers.pipeline_worker`.

Runs under ``QT_QPA_PLATFORM=offscreen`` (set by the GUI conftest). Verifies the
success path (the worker moved to a ``QThread`` emits ``finished`` with the task
result) and the failure path (a raising task emits ``error`` with the message).
All waits are event-driven via ``qtbot.waitSignal``; the banned timing APIs
(``time.sleep``, ``QThread.sleep``, ``QTest.qWait``) do not appear. Fabricated
data only; no confidential values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

import pandas as pd
from PySide6.QtCore import QThread

from src.gui.workers.pipeline_worker import PipelineWorker

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


class _SignalBlockerView(Protocol):
    """Typed view of the pytest-qt signal blocker's ``args`` attribute.

    pytest-qt types ``SignalBlocker.args`` loosely (``list[Unknown] | None``),
    so accessing it directly surfaces an unknown member type under Pyright
    strict. Casting the blocker to this view declares ``args`` with a known shape
    so the test reads the emitted payload without a per-call suppression — the
    same typed-view containment pattern used in ``src/pandas_io.py``.
    """

    args: list[object] | None


# A short event-driven wait budget; the deterministic task completes immediately,
# so this only bounds the wait and is never spent idling.
_SIGNAL_TIMEOUT_MS = 5000


def _derived() -> dict[str, pd.DataFrame]:
    """Return a fabricated derived-table result for the success path."""
    return {"mix_rollup_4": pd.DataFrame({"value": [42.0]})}


def test_worker_emits_finished_with_result_on_success(qtbot: QtBot) -> None:
    """A successful task moved to a QThread emits finished with the result."""
    # Arrange: a deterministic task and a worker moved onto its own thread.
    result = _derived()

    def _task() -> dict[str, pd.DataFrame]:
        return result

    thread = QThread()
    worker = PipelineWorker(_task)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)

    # Act / Assert: start the thread and wait (event-driven) for finished.
    try:
        with qtbot.waitSignal(worker.finished, timeout=_SIGNAL_TIMEOUT_MS) as blocker:
            thread.start()
        # The finished signal carries the derived-table dict. Access args through
        # a typed view of the blocker so the loose pytest-qt typing is contained,
        # narrow None, then read the payload (cast is a runtime no-op).
        args = cast("_SignalBlockerView", blocker).args
        assert args is not None
        emitted = cast("dict[str, pd.DataFrame]", args[0])
        assert set(emitted) == {"mix_rollup_4"}
    finally:
        thread.quit()
        thread.wait()


def test_worker_emits_error_with_message_on_failure(qtbot: QtBot) -> None:
    """A raising task emits error with the failure message."""

    # Arrange: a task that raises; the worker must surface it via error.
    def _task() -> dict[str, pd.DataFrame]:
        raise ValueError("pipeline blew up")

    thread = QThread()
    worker = PipelineWorker(_task)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)

    # Act / Assert: wait (event-driven) for the error signal.
    try:
        with qtbot.waitSignal(worker.error, timeout=_SIGNAL_TIMEOUT_MS) as blocker:
            thread.start()
        # Access args through the typed blocker view, narrow None, then read the
        # message payload as its known str type.
        args = cast("_SignalBlockerView", blocker).args
        assert args is not None
        assert cast("str", args[0]) == "pipeline blew up"
    finally:
        thread.quit()
        thread.wait()


def test_run_on_main_thread_emits_finished_with_result() -> None:
    """Calling run directly on the main thread emits finished with the result.

    Exercises the worker's ``run`` body on the main thread so the success path is
    covered deterministically without cross-thread coverage tracing. The signal
    is captured synchronously via a recorder slot.
    """
    # Arrange: record the finished payload via a connected slot.
    result = _derived()
    received: list[dict[str, pd.DataFrame]] = []
    worker = PipelineWorker(lambda: result)
    worker.finished.connect(received.append)

    # Act: run synchronously on the main thread.
    worker.run()

    # Assert: exactly one finished emission carrying the derived dict.
    assert len(received) == 1
    assert set(received[0]) == {"mix_rollup_4"}


def test_run_on_main_thread_emits_error_on_failure() -> None:
    """Calling run directly emits error (not finished) when the task raises.

    Exercises the worker's failure boundary on the main thread for deterministic
    coverage of the ``except`` path.
    """
    # Arrange: a raising task and recorders for both signals.
    errors: list[str] = []
    finished: list[dict[str, pd.DataFrame]] = []

    def _task() -> dict[str, pd.DataFrame]:
        raise ValueError("boom")

    worker = PipelineWorker(_task)
    worker.error.connect(errors.append)
    worker.finished.connect(finished.append)

    # Act
    worker.run()

    # Assert: the error was emitted and finished was not.
    assert errors == ["boom"]
    assert finished == []
