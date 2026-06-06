"""Pytest-qt tests for :class:`src.gui._key_mismatch_bridge.KeyMismatchBridge`.

Covers the cross-thread KEY-mismatch dialog bridge (issue #52, AC-1):
    - the same-thread guard calls the injected ``ask`` directly and returns its
      result without creating a ``threading.Event`` or blocking;
    - the cross-thread path marshals the dialog onto the GUI thread and unblocks
      the worker with the correct result;
    - an exception raised inside ``ask`` on the GUI thread is surfaced (re-raised)
      on the worker side and not swallowed.

The dialog is never a real modal: an ``ask`` stand-in is injected and the Qt
event loop is pumped deterministically with ``qtbot.waitUntil`` (no real
``exec()``, no ``time.sleep``, no temp files). Headless Qt is forced by
``tests/gui/conftest.py`` (QT_QPA_PLATFORM=offscreen).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import pytest

from src.gui._key_mismatch_bridge import KeyMismatchBridge

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

_WAIT_TIMEOUT_MS = 5000

# Representative diverging example pairs passed through the bridge.
_EXAMPLES: list[tuple[str, str]] = [("LEGACY_A", "CustA5GS")]


def test_same_thread_guard_calls_ask_directly_without_event(qtbot: QtBot) -> None:
    """On the GUI thread the bridge calls ask directly and never blocks (AC-1).

    Invoking ``resolve`` from the GUI (calling) thread takes the same-thread
    guard: ``ask`` is called inline and its result returned, with no
    ``threading.Event`` created and no queued-signal round trip.
    """
    # Arrange: an ask stand-in recording the thread it runs on.
    gui_thread = threading.current_thread()
    ask_threads: list[threading.Thread] = []

    def _ask(_window: object, examples: list[tuple[str, str]]) -> bool:
        ask_threads.append(threading.current_thread())
        assert examples == _EXAMPLES
        return True

    bridge = KeyMismatchBridge(_ask)
    # qtbot is required to ensure a QApplication exists for the QObject bridge.
    _ = qtbot

    # Act: resolve on the GUI thread (the same-thread path).
    result = bridge.resolve(_EXAMPLES)

    # Assert: ask ran inline on the GUI thread and its True mapped through.
    assert result is True
    assert ask_threads == [gui_thread]


@pytest.mark.parametrize("ask_result", [True, False])
def test_cross_thread_path_marshals_to_gui_thread(
    qtbot: QtBot, ask_result: bool
) -> None:
    """A worker-thread resolve marshals ask onto the GUI thread and unblocks (AC-1).

    The worker calls ``resolve`` from a separate thread; the bridge marshals
    ``ask`` onto the GUI thread via the queued signal while the worker blocks.
    Pumping the event loop delivers the slot, and the worker receives the
    GUI-thread result.
    """
    # Arrange: record the thread ask runs on and the worker's returned value.
    gui_thread = threading.current_thread()
    ask_threads: list[threading.Thread] = []
    worker_results: list[bool] = []

    def _ask(_window: object, _examples: list[tuple[str, str]]) -> bool:
        ask_threads.append(threading.current_thread())
        return ask_result

    bridge = KeyMismatchBridge(_ask)

    def _worker() -> None:
        worker_results.append(bridge.resolve(_EXAMPLES))

    # Act: run resolve on a worker thread and pump the GUI event loop until the
    # marshaled slot has delivered and the worker has recorded its result.
    worker = threading.Thread(target=_worker)
    worker.start()
    qtbot.waitUntil(lambda: len(worker_results) == 1, timeout=_WAIT_TIMEOUT_MS)
    worker.join(_WAIT_TIMEOUT_MS / 1000)

    # Assert: ask ran on the GUI thread (not the worker) and the result marshaled
    # back to the worker unchanged.
    assert ask_threads == [gui_thread]
    assert worker_results == [ask_result]


def test_cross_thread_exception_is_surfaced_on_worker(qtbot: QtBot) -> None:
    """An ask exception on the GUI thread is re-raised on the worker, not swallowed.

    The GUI-thread slot captures the exception and sets the completion event;
    ``resolve`` then re-raises it on the worker side so the failure is visible
    rather than silently returning a default.
    """
    # Arrange: an ask stand-in that raises on the GUI thread.
    captured: list[BaseException] = []

    def _ask(_window: object, _examples: list[tuple[str, str]]) -> bool:
        raise RuntimeError("dialog blew up on the GUI thread")

    bridge = KeyMismatchBridge(_ask)

    def _worker() -> None:
        # Record the exception re-raised on the worker side so the test can assert
        # it was surfaced rather than swallowed.
        try:
            bridge.resolve(_EXAMPLES)
        except RuntimeError as error:
            captured.append(error)

    # Act: run resolve on a worker thread and pump the event loop until the worker
    # has captured the surfaced exception.
    worker = threading.Thread(target=_worker)
    worker.start()
    qtbot.waitUntil(lambda: len(captured) == 1, timeout=_WAIT_TIMEOUT_MS)
    worker.join(_WAIT_TIMEOUT_MS / 1000)

    # Assert: the GUI-thread dialog error reached the worker unchanged.
    assert len(captured) == 1
    assert str(captured[0]) == "dialog blew up on the GUI thread"
