"""Composition-root wiring for off-thread import dispatch.

This helper connects the main window's ``import_one_requested`` and
``import_all_requested`` signals to handlers that build the import tasks on the
pipeline presenter and dispatch them through the injected
:class:`~src.gui.runners.RunnerProtocol`, routing success/error back to the
presenter callbacks. It lives in its own module so ``app.py`` stays under the
repository's 500-line file cap (per ``.claude/rules/general-code-change.md``).

Responsibilities:
    - Disable the relevant import button(s) and raise the busy flag at dispatch
      time so a repeat click cannot launch a second import.
    - Build the import task via the presenter and run it through the runner with
      the matching success/error callbacks (name/spec bound into closures).

The module performs Qt signal wiring only; it holds no domain or transform
logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from src.gui.main_window import MainWindow
    from src.gui.pipeline_service import ImportSpec
    from src.gui.presenters.pipeline_presenter import PipelinePresenter
    from src.gui.runners import RunnerProtocol

__all__ = ["wire_import_dispatch"]

# The three keyed import buttons disabled at import-all dispatch time.
_IMPORT_KEYS = ("LE", "aop", "sku_lu")


def wire_import_dispatch(
    window: MainWindow,
    pipeline_presenter: PipelinePresenter,
    runner: RunnerProtocol,
    current_import_spec: Callable[[MainWindow], ImportSpec],
) -> None:
    """Connect the import-one/import-all signals to runner-dispatched handlers.

    Args:
        window: The shell whose import signals are being wired.
        pipeline_presenter: The presenter that builds the import tasks and
            receives the success/error callbacks.
        runner: The injected runner that executes the import task (off the UI
            thread in production, synchronously in tests).
        current_import_spec: Reads the live per-input file/sheet selection from
            ``window`` into an :class:`ImportSpec` at the moment a signal fires.

    Returns:
        ``None``.

    Side effects:
        Connects ``window.import_one_requested`` and
        ``window.import_all_requested`` to closures that dispatch through
        ``runner``.
    """

    def _handle_import_one(name: str) -> None:
        """Dispatch a per-input import off the UI thread through the runner.

        Per spec section 4: the presenter builds the import task and the runner
        runs it off the UI thread, routing success/error back to the presenter
        callbacks. The keyed button is disabled and busy raised at dispatch so a
        second click cannot double-dispatch.
        """
        spec = current_import_spec(window)
        # Disable the keyed button and raise busy before dispatch so a repeat
        # click cannot launch a second import for the same key.
        pipeline_presenter.view.set_import_button_enabled(name, False)
        pipeline_presenter.set_busy(True)
        task = pipeline_presenter.make_import_one_task(name, spec)

        def _on_success(result: dict[str, pd.DataFrame]) -> None:
            # Bind name/spec captured at dispatch so the success callback records
            # the outcome against the key the user requested.
            pipeline_presenter.on_import_one_success(name, spec, result)

        def _on_error(message: str) -> None:
            # AC6: a failed import must leave the keyed button enabled so the
            # user can retry. The button was disabled at dispatch to prevent
            # double-dispatch, so re-enable it here before routing the error.
            pipeline_presenter.view.set_import_button_enabled(name, True)
            pipeline_presenter.on_import_one_error(message)

        runner.run(task, _on_success, _on_error)

    def _handle_import_all() -> None:
        """Dispatch the import-all off the UI thread through the runner.

        Disables Import All and the three keyed buttons and raises busy at
        dispatch time, then runs the bulk task through the runner with the
        import-all success/error callbacks.
        """
        spec = current_import_spec(window)
        # Disable Import All and the three keyed buttons before dispatch so a
        # repeat click cannot launch a second bulk import.
        window.import_all_btn.setEnabled(False)
        for key in _IMPORT_KEYS:
            pipeline_presenter.view.set_import_button_enabled(key, False)
        pipeline_presenter.set_busy(True)
        task = pipeline_presenter.make_import_all_task(spec)

        def _on_success(result: dict[str, pd.DataFrame]) -> None:
            # Bind the spec captured at dispatch so per-key paths are recorded.
            pipeline_presenter.on_import_all_success(spec, result)

        def _on_error(message: str) -> None:
            # A failed bulk import must leave the buttons enabled so the user can
            # retry; they were disabled at dispatch to prevent double-dispatch.
            window.import_all_btn.setEnabled(True)
            for key in _IMPORT_KEYS:
                pipeline_presenter.view.set_import_button_enabled(key, True)
            pipeline_presenter.on_import_all_error(message)

        runner.run(task, _on_success, _on_error)

    # Connect both import signals to their runner-dispatched handlers.
    window.import_one_requested.connect(_handle_import_one)
    window.import_all_requested.connect(_handle_import_all)
