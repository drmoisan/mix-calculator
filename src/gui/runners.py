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

from PySide6.QtCore import QThread

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


class ThreadedRunner:
    """Run the pipeline task on a worker :class:`QThread` (production default).

    Purpose:
        Execute the run task off the UI thread so the GUI stays responsive
        while the pipeline runs; report the outcome through the same callback
        contract as the synchronous seam.

    Responsibilities:
        Construct a :class:`PipelineWorker` for the task, move it to a fresh
        :class:`QThread`, connect ``worker.finished`` to ``on_success`` and
        ``worker.error`` to ``on_error``, and start the thread.

    Attributes:
        _thread: The active worker thread, or ``None`` before the first run.
        _worker: The active worker, or ``None`` before the first run.
    """

    def __init__(self) -> None:
        """Initialize with no active thread or worker yet."""
        # Hold references to keep the thread/worker alive across the
        # asynchronous handoff; without these the GC would tear them down.
        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None

    def run(
        self,
        task: Callable[[], dict[str, pd.DataFrame]],
        on_success: Callable[[dict[str, pd.DataFrame]], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Dispatch ``task`` off the UI thread and wire its result callbacks.

        Args:
            task: The zero-argument run task to execute.
            on_success: Called on the UI thread with the derived-table dict
                when the worker emits ``finished``.
            on_error: Called on the UI thread with the error message when the
                worker emits ``error``.

        Returns:
            ``None``.

        Side effects:
            Creates a :class:`QThread`, constructs a :class:`PipelineWorker`,
            moves the worker to the thread, connects the outcome signals, and
            starts the thread.
        """
        thread = QThread()
        worker = PipelineWorker(task)
        worker.moveToThread(thread)
        # Wire outcome signals first so a fast worker (already-resolved task)
        # cannot race ahead of the handlers before they are attached.
        worker.finished.connect(on_success)
        worker.error.connect(on_error)
        # Quit the thread after either terminal signal so it does not linger
        # past the work it was created for.
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        # Drive the worker's run slot from the thread's started signal so the
        # task actually executes on the worker thread.
        thread.started.connect(worker.run)
        self._thread = thread
        self._worker = worker
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
