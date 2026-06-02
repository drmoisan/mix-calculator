"""Composition-root wiring for application-shutdown worker-thread teardown.

This helper connects the :class:`~PySide6.QtWidgets.QApplication`
``aboutToQuit`` signal to a closure that drains the injected runner's live
worker threads at shutdown. It lives in its own module so ``app.py`` stays
under the repository's 500-line file cap (per
``.claude/rules/general-code-change.md``) and follows the ``_run_wiring.py`` /
``_schema_list_wiring.py`` sibling-module precedent.

Responsibilities:
    - ``wire_shutdown_cleanup``: connect ``app.aboutToQuit`` to a closure that
      calls ``runner.await_active()`` when the runner exposes it.

The module performs Qt signal wiring only; it holds no domain logic. The
shutdown contract (quit + wait every active worker thread) is implemented on
:class:`~src.gui.runners.ThreadedRunner.await_active`; this module only routes
the application's quit signal to that method so no worker thread is left
running when the process exits (the cross-thread QObject teardown that raises
``QBasicTimer::stop`` on shutdown).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

    from src.gui.runners import RunnerProtocol

__all__ = ["wire_shutdown_cleanup"]


def wire_shutdown_cleanup(app: QApplication, runner: RunnerProtocol) -> None:
    """Connect ``app.aboutToQuit`` to drain the runner's worker threads.

    Wires a closure to the application's ``aboutToQuit`` signal that asks the
    runner to quit and wait every live worker thread before the process exits.
    The teardown only runs when the runner exposes an ``await_active`` method,
    so the synchronous test seam (:class:`~src.gui.runners.SynchronousRunner`),
    which spawns no threads, is wired as a safe no-op rather than raising.

    Args:
        app: The Qt application whose ``aboutToQuit`` signal marks shutdown.
        runner: The injected runner. When it exposes ``await_active`` (the
            :class:`~src.gui.runners.ThreadedRunner` production path), that
            method is invoked on quit; otherwise the connection is a no-op.

    Returns:
        ``None``.

    Side effects:
        Connects ``app.aboutToQuit`` to a closure. The closure, when fired,
        calls ``runner.await_active()`` (quitting and waiting every active
        worker thread) for runners that provide it.
    """

    def _drain_active_threads() -> None:
        """Drain the runner's live worker threads when the app is quitting.

        Guarded with ``getattr`` so a runner without ``await_active`` (the
        synchronous test seam) is a no-op; only the threaded runner needs the
        quit-and-wait teardown.
        """
        # Resolve await_active at call time so a runner lacking it (the
        # synchronous seam, which has no threads) degrades to a no-op instead
        # of raising AttributeError during shutdown.
        await_active = getattr(runner, "await_active", None)
        if callable(await_active):
            await_active()

    app.aboutToQuit.connect(_drain_active_threads)
