"""Cross-thread bridge that marshals the KEY-mismatch dialog onto the GUI thread.

This module provides :class:`KeyMismatchBridge`, the seam that lets an off-UI
import worker resolve a diverging source ``KEY`` through a Qt modal without
constructing or showing the dialog on the worker thread. Showing a Qt widget off
the GUI thread is undefined behavior and produces the
``QBasicTimer::stop: Failed. Possibly trying to stop from a different thread``
diagnostic and a crash (issue #52). The bridge mirrors the queued-connection
pattern in :mod:`src.gui.runners`: it is constructed on the GUI thread, and when
``resolve`` is called from a worker thread it marshals the dialog onto the GUI
thread via a ``Qt.ConnectionType.QueuedConnection`` signal and blocks the worker
on a :class:`threading.Event` until the GUI-thread slot stores the result.

Responsibilities:
    - Hold the example-aware ``ask`` callable and the parent window captured on
      the GUI thread.
    - ``resolve``: return the user's boolean choice for a set of example pairs,
      taking a direct same-thread path or a marshaled cross-thread path.

Boundaries:
    - This module performs no disk, network, or database I/O. Its only side
      effect is showing the injected ``ask`` dialog (on the GUI thread) and Qt
      signal delivery.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui.main_window import MainWindow

__all__ = ["KeyMismatchBridge"]


class KeyMismatchBridge(QObject):
    """GUI-thread bridge that resolves a KEY mismatch via a marshaled dialog.

    Purpose:
        Let an off-UI import worker obtain the user's "Keep existing" / "Rebuild"
        choice for a diverging source ``KEY`` by showing the dialog on the GUI
        thread, eliminating the cross-thread Qt widget construction that crashes
        the worker (issue #52).

    Responsibilities:
        Capture the GUI thread, the example-aware ``ask`` callable, and the parent
        window at construction. On :meth:`resolve`, either call ``ask`` directly
        (same-thread guard) or marshal it onto the GUI thread via a queued signal
        and block the worker until the GUI-thread slot returns.

    Usage:
        Constructed once on the GUI thread at the composition root and held by the
        resolver returned from ``build_key_mismatch_resolver``. The resolver calls
        :meth:`resolve` from whichever thread the import runs on.

    Thread-affinity invariant:
        The bridge MUST be constructed on the GUI (application) thread. Its
        ``_request`` signal is connected to the ``_on_request`` slot with a queued
        connection, so emitting the signal from a worker thread delivers the slot
        on the GUI thread's event loop. The bridge is never moved with
        ``moveToThread``.

    Exception-surfacing contract:
        An exception raised while showing the dialog on the GUI thread is NOT
        swallowed: the GUI-thread slot captures it, sets the completion event, and
        :meth:`resolve` re-raises it on the worker side after the event is set.

    Attributes:
        _ask: The example-aware dialog callable ``ask(window, examples) -> bool``.
        _window: The parent window passed to ``ask`` (may be ``None``).
        _gui_thread: The GUI thread captured at construction; the same-thread
            guard compares the current thread against it.
        _result: The most recent boolean dialog result, stored by the slot.
        _error: The most recent ``Exception`` raised by ``ask`` on the GUI
            thread, or ``None``; re-raised on the worker side.
    """

    # Carries the example pairs and the completion event from the worker thread
    # to the GUI-thread slot. Typed as ``object`` because Qt's signal marshaling
    # passes the Python list and threading.Event through unchanged.
    _request = Signal(object, object)

    def __init__(
        self,
        ask: Callable[[MainWindow | None, list[tuple[str, str]]], bool],
        window: MainWindow | None = None,
    ) -> None:
        """Initialize the bridge on the GUI thread and wire the queued slot.

        Args:
            ask: The example-aware dialog callable invoked on the GUI thread; it
                receives the parent window and the example pairs and returns
                ``True`` for "Keep existing" (trust) or ``False`` for "Rebuild"
                (overwrite).
            window: The parent window forwarded to ``ask`` (may be ``None``).

        Side effects:
            Captures the current (GUI) thread as the bridge's affinity and
            connects ``_request`` to ``_on_request`` with a queued connection so a
            worker-thread emit is delivered on the GUI thread.
        """
        super().__init__(window)
        self._ask = ask
        self._window = window
        # Capture the construction thread as the GUI thread; the same-thread guard
        # in resolve() compares against this to choose the direct vs marshaled path.
        self._gui_thread = QThread.currentThread()
        self._result: bool = True
        self._error: Exception | None = None
        # Queued connection so an emit from a worker thread runs the slot on the
        # GUI thread's event loop (the affinity of this QObject), never inline.
        self._request.connect(self._on_request, Qt.ConnectionType.QueuedConnection)

    def resolve(self, examples: list[tuple[str, str]]) -> bool:
        """Return the user's choice for the diverging KEY examples.

        Chooses between a same-thread direct call and a cross-thread marshaled
        call based on the caller's thread.

        Args:
            examples: Up to three ``(existing, rebuilt)`` KEY example pairs to
                show in the dialog.

        Returns:
            ``True`` when the user chose "Keep existing" (trust); ``False`` when
            the user chose "Rebuild" (overwrite).

        Raises:
            Exception: Re-raises, on the worker side, any ``Exception`` the
                ``ask`` dialog raised on the GUI thread (the slot captures it and
                this method re-raises it after the event is set).

        Side effects:
            Shows the ``ask`` dialog on the GUI thread (directly when already on
            the GUI thread, else via a queued signal) and, on the cross-thread
            path, blocks the calling thread until the dialog returns.
        """
        # Same-thread guard: when already on the GUI thread (e.g. under
        # SynchronousRunner or in tests), call ask directly with no event and no
        # blocking, which avoids deadlocking on a thread that must also pump the
        # event loop that would deliver the queued slot.
        if QThread.currentThread() is self._gui_thread:
            return self._ask(self._window, examples)

        # Cross-thread path: hand the examples and a completion event to the
        # GUI-thread slot via the queued signal and block until the slot signals
        # completion. The slot stores either a result or an exception.
        done = threading.Event()
        self._error = None
        self._request.emit(examples, done)
        done.wait()
        # Surface a GUI-thread dialog error on the worker side rather than
        # silently returning a default; the slot never swallows it.
        if self._error is not None:
            raise self._error
        return self._result

    @Slot(object, object)
    def _on_request(
        self, examples: list[tuple[str, str]], done: threading.Event
    ) -> None:
        """Show the dialog on the GUI thread and signal the waiting worker.

        Args:
            examples: The ``(existing, rebuilt)`` KEY example pairs to show.
            done: The completion event the worker is blocked on; set in a
                ``finally`` block so the worker always unblocks.

        Side effects:
            Calls ``ask`` (which shows the modal) and stores the result or the
            raised exception, then sets ``done``. Runs on the GUI thread because
            it is delivered via a queued connection.
        """
        # Capture either the dialog result or its exception; never swallow the
        # exception, so resolve() can re-raise it on the worker side. The event is
        # always set in finally so the worker cannot block forever on an error.
        try:
            self._result = self._ask(self._window, examples)
        except Exception as error:
            self._error = error
        finally:
            done.set()
