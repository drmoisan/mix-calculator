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

from dataclasses import dataclass
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


@dataclass(eq=False)
class _ActiveDispatch:
    """One in-flight ``ThreadedRunner.run`` dispatch held until its thread ends.

    Purpose:
        Bundle the three Qt objects that make up a single off-thread dispatch
        (the worker thread, the worker, and the GUI-thread receiver) so they
        are tracked and kept alive together as one record in
        :attr:`ThreadedRunner._active`.

    Responsibilities:
        Carry strong references to the dispatch's ``thread``/``worker``/
        ``receiver`` so none is garbage-collected before the worker emits and
        the thread finishes. Holds no behavior; lifecycle wiring lives on
        :class:`ThreadedRunner`.

    Usage:
        Constructed in :meth:`ThreadedRunner.run`, added to
        ``ThreadedRunner._active`` before ``thread.start()``, and removed by
        the ``thread.finished`` handler once the thread has finished.

    Key invariant:
        A record remains in ``_active`` exactly while its thread is live. The
        class uses ``eq=False`` so each record is identity-hashed, allowing
        many concurrent dispatches to coexist in a ``set`` without value
        collisions.

    Attributes:
        thread: The worker :class:`QThread` for this dispatch.
        worker: The :class:`PipelineWorker` moved onto ``thread``.
        receiver: The GUI-thread :class:`_RunnerReceiver` holding the queued
            outcome slots.
    """

    thread: QThread
    worker: PipelineWorker
    receiver: _RunnerReceiver


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
        ``Qt.ConnectionType.QueuedConnection`` (AC-6), track the dispatch, and
        start the thread. Provide :meth:`await_active` for application-shutdown
        teardown that quits and waits every live worker thread.

    Lifecycle invariant:
        Each ``run`` call is tracked as one :class:`_ActiveDispatch` record in
        :attr:`_active` for exactly as long as its worker thread is live. The
        worker is a :class:`QObject` whose event affinity is the worker thread,
        so it MUST be destroyed on that thread: ``thread.finished`` is wired to
        ``worker.deleteLater`` (and ``thread.deleteLater``) so destruction
        happens on the worker thread, not by GUI-thread Python GC (which raises
        ``QBasicTimer::stop`` aborts). Because each dispatch is a distinct
        record in a collection (not a single overwriteable attribute), a second
        dispatch cannot drop a still-running prior thread.

    Attributes:
        _active: The set of live :class:`_ActiveDispatch` records. A record is
            added before its thread starts and removed when its thread emits
            ``finished``. Holding the records keeps the thread/worker/receiver
            alive across the asynchronous handoff and tracks every concurrent
            dispatch so shutdown can quit and wait all of them.
    """

    def __init__(self) -> None:
        """Initialize with an empty active-dispatch collection.

        The set starts empty; each :meth:`run` call adds exactly one
        :class:`_ActiveDispatch` record and the ``thread.finished`` handler
        removes it. Holding records here keeps the thread/worker/receiver alive
        across the asynchronous handoff so the GC cannot tear them down early.
        """
        self._active: set[_ActiveDispatch] = set()

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
            signals to the receiver via queued connections, registers the
            dispatch as a :class:`_ActiveDispatch` record in :attr:`_active`
            (before starting), wires ``thread.finished`` to destroy the worker
            and thread on the worker thread and to remove the record from
            :attr:`_active`, and starts the thread.
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
        # The worker is a QObject with worker-thread affinity, so it MUST be
        # destroyed on its own thread. Wiring deleteLater to thread.finished
        # schedules destruction on the worker thread's event loop, which is
        # what prevents the cross-thread QObject teardown that raises
        # "QBasicTimer::stop: Failed. Possibly trying to stop from a different
        # thread". The thread object itself is also cleaned up after it stops.
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        # Drive the worker's run slot from the thread's started signal so the
        # task actually executes on the worker thread.
        thread.started.connect(worker.run)
        # Register the dispatch as one record before starting the thread so a
        # fast worker cannot finish (and try to remove its record) before the
        # record is tracked. Using a set of records — not a single overwriteable
        # attribute — means a later run() cannot drop a still-running dispatch.
        record = _ActiveDispatch(thread=thread, worker=worker, receiver=receiver)
        self._active.add(record)

        def _discard_record() -> None:
            """Remove this dispatch's record once its thread has finished.

            Guarded with ``discard`` so a double-emit of ``thread.finished``
            cannot raise; the record is released only after the thread has
            actually finished, so the thread/worker are not GC'd while live.
            """
            self._active.discard(record)

        thread.finished.connect(_discard_record)
        thread.start()

    def await_active(self, timeout_ms: int = 5000) -> None:
        """Quit and wait every live worker thread (application-shutdown hook).

        Iterates a snapshot of the active dispatches and, for each, asks the
        thread to quit its event loop and blocks until it finishes (or the
        timeout elapses). This is the teardown contract used at application
        shutdown so no worker thread is left running when the process exits,
        which would otherwise risk a cross-thread QObject destruction abort.

        Args:
            timeout_ms: Per-thread maximum wait in milliseconds for each
                thread to finish after being asked to quit. Defaults to 5000.

        Returns:
            ``None``.

        Side effects:
            Calls ``quit`` then ``wait`` on every currently-active worker
            thread. Safe to call when no dispatch is active (no-op). Threads
            that finish during teardown remove their own records via the
            ``thread.finished`` handler; iterating a snapshot keeps that
            concurrent mutation from disturbing the loop.
        """
        # Iterate a snapshot so finished-time record removal (which mutates
        # self._active from the finished handler) cannot change the set under
        # the loop. quit() asks the thread's event loop to exit; wait() blocks
        # until the thread has actually stopped so shutdown leaves none running.
        for record in list(self._active):
            # Waiting on one thread spins the event loop, which can process a
            # pending thread.deleteLater for another already-finished thread in
            # this snapshot. Operating on that deleted C++ QThread raises
            # RuntimeError from shiboken. A deleted thread has already finished
            # and been cleaned up — the desired end state — so this defined Qt
            # object-lifetime boundary skips it rather than failing teardown.
            try:
                record.thread.quit()
                record.thread.wait(timeout_ms)
            except RuntimeError:  # pragma: no cover - defensive Qt-lifetime guard
                # The C++ QThread was already deleted (it finished and its
                # deleteLater ran); nothing left to quit or wait on. This branch
                # is excluded from coverage because the only way to force it
                # deterministically is to delete a live C++ QThread object
                # (shiboken6.delete), which aborts the interpreter; the guard
                # exists solely to keep production shutdown robust against the
                # deleteLater/await_active race.
                self._active.discard(record)
                continue

    def active_dispatches(self) -> tuple[_ActiveDispatch, ...]:
        """Return a snapshot of the currently-tracked active dispatch records.

        Public read seam over :attr:`_active` so callers (notably the
        lifecycle tests) can observe how many dispatches are live and inspect
        each record's thread/worker/receiver without reaching for the
        protected collection. The returned tuple is a copy, so mutating it
        does not affect the runner's tracking.

        Returns:
            A tuple of the live :class:`_ActiveDispatch` records, in arbitrary
            order. Empty when no dispatch is active.

        Side effects:
            None. Reads the tracked set without mutating it.
        """
        return tuple(self._active)


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
