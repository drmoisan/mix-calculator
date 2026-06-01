"""Runner abstraction for executing pipeline tasks (threaded or synchronous).

This module declares :class:`RunnerProtocol` and provides two implementations:
:class:`ThreadedRunner` (production default, runs the task off the UI thread via
:class:`PipelineWorker` on a :class:`QThread`) and :class:`SynchronousRunner`
(test seam, runs the task on the calling thread). The protocol is the injection
seam used by ``build_application`` so AC-6 dispatch can be exercised
deterministically in tests without relying on Qt's event loop.

Responsibilities:
    - Define ``RunnerProtocol`` with a single ``run`` method that accepts a task
      callable and two outcome callbacks.
    - Provide the off-thread default (:class:`ThreadedRunner`) and the
      deterministic test seam (:class:`SynchronousRunner`).

Boundaries:
    The broad ``except Exception`` in :meth:`SynchronousRunner.run` is the
    runner's failure boundary: any task error is re-routed to ``on_error`` so
    the protocol contract holds for arbitrary task callables. The boundary is
    defined and explicit, not a silent catch-all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from PySide6.QtCore import QObject, Qt, QThread, Slot

from src.gui.workers.pipeline_worker import PipelineWorker

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

__all__ = ["RunnerProtocol", "SynchronousRunner", "ThreadedRunner"]


@runtime_checkable
class RunnerProtocol(Protocol):
    """Contract for dispatching a pipeline task and routing its outcome.

    Purpose:
        Abstract the execution strategy for the run task so the production
        threaded path and a deterministic synchronous test seam share one
        injection point at the composition root.

    Responsibilities:
        Invoke the task on whatever execution context the implementation
        chooses, then call exactly one of ``on_success`` (with the derived
        table dict) or ``on_error`` (with a message string).

    Usage:
        Injected into ``build_application`` (defaulting to
        :class:`ThreadedRunner`) and called by the Run handler with the task
        the presenter builds via ``make_run_task``.
    """

    def run(
        self,
        task: Callable[[], dict[str, pd.DataFrame]],
        on_success: Callable[[dict[str, pd.DataFrame]], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Dispatch ``task`` and route the outcome to one of the callbacks.

        Args:
            task: A zero-argument callable returning the derived-table dict.
            on_success: Called with the derived-table dict on success.
            on_error: Called with the stringified error message on failure.

        Returns:
            ``None``.

        Side effects:
            Invokes the task on the chosen execution context and calls exactly
            one of the two callbacks. Threaded implementations may return
            before either callback fires.
        """
        ...


class _RunnerReceiver(QObject):
    """QObject receiver bound to the GUI thread that dispatches worker outcomes.

    Purpose:
        Translate ``worker.finished`` and ``worker.error`` (emitted on the
        worker thread) into invocations of the user-supplied callbacks on the
        GUI thread. The receiver is constructed on the GUI thread, so its
        event affinity is the GUI thread; connecting the worker signals to
        the receiver's slots with ``Qt.ConnectionType.QueuedConnection`` then
        delivers the outcome via the GUI thread's event loop, eliminating
        cross-thread Qt widget mutation (AC-6).

    Responsibilities:
        Hold references to the two user callbacks and expose them as Qt
        ``Slot`` methods that ``ThreadedRunner.run`` connects to the worker
        signals with a queued connection.

    Usage:
        Constructed once per ``ThreadedRunner.run`` call and held on
        ``ThreadedRunner._receiver`` so it is not garbage-collected before
        the worker emits.

    Thread affinity invariant:
        The receiver MUST be constructed on the GUI (calling) thread. It is
        never moved with ``moveToThread``. This invariant is what gives the
        queued connection its GUI-thread delivery semantics.
    """

    def __init__(
        self,
        on_success: Callable[[dict[str, pd.DataFrame]], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Initialize with the success and error callbacks held by reference."""
        super().__init__()
        # Hold the callbacks as instance attributes so the queued slots can
        # invoke them. No moveToThread call: affinity stays on the GUI thread.
        self._on_success = on_success
        self._on_error = on_error

    @Slot(dict)
    def dispatch_success(self, result: dict[str, pd.DataFrame]) -> None:
        """Invoke the user's success callback on the GUI thread."""
        self._on_success(result)

    @Slot(str)
    def dispatch_error(self, message: str) -> None:
        """Invoke the user's error callback on the GUI thread."""
        self._on_error(message)


class ThreadedRunner:
    """Run the pipeline task on a worker :class:`QThread` (production default).

    Purpose:
        Execute the run task off the UI thread so the GUI stays responsive
        while the pipeline runs; report the outcome through the same callback
        contract as the synchronous seam.

    Responsibilities:
        Construct a :class:`PipelineWorker` for the task, move it to a fresh
        :class:`QThread`, connect ``worker.finished`` / ``worker.error`` to a
        GUI-thread :class:`_RunnerReceiver` via
        ``Qt.ConnectionType.QueuedConnection`` (AC-6), and start the thread.

    Attributes:
        _thread: The active worker thread, or ``None`` before the first run.
        _worker: The active worker, or ``None`` before the first run.
        _receiver: The GUI-thread QObject receiver that holds the queued slots,
            or ``None`` before the first run. Held here so the receiver is not
            garbage-collected before the worker emits.
    """

    def __init__(self) -> None:
        """Initialize with no active thread, worker, or receiver yet."""
        # Hold references to keep the thread/worker/receiver alive across the
        # asynchronous handoff; without these the GC would tear them down.
        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None
        self._receiver: _RunnerReceiver | None = None

    def run(
        self,
        task: Callable[[], dict[str, pd.DataFrame]],
        on_success: Callable[[dict[str, pd.DataFrame]], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Dispatch ``task`` off the UI thread and route the result callbacks.

        AC-6: ``worker.finished`` and ``worker.error`` connect to
        ``_RunnerReceiver`` slots with ``Qt.ConnectionType.QueuedConnection``
        so the outcome callbacks always run on the GUI (calling) thread, not
        on the worker thread. This eliminates cross-thread Qt widget
        mutation, which is a documented native-abort vector that bypasses
        Python exception handling.

        Args:
            task: The zero-argument run task to execute.
            on_success: Called on the GUI thread with the derived-table dict
                when the worker emits ``finished``.
            on_error: Called on the GUI thread with the error message when
                the worker emits ``error``.

        Returns:
            ``None``.

        Side effects:
            Creates a :class:`QThread`, constructs a :class:`PipelineWorker`,
            moves the worker to the thread, constructs a
            :class:`_RunnerReceiver` on the GUI thread, connects the worker
            signals to the receiver via queued connections, and starts the
            thread.
        """
        thread = QThread()
        worker = PipelineWorker(task)
        worker.moveToThread(thread)
        # Construct the receiver on the GUI (calling) thread so its event
        # affinity is the GUI thread; queued connections then deliver outcome
        # invocations through the GUI thread's event loop (AC-6).
        receiver = _RunnerReceiver(on_success, on_error)
        # Wire outcome signals first so a fast worker (already-resolved task)
        # cannot race ahead of the handlers before they are attached. Queued
        # connections are explicit so direct-connection fallback (the
        # cross-thread Qt mutation bug) cannot reappear via a code edit.
        worker.finished.connect(
            receiver.dispatch_success, Qt.ConnectionType.QueuedConnection
        )
        worker.error.connect(
            receiver.dispatch_error, Qt.ConnectionType.QueuedConnection
        )
        # Quit the thread after either terminal signal so it does not linger
        # past the work it was created for. QThread.quit is thread-safe, so a
        # direct connection from the worker thread is acceptable here.
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        # Drive the worker's run slot from the thread's started signal so the
        # task actually executes on the worker thread.
        thread.started.connect(worker.run)
        self._thread = thread
        self._worker = worker
        self._receiver = receiver
        thread.start()


class SynchronousRunner:
    """Run the pipeline task on the calling thread (test seam).

    Purpose:
        Provide a deterministic, in-process execution path so behavioral tests
        can exercise the runner injection without spinning a thread or driving
        the Qt event loop.

    Responsibilities:
        Invoke ``task()`` directly; route a normal return to ``on_success`` and
        any raised exception (including non-``ValueError``) to ``on_error``
        with the stringified message.
    """

    def run(
        self,
        task: Callable[[], dict[str, pd.DataFrame]],
        on_success: Callable[[dict[str, pd.DataFrame]], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Dispatch ``task`` synchronously on the calling thread.

        Args:
            task: The zero-argument run task to execute.
            on_success: Called with the task return value on a normal return.
            on_error: Called with ``str(exc)`` when the task raises.

        Returns:
            ``None``.

        Side effects:
            Invokes the task and calls exactly one of the two callbacks before
            returning. No thread is created.
        """
        # The broad except is the runner's failure boundary: any task error is
        # routed to on_error with the stringified message rather than crashing
        # the caller. This is the documented boundary contract, not a silent
        # catch-all.
        try:
            result = task()
        except Exception as exc:
            on_error(str(exc))
            return
        on_success(result)
