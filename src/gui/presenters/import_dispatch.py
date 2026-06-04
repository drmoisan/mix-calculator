"""Import task-building and completion-callback logic for the pipeline presenter.

This module holds the off-thread import dispatch logic extracted from
:class:`~src.gui.presenters.pipeline_presenter.PipelinePresenter` so the
presenter file stays under the repository's 500-line file cap. It contains no Qt
import and no transform logic; it orchestrates the presenter's working state and
its passive view through a small :class:`ImportDispatchContext` protocol that the
presenter satisfies.

Responsibilities:
    - Build the zero-argument import tasks (one-key and all-keys) that the
      injected ``RunnerProtocol`` invokes off the UI thread.
    - Apply the success and error outcomes on the UI thread: record frames,
      invalidate derived tables, toggle import buttons, recompute Run/Save/
      Export enable states, clear the busy flag, and emit completion messages.

The functions operate on an explicitly-passed context object (the presenter) so
no hidden state lives in this module. Encapsulation is preserved because the
context exposes only the narrow set of state operations these callbacks need.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from src.gui.pipeline_service import ImportSpec, PipelineServiceProtocol
    from src.gui.protocols import PipelineViewProtocol

__all__ = [
    "ImportDispatchContext",
    "build_import_all_task",
    "build_import_one_task",
    "handle_import_all_error",
    "handle_import_all_success",
    "handle_import_one_error",
    "handle_import_one_success",
    "import_one_frame",
    "required_keys_present",
    "resolve_path_for_key",
    "run_import_all_sync",
    "run_import_one_sync",
]

# The three import-table keys the pipeline consumes. Mirrors the presenter's
# private constant so the import-all success path can disable every keyed button.
_IMPORT_KEYS = ("LE", "aop", "sku_lu")


def required_keys_present(
    imported: dict[str, pd.DataFrame],
    derived: dict[str, pd.DataFrame],
    is_running: bool,
) -> bool:
    """Return whether the Run gate is open for the given working state (WS3).

    Pure Run-gate predicate so the gate semantics live in one testable place.
    The gate is open only when the run can complete without a cascading
    ``KeyError`` from a missing import key:

    - All three required import keys (``"LE"``, ``"aop"``, ``"sku_lu"``) are
      present in ``imported`` (a complete fresh import), OR
    - A non-empty ``derived`` set exists (a prior successful run, so a re-run is
      permitted even though the imports may have been cleared),

    AND no pipeline/import job is currently in flight.

    A partial import (one or two keys present) therefore leaves Run disabled, so
    ``run_pipeline`` is never reached with a missing key (issue #48 / WS3,
    AC-5/AC-6).

    Args:
        imported: The in-memory imported frames keyed by table name.
        derived: The derived frames produced by the last successful run.
        is_running: Whether a pipeline or import job is currently in flight.

    Returns:
        ``True`` when all three import keys are present (or a non-empty derived
        set exists) and no job is in flight; ``False`` otherwise.
    """
    # A complete import requires every key the pipeline consumes; a non-empty
    # derived set means a prior run already produced downstream tables, so a
    # re-run is allowed. Either condition, with no in-flight job, opens the gate.
    all_keys_present = all(key in imported for key in _IMPORT_KEYS)
    has_derived = bool(derived)
    return (all_keys_present or has_derived) and not is_running


def resolve_path_for_key(key: str, spec: ImportSpec) -> str:
    """Return the source path the spec carries for an import key.

    Pure key-routing helper shared by the presenter and the import-success
    callbacks so the per-key path resolution lives in one place.

    Args:
        key: ``"LE"``, ``"aop"``, or ``"sku_lu"``.
        spec: The per-input file/sheet selection.

    Returns:
        The path the matching loader reads. For ``"sku_lu"`` an empty
        ``skulu_path`` falls back to the LE path, matching :func:`import_one_frame`.

    Raises:
        KeyError: When ``key`` is not a known import key.
    """
    # Routing table: each import key maps to the spec field its loader reads.
    if key == "LE":
        return spec.le_path
    if key == "aop":
        return spec.aop_path
    if key == "sku_lu":
        return spec.skulu_path if spec.skulu_path else spec.le_path
    raise KeyError(f"Unknown import key {key!r}.")


def import_one_frame(
    service: PipelineServiceProtocol, name: str, spec: ImportSpec
) -> pd.DataFrame:
    """Call the loader for one import key and return its frame.

    Pure key-routing helper shared by the presenter and the one-key task so the
    loader dispatch lives in one place.

    Args:
        service: The pipeline service seam exposing the per-key loaders.
        name: The import key to load.
        spec: The per-input selection supplying paths and sheet names.

    Returns:
        The imported frame for ``name``.

    Raises:
        ValueError: Propagated from the loader.
        KeyError: When ``name`` is not a known import key.
    """
    # Routing table: each import key maps to its loader call. Ordering is not
    # significant; only the matching key's loader runs.
    if name == "LE":
        return service.import_le(spec.le_path, spec.le_sheet)
    if name == "aop":
        return service.import_aop(spec.aop_path, spec.aop_sheet)
    if name == "sku_lu":
        skulu_path = spec.skulu_path if spec.skulu_path else spec.le_path
        return service.import_skulu(skulu_path, spec.skulu_sheet)
    raise KeyError(f"Unknown import key {name!r}.")


class ImportDispatchContext(Protocol):
    """Narrow state surface the import dispatch functions operate on.

    Purpose:
        Decouple the import dispatch logic from the concrete presenter so the
        logic can live in this module while the presenter retains ownership of
        its state. The presenter implements this protocol.

    Responsibilities:
        Expose the view, the service, the two working-state recorders, the
        action-enable recompute, the busy-flag setter, and ``can_run`` so the
        dispatch functions can apply an import outcome without reaching into
        private attributes. Pure key routing lives in the module-level
        :func:`import_one_frame` / :func:`resolve_path_for_key` helpers instead.

    Usage:
        The presenter passes ``self`` to the module functions, which read the
        ``view``/``service`` properties and call the recorder methods. The
        protocol intentionally surfaces protected-style helpers as public on the
        protocol so cross-module access stays type-checked and explicit.
    """

    @property
    def view(self) -> PipelineViewProtocol:
        """Return the passive pipeline view the callbacks update."""
        ...

    @property
    def service(self) -> PipelineServiceProtocol:
        """Return the pipeline service seam the tasks call."""
        ...

    def record_one_import_result(
        self, name: str, spec: ImportSpec, frame: pd.DataFrame
    ) -> None:
        """Record one import's frame, spec, path, and invalidate derived tables."""
        ...

    def record_all_import_result(
        self, spec: ImportSpec, frames: dict[str, pd.DataFrame]
    ) -> None:
        """Record an import-all result and invalidate derived tables."""
        ...

    def push_action_enabled_states(self) -> None:
        """Recompute Save/Export enabled flags from the working-table set."""
        ...

    def set_busy(self, is_running: bool) -> None:
        """Set the busy flag and notify the view."""
        ...

    def can_run(self) -> bool:
        """Return whether Run is permitted (non-empty working set, not busy)."""
        ...


def build_import_one_task(
    context: ImportDispatchContext, name: str, spec: ImportSpec
) -> Callable[[], dict[str, pd.DataFrame]]:
    """Return a zero-argument task that imports one key off the UI thread.

    Args:
        context: The presenter providing the single-key loader.
        name: The import key (``"LE"``, ``"aop"``, or ``"sku_lu"``).
        spec: The per-input file/sheet selection captured for the task.

    Returns:
        A ``Callable[[], dict[str, pd.DataFrame]]`` that loads the keyed frame
        and returns ``{name: frame}``. A loader ``ValueError`` propagates out of
        the callable so the runner routes it to the error callback.
    """

    # Capture name and spec so the returned callable is self-contained for the
    # worker thread; it performs no view updates (the runner's callbacks do).
    def _task() -> dict[str, pd.DataFrame]:
        frame = import_one_frame(context.service, name, spec)
        return {name: frame}

    return _task


def build_import_all_task(
    context: ImportDispatchContext, spec: ImportSpec
) -> Callable[[], dict[str, pd.DataFrame]]:
    """Return a zero-argument task that imports all three keys off the UI thread.

    Args:
        context: The presenter providing the bulk import service.
        spec: The per-input file/sheet selection captured for the task.

    Returns:
        A ``Callable[[], dict[str, pd.DataFrame]]`` that calls
        ``service.import_sources(spec)`` and returns the three-entry dict. A
        service ``ValueError`` propagates out of the callable.
    """

    # Capture the spec so the worker thread can call the bulk loader without
    # touching presenter state until the success callback runs.
    def _task() -> dict[str, pd.DataFrame]:
        return context.service.import_sources(spec)

    return _task


def handle_import_one_success(
    context: ImportDispatchContext,
    name: str,
    spec: ImportSpec,
    result: dict[str, pd.DataFrame],
) -> None:
    """Apply a successful one-key import on the UI thread.

    Args:
        context: The presenter whose state and view are updated.
        name: The import key that completed.
        spec: The spec used for the import (recorded for re-import tracking).
        result: The task result; ``{name: frame}``.

    Returns:
        ``None``.

    Side effects:
        Records the frame, updates the last-imported path, invalidates derived
        tables, disables the keyed import button, recomputes Run/Save/Export
        enable states, clears busy, and emits ``"Imported {name}."``.
    """
    # Record the frame/spec/path and invalidate derived tables in one call so
    # the presenter owns its private state mutation.
    context.record_one_import_result(name, spec, result[name])
    context.view.set_import_button_enabled(name, False)
    # Clear busy before recomputing Run so can_run() observes the idle state
    # (the busy flag is part of the can_run guard).
    context.set_busy(False)
    context.view.set_run_button_enabled(context.can_run())
    context.push_action_enabled_states()
    context.view.show_result(f"Imported {name}.")


def handle_import_one_error(context: ImportDispatchContext, message: str) -> None:
    """Apply a failed one-key import on the UI thread.

    Args:
        context: The presenter whose view is updated.
        message: The error message emitted by the runner.

    Returns:
        ``None``.

    Side effects:
        Clears busy, recomputes the Run button from the WS3 gate so a partial
        import leaves Run disabled (AC-6), then routes the message to
        ``view.show_error`` (busy is cleared first so the status surface ends on
        the error, not the idle clear). The keyed import button is left enabled
        so the user can retry.
    """
    context.set_busy(False)
    # Recompute Run from the gate: a failed import keeps the working set
    # incomplete, so Run stays disabled and the run path cannot cascade (AC-6).
    context.view.set_run_button_enabled(context.can_run())
    context.view.show_error(message)


def handle_import_all_success(
    context: ImportDispatchContext,
    spec: ImportSpec,
    result: dict[str, pd.DataFrame],
) -> None:
    """Apply a successful import-all on the UI thread.

    Args:
        context: The presenter whose state and view are updated.
        spec: The spec used for the import (recorded per key).
        result: The task result; the three-entry frame dict.

    Returns:
        ``None``.

    Side effects:
        Replaces all imported frames, records per-key paths and specs, disables
        the three keyed buttons, invalidates derived tables, recomputes Run/
        Save/Export, clears busy, and emits ``"Imported all 3 sources."``.
    """
    # Record all frames/specs/paths and invalidate derived tables in one call.
    context.record_all_import_result(spec, dict(result))
    # Disable each keyed button so the control row reflects the full import.
    for name in _IMPORT_KEYS:
        context.view.set_import_button_enabled(name, False)
    # Clear busy before recomputing Run so can_run() observes the idle state
    # (the busy flag is part of the can_run guard).
    context.set_busy(False)
    context.view.set_run_button_enabled(context.can_run())
    context.push_action_enabled_states()
    context.view.show_result("Imported all 3 sources.")


def handle_import_all_error(context: ImportDispatchContext, message: str) -> None:
    """Apply a failed import-all on the UI thread.

    Args:
        context: The presenter whose view is updated.
        message: The error message emitted by the runner.

    Returns:
        ``None``.

    Side effects:
        Clears busy, recomputes the Run button from the WS3 gate so a failed
        bulk import leaves Run disabled (AC-6), then routes the message to
        ``view.show_error`` (busy is cleared first so the status surface ends on
        the error, not the idle clear). The prior button states are otherwise
        left in place.
    """
    context.set_busy(False)
    # Recompute Run from the gate so a failed bulk import keeps Run disabled.
    context.view.set_run_button_enabled(context.can_run())
    context.view.show_error(message)


def run_import_one_sync(
    context: ImportDispatchContext, name: str, spec: ImportSpec
) -> None:
    """Run a one-key import inline and route the outcome through the callbacks.

    Retained in-presenter/test path: build the same task the runner would
    dispatch, run it synchronously, and route success/error through the shared
    callbacks so behavior matches the off-thread path.

    Args:
        context: The presenter whose state and view are updated.
        name: The import key (``"LE"``, ``"aop"``, or ``"sku_lu"``).
        spec: The per-input file/sheet selection.

    Returns:
        ``None``.

    Raises:
        KeyError: When ``name`` is not a known import key (genuine misuse is
            not hidden; only a loader ``ValueError`` is caught).

    Side effects:
        Raises the busy flag for the duration of the inline run (mirroring the
        off-thread dispatch), then applies the success callback on success, or
        the error callback (routing to ``show_error`` with the keyed button
        left enabled) on a loader ``ValueError``. Both callbacks clear busy.
    """
    # Bracket busy around the inline run so the synchronous path mirrors the
    # off-thread dispatch (busy True at dispatch, cleared by the callback).
    context.set_busy(True)
    task = build_import_one_task(context, name, spec)
    try:
        result = task()
    except ValueError as error:
        handle_import_one_error(context, str(error))
        return
    handle_import_one_success(context, name, spec, result)


def run_import_all_sync(context: ImportDispatchContext, spec: ImportSpec) -> None:
    """Run an import-all inline and route the outcome through the callbacks.

    Args:
        context: The presenter whose state and view are updated.
        spec: The per-input file/sheet selection.

    Returns:
        ``None``.

    Side effects:
        Raises the busy flag for the duration of the inline run (mirroring the
        off-thread dispatch), then applies the success callback on success, or
        the error callback (routing to ``show_error`` and leaving prior button
        states) on a service ``ValueError``. Both callbacks clear busy.
    """
    # Bracket busy around the inline run so the synchronous path mirrors the
    # off-thread dispatch (busy True at dispatch, cleared by the callback).
    context.set_busy(True)
    task = build_import_all_task(context, spec)
    try:
        result = task()
    except ValueError as error:
        handle_import_all_error(context, str(error))
        return
    handle_import_all_success(context, spec, result)
