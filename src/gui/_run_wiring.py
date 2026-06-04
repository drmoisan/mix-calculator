"""Composition-root wiring for the off-thread Run dispatch.

This helper connects the main window's ``run_requested`` signal to a handler that
builds the run task on the pipeline presenter and dispatches it through the
injected :class:`~src.gui.runners.RunnerProtocol`, routing success/error back to
the presenter callbacks. It lives in its own module so ``app.py`` stays under the
repository's 500-line file cap (per ``.claude/rules/general-code-change.md``).

Responsibilities:
    - ``wire_run``: connect ``run_requested`` to the runner-dispatched handler.

The module performs Qt signal wiring only; it holds no domain or transform
logic. The Run gate (``can_run``) and the disabled-Run feedback path remain on
the presenter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow
    from src.gui.presenters.pipeline_presenter import PipelinePresenter
    from src.gui.runners import RunnerProtocol

__all__ = ["wire_run"]


def wire_run(
    window: MainWindow,
    pipeline_presenter: PipelinePresenter,
    runner: RunnerProtocol,
) -> None:
    """Connect ``run_requested`` to the runner-dispatched run handler.

    Args:
        window: The shell whose ``run_requested`` signal is being wired.
        pipeline_presenter: The presenter that gates the run, builds the run
            task, and receives the success/error callbacks.
        runner: The injected runner that executes the run task (off the UI
            thread in production, synchronously in tests).

    Returns:
        ``None``.

    Side effects:
        Connects ``window.run_requested`` to a closure that dispatches the run
        task through ``runner``.
    """

    def _handle_run() -> None:
        """Dispatch the run task through the injected runner.

        Per spec section 4 / research Q6: the run task is built by the
        presenter and dispatched off the UI thread by the runner; the runner
        routes success/error back to the presenter callbacks. When the run gate
        is closed, the presenter's ``on_run`` surfaces the disabled-Run feedback
        instead of dispatching.
        """
        # Decision: gate the run first. A closed gate (incomplete imports or a
        # job already running) routes to the presenter's feedback path and never
        # builds or dispatches a task, so a partial import cannot cascade.
        if not pipeline_presenter.can_run():
            pipeline_presenter.on_run()
            return
        task = pipeline_presenter.make_run_task()
        runner.run(
            task,
            pipeline_presenter.on_run_success,
            pipeline_presenter.on_run_error,
        )

    window.run_requested.connect(_handle_run)
