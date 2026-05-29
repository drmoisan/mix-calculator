"""Off-UI-thread runner for the mix pipeline (QObject moved to a QThread).

This module provides :class:`PipelineWorker`, a ``QObject`` that runs an injected
task callable when its ``run`` slot is invoked and reports the outcome through Qt
signals. The composition root moves the worker to a ``QThread`` so the pipeline
run does not block the UI thread; the presenter connects to the signals.

Responsibilities:
    - Run the injected task in ``run`` and emit ``finished(result)`` on success
      or ``error(message)`` on failure.

The broad ``except Exception`` in :meth:`run` is a defined worker boundary: a
task failure must be reported to the UI thread via the ``error`` signal (and
logged) rather than crashing the worker thread silently. It re-emits the failure
with context; it does not swallow it.

Pyright note: PySide6 6.11 stubs type ``Signal`` class attributes, ``emit``, and
``connect`` cleanly under strict mode (verified at implementation), so the
signals are declared directly without a typed Protocol wrapper.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

__all__ = ["PipelineWorker"]

logger = logging.getLogger(__name__)


class PipelineWorker(QObject):
    """QObject that runs a pipeline task off the UI thread and signals the result.

    Purpose:
        Execute the injected pipeline task on a worker thread and report success
        or failure to the UI thread through signals.

    Responsibilities:
        Invoke the task in :meth:`run`, emit ``finished`` with the derived-table
        dict on success, and emit ``error`` with the message on failure. It holds
        no pipeline logic; the task callable owns the work.

    Usage:
        Constructed with a zero-argument task, moved to a ``QThread`` at the
        composition root, and started via the thread's ``started`` signal wired
        to :meth:`run`. The presenter connects to ``finished``/``error``.

    Attributes:
        finished: Emitted with the derived-table dict on a successful run.
        error: Emitted with the error message string on a failed run.
        progress: Emitted with a progress message string (reserved for UX).
    """

    finished: Signal = Signal(dict)
    error: Signal = Signal(str)
    progress: Signal = Signal(str)

    def __init__(
        self,
        task: Callable[[], dict[str, pd.DataFrame]],
        parent: QObject | None = None,
    ) -> None:
        """Initialize the worker with the task it will run.

        Args:
            task: A zero-argument callable returning the derived-table dict. It
                is invoked once per :meth:`run` call on the worker thread.
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        self._task = task

    @Slot()
    def run(self) -> None:
        """Run the injected task and emit the result or the error.

        Returns:
            ``None``. Communicates the outcome through the ``finished``/``error``
            signals rather than a return value.

        Side effects:
            Invokes the task and emits exactly one of ``finished`` (with the
            result dict) or ``error`` (with the failure message).
        """
        # The broad except is the worker's failure boundary: any task error is
        # reported to the UI thread via the error signal (and logged), not
        # swallowed. This is the documented boundary, not a silent catch-all.
        try:
            result = self._task()
        except Exception as exc:
            logger.error("Pipeline task failed: %s", exc)
            self.error.emit(str(exc))
            return
        self.finished.emit(result)
