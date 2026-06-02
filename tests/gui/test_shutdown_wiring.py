"""Tests for :func:`src.gui._shutdown_wiring.wire_shutdown_cleanup`.

Covers R-AC-7 (c) of issue #48: the production shutdown caller must invoke the
runner's ``await_active`` teardown when the application is quitting, and must
degrade to a safe no-op for a runner (the synchronous test seam) that exposes
no ``await_active`` method.

A lightweight ``QObject`` subclass carrying an ``aboutToQuit`` :class:`Signal`
stands in for the real ``QApplication`` quit signal, so the wiring is exercised
without constructing a second application instance. Headless Qt is forced by
``tests/gui/conftest.py`` (QT_QPA_PLATFORM=offscreen).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QObject, Signal

from src.gui._shutdown_wiring import wire_shutdown_cleanup
from src.gui.runners import SynchronousRunner

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

    from src.gui.runners import RunnerProtocol


class _FakeApp(QObject):
    """Minimal ``QApplication`` stand-in exposing an ``aboutToQuit`` signal.

    Purpose:
        Provide a real Qt signal named ``aboutToQuit`` so
        :func:`wire_shutdown_cleanup` can connect to it and the test can emit
        it, without constructing a second ``QApplication`` instance.

    Responsibilities:
        Declare the ``aboutToQuit`` signal only; it holds no application
        behavior.

    Attributes:
        aboutToQuit: Emitted by the test to simulate application shutdown.
    """

    aboutToQuit: Signal = Signal()


class _RecordingRunner:
    """Fake runner whose ``await_active`` records each call.

    Purpose:
        Capture whether (and how often) the shutdown wiring invoked the
        teardown method.

    Responsibilities:
        Implement ``run`` (unused here) and ``await_active``; record the number
        of ``await_active`` invocations.

    Attributes:
        await_active_calls: The count of ``await_active`` invocations.
    """

    def __init__(self) -> None:
        """Initialize with a zero ``await_active`` call count."""
        self.await_active_calls = 0

    def run(self, task: object, on_success: object, on_error: object) -> None:
        """No-op run; this fake only records shutdown teardown calls."""

    def await_active(self, timeout_ms: int = 5000) -> None:
        """Record one shutdown teardown invocation.

        Args:
            timeout_ms: Accepted to match the real signature; unused here.

        Returns:
            ``None``.
        """
        self.await_active_calls += 1


def test_about_to_quit_calls_await_active() -> None:
    """Emitting ``aboutToQuit`` invokes the runner's ``await_active`` once.

    Demonstrates that the production shutdown caller drains the runner's worker
    threads exactly once when the application is quitting (R-AC-7 c).
    """
    # Arrange: a fake app with an aboutToQuit signal and a recording runner.
    app = _FakeApp()
    runner = _RecordingRunner()
    wire_shutdown_cleanup(cast("QApplication", app), cast("RunnerProtocol", runner))

    # Act: simulate application shutdown.
    app.aboutToQuit.emit()

    # Assert: the teardown ran exactly once.
    assert runner.await_active_calls == 1


def test_wire_shutdown_cleanup_noop_for_runner_without_await_active() -> None:
    """A runner without ``await_active`` is wired without error and is a no-op.

    The synchronous test seam (:class:`SynchronousRunner`) spawns no threads and
    exposes no ``await_active``; wiring it and emitting ``aboutToQuit`` must not
    raise (R-AC-7 c degradation path).
    """
    # Arrange: a SynchronousRunner has no await_active method.
    app = _FakeApp()
    runner = SynchronousRunner()
    wire_shutdown_cleanup(cast("QApplication", app), runner)

    # Act + Assert: emitting aboutToQuit is a no-op and raises nothing.
    app.aboutToQuit.emit()
